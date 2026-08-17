"""Build and run the managed multi-store migration gate during startup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from flask_migrate import upgrade
from sqlalchemy import create_engine

from backend.product_version import CONTRACT_VERSIONS, PRODUCT_VERSION
from backend.storage.migration_coordinator import MigrationCoordinator
from backend.storage.store_migration_adapters import (
    ChromaMigrationAdapter,
    LocalJsonMemoryMigrationAdapter,
    MinIOMigrationAdapter,
    Neo4jMigrationAdapter,
    PostgreSQLMigrationAdapter,
    RedisMigrationAdapter,
    RetainedConfigurationMigrationAdapter,
)
from backend.storage.legacy_sqlite_adoption import (
    LegacyAdoptionError,
    build_sqlite_adoption_plan,
    create_verified_sqlite_recovery_copy,
    import_legacy_objects,
    import_sqlite_rows,
    synchronize_postgresql_sequences,
    write_adoption_receipt,
)
from backend.storage.legacy_neo4j_adoption import import_legacy_neo4j_snapshot
from backend.storage.retained_data import ADOPTION_RECEIPT_RELATIVE_PATH
from extensions import db

ROOT = Path(__file__).resolve().parents[2]
POSTGRESQL_TARGET_REVISION = CONTRACT_VERSIONS["data_plane_schema"]
POSTGRESQL_PROVIDER_DEFAULT_SOURCE_REVISION = "0a1b2c3d4e5f"
SUPPORTED_RUNTIME_MIGRATION_PATHS = {
    (
        "postgresql",
        POSTGRESQL_PROVIDER_DEFAULT_SOURCE_REVISION,
        POSTGRESQL_TARGET_REVISION,
    ),
}
# This revision only substitutes the two retired provider-default identifiers.
# Alembic applies it transactionally and its downgrade restores those identifiers,
# so it is authorized as lossless and does not require a coordinated recovery set.
BACKUP_REQUIRED_RUNTIME_MIGRATION_PATHS: set[tuple[str, str, str]] = set()
MANAGED_STORE_TARGETS = {
    "chroma": "dle.chroma.v1",
    "local_json_memory": "unified-memory.v2",
    "minio": "dle.minio.v1",
    "neo4j": "dle.neo4j.v1",
    "postgresql": POSTGRESQL_TARGET_REVISION,
    "redis": "dle.redis.v1",
    "retained_configuration": "configuration.v1",
}


class RuntimeMigrationResources:
    """Own migration-only clients so startup can close them deterministically."""

    def __init__(self) -> None:
        self._resources: list[Any] = []

    def own(self, resource: Any) -> Any:
        self._resources.append(resource)
        return resource

    def close(self) -> None:
        for resource in reversed(self._resources):
            close = getattr(resource, "close", None)
            dispose = getattr(resource, "dispose", None)
            try:
                if callable(close):
                    close()
                elif callable(dispose):
                    dispose()
            except Exception:  # noqa: BLE001, S112
                # Startup success/failure is determined by the verified migration
                # result. Cleanup failures must not replace its safe reason.
                continue


def _json_object_is_valid(path: Path) -> bool:
    try:
        return path.is_file() and isinstance(
            json.loads(path.read_text(encoding="utf-8")), dict
        )
    except (OSError, ValueError):
        return False


def _retained_configuration_validators(runtime, manager) -> tuple:
    return (
        lambda: _json_object_is_valid(runtime.ownership.identity_path),
        lambda: _json_object_is_valid(manager.lock_path),
        lambda: _json_object_is_valid(manager.vault.path),
    )


def build_managed_migration_coordinator(app, runtime, resources):
    """Construct store-native adapters from supervisor-owned loopback endpoints."""

    manager = app.extensions.get("dle_data_plane_manager")
    if manager is None:
        raise RuntimeError("managed_migration_data_plane_manager_missing")

    settings = manager.connection_settings()
    migration_settings = manager.migration_connection_settings()
    migration_url = str(migration_settings["database_url"])
    app.config["DLE_MIGRATION_DATABASE_URL"] = migration_url

    postgres_engine = resources.own(create_engine(migration_url, pool_pre_ping=True))

    import redis
    from neo4j import GraphDatabase

    from backend.storage.chroma_http import ChromaHttpClient

    redis_client = resources.own(
        redis.Redis.from_url(
            str(settings["redis_url"]),
            socket_connect_timeout=3,
            socket_timeout=3,
        )
    )
    neo4j_driver = resources.own(
        GraphDatabase.driver(
            str(settings["neo4j_uri"]),
            auth=(str(settings["neo4j_user"]), str(settings["neo4j_password"])),
            connection_timeout=3,
        )
    )
    chroma_client = resources.own(
        ChromaHttpClient(
            host=str(settings["chroma_host"]),
            port=int(settings["chroma_port"]),
        )
    )

    with app.app_context():
        from backend.storage.object_store import get_object_store

        object_store = get_object_store()

    adapters = {
        "chroma": ChromaMigrationAdapter(chroma_client),
        "local_json_memory": LocalJsonMemoryMigrationAdapter(
            runtime.runtime_root / "databases" / "memory" / "memory_graph.json"
        ),
        # "minio" is retained as the persisted migration component key for
        # upgrade compatibility. ADR-0010 makes the contract vendor-neutral and
        # selects SeaweedFS for rebuilt installed qualification.
        "minio": MinIOMigrationAdapter(object_store, settings["object_buckets"]),
        "neo4j": Neo4jMigrationAdapter(neo4j_driver),
        "postgresql": PostgreSQLMigrationAdapter(
            postgres_engine,
            lambda target: upgrade(
                directory=str(ROOT / "migrations"),
                revision=target,
            ),
        ),
        "redis": RedisMigrationAdapter(redis_client),
        "retained_configuration": RetainedConfigurationMigrationAdapter(
            runtime.runtime_root / "config" / "migration-version.json",
            validators=_retained_configuration_validators(runtime, manager),
        ),
    }
    return MigrationCoordinator(
        adapters=adapters,
        target_versions=MANAGED_STORE_TARGETS,
        ledger_path=runtime.runtime_root / "migrations" / "migration-ledger.json",
        product_version=str(app.config.get("APP_VERSION", PRODUCT_VERSION)),
        supported_paths=SUPPORTED_RUNTIME_MIGRATION_PATHS,
        backup_required_paths=BACKUP_REQUIRED_RUNTIME_MIGRATION_PATHS,
        backup_verifier=None,
    )


def run_managed_data_plane_migrations(app, runtime) -> dict[str, object]:
    """Run the fail-closed gate and remove migration credentials afterward."""

    resources = RuntimeMigrationResources()
    previous_url = app.config.get("DLE_MIGRATION_DATABASE_URL")
    try:
        with app.app_context():
            coordinator = build_managed_migration_coordinator(app, runtime, resources)
            ledger = coordinator.run()
            sequence_engine = resources.own(
                create_engine(
                    str(app.config["DLE_MIGRATION_DATABASE_URL"]),
                    pool_pre_ping=True,
                )
            )
            synchronized_sequences = synchronize_postgresql_sequences(sequence_engine)
            if synchronized_sequences:
                ledger["postgresql_sequences"] = {
                    "status": "verified",
                    "count": len(synchronized_sequences),
                }
            discovery = app.extensions.get("dle_retained_data_discovery") or {}
            if not discovery.get("requires_adoption"):
                return ledger

            source = runtime.runtime_root / "ukg_database.db"
            plan = build_sqlite_adoption_plan(source, db.engine)
            if not plan["ready"]:
                raise LegacyAdoptionError("retained_sqlite_adoption_plan_blocked")
            recovery_path = (
                runtime.runtime_root
                / "recovery"
                / "retained-data"
                / f"ukg-database-{plan['source_sha256'][:16]}.sqlite3"
            )
            backup = create_verified_sqlite_recovery_copy(source, recovery_path)
            with app.app_context():
                from backend.storage.object_store import get_object_store

                objects = import_legacy_objects(
                    runtime.runtime_root / "databases" / "objects",
                    get_object_store(),
                )
            from neo4j import GraphDatabase

            settings = app.extensions["dle_data_plane_manager"].connection_settings()
            legacy_graph_driver = GraphDatabase.driver(
                str(settings["neo4j_uri"]),
                auth=(str(settings["neo4j_user"]), str(settings["neo4j_password"])),
                connection_timeout=3,
            )
            try:
                graph = import_legacy_neo4j_snapshot(
                    runtime.runtime_root
                    / "recovery"
                    / "retained-data"
                    / "legacy-neo4j.snapshot.json",
                    legacy_graph_driver,
                )
            finally:
                legacy_graph_driver.close()
            imported_tables = import_sqlite_rows(
                source,
                db.engine,
                plan=plan,
            )
            write_adoption_receipt(
                runtime.runtime_root / ADOPTION_RECEIPT_RELATIVE_PATH,
                {
                    "target_version": str(app.config.get("APP_VERSION", PRODUCT_VERSION)),
                    "source_sha256": plan["source_sha256"],
                    "backup_sha256": backup["sha256"],
                    "tables": imported_tables,
                    "objects": objects,
                    "graph": graph,
                },
            )
            ledger["retained_data_adoption"] = {
                "status": "verified",
                "source_version": plan["source_version"],
                "tables": imported_tables,
                "object_count": objects["object_count"],
                "graph_node_count": graph["node_count"],
                "graph_relationship_count": graph["relationship_count"],
                "backup_sha256": backup["sha256"],
            }
            return ledger
    finally:
        resources.close()
        if previous_url is None:
            app.config.pop("DLE_MIGRATION_DATABASE_URL", None)
        else:
            app.config["DLE_MIGRATION_DATABASE_URL"] = previous_url

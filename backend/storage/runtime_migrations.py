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


ROOT = Path(__file__).resolve().parents[2]
POSTGRESQL_TARGET_REVISION = CONTRACT_VERSIONS["data_plane_schema"]
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
            except Exception:
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

    postgres_engine = resources.own(
        create_engine(migration_url, pool_pre_ping=True)
    )

    import chromadb
    import redis
    from neo4j import GraphDatabase

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
        chromadb.HttpClient(
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
        # The product authority remains MinIO. The currently locked SeaweedFS
        # artifact is qualification-only and does not change this contract.
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
        supported_paths=set(),
        backup_verifier=None,
    )


def run_managed_data_plane_migrations(app, runtime) -> dict[str, object]:
    """Run the fail-closed gate and remove migration credentials afterward."""

    resources = RuntimeMigrationResources()
    previous_url = app.config.get("DLE_MIGRATION_DATABASE_URL")
    try:
        with app.app_context():
            coordinator = build_managed_migration_coordinator(app, runtime, resources)
            return coordinator.run()
    finally:
        resources.close()
        if previous_url is None:
            app.config.pop("DLE_MIGRATION_DATABASE_URL", None)
        else:
            app.config["DLE_MIGRATION_DATABASE_URL"] = previous_url

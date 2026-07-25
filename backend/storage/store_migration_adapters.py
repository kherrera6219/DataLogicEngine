"""Store-native version adapters used by the Phase 4 migration coordinator."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, text

from backend.storage.chroma_security import (
    safe_get_collection,
    safe_get_or_create_collection,
)


class StoreMigrationError(RuntimeError):
    """Safely reportable store migration adapter failure."""


class PostgreSQLMigrationAdapter:
    def __init__(self, engine, upgrade_callback: Callable[[str], None]):
        self.engine = engine
        self.upgrade_callback = upgrade_callback

    def probe_version(self) -> str | None:
        inspector = inspect(self.engine)
        if "alembic_version" not in inspector.get_table_names():
            return None
        with self.engine.connect() as connection:
            rows = (
                connection.execute(text("SELECT version_num FROM alembic_version"))
                .scalars()
                .all()
            )
        if len(rows) != 1:
            raise StoreMigrationError("postgresql_alembic_version_count_invalid")
        return str(rows[0])

    def is_empty(self) -> bool:
        tables = set(inspect(self.engine).get_table_names())
        return not (tables - {"alembic_version"})

    def bootstrap(self, target_version: str) -> None:
        if not self.is_empty():
            raise StoreMigrationError("postgresql_bootstrap_requires_empty_database")
        self.upgrade_callback(target_version)

    def migrate(self, current_version: str, target_version: str) -> None:
        if self.probe_version() != current_version:
            raise StoreMigrationError("postgresql_source_version_changed")
        self.upgrade_callback(target_version)


class RedisMigrationAdapter:
    VERSION_KEY = "dle:schema:redis"

    def __init__(self, client):
        self.client = client

    def probe_version(self) -> str | None:
        value = self.client.get(self.VERSION_KEY)
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return str(value)

    def is_empty(self) -> bool:
        return int(self.client.dbsize()) == 0

    def bootstrap(self, target_version: str) -> None:
        if not self.is_empty():
            raise StoreMigrationError("redis_bootstrap_requires_empty_database")
        created = self.client.set(self.VERSION_KEY, target_version, nx=True)
        if not created:
            raise StoreMigrationError("redis_version_bootstrap_conflict")

    def migrate(self, current_version: str, target_version: str) -> None:
        raise StoreMigrationError(
            f"redis_migration_path_not_implemented:{current_version}:{target_version}"
        )


class Neo4jMigrationAdapter:
    def __init__(self, driver):
        self.driver = driver

    def probe_version(self) -> str | None:
        with self.driver.session() as session:
            record = session.run(
                "MATCH (v:DLESchemaVersion {component: $component}) "
                "RETURN v.version AS version",
                component="neo4j",
            ).single()
        return str(record["version"]) if record and record.get("version") else None

    def is_empty(self) -> bool:
        with self.driver.session() as session:
            record = session.run("MATCH (n) RETURN count(n) AS count").single()
        return int(record["count"] if record else 0) == 0

    def bootstrap(self, target_version: str) -> None:
        if not self.is_empty():
            raise StoreMigrationError("neo4j_bootstrap_requires_empty_database")
        with self.driver.session() as session:
            session.run(
                "CREATE (v:DLESchemaVersion {component: $component, version: $version, "
                "updated_at: $updated_at})",
                component="neo4j",
                version=target_version,
                updated_at=datetime.now(UTC).isoformat(),
            ).consume()

    def migrate(self, current_version: str, target_version: str) -> None:
        raise StoreMigrationError(
            f"neo4j_migration_path_not_implemented:{current_version}:{target_version}"
        )


class ChromaMigrationAdapter:
    REGISTRY_COLLECTION = "dle_schema_registry"

    def __init__(self, client):
        self.client = client

    def _collection_names(self) -> set[str]:
        names: set[str] = set()
        for item in self.client.list_collections():
            names.add(str(item if isinstance(item, str) else item.name))
        return names

    def probe_version(self) -> str | None:
        if self.REGISTRY_COLLECTION not in self._collection_names():
            return None
        collection = safe_get_collection(
            self.client,
            name=self.REGISTRY_COLLECTION,
        )
        metadata = getattr(collection, "metadata", None) or {}
        value = metadata.get("schema_version")
        return str(value) if value else None

    def is_empty(self) -> bool:
        return not self._collection_names()

    def bootstrap(self, target_version: str) -> None:
        if not self.is_empty():
            raise StoreMigrationError("chroma_bootstrap_requires_empty_database")
        safe_get_or_create_collection(
            self.client,
            name=self.REGISTRY_COLLECTION,
            metadata={
                "schema_version": target_version,
                "source_revision_contract": "required",
            },
        )

    def migrate(self, current_version: str, target_version: str) -> None:
        raise StoreMigrationError(
            f"chroma_migration_path_not_implemented:{current_version}:{target_version}"
        )


class MinIOMigrationAdapter:
    """Version the vendor-neutral S3 object contract through ObjectStore.

    The class and stored schema key retain their legacy names so existing
    installations can be upgraded without silently changing persisted identity.
    """

    VERSION_BUCKET = "audit-logs"
    VERSION_KEY = "_system/data-plane-schema.json"

    def __init__(self, store, buckets: Iterable[str]):
        self.store = store
        self.buckets = tuple(str(bucket) for bucket in buckets)

    def probe_version(self) -> str | None:
        if not self.store.exists(self.VERSION_BUCKET, self.VERSION_KEY):
            return None
        try:
            payload = json.loads(
                self.store.get(self.VERSION_BUCKET, self.VERSION_KEY).decode("utf-8")
            )
        except (AttributeError, UnicodeDecodeError, ValueError) as exc:
            raise StoreMigrationError("minio_schema_manifest_invalid") from exc
        value = payload.get("schema_version") if isinstance(payload, dict) else None
        return str(value) if value else None

    def is_empty(self) -> bool:
        for bucket in self.buckets:
            for item in self.store.list(bucket):
                key = str(getattr(item, "key", "") or "")
                if not (bucket == self.VERSION_BUCKET and key == self.VERSION_KEY):
                    return False
        return True

    def bootstrap(self, target_version: str) -> None:
        if not self.is_empty():
            raise StoreMigrationError("minio_bootstrap_requires_empty_buckets")
        if not self.store.create_bucket(self.VERSION_BUCKET):
            raise StoreMigrationError("minio_schema_bucket_unavailable")
        payload = json.dumps(
            {
                "schema_version": target_version,
                "object_store_architecture": "app_owned_s3_compatible",
                "seaweedfs_production_selected": True,
                "object_store_production_approved": False,
            },
            sort_keys=True,
        ).encode("utf-8")
        self.store.put(
            self.VERSION_BUCKET,
            self.VERSION_KEY,
            payload,
            content_type="application/json",
            metadata={"artifact_type": "data_plane_schema"},
        )

    def migrate(self, current_version: str, target_version: str) -> None:
        raise StoreMigrationError(
            f"minio_migration_path_not_implemented:{current_version}:{target_version}"
        )


class LocalJsonMemoryMigrationAdapter:
    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()

    def _payload(self) -> dict[str, Any] | None:
        if not self.path.exists() or not self.path.read_text(encoding="utf-8").strip():
            return None
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise StoreMigrationError("local_json_memory_invalid") from exc
        if not isinstance(payload, dict):
            raise StoreMigrationError("local_json_memory_invalid")
        return payload

    def probe_version(self) -> str | None:
        payload = self._payload()
        if payload is None or payload.get("version") is None:
            return None
        version = str(payload["version"])
        return (
            version
            if version.startswith("unified-memory.v")
            else f"unified-memory.v{version}"
        )

    def is_empty(self) -> bool:
        return self._payload() is None

    def bootstrap(self, target_version: str) -> None:
        if not self.is_empty():
            raise StoreMigrationError("local_json_memory_bootstrap_requires_empty_file")
        try:
            version = int(target_version.rsplit(".v", 1)[1])
        except (IndexError, ValueError) as exc:
            raise StoreMigrationError("local_json_memory_target_invalid") from exc
        payload = {
            "version": version,
            "saved_at": datetime.now(UTC).isoformat(),
            "last_recall_timestamp": None,
            "vertices": [],
            "edges": [],
        }
        if version >= 2:
            payload["integrity_sha256"] = self._integrity(payload)
        self._atomic_write(payload)

    def migrate(self, current_version: str, target_version: str) -> None:
        if (
            current_version != "unified-memory.v1"
            or target_version != "unified-memory.v2"
        ):
            raise StoreMigrationError(
                f"local_json_memory_migration_path_not_implemented:{current_version}:{target_version}"
            )
        payload = self._payload()
        if payload is None or payload.get("version") != 1:
            raise StoreMigrationError("local_json_memory_v1_source_invalid")
        for vertex in payload.get("vertices", []):
            if not isinstance(vertex, dict):
                continue
            metadata = (
                vertex.get("metadata")
                if isinstance(vertex.get("metadata"), dict)
                else {}
            )
            metadata.setdefault("validation_state", "working")
            metadata.setdefault("policy_result", "legacy_working_only")
            metadata.setdefault("retention_class", "session_working_memory")
            metadata.setdefault("source_run_id", None)
            vertex["metadata"] = metadata
        payload["version"] = 2
        payload["saved_at"] = datetime.now(UTC).isoformat()
        payload["integrity_sha256"] = self._integrity(payload)
        self._atomic_write(payload)

    @staticmethod
    def _integrity(payload: dict[str, Any]) -> str:
        canonical = dict(payload)
        canonical.pop("integrity_sha256", None)
        return hashlib.sha256(
            json.dumps(
                canonical, sort_keys=True, separators=(",", ":"), default=str
            ).encode("utf-8")
        ).hexdigest()

    def _atomic_write(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(payload, sort_keys=True, indent=2) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)


class RetainedConfigurationMigrationAdapter:
    def __init__(
        self,
        marker_path: str | Path,
        validators: Iterable[Callable[[], bool]],
    ) -> None:
        self.marker_path = Path(marker_path).resolve()
        self.validators = tuple(validators)

    def probe_version(self) -> str | None:
        if not self.marker_path.exists():
            return None
        try:
            payload = json.loads(self.marker_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise StoreMigrationError("retained_configuration_marker_invalid") from exc
        value = payload.get("schema_version") if isinstance(payload, dict) else None
        return str(value) if value else None

    def is_empty(self) -> bool:
        try:
            return all(bool(validator()) for validator in self.validators)
        except Exception as exc:
            raise StoreMigrationError(
                "retained_configuration_validation_failed"
            ) from exc

    def bootstrap(self, target_version: str) -> None:
        if not self.is_empty():
            raise StoreMigrationError("retained_configuration_incompatible")
        self.marker_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.marker_path.with_suffix(self.marker_path.suffix + ".tmp")
        payload = {
            "schema_version": target_version,
            "validated_at": datetime.now(UTC).isoformat(),
        }
        try:
            temporary.write_text(
                json.dumps(payload, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            os.replace(temporary, self.marker_path)
        finally:
            temporary.unlink(missing_ok=True)

    def migrate(self, current_version: str, target_version: str) -> None:
        raise StoreMigrationError(
            f"retained_configuration_migration_path_not_implemented:{current_version}:{target_version}"
        )

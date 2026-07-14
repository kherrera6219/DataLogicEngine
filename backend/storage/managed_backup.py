"""Store-native adapters for the supervised six-component recovery set."""

from __future__ import annotations

import base64
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Any

from backend.storage.coordinated_backup import (
    BackupComponent,
    CoordinatedBackupCoordinator,
    CoordinatedBackupError,
)
from backend.storage.object_snapshot import export_bucket, restore_bucket, verify_snapshot


MANAGED_BACKUP_COMPONENTS = (
    "postgresql",
    "redis",
    "neo4j",
    "chroma",
    "minio",
    "retained",
)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "tolist"):
        return _json_safe(value.tolist())
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, bytes):
        return {"base64": base64.b64encode(value).decode("ascii")}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


class _ManagedAdapter:
    """Shared restore result handling for store-native adapters."""

    _restore_result: dict[str, Any] | None = None

    def _verified_result(self, component: BackupComponent) -> dict[str, Any]:
        result = dict(self._restore_result or {})
        if result.get("status") != "pass":
            return {"status": "fail", "safe_reason": "managed_restore_not_completed"}
        if int(result.get("item_count", -1)) != int(component.item_count):
            return {"status": "fail", "safe_reason": "managed_restore_count_mismatch"}
        return result


class PostgreSQLDumpBackupAdapter(_ManagedAdapter):
    def __init__(self, manager, service_version: str, schema_version: str, outstanding: int):
        self.manager = manager
        self.service_version = service_version
        self.schema_version = schema_version
        self.outstanding = int(outstanding)

    def export(self, destination: Path) -> BackupComponent:
        dump = destination / "datalogic.pg_dump"
        self.manager.export_postgresql_logical_backup(dump)
        return BackupComponent(
            name="postgresql",
            schema_version=self.schema_version,
            service_version=self.service_version,
            source_revision=self.schema_version,
            item_count=1,
            logical_size_bytes=dump.stat().st_size,
            outstanding_work=self.outstanding,
        )

    def restore(self, source: Path, _isolated_root: Path) -> None:
        result = dict(
            self.manager.restore_postgresql_logical_backup(source / "datalogic.pg_dump")
        )
        result.update({"status": "pass", "item_count": 1})
        self._restore_result = result

    def verify_restore(self, _isolated_root: Path, component: BackupComponent):
        result = self._verified_result(component)
        if result.get("status") != "pass":
            return result
        if str(result.get("schema_revision") or "") != component.schema_version:
            return {"status": "fail", "safe_reason": "postgresql_restore_schema_mismatch"}
        return result


class RedisDurableExportAdapter(_ManagedAdapter):
    DISPOSABLE_PREFIXES = (b"cache:", b"rate:", b"limiter:", b"session:")

    def __init__(self, client, service_version: str, schema_version: str):
        self.client = client
        self.service_version = service_version
        self.schema_version = schema_version

    def export(self, destination: Path) -> BackupComponent:
        path = destination / "redis-durable.jsonl"
        item_count = 0
        logical_size = 0
        disposable: list[str] = []
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for key in sorted(self.client.scan_iter(match="*")):
                key_bytes = key if isinstance(key, bytes) else str(key).encode("utf-8")
                if key_bytes.startswith(self.DISPOSABLE_PREFIXES):
                    disposable.append(key_bytes.decode("utf-8", errors="replace"))
                    continue
                dumped = self.client.dump(key)
                if dumped is None:
                    continue
                dumped_bytes = dumped if isinstance(dumped, bytes) else bytes(dumped)
                record = {
                    "key_base64": base64.b64encode(key_bytes).decode("ascii"),
                    "dump_base64": base64.b64encode(dumped_bytes).decode("ascii"),
                    "pttl": int(self.client.pttl(key)),
                    "type": (
                        self.client.type(key).decode("ascii")
                        if isinstance(self.client.type(key), bytes)
                        else str(self.client.type(key))
                    ),
                }
                handle.write(json.dumps(record, sort_keys=True) + "\n")
                item_count += 1
                logical_size += len(key_bytes) + len(dumped_bytes)
        return BackupComponent(
            name="redis",
            schema_version=self.schema_version,
            service_version=self.service_version,
            source_revision=self.schema_version,
            item_count=item_count,
            logical_size_bytes=logical_size,
            disposable_state=tuple(sorted(disposable)),
        )

    def restore(self, source: Path, _isolated_root: Path) -> None:
        path = source / "redis-durable.jsonl"
        if not path.is_file():
            raise CoordinatedBackupError("redis_restore_export_missing")
        existing = list(self.client.scan_iter(match="*"))
        if existing:
            raise CoordinatedBackupError("redis_restore_target_not_empty")
        restored = 0
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                record = json.loads(line)
                key = base64.b64decode(record["key_base64"], validate=True)
                dumped = base64.b64decode(record["dump_base64"], validate=True)
                ttl = int(record.get("pttl", -1))
                if not self.client.restore(key, ttl if ttl > 0 else 0, dumped, replace=False):
                    raise CoordinatedBackupError("redis_restore_key_failed")
                restored += 1
        except CoordinatedBackupError:
            raise
        except Exception as exc:
            raise CoordinatedBackupError("redis_restore_export_invalid") from exc
        self._restore_result = {"status": "pass", "item_count": restored}

    def verify_restore(self, _isolated_root: Path, component: BackupComponent):
        result = self._verified_result(component)
        if result.get("status") != "pass":
            return result
        if any(
            (key if isinstance(key, bytes) else str(key).encode()).startswith(
                self.DISPOSABLE_PREFIXES
            )
            for key in self.client.scan_iter(match="*")
        ):
            return {"status": "fail", "safe_reason": "redis_disposable_state_restored"}
        version = self.client.get("dle:schema:redis")
        if isinstance(version, bytes):
            version = version.decode("utf-8")
        if str(version or "") != component.schema_version:
            return {"status": "fail", "safe_reason": "redis_restore_schema_mismatch"}
        return result


class Neo4jLogicalBackupAdapter(_ManagedAdapter):
    def __init__(self, driver, service_version: str, schema_version: str):
        self.driver = driver
        self.service_version = service_version
        self.schema_version = schema_version

    def export(self, destination: Path) -> BackupComponent:
        with self.driver.session() as session:
            nodes = [
                dict(record)
                for record in session.run(
                    "MATCH (n) RETURN elementId(n) AS backup_id, labels(n) AS labels, "
                    "properties(n) AS properties ORDER BY elementId(n)"
                )
            ]
            relationships = [
                dict(record)
                for record in session.run(
                    "MATCH (a)-[r]->(b) RETURN elementId(r) AS backup_id, "
                    "elementId(a) AS source_backup_id, elementId(b) AS target_backup_id, "
                    "type(r) AS relationship_type, properties(r) AS properties "
                    "ORDER BY elementId(r)"
                )
            ]
            constraints = [dict(record) for record in session.run("SHOW CONSTRAINTS")]
            indexes = [dict(record) for record in session.run("SHOW INDEXES")]
        payload = _json_safe(
            {
                "nodes": nodes,
                "relationships": relationships,
                "constraints": constraints,
                "indexes": indexes,
            }
        )
        path = destination / "neo4j-logical.json"
        path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        return BackupComponent(
            name="neo4j",
            schema_version=self.schema_version,
            service_version=self.service_version,
            source_revision=self.schema_version,
            item_count=len(nodes) + len(relationships),
            logical_size_bytes=path.stat().st_size,
        )

    @staticmethod
    def _identifier(value: str) -> str:
        candidate = str(value)
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", candidate):
            raise CoordinatedBackupError("neo4j_restore_identifier_invalid")
        return candidate

    @staticmethod
    def _schema_statement(value: object) -> str:
        statement = str(value or "").strip().rstrip(";")
        normalized = " ".join(statement.upper().split())
        if not normalized.startswith(("CREATE CONSTRAINT ", "CREATE INDEX ", "CREATE LOOKUP INDEX ", "CREATE FULLTEXT INDEX ", "CREATE POINT INDEX ", "CREATE RANGE INDEX ", "CREATE TEXT INDEX ", "CREATE VECTOR INDEX ")):
            raise CoordinatedBackupError("neo4j_restore_schema_statement_invalid")
        return statement

    def restore(self, source: Path, _isolated_root: Path) -> None:
        path = source / "neo4j-logical.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            nodes = list(payload["nodes"])
            relationships = list(payload["relationships"])
            constraints = list(payload.get("constraints") or [])
            indexes = list(payload.get("indexes") or [])
        except (OSError, TypeError, ValueError, KeyError) as exc:
            raise CoordinatedBackupError("neo4j_restore_export_invalid") from exc
        with self.driver.session() as session:
            existing = session.run("MATCH (n) RETURN count(n) AS count").single()
            if existing and int(existing["count"]) != 0:
                raise CoordinatedBackupError("neo4j_restore_target_not_empty")
            for node in nodes:
                labels = [self._identifier(value) for value in node.get("labels") or []]
                label_clause = "".join(f":`{label}`" for label in labels)
                session.run(
                    f"CREATE (n{label_clause}) SET n = $properties "
                    "SET n.__dle_restore_backup_id = $backup_id",
                    properties=dict(node.get("properties") or {}),
                    backup_id=str(node["backup_id"]),
                )
            for relationship in relationships:
                relationship_type = self._identifier(relationship["relationship_type"])
                session.run(
                    "MATCH (a {__dle_restore_backup_id: $source_backup_id}), "
                    "(b {__dle_restore_backup_id: $target_backup_id}) "
                    f"CREATE (a)-[r:`{relationship_type}`]->(b) SET r = $properties",
                    source_backup_id=str(relationship["source_backup_id"]),
                    target_backup_id=str(relationship["target_backup_id"]),
                    properties=dict(relationship.get("properties") or {}),
                )
            session.run("MATCH (n) REMOVE n.__dle_restore_backup_id")
            restored_schema = 0
            for record in [*constraints, *indexes]:
                create_statement = record.get("createStatement")
                if not create_statement:
                    continue
                session.run(self._schema_statement(create_statement)).consume()
                restored_schema += 1
        self._restore_result = {
            "status": "pass",
            "item_count": len(nodes) + len(relationships),
            "source_schema_items": len(constraints) + len(indexes),
            "restored_schema_statements": restored_schema,
        }

    def verify_restore(self, _isolated_root: Path, component: BackupComponent):
        result = self._verified_result(component)
        if result.get("status") != "pass":
            return result
        with self.driver.session() as session:
            nodes = session.run("MATCH (n) RETURN count(n) AS count").single()
            relationships = session.run(
                "MATCH ()-[r]->() RETURN count(r) AS count"
            ).single()
        observed = int(nodes["count"] if nodes else 0) + int(
            relationships["count"] if relationships else 0
        )
        if observed != component.item_count:
            return {"status": "fail", "safe_reason": "neo4j_restore_count_mismatch"}
        with self.driver.session() as session:
            version = session.run(
                "MATCH (v:DLESchemaVersion {component: $component}) "
                "RETURN v.version AS version",
                component="neo4j",
            ).single()
        if not version or str(version.get("version") or "") != component.schema_version:
            return {"status": "fail", "safe_reason": "neo4j_restore_schema_mismatch"}
        with self.driver.session() as session:
            constraint_count = len(list(session.run("SHOW CONSTRAINTS")))
            index_count = len(list(session.run("SHOW INDEXES")))
        if constraint_count + index_count != int(result.get("source_schema_items") or 0):
            return {"status": "fail", "safe_reason": "neo4j_restore_schema_count_mismatch"}
        return result


class ChromaCollectionBackupAdapter(_ManagedAdapter):
    PAGE_SIZE = 500

    def __init__(self, client, service_version: str, schema_version: str):
        self.client = client
        self.service_version = service_version
        self.schema_version = schema_version

    def export(self, destination: Path) -> BackupComponent:
        manifest: list[dict[str, Any]] = []
        item_count = 0
        logical_size = 0
        collections = sorted(
            self.client.list_collections(),
            key=lambda item: str(item if isinstance(item, str) else item.name),
        )
        for listed in collections:
            name = str(listed if isinstance(listed, str) else listed.name)
            collection = self.client.get_collection(name=name)
            collection_dir = destination / hashlib.sha256(name.encode()).hexdigest()[:24]
            collection_dir.mkdir()
            pages = 0
            count = int(collection.count())
            for offset in range(0, count, self.PAGE_SIZE):
                page = collection.get(
                    offset=offset,
                    limit=self.PAGE_SIZE,
                    include=["documents", "embeddings", "metadatas", "uris"],
                )
                page_path = collection_dir / f"page-{pages:08d}.json"
                page_path.write_text(
                    json.dumps(_json_safe(page), sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                logical_size += page_path.stat().st_size
                pages += 1
            manifest.append(
                {
                    "name": name,
                    "metadata": _json_safe(getattr(collection, "metadata", None) or {}),
                    "count": count,
                    "pages": pages,
                }
            )
            item_count += count
        manifest_path = destination / "collections.json"
        manifest_path.write_text(
            json.dumps(manifest, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        logical_size += manifest_path.stat().st_size
        return BackupComponent(
            name="chroma",
            schema_version=self.schema_version,
            service_version=self.service_version,
            source_revision=self.schema_version,
            item_count=item_count,
            logical_size_bytes=logical_size,
        )

    @staticmethod
    def _page_values(page: dict[str, Any], key: str):
        values = page.get(key)
        return values if isinstance(values, list) else None

    def restore(self, source: Path, _isolated_root: Path) -> None:
        try:
            manifest = json.loads((source / "collections.json").read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError) as exc:
            raise CoordinatedBackupError("chroma_restore_manifest_invalid") from exc
        if self.client.list_collections():
            raise CoordinatedBackupError("chroma_restore_target_not_empty")
        restored = 0
        for item in manifest:
            name = str(item["name"])
            collection_arguments: dict[str, Any] = {"name": name}
            metadata = dict(item.get("metadata") or {})
            if metadata:
                collection_arguments["metadata"] = metadata
            collection = self.client.create_collection(**collection_arguments)
            collection_dir = source / hashlib.sha256(name.encode()).hexdigest()[:24]
            for page_number in range(int(item.get("pages", 0))):
                try:
                    page = json.loads(
                        (collection_dir / f"page-{page_number:08d}.json").read_text(
                            encoding="utf-8"
                        )
                    )
                except (OSError, TypeError, ValueError) as exc:
                    raise CoordinatedBackupError("chroma_restore_page_invalid") from exc
                ids = [str(value) for value in page.get("ids") or []]
                if not ids:
                    continue
                arguments: dict[str, Any] = {"ids": ids}
                for source_key, target_key in (
                    ("documents", "documents"),
                    ("embeddings", "embeddings"),
                    ("metadatas", "metadatas"),
                    ("uris", "uris"),
                ):
                    values = self._page_values(page, source_key)
                    if values is not None and any(value is not None for value in values):
                        arguments[target_key] = values
                collection.upsert(**arguments)
                restored += len(ids)
        self._restore_result = {"status": "pass", "item_count": restored}

    def verify_restore(self, _isolated_root: Path, component: BackupComponent):
        result = self._verified_result(component)
        if result.get("status") != "pass":
            return result
        observed = sum(
            int(self.client.get_collection(name=(item if isinstance(item, str) else item.name)).count())
            for item in self.client.list_collections()
        )
        if observed != component.item_count:
            return {"status": "fail", "safe_reason": "chroma_restore_count_mismatch"}
        try:
            registry = self.client.get_collection(name="dle_schema_registry")
            version = (getattr(registry, "metadata", None) or {}).get("schema_version")
        except Exception:
            version = None
        if str(version or "") != component.schema_version:
            return {"status": "fail", "safe_reason": "chroma_restore_schema_mismatch"}
        return result


class MinIOPortableBackupAdapter(_ManagedAdapter):
    def __init__(self, store, buckets, service_version: str, schema_version: str):
        self.store = store
        self.buckets = tuple(buckets)
        self.service_version = service_version
        self.schema_version = schema_version

    def export(self, destination: Path) -> BackupComponent:
        item_count = 0
        logical_size = 0
        for bucket in self.buckets:
            summary = export_bucket(self.store, bucket, destination / bucket)
            verified = verify_snapshot(destination / bucket)
            if verified != summary:
                raise CoordinatedBackupError("minio_snapshot_verification_failed")
            item_count += summary.object_count
            logical_size += summary.total_bytes
        return BackupComponent(
            name="minio",
            schema_version=self.schema_version,
            service_version=self.service_version,
            source_revision=self.schema_version,
            item_count=item_count,
            logical_size_bytes=logical_size,
        )

    def restore(self, source: Path, _isolated_root: Path) -> None:
        item_count = 0
        logical_size = 0
        for bucket in self.buckets:
            self.store.create_bucket(bucket)
            if self.store.list(bucket):
                raise CoordinatedBackupError("minio_restore_target_not_empty")
            summary = restore_bucket(self.store, source / bucket, target_bucket=bucket)
            item_count += summary.object_count
            logical_size += summary.total_bytes
        self._restore_result = {
            "status": "pass",
            "item_count": item_count,
            "logical_size_bytes": logical_size,
        }

    def verify_restore(self, _isolated_root: Path, component: BackupComponent):
        result = self._verified_result(component)
        if result.get("status") != "pass":
            return result
        observed_count = sum(len(self.store.list(bucket)) for bucket in self.buckets)
        if observed_count != component.item_count:
            return {"status": "fail", "safe_reason": "minio_restore_count_mismatch"}
        try:
            version_payload = json.loads(
                self.store.get(
                    "audit-logs",
                    "_system/data-plane-schema.json",
                ).decode("utf-8")
            )
        except Exception:
            version_payload = {}
        if str(version_payload.get("schema_version") or "") != component.schema_version:
            return {"status": "fail", "safe_reason": "minio_restore_schema_mismatch"}
        return result


class RetainedFilesBackupAdapter(_ManagedAdapter):
    def __init__(self, runtime_root: Path, schema_version: str):
        self.runtime_root = runtime_root
        self.schema_version = schema_version

    def export(self, destination: Path) -> BackupComponent:
        allowed = (
            self.runtime_root / "databases" / "memory" / "memory_graph.json",
            self.runtime_root / "config" / "migration-version.json",
            self.runtime_root / "migrations" / "migration-ledger.json",
        )
        copied = 0
        logical_size = 0
        for source in allowed:
            if not source.is_file():
                continue
            relative = source.relative_to(self.runtime_root)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied += 1
            logical_size += target.stat().st_size
        if copied == 0:
            raise CoordinatedBackupError("retained_backup_files_missing")
        return BackupComponent(
            name="retained",
            schema_version=self.schema_version,
            service_version="filesystem.v1",
            source_revision=self.schema_version,
            item_count=copied,
            logical_size_bytes=logical_size,
        )

    def restore(self, source: Path, isolated_root: Path) -> None:
        restored = 0
        for path in sorted(item for item in source.rglob("*") if item.is_file()):
            relative = path.relative_to(source)
            if relative.parts and relative.parts[0] not in {"config", "databases", "migrations"}:
                raise CoordinatedBackupError("retained_restore_path_invalid")
            target = isolated_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            restored += 1
        self._restore_result = {"status": "pass", "item_count": restored}

    def verify_restore(self, isolated_root: Path, component: BackupComponent):
        result = self._verified_result(component)
        if result.get("status") != "pass":
            return result
        marker = isolated_root / "config" / "migration-version.json"
        try:
            version = json.loads(marker.read_text(encoding="utf-8")).get("schema_version")
        except (OSError, TypeError, ValueError):
            version = None
        if str(version or "") != component.schema_version:
            return {"status": "fail", "safe_reason": "retained_restore_schema_mismatch"}
        return result


class ManagedBackupResources:
    def __init__(self):
        self.resources: list[Any] = []

    def own(self, value):
        self.resources.append(value)
        return value

    def close(self):
        for value in reversed(self.resources):
            close = getattr(value, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    continue


def build_managed_backup_coordinator(app, runtime, resources):
    """Create export adapters only after the migration ledger is current."""
    manager = app.extensions.get("dle_data_plane_manager")
    ledger = app.extensions.get("dle_migration_ledger")
    if manager is None or not isinstance(ledger, dict) or ledger.get("status") != "ready":
        raise CoordinatedBackupError("managed_backup_migration_ledger_not_ready")
    settings = manager.connection_settings()
    versions = {
        name: str(item.get("observed_version") or item.get("target_version") or "unknown")
        for name, item in dict(ledger.get("stores") or {}).items()
    }
    metadata = manager.service_metadata()

    import chromadb
    import redis
    from neo4j import GraphDatabase
    from extensions import db
    from models import CrossStoreOutboxEvent
    from backend.storage.object_store import get_object_store

    redis_client = resources.own(redis.Redis.from_url(settings["redis_url"]))
    neo4j_driver = resources.own(
        GraphDatabase.driver(
            settings["neo4j_uri"],
            auth=(settings["neo4j_user"], settings["neo4j_password"]),
        )
    )
    chroma_client = resources.own(
        chromadb.HttpClient(host=settings["chroma_host"], port=settings["chroma_port"])
    )
    outstanding = db.session.query(CrossStoreOutboxEvent).filter(
        CrossStoreOutboxEvent.status != "succeeded"
    ).count()
    adapters = {
        "postgresql": PostgreSQLDumpBackupAdapter(
            manager,
            str(metadata["postgresql"]["version"]),
            versions["postgresql"],
            outstanding,
        ),
        "redis": RedisDurableExportAdapter(
            redis_client,
            str(metadata["redis"]["version"]),
            versions["redis"],
        ),
        "neo4j": Neo4jLogicalBackupAdapter(
            neo4j_driver,
            str(metadata["neo4j"]["version"]),
            versions["neo4j"],
        ),
        "chroma": ChromaCollectionBackupAdapter(
            chroma_client,
            str(metadata["chroma"]["version"]),
            versions["chroma"],
        ),
        "minio": MinIOPortableBackupAdapter(
            get_object_store(),
            settings["object_buckets"],
            str(metadata["minio"]["version"]),
            versions["minio"],
        ),
        "retained": RetainedFilesBackupAdapter(
            runtime.runtime_root,
            versions["retained_configuration"],
        ),
    }
    return CoordinatedBackupCoordinator(
        adapters=adapters,
        product_version=str(app.config.get("APP_VERSION", "0.1.1")),
        migration_versions=versions,
        required_components=MANAGED_BACKUP_COMPONENTS,
    )


def create_managed_backup(app, runtime, target_dir: str | Path, recovery_secret: str):
    resources = ManagedBackupResources()
    materializer = app.extensions.get("dle_materialization_worker")
    if materializer is not None:
        materializer.stop()
    try:
        with app.app_context():
            coordinator = build_managed_backup_coordinator(app, runtime, resources)
            result = coordinator.create_backup(target_dir, recovery_secret=recovery_secret)
        result["manifest"] = {
            "backup_id": result["backup_id"],
            "component_count": result["component_count"],
            "encrypted": result["encrypted"],
            "integrity_verified": result["integrity_verified"],
        }
        return result
    finally:
        resources.close()
        if materializer is not None:
            materializer.start(runtime)

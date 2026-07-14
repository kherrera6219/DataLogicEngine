"""Store-native export coverage for the managed recovery set."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from backend.storage.managed_backup import (
    ChromaCollectionBackupAdapter,
    MinIOPortableBackupAdapter,
    Neo4jLogicalBackupAdapter,
    PostgreSQLDumpBackupAdapter,
    RedisDurableExportAdapter,
    RetainedFilesBackupAdapter,
)
from backend.storage.object_store import LocalFileBackend


class FakePostgresManager:
    def __init__(self):
        self.restored = False

    def export_postgresql_logical_backup(self, destination):
        Path(destination).write_bytes(b"PGDMP\x01logical-backup")

    def restore_postgresql_logical_backup(self, source):
        assert Path(source).read_bytes().startswith(b"PGDMP")
        self.restored = True
        return {"status": "pass", "schema_revision": "alembic-head", "table_count": 67}


class FakeRedis:
    def __init__(self):
        self.values = {
            b"dle:schema:redis": b"dle.redis.v1",
            b"job:1": b"job",
            b"cache:temporary": b"cache",
        }

    def scan_iter(self, match="*"):
        return iter(self.values)

    def dump(self, key):
        return self.values[key]

    def pttl(self, _key):
        return -1

    def type(self, _key):
        return b"string"

    def get(self, key):
        normalized = key if isinstance(key, bytes) else str(key).encode("utf-8")
        return self.values.get(normalized)


class FakeRedisRestore(FakeRedis):
    def __init__(self):
        self.values = {}

    def restore(self, key, _ttl, dumped, replace=False):
        assert replace is False
        if key in self.values:
            return False
        self.values[key] = dumped
        return True


class FakeNeo4jSession:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def run(self, query):
        if query.startswith("MATCH (n)"):
            return [
                {
                    "backup_id": "n1",
                    "labels": ["KnowledgeNode"],
                    "properties": {"uid": "node-1", "created_at": datetime.now(UTC)},
                },
                {
                    "backup_id": "schema-1",
                    "labels": ["DLESchemaVersion"],
                    "properties": {"component": "neo4j", "version": "dle.neo4j.v1"},
                },
            ]
        if query.startswith("MATCH (a)"):
            return []
        if query == "SHOW CONSTRAINTS":
            return [
                {
                    "name": "knowledge_uid_unique",
                    "createStatement": (
                        "CREATE CONSTRAINT knowledge_uid_unique IF NOT EXISTS "
                        "FOR (n:KnowledgeNode) REQUIRE n.uid IS UNIQUE"
                    ),
                }
            ]
        return [
            {
                "name": "knowledge_uid_index",
                "createStatement": (
                    "CREATE INDEX knowledge_uid_index IF NOT EXISTS "
                    "FOR (n:KnowledgeNode) ON (n.uid)"
                ),
            }
        ]


class FakeNeo4j:
    def session(self):
        return FakeNeo4jSession()


class FakeNeo4jRestoreResult:
    def __init__(self, record=None, records=None):
        self.record = record
        self.records = list(records or ([] if record is None else [record]))

    def single(self):
        return self.record

    def consume(self):
        return self

    def __iter__(self):
        return iter(self.records)


class FakeNeo4jRestoreSession:
    def __init__(self):
        self.nodes = []
        self.relationships = []
        self.constraints = []
        self.indexes = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def run(self, query, **parameters):
        if query == "MATCH (n) RETURN count(n) AS count":
            return FakeNeo4jRestoreResult({"count": len(self.nodes)})
        if query == "MATCH ()-[r]->() RETURN count(r) AS count":
            return FakeNeo4jRestoreResult({"count": len(self.relationships)})
        if query.startswith("MATCH (v:DLESchemaVersion"):
            version = next(
                (
                    item["properties"]["version"]
                    for item in self.nodes
                    if item["properties"].get("component") == "neo4j"
                ),
                None,
            )
            return FakeNeo4jRestoreResult({"version": version} if version else None)
        if query == "SHOW CONSTRAINTS":
            return FakeNeo4jRestoreResult(records=self.constraints)
        if query == "SHOW INDEXES":
            return FakeNeo4jRestoreResult(records=self.indexes)
        if query.startswith("CREATE (n"):
            self.nodes.append(parameters)
        elif "CREATE (a)-[r:" in query:
            self.relationships.append(parameters)
        elif query.startswith("CREATE CONSTRAINT"):
            self.constraints.append({"query": query})
        elif query.startswith("CREATE INDEX"):
            self.indexes.append({"query": query})
        return FakeNeo4jRestoreResult({"count": 0})


class FakeNeo4jRestore:
    def __init__(self):
        self.target = FakeNeo4jRestoreSession()

    def session(self):
        return self.target


class FakeCollection:
    def __init__(self, name="knowledge_nodes"):
        self.name = name
        self.metadata = {"schema_version": "dle.chroma.v1"}

    def count(self):
        return 0 if self.name == "dle_schema_registry" else 1

    def get(self, **_kwargs):
        if self.name == "dle_schema_registry":
            return {"ids": [], "documents": [], "embeddings": [], "metadatas": [], "uris": []}
        return {
            "ids": ["node-1"],
            "documents": ["source content"],
            "embeddings": [[0.1, 0.2]],
            "metadatas": [{"source_revision": "source-1"}],
            "uris": [None],
        }


class FakeChroma:
    def list_collections(self):
        return [FakeCollection(), FakeCollection("dle_schema_registry")]

    def get_collection(self, name, **_kwargs):
        assert name in {"knowledge_nodes", "dle_schema_registry"}
        return FakeCollection(name)


class FakeChromaRestoreCollection:
    def __init__(self, name, metadata):
        self.name = name
        self.metadata = metadata
        self.records = {}

    def upsert(self, ids, **values):
        for index, item_id in enumerate(ids):
            self.records[item_id] = {
                key: items[index] for key, items in values.items()
            }

    def count(self):
        return len(self.records)


class FakeChromaRestore:
    def __init__(self):
        self.collections = {}

    def list_collections(self):
        return list(self.collections.values())

    def create_collection(self, name, metadata=None, **_kwargs):
        collection = FakeChromaRestoreCollection(name, metadata or {})
        self.collections[name] = collection
        return collection

    def get_collection(self, name, **_kwargs):
        return self.collections[name]


def test_managed_store_exports_capture_versions_state_and_hashable_artifacts(tmp_path):
    (tmp_path / "postgresql").mkdir()
    postgres = PostgreSQLDumpBackupAdapter(
        FakePostgresManager(), "18.4", "alembic-head", outstanding=2
    ).export(tmp_path / "postgresql")
    (tmp_path / "redis").mkdir()
    redis = RedisDurableExportAdapter(
        FakeRedis(), "8.8.0", "dle.redis.v1"
    ).export(tmp_path / "redis")
    (tmp_path / "neo4j").mkdir()
    neo4j = Neo4jLogicalBackupAdapter(
        FakeNeo4j(), "5.26.28", "dle.neo4j.v1"
    ).export(tmp_path / "neo4j")
    (tmp_path / "chroma").mkdir()
    chroma = ChromaCollectionBackupAdapter(
        FakeChroma(), "1.5.9", "dle.chroma.v1"
    ).export(tmp_path / "chroma")

    assert postgres.outstanding_work == 2
    assert postgres.logical_size_bytes > 0
    assert redis.item_count == 2
    assert redis.disposable_state == ("cache:temporary",)
    assert neo4j.item_count == 2
    assert chroma.item_count == 1
    assert (tmp_path / "chroma" / "collections.json").is_file()


def test_minio_portable_export_preserves_object_content_and_metadata(tmp_path):
    store = LocalFileBackend(str(tmp_path / "objects"))
    buckets = ("audit-logs", "deliverables")
    for bucket in buckets:
        store.create_bucket(bucket)
    store.put(
        "audit-logs",
        "run-1.json",
        b'{"run":"1"}',
        content_type="application/json",
        metadata={"source_revision": "revision-1"},
    )
    store.put(
        "audit-logs",
        "_system/data-plane-schema.json",
        b'{"schema_version":"dle.minio.v1"}',
        content_type="application/json",
        metadata={"artifact_type": "data_plane_schema"},
    )
    destination = tmp_path / "snapshot"
    destination.mkdir()

    component = MinIOPortableBackupAdapter(
        store,
        buckets,
        "candidate-qualification-version",
        "dle.minio.v1",
    ).export(destination)

    assert component.item_count == 2
    assert component.logical_size_bytes > len(b'{"run":"1"}')
    assert (destination / "audit-logs" / "manifest.sha256").is_file()


def test_retained_export_allowlists_versions_and_excludes_credentials(tmp_path):
    root = tmp_path / "runtime"
    (root / "databases" / "memory").mkdir(parents=True)
    (root / "config").mkdir()
    (root / "migrations").mkdir()
    (root / "security").mkdir()
    (root / "databases" / "memory" / "memory_graph.json").write_text(
        '{"version":1}', encoding="utf-8"
    )
    (root / "config" / "migration-version.json").write_text(
        '{"schema_version":"configuration.v1"}', encoding="utf-8"
    )
    (root / "migrations" / "migration-ledger.json").write_text(
        '{"status":"ready"}', encoding="utf-8"
    )
    (root / "security" / "data-plane-credentials.json").write_text(
        "credential-secret-sentinel", encoding="utf-8"
    )
    destination = tmp_path / "retained"
    destination.mkdir()

    component = RetainedFilesBackupAdapter(root, "configuration.v1").export(destination)

    assert component.item_count == 3
    all_bytes = b"".join(path.read_bytes() for path in destination.rglob("*") if path.is_file())
    assert b"credential-secret-sentinel" not in all_bytes


def test_managed_restore_adapters_reproduce_store_native_exports(tmp_path):
    export_root = tmp_path / "exports"
    restore_root = tmp_path / "isolated"
    export_root.mkdir()
    restore_root.mkdir()

    postgres_source = export_root / "postgresql"
    postgres_source.mkdir()
    postgres_source.joinpath("datalogic.pg_dump").write_bytes(b"PGDMP\x01logical-backup")
    postgres_manager = FakePostgresManager()
    postgres = PostgreSQLDumpBackupAdapter(
        postgres_manager, "18.4", "alembic-head", outstanding=0
    )
    postgres.restore(postgres_source, restore_root)
    assert postgres.verify_restore(
        restore_root,
        postgres.export(postgres_source),
    )["status"] == "pass"

    redis_source = export_root / "redis"
    redis_source.mkdir()
    redis_component = RedisDurableExportAdapter(
        FakeRedis(), "8.8.0", "dle.redis.v1"
    ).export(redis_source)
    redis_target = RedisDurableExportAdapter(
        FakeRedisRestore(), "8.8.0", "dle.redis.v1"
    )
    redis_target.restore(redis_source, restore_root)
    assert redis_target.verify_restore(restore_root, redis_component)["status"] == "pass"

    neo4j_source = export_root / "neo4j"
    neo4j_source.mkdir()
    neo4j_component = Neo4jLogicalBackupAdapter(
        FakeNeo4j(), "5.26.28", "dle.neo4j.v1"
    ).export(neo4j_source)
    neo4j_target = Neo4jLogicalBackupAdapter(
        FakeNeo4jRestore(), "5.26.28", "dle.neo4j.v1"
    )
    neo4j_target.restore(neo4j_source, restore_root)
    assert neo4j_target.verify_restore(restore_root, neo4j_component)["status"] == "pass"

    chroma_source = export_root / "chroma"
    chroma_source.mkdir()
    chroma_component = ChromaCollectionBackupAdapter(
        FakeChroma(), "1.5.9", "dle.chroma.v1"
    ).export(chroma_source)
    chroma_target = ChromaCollectionBackupAdapter(
        FakeChromaRestore(), "1.5.9", "dle.chroma.v1"
    )
    chroma_target.restore(chroma_source, restore_root)
    assert chroma_target.verify_restore(restore_root, chroma_component)["status"] == "pass"


def test_minio_and_retained_restore_preserve_hashes_and_exclude_secrets(tmp_path):
    source_store = LocalFileBackend(str(tmp_path / "source-objects"))
    target_store = LocalFileBackend(str(tmp_path / "target-objects"))
    bucket = "deliverables"
    source_store.create_bucket(bucket)
    source_store.put(
        bucket,
        "user/result.json",
        b'{"result":true}',
        content_type="application/json",
        metadata={"user_id": "42", "source_revision": "revision-1"},
    )
    source_store.create_bucket("audit-logs")
    source_store.put(
        "audit-logs",
        "_system/data-plane-schema.json",
        b'{"schema_version":"dle.minio.v1"}',
        content_type="application/json",
        metadata={"artifact_type": "data_plane_schema"},
    )
    object_source = tmp_path / "object-export"
    object_source.mkdir()
    component = MinIOPortableBackupAdapter(
        source_store, ("audit-logs", bucket), "candidate", "dle.minio.v1"
    ).export(object_source)
    target_adapter = MinIOPortableBackupAdapter(
        target_store, ("audit-logs", bucket), "candidate", "dle.minio.v1"
    )
    target_adapter.restore(object_source, tmp_path / "isolated")
    assert target_adapter.verify_restore(tmp_path / "isolated", component)["status"] == "pass"
    assert target_store.get(bucket, "user/result.json") == b'{"result":true}'

    runtime_root = tmp_path / "runtime"
    (runtime_root / "databases" / "memory").mkdir(parents=True)
    (runtime_root / "databases" / "memory" / "memory_graph.json").write_text(
        '{"schema_version":1}', encoding="utf-8"
    )
    (runtime_root / "config").mkdir()
    (runtime_root / "config" / "migration-version.json").write_text(
        '{"schema_version":"configuration.v1"}', encoding="utf-8"
    )
    retained_source = tmp_path / "retained-export"
    retained_source.mkdir()
    retained_export = RetainedFilesBackupAdapter(runtime_root, "configuration.v1")
    retained_component = retained_export.export(retained_source)
    isolated = tmp_path / "retained-isolated"
    isolated.mkdir()
    retained_target = RetainedFilesBackupAdapter(isolated, "configuration.v1")
    retained_target.restore(retained_source, isolated)
    assert retained_target.verify_restore(isolated, retained_component)["status"] == "pass"
    assert not (isolated / "security" / "data-plane-credentials.json").exists()

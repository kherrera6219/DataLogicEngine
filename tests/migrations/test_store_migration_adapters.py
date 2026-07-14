"""Store-native migration-version adapter tests."""

from __future__ import annotations

import json

from sqlalchemy import create_engine, text

from backend.storage.object_store import LocalFileBackend
from backend.storage.store_migration_adapters import (
    ChromaMigrationAdapter,
    LocalJsonMemoryMigrationAdapter,
    MinIOMigrationAdapter,
    Neo4jMigrationAdapter,
    PostgreSQLMigrationAdapter,
    RedisMigrationAdapter,
    RetainedConfigurationMigrationAdapter,
)


class FakeRedis:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def dbsize(self):
        return len(self.data)

    def set(self, key, value, nx=False):
        if nx and key in self.data:
            return False
        self.data[key] = value.encode() if isinstance(value, str) else value
        return True


class FakeCollection:
    def __init__(self, name, metadata=None):
        self.name = name
        self.metadata = metadata or {}


class FakeChroma:
    def __init__(self):
        self.collections = {}

    def list_collections(self):
        return list(self.collections.values())

    def get_collection(self, name, **_kwargs):
        return self.collections[name]

    def get_or_create_collection(self, name, metadata=None, **_kwargs):
        return self.collections.setdefault(name, FakeCollection(name, metadata))


class FakeResult:
    def __init__(self, record=None, callback=None):
        self.record = record
        self.callback = callback

    def single(self):
        return self.record

    def consume(self):
        if self.callback:
            self.callback()


class FakeNeo4jSession:
    def __init__(self, driver):
        self.driver = driver

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def run(self, query, **params):
        if "RETURN count(n)" in query:
            return FakeResult({"count": 1 if self.driver.version else 0})
        if "RETURN v.version" in query:
            return FakeResult({"version": self.driver.version} if self.driver.version else None)
        return FakeResult(callback=lambda: setattr(self.driver, "version", params["version"]))


class FakeNeo4j:
    def __init__(self):
        self.version = None

    def session(self):
        return FakeNeo4jSession(self)


def test_postgresql_adapter_bootstraps_alembic_head():
    engine = create_engine("sqlite:///:memory:")

    def upgrade(target):
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32))"))
            connection.execute(
                text("INSERT INTO alembic_version (version_num) VALUES (:target)"),
                {"target": target},
            )

    adapter = PostgreSQLMigrationAdapter(engine, upgrade)
    assert adapter.probe_version() is None
    assert adapter.is_empty() is True
    adapter.bootstrap("head-1")
    assert adapter.probe_version() == "head-1"


def test_redis_neo4j_and_chroma_bootstrap_version_ledgers():
    redis_adapter = RedisMigrationAdapter(FakeRedis())
    neo4j_adapter = Neo4jMigrationAdapter(FakeNeo4j())
    chroma_adapter = ChromaMigrationAdapter(FakeChroma())

    for adapter, target in (
        (redis_adapter, "dle.redis.v1"),
        (neo4j_adapter, "dle.neo4j.v1"),
        (chroma_adapter, "dle.chroma.v1"),
    ):
        assert adapter.probe_version() is None
        assert adapter.is_empty() is True
        adapter.bootstrap(target)
        assert adapter.probe_version() == target


def test_minio_contract_manifest_keeps_product_authority(tmp_path):
    backend = LocalFileBackend(str(tmp_path / "objects"))
    buckets = (
        "audit-logs",
        "simulation-artifacts",
        "deliverables",
        "graphs",
        "evaluation-data",
        "trace-exports",
    )
    for bucket in buckets:
        backend.create_bucket(bucket)
    adapter = MinIOMigrationAdapter(backend, buckets)

    assert adapter.is_empty() is True
    adapter.bootstrap("dle.minio.v1")

    assert adapter.probe_version() == "dle.minio.v1"
    payload = backend.get("audit-logs", "_system/data-plane-schema.json").decode()
    assert '"object_store_architecture": "minio"' in payload
    assert '"seaweedfs_production_selected": false' in payload


def test_local_json_and_retained_configuration_are_versioned_atomically(tmp_path):
    memory = LocalJsonMemoryMigrationAdapter(tmp_path / "memory" / "memory_graph.json")
    config = RetainedConfigurationMigrationAdapter(
        tmp_path / "config" / "migration-version.json",
        validators=(lambda: True,),
    )

    memory.bootstrap("unified-memory.v2")
    config.bootstrap("configuration.v1")

    assert memory.probe_version() == "unified-memory.v2"
    assert config.probe_version() == "configuration.v1"
    assert not list(tmp_path.rglob("*.tmp"))


def test_local_json_memory_v1_migrates_to_integrity_checked_working_only_v2(tmp_path):
    path = tmp_path / "memory" / "memory_graph.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "saved_at": "2026-07-13T00:00:00+00:00",
                "last_recall_timestamp": None,
                "vertices": [
                    {
                        "vertex_id": "legacy",
                        "content": "unclassified legacy memory",
                        "metadata": {},
                    }
                ],
                "edges": [],
            }
        ),
        encoding="utf-8",
    )
    adapter = LocalJsonMemoryMigrationAdapter(path)

    adapter.migrate("unified-memory.v1", "unified-memory.v2")

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert adapter.probe_version() == "unified-memory.v2"
    assert payload["integrity_sha256"]
    assert payload["vertices"][0]["metadata"]["validation_state"] == "working"

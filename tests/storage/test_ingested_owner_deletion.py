"""Deletion must resolve historical ownership and preserve other principals."""

import json
from types import SimpleNamespace

import pytest
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    JSON,
    MetaData,
    String,
    Table,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import Session

from backend.storage.retention import DeletionSubject, RetentionDeleteError
from backend.storage.user_deletion import (
    PostgreSQLUserDeletionAdapter,
    ChromaUserDeletionAdapter,
    Neo4jUserDeletionAdapter,
)


@pytest.fixture
def authority():
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    users = Table("users", metadata, Column("id", Integer, primary_key=True))
    nodes = Table(
        "ukg_knowledge_nodes",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("uid", String),
        Column("node_metadata", JSON),
        Column("tenant_id", String),
    )
    jobs = Table(
        "ingestion_jobs",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer, ForeignKey("users.id")),
        Column("tenant_id", String),
    )
    Table(
        "ingestion_files",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("job_id", Integer, ForeignKey("ingestion_jobs.id")),
        Column("status", String),
    )
    chunks = Table(
        "ingestion_chunks",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("job_id", Integer, ForeignKey("ingestion_jobs.id")),
        Column("node_uid", String),
        Column("file_id", Integer, ForeignKey("ingestion_files.id")),
    )
    for name in ("cross_store_materialization_states", "cross_store_outbox_events"):
        Table(
            name,
            metadata,
            Column("id", Integer, primary_key=True),
            Column("entity_id", String),
        )
    metadata.create_all(engine)
    try:
        with Session(engine) as session:
            session.execute(users.insert(), [{"id": 1}, {"id": 2}])
            session.execute(
                nodes.insert(),
                [
                    {
                        "id": 1,
                        "uid": "one",
                        "tenant_id": "same",
                        "node_metadata": {"permissions": {"owner_user_id": 1}},
                    },
                    {
                        "id": 2,
                        "uid": "two",
                        "tenant_id": "same",
                        "node_metadata": {
                            "permissions": json.dumps({"owner_user_id": "2"})
                        },
                    },
                ],
            )
            session.commit()
            yield session, metadata, nodes, jobs, chunks
    finally:
        engine.dispose()


def test_relational_nested_owner_is_removed_without_tenant_wide_deletion(authority):
    session, metadata, nodes, _, _ = authority
    for name in ("cross_store_materialization_states", "cross_store_outbox_events"):
        session.execute(
            metadata.tables[name].insert(),
            [{"id": 1, "entity_id": "one"}, {"id": 2, "entity_id": "two"}],
        )
    session.commit()
    adapter = PostgreSQLUserDeletionAdapter(session, metadata)
    subject = DeletionSubject("user", "1", tenant_id="same")
    assert adapter.remnant_count(subject) > 0
    adapter.delete(subject)
    assert adapter.remnant_count(subject) == 0
    assert session.execute(select(nodes.c.uid)).scalars().all() == ["two"]
    for name in ("cross_store_materialization_states", "cross_store_outbox_events"):
        assert session.execute(
            select(metadata.tables[name].c.entity_id)
        ).scalars().all() == ["two"]


def test_shared_knowledge_reference_stops_deletion_before_mutation(authority):
    session, metadata, nodes, jobs, chunks = authority
    session.execute(
        jobs.insert(),
        [
            {"id": 1, "user_id": 1, "tenant_id": "same"},
            {"id": 2, "user_id": 2, "tenant_id": "same"},
        ],
    )
    session.execute(
        chunks.insert(),
        [
            {"id": 1, "job_id": 1, "node_uid": "one"},
            {"id": 2, "job_id": 2, "node_uid": "one"},
        ],
    )
    session.commit()
    with pytest.raises(RetentionDeleteError, match="shared"):
        PostgreSQLUserDeletionAdapter(session, metadata).delete(
            DeletionSubject("user", "1")
        )
    assert session.scalar(select(func.count()).select_from(nodes)) == 2


class Collection:
    def __init__(self):
        self.rows = {
            "one": {
                "permissions": json.dumps({"owner_user_id": 1}),
                "tenant_id": "same",
            },
            "two": {
                "permissions": json.dumps({"owner_user_id": "2"}),
                "tenant_id": "same",
            },
            "legacy-uid:chunk:1": {"vector_parent_id": "legacy-uid"},
        }

    def count(self):
        return len(self.rows)

    def get(self, *, where=None, limit=500, offset=0, include=None):
        rows = list(self.rows.items())
        if where:
            key, value = next(iter(where.items()))
            rows = [(key_id, meta) for key_id, meta in rows if meta.get(key) == value]
        rows = rows[offset : offset + limit]
        return {
            "ids": [key for key, _ in rows],
            "metadatas": [meta for _, meta in rows],
        }

    def delete(self, ids):
        for item in ids:
            self.rows.pop(item, None)


class Client:
    def __init__(self):
        self.collection = Collection()

    def list_collections(self, limit=100, offset=0):
        return [SimpleNamespace(name="knowledge_nodes")][offset : offset + limit]

    def get_collection(self, **kwargs):
        return self.collection


def test_search_nested_owners_and_authoritative_uids_are_deleted_scopingly():
    client = Client()
    adapter = ChromaUserDeletionAdapter(client, knowledge_uids={"legacy-uid"})
    subject = DeletionSubject("user", "1", tenant_id="same")
    assert adapter.remnant_count(subject) == 2
    adapter.delete(subject)
    assert set(client.collection.rows) == {"two"}
    assert adapter.remnant_count(subject) == 0


def test_malformed_ownership_cannot_be_reported_as_zero_search_remnants():
    client = Client()
    client.collection.rows["one"]["permissions"] = "{broken"
    with pytest.raises(RetentionDeleteError):
        ChromaUserDeletionAdapter(client).delete(DeletionSubject("user", "1"))
    assert len(client.collection.rows) == 3


class GraphResult(list):
    def single(self):
        return self[0] if self else None


class Graph:
    def __init__(self):
        self.rows = {
            "one": {
                "permissions": json.dumps({"owner_user_id": 1}),
                "tenant_id": "same",
            },
            "two": {"user_id": "2", "tenant_id": "same"},
            "legacy": {"uid": "legacy-uid"},
        }

    def session(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def run(self, query, **params):
        if "element_ids" in params:
            count = 0
            for key in params["element_ids"]:
                count += key in self.rows
                self.rows.pop(key, None)
            return GraphResult([{"count": count}])
        return GraphResult(
            [{"element_id": key, "properties": meta} for key, meta in self.rows.items()]
        )


def test_graph_nested_owners_and_authoritative_uids_preserve_other_owner():
    driver = Graph()
    adapter = Neo4jUserDeletionAdapter(driver, knowledge_uids={"legacy-uid"})
    subject = DeletionSubject("user", "1", tenant_id="same")
    assert adapter.remnant_count(subject) == 2
    adapter.delete(subject)
    assert set(driver.rows) == {"two"}
    assert adapter.remnant_count(subject) == 0


def test_authoritative_uid_owner_conflict_is_explicit_and_does_not_delete():
    driver = Graph()
    driver.rows["legacy"]["user_id"] = "2"
    with pytest.raises(RetentionDeleteError, match="ownership"):
        Neo4jUserDeletionAdapter(driver, knowledge_uids={"legacy-uid"}).delete(
            DeletionSubject("user", "1")
        )
    assert len(driver.rows) == 3


def test_search_pagination_removes_all_owned_records_and_preserves_other_owner():
    client = Client()
    for index in range(600):
        client.collection.rows[f"owned-{index}"] = {
            "permissions": json.dumps({"owner_user_id": "1"})
        }
    adapter = ChromaUserDeletionAdapter(client, knowledge_uids={"legacy-uid"})
    assert adapter.delete(DeletionSubject("user", "1")).deleted_count == 602
    assert set(client.collection.rows) == {"two"}


def test_ignored_search_page_offset_is_failure_without_mutation():
    client = Client()
    for index in range(600):
        client.collection.rows[f"owned-{index}"] = {"user_id": "1"}
    original = client.collection.get
    client.collection.get = lambda **kwargs: original(**{**kwargs, "offset": 0})
    with pytest.raises(RetentionDeleteError):
        ChromaUserDeletionAdapter(client).delete(DeletionSubject("user", "1"))
    assert len(client.collection.rows) == 603


def test_relational_malformed_owner_metadata_fails_before_deleting_identity(authority):
    session, metadata, nodes, _, _ = authority
    session.execute(
        nodes.update()
        .where(nodes.c.id == 1)
        .values(node_metadata={"permissions": "{broken"})
    )
    session.commit()
    with pytest.raises(RetentionDeleteError):
        PostgreSQLUserDeletionAdapter(session, metadata).delete(
            DeletionSubject("user", "1")
        )
    assert (
        session.scalar(select(func.count()).select_from(metadata.tables["users"])) == 2
    )


def test_completed_file_deletion_does_not_create_a_false_shared_owner_conflict(
    authority,
):
    session, metadata, nodes, jobs, chunks = authority
    session.execute(
        jobs.insert(),
        [
            {"id": 1, "user_id": 1, "tenant_id": "same"},
            {"id": 2, "user_id": 2, "tenant_id": "same"},
        ],
    )
    files = metadata.tables["ingestion_files"]
    session.execute(
        files.insert(),
        [
            {"id": 1, "job_id": 1, "status": "ready"},
            {"id": 2, "job_id": 2, "status": "deleted"},
        ],
    )
    session.execute(
        chunks.insert(),
        [
            {"id": 1, "job_id": 1, "node_uid": "one", "file_id": 1},
            {"id": 2, "job_id": 2, "node_uid": "one", "file_id": 2},
        ],
    )
    session.commit()
    PostgreSQLUserDeletionAdapter(session, metadata).delete(
        DeletionSubject("user", "1")
    )
    assert session.execute(select(nodes.c.uid)).scalars().all() == ["two"]


def test_tenant_deletion_includes_both_flat_and_nested_tenant_ownership(authority):
    session, metadata, nodes, _, _ = authority
    session.execute(
        nodes.update()
        .where(nodes.c.id == 2)
        .values(
            tenant_id=None,
            node_metadata={"permissions": {"owner_user_id": 2, "tenant_id": "same"}},
        )
    )
    session.commit()
    adapter = PostgreSQLUserDeletionAdapter(session, metadata)
    adapter.delete(DeletionSubject("tenant", "same"))
    assert session.scalar(select(func.count()).select_from(nodes)) == 0

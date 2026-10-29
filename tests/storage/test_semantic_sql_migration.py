"""Batch coordinator tests without touching a real or customer database."""

from contextlib import nullcontext
from types import SimpleNamespace
from uuid import UUID

import pytest

from backend.storage import semantic_sql_migration as migration
from backend.storage.semantic_index_profile import ProfiledChromaBackend


class FakeSession:
    def __init__(self, ids):
        self.ids = ids

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def connection(self):
        return SimpleNamespace(get_isolation_level=lambda: "READ COMMITTED")

    def query(self, *_args):
        return self

    def order_by(self, *_args):
        return self

    def filter(self, *_args):
        return self

    def limit(self, count):
        return SimpleNamespace(all=lambda: [(item,) for item in self.ids[:count]])

    def expire_all(self):
        pass


class FakeProvider:
    def chunk_spans(self, *_args, **_kwargs):
        return [("hello", 0, 5)]

    def __call__(self, _text):
        return [0.6, 0.8]


@pytest.fixture
def setup(monkeypatch, tmp_path):
    ids = [UUID(int=1), UUID(int=2), UUID(int=3)]
    monkeypatch.setattr(migration, "Session", lambda _engine: FakeSession(ids))
    monkeypatch.setattr(migration, "_require_staging_prerequisites", lambda: None)
    monkeypatch.setattr(migration, "_require_managed_runtime", lambda *_: None)
    monkeypatch.setattr(migration, "chat_index_guard", lambda _root: nullcontext())
    target = object.__new__(ProfiledChromaBackend)
    target.profile = SimpleNamespace(
        record_metadata={}, dimensions=2, profile_id="profile"
    )
    monkeypatch.setattr(ProfiledChromaBackend, "_get_collection", lambda *_: object())
    provider = FakeProvider()
    rag = SimpleNamespace(
        _uses_local_model=lambda: True,
        _get_vector_store=lambda: target,
        _embedding_provider=provider,
        COLLECTION_CHAT_HISTORY="chat_history",
        COLLECTION_KNOWLEDGE="knowledge_nodes",
        embedding_revision="revision",
        store_chat_message=lambda *_args, **_kwargs: True,
    )
    runtime = SimpleNamespace(
        runtime_root=tmp_path,
        instance_id="id",
        ownership=SimpleNamespace(identity=None),
    )
    engine = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
    calls = []
    monkeypatch.setattr(
        migration, "verify_semantic_family", lambda *_a, **kw: calls.append(kw)
    )
    return ids, rag, runtime, engine, calls


def test_staging_is_disabled_before_inspecting_any_runtime_or_service():
    class Untouchable:
        def __getattribute__(self, _name):
            raise AssertionError("disabled staging accessed a runtime or service")

    target = Untouchable()
    with pytest.raises(migration.SemanticMigrationError, match="staging_disabled"):
        migration.stage_semantic_sql_batch(
            engine=target, runtime=target, rag=target, kind="chat"
        )


def test_bounded_batch_requires_profile_and_returns_cursor(setup, monkeypatch):
    ids, rag, runtime, engine, calls = setup
    monkeypatch.setattr(
        migration,
        "_source",
        lambda _s, _k, item, _key: {
            "kind": "chat",
            "id": str(item),
            "text": "hello",
            "session_id": "s",
            "user_id": "owner",
            "role": "user",
        },
    )
    result = migration.stage_semantic_sql_batch(
        engine=engine, runtime=runtime, rag=rag, kind="chat", limit=2
    )
    assert result == {
        "status": "staged_not_activated",
        "kind": "chat",
        "processed": 2,
        "cursor": str(ids[1]),
        "has_more": True,
        "profile_id": "profile",
    }
    assert [call["parent_id"] for call in calls] == [str(ids[0]), str(ids[1])]


def test_drift_after_write_rejects_batch_without_cursor(setup, monkeypatch):
    _ids, rag, runtime, engine, _calls = setup
    states = iter(
        [
            {
                "kind": "chat",
                "id": "p",
                "text": "hello",
                "session_id": "s",
                "user_id": "u",
                "role": "user",
            },
            {
                "kind": "chat",
                "id": "p",
                "text": "changed",
                "session_id": "s",
                "user_id": "u",
                "role": "user",
            },
        ]
    )
    monkeypatch.setattr(migration, "_source", lambda *_args: next(states))
    with pytest.raises(
        migration.SemanticMigrationError, match="semantic_source_changed"
    ):
        migration.stage_semantic_sql_batch(
            engine=engine, runtime=runtime, rag=rag, kind="chat", limit=1
        )


def test_rejects_sqlite_and_invalid_bounds(setup):
    _ids, rag, runtime, _engine, _calls = setup
    with pytest.raises(migration.SemanticMigrationError, match="configuration_invalid"):
        migration.stage_semantic_sql_batch(
            engine=SimpleNamespace(dialect=SimpleNamespace(name="sqlite")),
            runtime=runtime,
            rag=rag,
            kind="chat",
        )
    with pytest.raises(migration.SemanticMigrationError, match="configuration_invalid"):
        migration.stage_semantic_sql_batch(
            engine=SimpleNamespace(dialect=SimpleNamespace(name="postgresql")),
            runtime=runtime,
            rag=rag,
            kind="chat",
            limit=0,
        )

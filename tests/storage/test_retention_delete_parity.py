"""Cross-store retention, deletion parity, remnant, and tombstone tests."""

from __future__ import annotations

import json

import pytest

from extensions import db
from backend.storage.retention import (
    RETENTION_CLASSES,
    DeleteResult,
    DeletionSubject,
    RetentionDeleteCoordinator,
    RetentionDeleteError,
)
from models import DataDeletionTombstone
from backend.storage.user_deletion import ChromaUserDeletionAdapter


def test_user_deletion_requires_the_same_chat_index_lock(tmp_path, monkeypatch):
    from types import SimpleNamespace

    import backend.storage.chat_index_coordination as coordination
    import backend.storage.user_deletion as deletion

    real_guard = coordination.chat_index_guard
    monkeypatch.setattr(
        coordination,
        "chat_index_guard",
        lambda root: real_guard(root, timeout_seconds=0.1),
    )
    calls = []
    monkeypatch.setattr(
        deletion, "_run_user_deletion_locked", lambda *_args: calls.append(True)
    )
    app = SimpleNamespace(
        extensions={"dle_runtime": SimpleNamespace(runtime_root=tmp_path)}
    )
    with real_guard(tmp_path):
        with pytest.raises(RetentionDeleteError, match="chat_index_lock_unavailable"):
            deletion.run_user_deletion(app, DeletionSubject("user", "1"))
    assert calls == []


class FakeDeletionAdapter:
    def __init__(self, count: int, *, retained: int = 0, basis: str | None = None):
        self.count = count
        self.retained = retained
        self.basis = basis

    def delete(self, _subject):
        deleted = self.count - self.retained
        self.count = self.retained
        return DeleteResult(deleted, self.retained, self.basis)

    def remnant_count(self, _subject):
        return self.count


REQUIRED_STORES = (
    "postgresql",
    "neo4j",
    "chroma",
    "redis",
    "minio",
    "local_json",
    "logs",
)


def _coordinator(db_session, adapters):
    return RetentionDeleteCoordinator(
        session=db_session,
        adapters=adapters,
        required_stores=REQUIRED_STORES,
        digest_key="installation-scoped-tombstone-key",
    )


def test_required_retention_classes_are_explicit():
    assert {
        "chats",
        "traces",
        "prompts",
        "provider_responses",
        "external_client_requests",
        "idempotency_state",
        "gateway_jobs_results",
        "usage",
        "client_key_metadata",
        "gateway_audits",
        "evidence",
        "logs",
        "simulations",
        "ingested_content",
        "exports",
        "backups",
        "cache",
    } == set(RETENTION_CLASSES)


def test_delete_parity_completes_only_after_every_store_has_no_remnants(app):
    with app.app_context():
        adapters = {name: FakeDeletionAdapter(2) for name in REQUIRED_STORES}
        tombstone = _coordinator(db.session, adapters).run(
            DeletionSubject("user", "raw-user-id", tenant_id="tenant-1")
        )

        assert tombstone.status == "completed"
        assert set(tombstone.store_status) == set(REQUIRED_STORES)
        assert all(item["status"] == "pass" for item in tombstone.store_status.values())
        persisted = DataDeletionTombstone.query.one()
        serialized = json.dumps(persisted.store_status) + persisted.subject_digest
        assert "raw-user-id" not in serialized
        assert len(persisted.subject_digest) == 64


def test_explicit_immutable_audit_retention_is_visible_and_allowed(app):
    with app.app_context():
        adapters = {name: FakeDeletionAdapter(1) for name in REQUIRED_STORES}
        adapters["logs"] = FakeDeletionAdapter(
            1,
            retained=1,
            basis="security_audit_legal_hold_2026",
        )
        tombstone = _coordinator(db.session, adapters).run(
            DeletionSubject("user", "user-7")
        )

        assert tombstone.status == "completed"
        assert tombstone.store_status["logs"]["status"] == "retained_by_policy"
        assert tombstone.store_status["logs"]["retention_basis"]


def test_unapproved_remnant_fails_closed_but_preserves_retry_tombstone(app):
    with app.app_context():
        adapters = {name: FakeDeletionAdapter(1) for name in REQUIRED_STORES}
        adapters["minio"] = FakeDeletionAdapter(1, retained=1, basis=None)

        with pytest.raises(
            RetentionDeleteError, match="cross_store_deletion_incomplete"
        ):
            _coordinator(db.session, adapters).run(DeletionSubject("user", "user-8"))

        tombstone = DataDeletionTombstone.query.one()
        assert tombstone.status == "partial_failure"
        assert tombstone.store_status["minio"]["status"] == "failed"
        assert tombstone.safe_reason == "cross_store_deletion_incomplete"


def test_chroma_lookup_failure_cannot_be_reported_as_complete_deletion(app):
    class BrokenCollection:
        def get(self, **kwargs):
            raise RuntimeError("private storage detail")

    class BrokenClient:
        def list_collections(self, limit=100, offset=0):
            return ["synthetic"]

        def get_collection(self, **kwargs):
            return BrokenCollection()

    subject = DeletionSubject("user", "user-9")
    adapter = ChromaUserDeletionAdapter(BrokenClient())
    with pytest.raises(RetentionDeleteError, match="chroma_deletion_lookup_failed"):
        adapter.delete(subject)
    with pytest.raises(RetentionDeleteError, match="chroma_deletion_lookup_failed"):
        adapter.remnant_count(subject)

    with app.app_context():
        adapters = {name: FakeDeletionAdapter(0) for name in REQUIRED_STORES}
        adapters["chroma"] = adapter
        with pytest.raises(
            RetentionDeleteError, match="cross_store_deletion_incomplete"
        ):
            _coordinator(db.session, adapters).run(subject)
        tombstone = DataDeletionTombstone.query.one()
        assert tombstone.status == "partial_failure"
        assert tombstone.store_status["chroma"]["status"] == "failed"
        assert tombstone.store_status["chroma"]["retained_count"] is None
        assert "private storage detail" not in json.dumps(tombstone.store_status)


def test_failed_external_store_preserves_authority_for_a_successful_retry(app):
    from backend.storage.user_deletion import PostgreSQLUserDeletionAdapter
    from models import User, KnowledgeGraphNode
    from tests.conftest import create_test_user

    class UnavailableStore:
        def delete(self, subject):
            raise RetentionDeleteError("synthetic_store_unavailable")

        def remnant_count(self, subject):
            raise RetentionDeleteError("synthetic_store_unavailable")

    with app.app_context():
        owner = create_test_user(
            username="deletion-retry-owner",
            email="deletion-retry@example.com",
            password="SecureTest789$#@",
        )
        node = KnowledgeGraphNode(
            uid="retry-owned",
            node_type="ingested_document_chunk",
            content="synthetic retained authority",
            node_metadata={"permissions": {"owner_user_id": owner}},
        )
        db.session.add(node)
        db.session.commit()
        adapters = {name: FakeDeletionAdapter(0) for name in REQUIRED_STORES}
        adapters["postgresql"] = PostgreSQLUserDeletionAdapter(db.session, db.metadata)
        adapters["chroma"] = UnavailableStore()
        subject = DeletionSubject("user", str(owner))
        with pytest.raises(
            RetentionDeleteError, match="cross_store_deletion_incomplete"
        ):
            _coordinator(db.session, adapters).run(subject)
        assert db.session.get(User, owner) is not None
        assert KnowledgeGraphNode.query.filter_by(uid="retry-owned").count() == 1
        pending = DataDeletionTombstone.query.order_by(
            DataDeletionTombstone.requested_at.desc()
        ).first()
        assert (
            pending.store_status["postgresql"]["safe_reason"]
            == "authority_retained_for_retry"
        )
        adapters["chroma"] = FakeDeletionAdapter(0)
        assert _coordinator(db.session, adapters).run(subject).status == "completed"
        assert db.session.get(User, owner) is None
        assert KnowledgeGraphNode.query.filter_by(uid="retry-owned").count() == 0

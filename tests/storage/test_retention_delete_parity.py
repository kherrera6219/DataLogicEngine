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

        with pytest.raises(RetentionDeleteError, match="cross_store_deletion_incomplete"):
            _coordinator(db.session, adapters).run(
                DeletionSubject("user", "user-8")
            )

        tombstone = DataDeletionTombstone.query.one()
        assert tombstone.status == "partial_failure"
        assert tombstone.store_status["minio"]["status"] == "failed"
        assert tombstone.safe_reason == "cross_store_deletion_incomplete"

"""Durable chat-index recovery must honor source ownership and deletion."""

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
import uuid

from backend.llm_gateway.gateway import LLMGateway
from backend.storage.materialization_dispatcher import CrossStoreMaterializationDispatcher
from extensions import db
from models import ChatMessage, ChatSession, CrossStoreOutboxEvent
from tests.conftest import create_test_user


def _save(app, monkeypatch):
    monkeypatch.setattr("backend.services.rag_service.get_rag_service",
                        lambda: SimpleNamespace(store_chat_message=lambda *a, **k: False))
    owner = create_test_user(username="recovery-owner", email="recovery@example.com",
                             password="SecureTest789$#@")
    session_id = uuid.uuid4()
    db.session.add(ChatSession(id=session_id, user_id=owner, mode="chat"))
    db.session.commit()
    result = asyncio.run(LLMGateway(db_session=db.session)._save_chat_message(
        str(session_id), owner, "user", "synthetic private transcript"))
    assert result.ok and result.rag_status == "failed"
    return result, owner


def test_failed_index_recovers_after_new_database_session(app, monkeypatch):
    with app.app_context():
        result, owner = _save(app, monkeypatch)
        queued = CrossStoreOutboxEvent.query.filter_by(entity_id=result.message_id).one()
        assert "synthetic private transcript" not in repr(queued.payload)
        db.session.remove()
        calls = []
        monkeypatch.setattr("backend.services.rag_service.get_rag_service",
            lambda: SimpleNamespace(store_chat_message=lambda *a, **k: calls.append((a, k)) or True))
        outcome = CrossStoreMaterializationDispatcher(db.session).run_once()
        assert outcome == {"claimed": 1, "succeeded": 1, "failed": 0}
        assert calls[0][0][1] == result.message_id
        assert calls[0][1]["user_id"] == str(owner)
        assert CrossStoreMaterializationDispatcher(db.session).run_once()["claimed"] == 0


def test_retry_never_reindexes_a_deleted_message(app, monkeypatch):
    with app.app_context():
        result, _ = _save(app, monkeypatch)
        db.session.delete(db.session.get(ChatMessage, uuid.UUID(result.message_id)))
        db.session.commit()
        calls = []
        monkeypatch.setattr("backend.services.rag_service.get_rag_service",
            lambda: SimpleNamespace(store_chat_message=lambda *a, **k: calls.append(a) or True))
        assert CrossStoreMaterializationDispatcher(db.session).run_once()["succeeded"] == 1
        assert calls == []


def test_retry_rejects_changed_source_and_stops_after_attempt_limit(app, monkeypatch):
    with app.app_context():
        result, _ = _save(app, monkeypatch)
        message = db.session.get(ChatMessage, uuid.UUID(result.message_id))
        message.content = "changed synthetic transcript"
        db.session.commit()
        calls = []
        monkeypatch.setattr("backend.services.rag_service.get_rag_service",
            lambda: SimpleNamespace(store_chat_message=lambda *a, **k: calls.append(a) or True))
        assert CrossStoreMaterializationDispatcher(db.session).run_once()["failed"] == 1
        assert calls == []
        event = CrossStoreOutboxEvent.query.filter_by(entity_id=result.message_id).one()
        assert event.status == "failed" and event.safe_reason == "chroma_delivery_failed"
        event.attempts = 8
        event.available_at = datetime.now(UTC) - timedelta(seconds=1)
        db.session.commit()
        assert CrossStoreMaterializationDispatcher(db.session).run_once()["claimed"] == 0


def test_retention_removes_chat_retry_records(app, monkeypatch):
    from backend.retention_service import DataRetentionService, RetentionCategory
    from models import CrossStoreMaterializationState

    with app.app_context():
        result, _ = _save(app, monkeypatch)
        session = db.session.get(ChatSession, uuid.UUID(result.session_id))
        session.created_at = datetime.now(UTC) - timedelta(days=100)
        db.session.commit()
        monkeypatch.setattr("backend.services.rag_service.get_rag_service",
                            lambda: SimpleNamespace(delete_chat_session=lambda _: None))
        service = DataRetentionService()
        service.set_policy(RetentionCategory.SESSIONS, 90, archive_before_delete=False)
        assert service.cleanup_sessions()["deleted_count"] == 1
        assert CrossStoreOutboxEvent.query.filter_by(entity_id=result.message_id).count() == 0
        assert CrossStoreMaterializationState.query.filter_by(entity_id=result.message_id).count() == 0


def test_partial_profile_deletion_blocks_retry(app, monkeypatch):
    import hashlib
    import hmac
    from models import DataDeletionTombstone

    with app.app_context():
        result, owner = _save(app, monkeypatch)
        runtime = app.extensions["dle_runtime"]
        identity = runtime.ownership.identity
        key = identity.installation_id if identity is not None else runtime.instance_id
        digest = hmac.new(str(key).encode(), f"user:{owner}".encode(), hashlib.sha256).hexdigest()
        db.session.add(DataDeletionTombstone(subject_type="user", subject_digest=digest,
            policy_version="test-v1", status="partial_failure", store_status={}))
        db.session.commit()
        calls = []
        monkeypatch.setattr("backend.services.rag_service.get_rag_service",
            lambda: SimpleNamespace(store_chat_message=lambda *a, **k: calls.append(a) or True))
        assert CrossStoreMaterializationDispatcher(db.session).run_once()["failed"] == 1
        assert calls == []
        assert db.session.get(ChatMessage, uuid.UUID(result.message_id)) is not None


def test_crashed_claim_is_recovered_without_duplicate_vectors(app, monkeypatch):
    from backend.storage.outbox import CrossStoreOutbox

    with app.app_context():
        result, _ = _save(app, monkeypatch)
        event = CrossStoreOutbox(db.session).claim_batch(limit=1)[0]
        event.locked_at = datetime.now(UTC) - timedelta(minutes=10)
        db.session.commit()
        db.session.remove()
        vectors = {}
        def store(session_id, message_id, role, content, **kwargs):
            vectors[message_id] = content
            return True
        monkeypatch.setattr("backend.services.rag_service.get_rag_service",
                            lambda: SimpleNamespace(store_chat_message=store))
        assert CrossStoreMaterializationDispatcher(db.session).run_once()["succeeded"] == 1
        assert vectors == {result.message_id: "synthetic private transcript"}

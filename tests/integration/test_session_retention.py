"""Session retention must not leave indexed copies or claim a fake archive."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
import uuid

from backend.retention_service import DataRetentionService, RetentionCategory
from extensions import db
from models import ChatMessage, ChatSession
from tests.conftest import create_test_user


def _session(app):
    user_id = create_test_user(
        username="retention-owner",
        email="retention-owner@example.com",
        password="SecureTest789$#@",
    )
    session_id = uuid.uuid4()
    db.session.add(
        ChatSession(
            id=session_id,
            user_id=user_id,
            mode="chat",
            created_at=datetime.now(UTC) - timedelta(days=100),
        )
    )
    db.session.add(ChatMessage(session_id=session_id, role="user", content="synthetic"))
    db.session.commit()
    return session_id


def _service():
    service = DataRetentionService()
    service.set_policy(RetentionCategory.SESSIONS, 90, archive_before_delete=False)
    return service


def test_session_cleanup_removes_index_before_transcript(app, monkeypatch):
    with app.app_context():
        session_id = _session(app)
        indexed = {str(session_id)}

        def remove_index(value):
            assert db.session.get(ChatSession, session_id) is not None
            indexed.remove(value)

        monkeypatch.setattr(
            "backend.services.rag_service.get_rag_service",
            lambda: SimpleNamespace(delete_chat_session=remove_index),
        )
        result = _service().cleanup_sessions()
        assert result["status"] == "success"
        assert result["deleted_count"] == 1
        assert result["archived_count"] == 0
        assert indexed == set()
        assert db.session.get(ChatSession, session_id) is None
        assert ChatMessage.query.filter_by(session_id=session_id).count() == 0


def test_session_cleanup_preserves_transcript_when_index_unavailable(app, monkeypatch):
    with app.app_context():
        session_id = _session(app)

        def fail(_value):
            raise RuntimeError("synthetic-index-secret")

        monkeypatch.setattr(
            "backend.services.rag_service.get_rag_service",
            lambda: SimpleNamespace(delete_chat_session=fail),
        )
        result = _service().cleanup_sessions()
        assert result["status"] == "error"
        assert result["deleted_count"] == 0
        assert "synthetic-index-secret" not in repr(result)
        assert db.session.get(ChatSession, session_id) is not None
        assert ChatMessage.query.filter_by(session_id=session_id).count() == 1


def test_archive_required_blocks_deletion_and_dry_run_is_read_only(app, monkeypatch):
    with app.app_context():
        session_id = _session(app)

        def unexpected_index():
            raise AssertionError("retention should not contact the index")

        monkeypatch.setattr("backend.services.rag_service.get_rag_service", unexpected_index)
        service = DataRetentionService()
        dry = service.cleanup_sessions(dry_run=True)
        assert dry["status"] == "success"
        assert dry["eligible_count"] == 1
        result = service.cleanup_sessions()
        assert result["status"] == "error"
        assert result["archived_count"] == result["deleted_count"] == 0
        assert db.session.get(ChatSession, session_id) is not None

"""Session retention must not leave indexed copies or claim a fake archive."""

from datetime import UTC, datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from types import SimpleNamespace
import uuid

from backend.retention_service import DataRetentionService, RetentionCategory
from backend.llm_gateway.gateway import LLMGateway
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


def test_session_cleanup_reports_remaining_batch(app, monkeypatch):
    with app.app_context():
        session_id = _session(app)
        owner = db.session.get(ChatSession, session_id).user_id
        second_id = uuid.uuid4()
        db.session.add(ChatSession(id=second_id, user_id=owner, mode="chat",
                                   created_at=datetime.now(UTC) - timedelta(days=99)))
        db.session.commit()
        monkeypatch.setattr("backend.retention_service.SESSION_CLEANUP_BATCH_SIZE", 1)
        monkeypatch.setattr("backend.services.rag_service.get_rag_service",
                            lambda: SimpleNamespace(delete_chat_session=lambda _: None))
        result = _service().cleanup_sessions()
        assert result["status"] == "partial"
        assert result["eligible_count"] == 2
        assert result["deleted_count"] == 1
        assert db.session.get(ChatSession, second_id) is not None


def test_concurrent_chat_write_cannot_recreate_deleted_index(app, monkeypatch):
    import backend.storage.chat_index_coordination as coordination

    with app.app_context():
        session_id = _session(app)
        user_id = db.session.get(ChatSession, session_id).user_id

    cleanup_holds_lock = Event()
    write_waiting = Event()
    indexed = {str(session_id)}
    writes = []
    real_guard = coordination.chat_index_guard

    def guard(root, **kwargs):
        if cleanup_holds_lock.is_set():
            write_waiting.set()
        return real_guard(root, **kwargs)

    def delete_session(value):
        cleanup_holds_lock.set()
        assert write_waiting.wait(8)
        indexed.remove(value)

    rag = SimpleNamespace(
        delete_chat_session=delete_session,
        store_chat_message=lambda *args, **kwargs: writes.append(args) or True,
    )
    monkeypatch.setattr(coordination, "chat_index_guard", guard)
    monkeypatch.setattr("backend.services.rag_service.get_rag_service", lambda: rag)

    def cleanup():
        with app.app_context():
            return _service().cleanup_sessions()

    def write():
        assert cleanup_holds_lock.wait(8)
        with app.app_context():
            return asyncio.run(
                LLMGateway(db_session=db.session)._save_chat_message(
                    str(session_id), user_id, "user", "synthetic concurrent message"
                )
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        cleanup_future = executor.submit(cleanup)
        write_future = executor.submit(write)
        cleanup_result = cleanup_future.result(timeout=20)
        write_result = write_future.result(timeout=20)

    assert cleanup_result["status"] == "success"
    assert write_result.rag_status == "failed"
    assert indexed == set()
    assert writes == []
    with app.app_context():
        assert db.session.get(ChatSession, session_id) is None

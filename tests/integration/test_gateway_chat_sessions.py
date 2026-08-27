import uuid

import pytest

from backend.llm_gateway.gateway import LLMGateway
from extensions import db
from models import ChatMessage, ChatSession, User
from tests.conftest import create_test_user


def _authenticated_user_id(app) -> int:
    with app.app_context():
        user = User.query.filter_by(username="testuser").one()
        return int(user.id)


def test_desktop_session_create_is_idempotent_and_principal_owned(
    app,
    authenticated_client,
):
    session_id = str(uuid.uuid4())

    created = authenticated_client.post(
        "/api/v1/gateway/sessions",
        json={"session_id": session_id, "mode": "chat"},
    )
    repeated = authenticated_client.post(
        "/api/v1/gateway/sessions",
        json={"session_id": session_id, "mode": "chat"},
    )

    assert created.status_code == 201, created.get_json()
    assert repeated.status_code == 200, repeated.get_json()
    assert created.get_json()["session"]["id"] == session_id
    assert repeated.get_json()["session"]["id"] == session_id
    assert created.get_json()["created"] is True
    assert repeated.get_json()["created"] is False

    user_id = _authenticated_user_id(app)
    with app.app_context():
        sessions = ChatSession.query.filter_by(id=uuid.UUID(session_id)).all()
        assert len(sessions) == 1
        assert sessions[0].user_id == user_id


def test_desktop_session_create_hides_another_principals_session(
    app,
    authenticated_client,
):
    session_id = uuid.uuid4()
    with app.app_context():
        other_id = create_test_user(
            username="chat-session-other",
            email="chat-session-other@example.com",
            password="SecureTest789$#@",
        )
        db.session.add(ChatSession(id=session_id, user_id=other_id, mode="chat"))
        db.session.commit()

    response = authenticated_client.post(
        "/api/v1/gateway/sessions",
        json={"session_id": str(session_id), "mode": "chat"},
    )

    assert response.status_code == 404
    assert response.get_json()["code"] == "CHAT_SESSION_NOT_FOUND"


@pytest.mark.asyncio
async def test_chat_message_persistence_rejects_wrong_principal(app):
    session_id = uuid.uuid4()
    with app.app_context():
        owner_id = create_test_user(
            username="chat-session-owner",
            email="chat-session-owner@example.com",
            password="SecureTest789$#@",
        )
        other_id = create_test_user(
            username="chat-session-writer",
            email="chat-session-writer@example.com",
            password="SecureTest789$#@",
        )
        db.session.add(ChatSession(id=session_id, user_id=owner_id, mode="chat"))
        db.session.commit()

        gateway = LLMGateway(db_session=db.session)
        result = await gateway._save_chat_message(
            str(session_id),
            other_id,
            "user",
            "Must not cross the principal boundary",
        )

        assert result.ok is False
        assert result.code == "CHAT_SESSION_NOT_FOUND"
        assert ChatMessage.query.filter_by(session_id=session_id).count() == 0


@pytest.mark.asyncio
async def test_chat_message_persistence_returns_correlation_receipt(app):
    session_id = uuid.uuid4()
    run_id = uuid.uuid4()
    with app.app_context():
        user_id = create_test_user(
            username="chat-session-receipt",
            email="chat-session-receipt@example.com",
            password="SecureTest789$#@",
        )
        db.session.add(ChatSession(id=session_id, user_id=user_id, mode="chat"))
        db.session.commit()

        gateway = LLMGateway(db_session=db.session)
        result = await gateway._save_chat_message(
            str(session_id),
            user_id,
            "user",
            "Correlate this transcript row",
            str(run_id),
        )

        assert result.ok is True
        assert result.code == "CHAT_MESSAGE_PERSISTED"
        assert result.session_id == str(session_id)
        assert result.run_id == str(run_id)
        message = db.session.get(ChatMessage, uuid.UUID(result.message_id))
        assert message is not None
        assert message.run_id == run_id

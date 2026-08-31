"""Principal-owned durable chat-session lifecycle."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from models import ChatSession


class ChatSessionError(RuntimeError):
    """Base error for explicit chat-session lifecycle failures."""

    code = "CHAT_SESSION_ERROR"


class ChatSessionInvalid(ChatSessionError):
    code = "INVALID_CHAT_SESSION"


class ChatSessionNotFound(ChatSessionError):
    code = "CHAT_SESSION_NOT_FOUND"


class ChatSessionPersistenceError(ChatSessionError):
    code = "CHAT_SESSION_PERSISTENCE_FAILED"


@dataclass(frozen=True)
class ChatSessionEnsureResult:
    session: ChatSession
    created: bool


def normalize_chat_mode(value: str | None) -> str:
    normalized = str(value or "standard").strip().lower()
    compatibility = {
        "chat": "standard",
        "trace": "standard",
        "explain": "standard",
        "quad": "enhanced",
    }
    normalized = compatibility.get(normalized, normalized)
    if normalized not in {"standard", "enhanced", "local_review"}:
        raise ChatSessionInvalid("Unsupported governed chat mode")
    return normalized


def _parse_session_id(value: str | uuid.UUID | None) -> uuid.UUID:
    if value is None:
        return uuid.uuid4()
    try:
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ChatSessionInvalid("Chat session ID must be a UUID") from exc


def ensure_chat_session(
    db_session,
    *,
    session_id: str | uuid.UUID | None,
    user_id: int | None,
    mode: str,
) -> ChatSessionEnsureResult:
    """Create or resolve exactly one session owned by ``user_id``."""

    if user_id is None:
        raise ChatSessionInvalid("An authenticated owner is required")

    parsed_id = _parse_session_id(session_id)
    normalized_mode = normalize_chat_mode(mode)
    existing = db_session.get(ChatSession, parsed_id)
    if existing is not None:
        if int(existing.user_id) != int(user_id):
            # Do not disclose another principal's session existence.
            raise ChatSessionNotFound("Chat session was not found")
        if existing.mode != normalized_mode:
            existing.mode = normalized_mode
            try:
                db_session.commit()
            except SQLAlchemyError as exc:
                db_session.rollback()
                raise ChatSessionPersistenceError(
                    "Chat session mode could not be persisted"
                ) from exc
        return ChatSessionEnsureResult(session=existing, created=False)

    record = ChatSession(
        id=parsed_id,
        user_id=int(user_id),
        mode=normalized_mode,
    )
    db_session.add(record)
    try:
        db_session.commit()
        return ChatSessionEnsureResult(session=record, created=True)
    except IntegrityError as exc:
        db_session.rollback()
        concurrent = db_session.get(ChatSession, parsed_id)
        if concurrent is not None and int(concurrent.user_id) == int(user_id):
            return ChatSessionEnsureResult(session=concurrent, created=False)
        if concurrent is not None:
            raise ChatSessionNotFound("Chat session was not found") from exc
        raise ChatSessionPersistenceError("Chat session could not be persisted") from exc
    except SQLAlchemyError as exc:
        db_session.rollback()
        raise ChatSessionPersistenceError("Chat session could not be persisted") from exc

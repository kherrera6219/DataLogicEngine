"""Recover chat vectors from retained authority rows without copying text."""

from __future__ import annotations

import hashlib
import hmac
import json
from uuid import UUID

from backend.storage.outbox import CHAT_INDEX_MAX_ATTEMPTS, CrossStoreOutbox


def source_revision(message, session) -> str:
    source = [
        str(message.id),
        str(session.id),
        str(session.user_id),
        message.role,
        message.content,
    ]
    return hashlib.sha256(
        json.dumps(source, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def enqueue_chat_index(session, message, chat_session) -> None:
    CrossStoreOutbox(session).enqueue(
        entity_type="chat_message",
        entity_id=str(message.id),
        destination="chroma",
        operation="upsert_chat_message",
        schema_version="chat-index-v1",
        source_revision=source_revision(message, chat_session),
        payload={},
        correlation_id=str(message.id),
    )


def complete_immediate_index(session, message_id: str) -> None:
    """Complete an unclaimed receipt while the caller holds the index lock."""
    from models import CrossStoreOutboxEvent

    event = (
        session.query(CrossStoreOutboxEvent)
        .filter_by(
            entity_type="chat_message",
            entity_id=message_id,
            destination="chroma",
            operation="upsert_chat_message",
        )
        .one()
    )
    if event.status in {"pending", "failed"}:
        CrossStoreOutbox(session).mark_succeeded(
            event, observed_revision=event.source_revision
        )
        session.commit()


def deliver_chat_index(event) -> str:
    from flask import current_app
    from sqlalchemy.orm import object_session

    from backend.services.rag_service import get_rag_service
    from backend.storage.chat_index_coordination import chat_index_guard
    from backend.storage.materialization_dispatcher import MaterializationDeliveryError
    from models import ChatMessage, ChatSession, DataDeletionTombstone

    session = object_session(event)
    if session is None or event.entity_type != "chat_message":
        raise MaterializationDeliveryError("chat_index_source_invalid")
    if event.attempts > CHAT_INDEX_MAX_ATTEMPTS:
        raise MaterializationDeliveryError("chat_index_retry_exhausted")
    with chat_index_guard(current_app.extensions["dle_runtime"].runtime_root):
        row = (
            session.query(ChatMessage, ChatSession)
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .filter(ChatMessage.id == UUID(event.entity_id))
            .populate_existing()
            .one_or_none()
        )
        # A deleted authority row must never be reconstructed from a queue.
        if row is None:
            return event.source_revision
        message, chat_session = row
        runtime = current_app.extensions["dle_runtime"]
        identity = runtime.ownership.identity
        key = identity.installation_id if identity is not None else runtime.instance_id
        digest = hmac.new(
            str(key).encode("utf-8"),
            f"user:{chat_session.user_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if (
            session.query(DataDeletionTombstone.deletion_id)
            .filter_by(subject_type="user", subject_digest=digest)
            .first()
            is not None
        ):
            raise MaterializationDeliveryError("chat_index_owner_deleted")
        if (
            message.role not in {"user", "assistant"}
            or source_revision(message, chat_session) != event.source_revision
        ):
            raise MaterializationDeliveryError("chat_index_source_changed")
        if not get_rag_service().store_chat_message(
            str(chat_session.id),
            str(message.id),
            message.role,
            message.content,
            user_id=str(chat_session.user_id),
        ):
            raise MaterializationDeliveryError("chat_index_write_unacknowledged")
        return event.source_revision


def remove_session_retries(session, session_id) -> None:
    from sqlalchemy import select
    from models import (
        ChatMessage,
        CrossStoreMaterializationState,
        CrossStoreOutboxEvent,
    )

    message_ids = select(ChatMessage.id).where(ChatMessage.session_id == session_id)
    rows = session.scalars(message_ids).yield_per(500)

    def remove(ids):
        for model in (CrossStoreOutboxEvent, CrossStoreMaterializationState):
            session.query(model).filter(
                model.entity_type == "chat_message", model.entity_id.in_(ids)
            ).delete(synchronize_session=False)

    ids = []
    for value in rows:
        ids.append(str(value))
        if len(ids) == 500:
            remove(ids)
            ids = []
    if ids:
        remove(ids)

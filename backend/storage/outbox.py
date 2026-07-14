"""Transactional PostgreSQL outbox and cross-store reconciliation ledger."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import json
import re
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.storage.data_contracts import CrossStoreRecord
from models import CrossStoreMaterializationState, CrossStoreOutboxEvent


_DESTINATIONS = {"neo4j", "chroma", "minio"}
_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,119}$")
_SAFE_REASON_RE = re.compile(r"^[a-z0-9][a-z0-9_:.-]{0,119}$")


def canonical_payload_sha256(payload: dict[str, Any]) -> str:
    """Hash a JSON payload independently of dictionary insertion order."""

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _required(value: object, reason: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(reason)
    return normalized


def _safe_reason(value: object) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if _SAFE_REASON_RE.fullmatch(normalized) else "delivery_failed"


class CrossStoreOutbox:
    """Enqueue and reconcile required materializations in the caller's SQL tx."""

    def __init__(self, session: Session):
        self.session = session

    def enqueue(
        self,
        *,
        entity_type: str,
        entity_id: str,
        destination: str,
        operation: str,
        schema_version: str,
        source_revision: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> CrossStoreOutboxEvent:
        normalized_destination = _required(destination, "destination_required").lower()
        if normalized_destination not in _DESTINATIONS:
            raise ValueError("destination_not_supported")
        normalized_entity_type = _required(entity_type, "entity_type_required").lower()
        normalized_operation = _required(operation, "operation_required").lower()
        if not _IDENTIFIER_RE.fullmatch(normalized_entity_type):
            raise ValueError("entity_type_invalid")
        if not _IDENTIFIER_RE.fullmatch(normalized_operation):
            raise ValueError("operation_invalid")
        if not isinstance(payload, dict):
            raise ValueError("payload_object_required")

        payload_hash = canonical_payload_sha256(payload)
        record = CrossStoreRecord(
            entity_type=normalized_entity_type,
            entity_id=_required(entity_id, "entity_id_required"),
            schema_version=_required(schema_version, "schema_version_required"),
            source_revision=_required(source_revision, "source_revision_required"),
            correlation_id=_required(correlation_id, "correlation_id_required"),
            occurred_at=datetime.now(UTC),
            payload_sha256=payload_hash,
        )
        existing = (
            self.session.query(CrossStoreOutboxEvent)
            .filter_by(
                entity_type=record.entity_type,
                entity_id=record.entity_id,
                destination=normalized_destination,
                operation=normalized_operation,
                source_revision=record.source_revision,
            )
            .one_or_none()
        )
        if existing is not None:
            if existing.payload_sha256 != payload_hash:
                raise ValueError("source_revision_payload_hash_conflict")
            return existing

        event = CrossStoreOutboxEvent(
            entity_type=record.entity_type,
            entity_id=record.entity_id,
            destination=normalized_destination,
            operation=normalized_operation,
            schema_version=record.schema_version,
            source_revision=record.source_revision,
            correlation_id=record.correlation_id,
            payload=payload,
            payload_sha256=payload_hash,
            status="pending",
            attempts=0,
        )
        self.session.add(event)

        state = self._state_for(
            record.entity_type,
            record.entity_id,
            normalized_destination,
        )
        if state is None:
            state = CrossStoreMaterializationState(
                entity_type=record.entity_type,
                entity_id=record.entity_id,
                destination=normalized_destination,
                schema_version=record.schema_version,
                source_revision=record.source_revision,
                payload_sha256=payload_hash,
                state="pending",
                attempts=0,
            )
            self.session.add(state)
        else:
            state.schema_version = record.schema_version
            state.source_revision = record.source_revision
            state.payload_sha256 = payload_hash
            state.state = "pending"
            state.observed_revision = None
            state.safe_reason = None
            state.completed_at = None
        self.session.flush()
        return event

    def claim_batch(
        self,
        *,
        destination: str | None = None,
        limit: int = 100,
        processing_timeout_seconds: int = 300,
    ) -> list[CrossStoreOutboxEvent]:
        """Claim retryable work; PostgreSQL workers use skip-locked row claims."""

        if limit < 1 or limit > 1000:
            raise ValueError("claim_limit_invalid")
        if processing_timeout_seconds < 30 or processing_timeout_seconds > 86_400:
            raise ValueError("processing_timeout_invalid")
        now = datetime.now(UTC)
        stale_processing = now - timedelta(seconds=processing_timeout_seconds)
        query = self.session.query(CrossStoreOutboxEvent).filter(
            or_(
                (
                    CrossStoreOutboxEvent.status.in_(("pending", "failed"))
                    & or_(
                        CrossStoreOutboxEvent.available_at.is_(None),
                        CrossStoreOutboxEvent.available_at <= now,
                    )
                ),
                (
                    (CrossStoreOutboxEvent.status == "processing")
                    & (CrossStoreOutboxEvent.locked_at <= stale_processing)
                ),
            ),
        )
        if destination is not None:
            normalized_destination = str(destination).strip().lower()
            if normalized_destination not in _DESTINATIONS:
                raise ValueError("destination_not_supported")
            query = query.filter(CrossStoreOutboxEvent.destination == normalized_destination)
        events = (
            query.order_by(
                CrossStoreOutboxEvent.created_at,
                CrossStoreOutboxEvent.id,
            )
            .with_for_update(skip_locked=True)
            .limit(limit)
            .all()
        )
        for event in events:
            event.status = "processing"
            event.attempts = int(event.attempts or 0) + 1
            event.locked_at = now
            event.safe_reason = None
            state = self._state_for(event.entity_type, event.entity_id, event.destination)
            if state is not None:
                state.state = "processing"
                state.attempts = event.attempts
                state.last_attempt_at = now
                state.safe_reason = None
        self.session.flush()
        return events

    def mark_succeeded(
        self,
        event: CrossStoreOutboxEvent,
        *,
        observed_revision: str,
    ) -> None:
        now = datetime.now(UTC)
        event.status = "succeeded"
        event.completed_at = now
        event.locked_at = None
        event.available_at = None
        event.safe_reason = None
        state = self._required_state(event)
        state.state = "succeeded"
        state.observed_revision = _required(
            observed_revision,
            "observed_revision_required",
        )
        state.source_revision = event.source_revision
        state.payload_sha256 = event.payload_sha256
        state.attempts = event.attempts
        state.last_attempt_at = now
        state.completed_at = now
        state.safe_reason = None
        self.session.flush()

    def mark_failed(
        self,
        event: CrossStoreOutboxEvent,
        *,
        safe_reason: str,
    ) -> None:
        now = datetime.now(UTC)
        delay_seconds = min(300, 2 ** max(1, int(event.attempts or 1)))
        reason = _safe_reason(safe_reason)
        event.status = "failed"
        event.locked_at = None
        event.completed_at = None
        event.available_at = now + timedelta(seconds=delay_seconds)
        event.safe_reason = reason
        state = self._required_state(event)
        state.state = "failed"
        state.attempts = event.attempts
        state.last_attempt_at = now
        state.completed_at = None
        state.safe_reason = reason
        self.session.flush()

    def _state_for(
        self,
        entity_type: str,
        entity_id: str,
        destination: str,
    ) -> CrossStoreMaterializationState | None:
        return (
            self.session.query(CrossStoreMaterializationState)
            .filter_by(
                entity_type=entity_type,
                entity_id=entity_id,
                destination=destination,
            )
            .one_or_none()
        )

    def _required_state(
        self,
        event: CrossStoreOutboxEvent,
    ) -> CrossStoreMaterializationState:
        state = self._state_for(event.entity_type, event.entity_id, event.destination)
        if state is None:
            raise RuntimeError("materialization_state_missing")
        return state

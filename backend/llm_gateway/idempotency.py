"""Durable PostgreSQL authority for external gateway idempotency."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import json
from typing import Any
import uuid

from sqlalchemy.exc import IntegrityError


@dataclass(frozen=True, slots=True)
class IdempotencyDecision:
    disposition: str
    record: Any


def request_fingerprint(payload: dict[str, Any]) -> str:
    """Hash execution-affecting fields while excluding transport retry identity."""
    canonical_payload = {
        key: value
        for key, value in payload.items()
        if key not in {"idempotency_key", "request_id"}
    }
    canonical = json.dumps(
        canonical_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _is_expired(record: Any, now: datetime) -> bool:
    expiry = getattr(record, "expires_at", None)
    if expiry is None:
        return False
    compare_now = now.replace(tzinfo=None) if expiry.tzinfo is None else now
    return expiry <= compare_now


def begin_idempotent_request(
    session,
    model_cls,
    *,
    api_key_id: Any,
    idempotency_key: str,
    request_id: str,
    payload: dict[str, Any],
    retention_hours: int = 24,
) -> IdempotencyDecision:
    """Create one pending authority row or classify the existing row."""
    key = str(idempotency_key or "").strip()
    if not 8 <= len(key) <= 128:
        raise ValueError("idempotency_key must contain 8 to 128 characters")
    client_id = uuid.UUID(str(api_key_id))
    digest = request_fingerprint(payload)
    now = datetime.now(UTC)

    def existing_record():
        return session.query(model_cls).filter_by(
            api_key_id=client_id,
            idempotency_key=key,
        ).first()

    existing = existing_record()
    if existing is not None and _is_expired(existing, now):
        session.delete(existing)
        session.commit()
        existing = None
    if existing is not None:
        if existing.request_sha256 != digest:
            return IdempotencyDecision("conflict", existing)
        if existing.state in {"completed", "failed"} and existing.response_payload is not None:
            return IdempotencyDecision("replay", existing)
        return IdempotencyDecision("in_progress", existing)

    record = model_cls(
        api_key_id=client_id,
        idempotency_key=key,
        request_sha256=digest,
        request_id=str(request_id),
        state="pending",
        expires_at=now + timedelta(hours=max(1, min(168, int(retention_hours)))),
    )
    session.add(record)
    try:
        session.commit()
        return IdempotencyDecision("created", record)
    except IntegrityError:
        session.rollback()
        raced = existing_record()
        if raced is None:
            raise
        if raced.request_sha256 != digest:
            return IdempotencyDecision("conflict", raced)
        if raced.state in {"completed", "failed"} and raced.response_payload is not None:
            return IdempotencyDecision("replay", raced)
        return IdempotencyDecision("in_progress", raced)


def complete_idempotent_request(
    session,
    record: Any,
    *,
    response_payload: dict[str, Any],
    response_status: int,
    run_id: str | None = None,
    failed: bool = False,
) -> None:
    """Commit the replayable terminal envelope after governed work finishes."""
    record.state = "failed" if failed else "completed"
    record.response_status = int(response_status)
    record.response_payload = response_payload
    record.updated_at = datetime.now(UTC)
    try:
        record.run_id = str(uuid.UUID(str(run_id))) if run_id else None
    except (TypeError, ValueError, AttributeError):
        record.run_id = None
    session.commit()

"""Encrypted, bounded desktop replay queue for transient provider failures."""

from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken

from backend.security.dpapi_store import decrypt_data, encrypt_data, is_available


REPLAYABLE_FAILURE_CLASSES = frozenset({"network", "provider_outage", "timeout"})
QUEUE_SCHEMA_VERSION = "offline-queue.v2"


def _queue_path() -> Path:
    explicit_path = os.environ.get("DATALOGIC_OFFLINE_QUEUE_PATH")
    if explicit_path:
        return Path(explicit_path)
    settings_path = os.environ.get("DATALOGIC_STORAGE_SETTINGS_PATH")
    if settings_path:
        return Path(settings_path).resolve().parent / "offline_queue.json"
    return Path.cwd() / "offline_queue.json"


def _bounded_env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(maximum, int(os.environ.get(name, default))))
    except (TypeError, ValueError):
        return default


def _fallback_fernet() -> Fernet:
    secret = (
        os.environ.get("ENCRYPTION_KEK_SECRET")
        or os.environ.get("SESSION_SECRET")
        or os.environ.get("FLASK_SECRET_KEY")
    )
    production_desktop = (
        os.environ.get("FLASK_ENV", "").lower() == "production"
        and os.environ.get("IS_DESKTOP_APP", "false").lower() == "true"
    )
    if production_desktop or not secret:
        raise RuntimeError("DPAPI is required for the desktop production replay queue")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def _encrypt_payload(payload: dict[str, Any]) -> tuple[str, str, int]:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload_bytes = serialized.encode("utf-8")
    if is_available():
        encrypted = encrypt_data(serialized)
        if not encrypted:
            raise RuntimeError("DPAPI replay queue encryption failed")
        return "dpapi:v1", encrypted, len(payload_bytes)
    encrypted = _fallback_fernet().encrypt(payload_bytes).decode("ascii")
    return "fernet:v1", encrypted, len(payload_bytes)


def _decrypt_payload(item: dict[str, Any]) -> dict[str, Any]:
    encryption = str(item.get("encryption") or "")
    ciphertext = str(item.get("payload_ciphertext") or "")
    if encryption == "dpapi:v1":
        serialized = decrypt_data(ciphertext)
        if not serialized:
            raise ValueError("DPAPI replay queue decryption failed")
    elif encryption == "fernet:v1":
        try:
            serialized = _fallback_fernet().decrypt(ciphertext.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Replay queue ciphertext failed authentication") from exc
    else:
        raise ValueError("Unsupported replay queue encryption")
    payload = json.loads(serialized)
    if not isinstance(payload, dict):
        raise ValueError("Replay queue payload is not an object")
    return payload


def _parse_datetime(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _read_items() -> list[dict[str, Any]]:
    path = _queue_path()
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(payload, dict) or payload.get("schema_version") != QUEUE_SCHEMA_VERSION:
        return []
    items = [item for item in payload.get("items") or [] if isinstance(item, dict)]
    now = datetime.now(UTC)
    changed = False
    for item in items:
        expires_at = _parse_datetime(item.get("expires_at"))
        if expires_at and expires_at <= now and item.get("status") == "pending":
            item["status"] = "expired"
            item["updated_at"] = now.isoformat()
            changed = True
    if changed:
        _write_items(items)
    return items


def _write_items(items: list[dict[str, Any]]) -> None:
    path = _queue_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        {"schema_version": QUEUE_SCHEMA_VERSION, "items": items},
        indent=2,
        ensure_ascii=False,
    )
    max_bytes = _bounded_env_int("DATALOGIC_OFFLINE_QUEUE_MAX_BYTES", 10_000_000, 1_024, 100_000_000)
    if len(serialized.encode("utf-8")) > max_bytes:
        raise ValueError("Offline replay queue size limit exceeded")
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8")
    os.replace(temporary, path)


def enqueue_chat_request(
    payload: dict[str, Any],
    reason: str = "network",
    *,
    failure_class: str | None = None,
) -> dict[str, Any]:
    """Encrypt and persist a classified transient request for later replay."""
    classification = str(failure_class or reason).strip().lower()
    if classification not in REPLAYABLE_FAILURE_CLASSES:
        raise ValueError(f"Failure class {classification!r} is not replayable")

    items = _read_items()
    max_items = _bounded_env_int("DATALOGIC_OFFLINE_QUEUE_MAX_ITEMS", 100, 1, 10_000)
    active_items = [item for item in items if item.get("status") == "pending"]
    if len(active_items) >= max_items:
        raise ValueError("Offline replay queue item limit exceeded")

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    idempotency_key = str(payload.get("request_id") or hashlib.sha256(canonical.encode("utf-8")).hexdigest())
    duplicate = next(
        (
            item
            for item in active_items
            if item.get("idempotency_key") == idempotency_key
        ),
        None,
    )
    if duplicate is not None:
        return _public_item(duplicate)

    encryption, ciphertext, payload_bytes = _encrypt_payload(payload)
    now = datetime.now(UTC)
    expiry_hours = _bounded_env_int("DATALOGIC_OFFLINE_QUEUE_EXPIRY_HOURS", 72, 1, 24 * 30)
    item = {
        "id": str(uuid4()),
        "kind": "gateway_chat",
        "status": "pending",
        "failure_class": classification,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=expiry_hours)).isoformat(),
        "attempts": 0,
        "last_error": None,
        "idempotency_key": idempotency_key,
        "payload_bytes": payload_bytes,
        "encryption": encryption,
        "payload_ciphertext": ciphertext,
    }
    items.append(item)
    _write_items(items)
    return _public_item(item)


def _public_item(item: dict[str, Any], *, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    public = {
        key: value
        for key, value in item.items()
        if key not in {"payload_ciphertext", "encryption"}
    }
    public["encrypted"] = bool(item.get("payload_ciphertext"))
    if payload is not None:
        public["payload"] = payload
    return public


def list_queue(*, include_payload: bool = False) -> dict[str, Any]:
    """Return queue metadata; decrypted payload is opt-in for internal replay."""
    items = _read_items()
    public_items: list[dict[str, Any]] = []
    for item in items:
        payload = _decrypt_payload(item) if include_payload else None
        public_items.append(_public_item(item, payload=payload))
    counts: dict[str, int] = {}
    for item in public_items:
        status = str(item.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return {
        "items": public_items,
        "counts": counts,
        "snapshot_at": datetime.now(UTC).isoformat(),
    }


def mark_item(
    item_id: str,
    status: str,
    error: str | None = None,
    response: dict[str, Any] | None = None,
) -> None:
    """Update a queue item after replay without persisting response content."""
    items = _read_items()
    now = datetime.now(UTC).isoformat()
    for item in items:
        if item.get("id") == item_id:
            item["status"] = status
            item["updated_at"] = now
            item["last_error"] = str(error or "")[:500] or None
            if response is not None:
                item["response"] = {
                    key: response.get(key)
                    for key in ("run_id", "provider_used", "model_used")
                    if response.get(key) is not None
                }
            if status == "pending":
                item["attempts"] = int(item.get("attempts") or 0) + 1
            break
    _write_items(items)


def delete_item(item_id: str) -> bool:
    items = _read_items()
    retained = [item for item in items if item.get("id") != item_id]
    if len(retained) == len(items):
        return False
    _write_items(retained)
    return True

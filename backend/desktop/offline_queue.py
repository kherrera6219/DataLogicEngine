"""Durable desktop offline queue for local-first chat replay."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4


def _queue_path() -> Path:
    explicit_path = os.environ.get("DATALOGIC_OFFLINE_QUEUE_PATH")
    if explicit_path:
        return Path(explicit_path)

    settings_path = os.environ.get("DATALOGIC_STORAGE_SETTINGS_PATH")
    if settings_path:
        return Path(settings_path).resolve().parent / "offline_queue.json"

    return Path.cwd() / "offline_queue.json"


def _read_items() -> list[dict[str, Any]]:
    path = _queue_path()
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _write_items(items: list[dict[str, Any]]) -> None:
    path = _queue_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, indent=2), encoding="utf-8")


def enqueue_chat_request(payload: dict[str, Any], reason: str = "network_unavailable") -> dict[str, Any]:
    """Persist a failed desktop chat request for later replay."""
    items = _read_items()
    item = {
        "id": str(uuid4()),
        "kind": "gateway_chat",
        "status": "pending",
        "reason": reason,
        "created_at": datetime.now(UTC).isoformat(),
        "attempts": 0,
        "last_error": None,
        "payload": payload,
    }
    items.append(item)
    _write_items(items)
    return item


def list_queue() -> dict[str, Any]:
    """Return queue items plus a compact status summary."""
    items = _read_items()
    counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return {
        "path": str(_queue_path()),
        "items": items,
        "counts": counts,
    }


def mark_item(item_id: str, status: str, error: str | None = None, response: dict[str, Any] | None = None) -> None:
    """Update a queue item after replay."""
    items = _read_items()
    now = datetime.now(UTC).isoformat()
    for item in items:
        if item.get("id") == item_id:
            item["status"] = status
            item["updated_at"] = now
            item["last_error"] = error
            if response is not None:
                item["response"] = response
            if status == "pending":
                item["attempts"] = int(item.get("attempts") or 0) + 1
            break
    _write_items(items)

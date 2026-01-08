from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .base import AuditEvent, AuditStore


class FileAuditStore(AuditStore):
    """Append-only JSONL audit log with hash chaining.

    This is "compliance-grade" in the sense that it is:
      - append-only
      - includes a deterministic hash chain (tamper-evident)
    For higher assurance, store logs on WORM media and/or sign batches.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash: Optional[str] = None
        if self.path.exists():
            self._last_hash = self._read_last_hash()

    async def append(self, event: AuditEvent) -> AuditEvent:
        if event.payload is None:
            event.payload = {}
        if not event.ts:
            event.ts = datetime.now(timezone.utc).isoformat()
        event.prev_hash = self._last_hash
        event.hash = _hash_event(event)
        line = json.dumps(event.__dict__, default=str, sort_keys=True)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        self._last_hash = event.hash
        return event

    def _read_last_hash(self) -> Optional[str]:
        last = None
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last = line
        if not last:
            return None
        try:
            data = json.loads(last)
            return data.get("hash")
        except Exception:
            return None


def _hash_event(e: AuditEvent) -> str:
    h = hashlib.sha256()
    payload = {
        "event_id": e.event_id,
        "ts": e.ts,
        "kind": e.kind,
        "actor": e.actor,
        "session_id": e.session_id,
        "ka_id": e.ka_id,
        "layer": e.layer,
        "coordinate": e.coordinate,
        "payload": e.payload or {},
        "prev_hash": e.prev_hash,
    }
    h.update(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return h.hexdigest()

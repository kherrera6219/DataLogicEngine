from __future__ import annotations

from typing import Dict, Optional
from datetime import datetime, timezone

from .base import MemoryAdapter, MemoryRecord


class InMemoryMemoryAdapter(MemoryAdapter):
    def __init__(self):
        self._store: Dict[str, MemoryRecord] = {}

    async def get(self, key: str) -> Optional[MemoryRecord]:
        return self._store.get(key)

    async def set(self, record: MemoryRecord) -> None:
        now = datetime.now(timezone.utc).isoformat()
        if record.created_at is None:
            record.created_at = now
        record.updated_at = now
        self._store[record.key] = record

    async def search(self, *, coordinate: str | None = None, tier: str | None = None, limit: int = 50) -> list[MemoryRecord]:
        out = list(self._store.values())
        if coordinate is not None:
            out = [r for r in out if r.coordinate == coordinate]
        if tier is not None:
            out = [r for r in out if r.tier == tier]
        return out[:limit]

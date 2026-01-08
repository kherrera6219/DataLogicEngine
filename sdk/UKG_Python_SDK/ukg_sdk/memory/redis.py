from __future__ import annotations

import json
from typing import Optional

from .base import MemoryAdapter, MemoryRecord

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None


class RedisMemoryAdapter(MemoryAdapter):
    """Redis-backed memory adapter.

    Storage model:
      - key -> JSON blob (MemoryRecord)
      - optional search is not supported by default (use RediSearch or secondary index)
    """

    def __init__(self, url: str, *, prefix: str = "ukg:mem:"):
        if redis is None:
            raise ImportError("redis is required for RedisMemoryAdapter. Install with: pip install ukg-sdk[redis]")
        self.url = url
        self.prefix = prefix
        self._client = redis.from_url(url)

    def _k(self, key: str) -> str:
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[MemoryRecord]:
        raw = await self._client.get(self._k(key))
        if raw is None:
            return None
        data = json.loads(raw)
        return MemoryRecord(**data)

    async def set(self, record: MemoryRecord) -> None:
        await self._client.set(self._k(record.key), json.dumps(record.__dict__, default=str))

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class MemoryRecord:
    key: str
    value: Dict[str, Any]
    tier: str = "short"  # short | long | archive
    coordinate: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MemoryAdapter(ABC):
    """Pluggable memory adapter (UKG/USKD persistence layer).

    This SDK keeps memory operations simple:
      - get/set by key
      - search by tags/coordinate (optional)
      - append trace/audit pointers (optional)
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[MemoryRecord]: ...

    @abstractmethod
    async def set(self, record: MemoryRecord) -> None: ...

    async def upsert(self, key: str, value: Dict[str, Any], *, tier: str = "short", coordinate: str | None = None) -> None:
        rec = MemoryRecord(key=key, value=value, tier=tier, coordinate=coordinate)
        await self.set(rec)

    async def search(self, *, coordinate: str | None = None, tier: str | None = None, limit: int = 50) -> list[MemoryRecord]:
        return []

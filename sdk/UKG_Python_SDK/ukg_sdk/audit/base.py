from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AuditEvent:
    """Compliance-grade audit event (append-only)."""

    event_id: str
    ts: str
    kind: str
    actor: str
    session_id: str
    ka_id: Optional[str] = None
    layer: Optional[str] = None
    coordinate: Optional[str] = None
    correlation_id: Optional[str] = None
    payload: Dict[str, Any] = None  # type: ignore
    prev_hash: Optional[str] = None
    hash: Optional[str] = None


class AuditStore(ABC):
    @abstractmethod
    async def append(self, event: AuditEvent) -> AuditEvent: ...

    async def flush(self) -> None:
        return None


class InMemoryAuditStore(AuditStore):
    """Append-to-list audit store for tests and ephemeral use cases."""

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    async def append(self, event: AuditEvent) -> AuditEvent:
        self.events.append(event)
        return event

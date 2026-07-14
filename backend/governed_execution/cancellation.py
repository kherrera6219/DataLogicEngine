"""Cross-thread cancellation registry for active governed requests."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from threading import Lock


@dataclass(slots=True)
class CancellationEntry:
    request_id: str
    trace_id: str
    loop: asyncio.AbstractEventLoop
    event: asyncio.Event = field(default_factory=asyncio.Event)

    def cancel(self) -> None:
        self.loop.call_soon_threadsafe(self.event.set)


class CancellationRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._entries: dict[str, CancellationEntry] = {}

    def register(self, request_id: str, trace_id: str) -> CancellationEntry:
        entry = CancellationEntry(
            request_id=str(request_id),
            trace_id=str(trace_id),
            loop=asyncio.get_running_loop(),
        )
        with self._lock:
            self._entries[entry.request_id] = entry
            self._entries[entry.trace_id] = entry
        return entry

    def cancel(self, identifier: str) -> bool:
        with self._lock:
            entry = self._entries.get(str(identifier))
        if entry is None:
            return False
        entry.cancel()
        return True

    def unregister(self, entry: CancellationEntry) -> None:
        with self._lock:
            for identifier in (entry.request_id, entry.trace_id):
                if self._entries.get(identifier) is entry:
                    self._entries.pop(identifier, None)


CANCELLATION_REGISTRY = CancellationRegistry()

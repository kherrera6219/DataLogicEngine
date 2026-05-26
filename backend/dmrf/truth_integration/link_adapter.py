"""TruthLink adapter for DMRF events."""

from __future__ import annotations

from collections import defaultdict
import json
import os
from typing import Any


class InMemoryTruthLinkBus:
    """Minimal in-memory event bus for desktop DMRF events."""

    def __init__(self):
        self.events: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def publish(self, topic: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.events[topic].append(payload)
        return {"published": True, "topic": topic, "count": len(self.events[topic])}


class TruthLinkDMRFAdapter:
    """Publish DMRF events to the configured TruthLink bus."""

    def __init__(self, bus: Any | None = None, *, redis_url: str | None = None, desktop_mode: bool | None = None):
        self.desktop_mode = self._desktop_mode() if desktop_mode is None else desktop_mode
        self.redis_url = redis_url or os.environ.get("REDIS_URL")
        self.bus = bus or self._default_bus()

    def publish(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        topic = f"dmrf.{event_type}"
        if hasattr(self.bus, "xadd"):
            try:
                message_id = self.bus.xadd(topic, {"payload": json.dumps(payload, sort_keys=True, default=str)})
                return {"published": True, "topic": topic, "message_id": message_id, "backend": "redis_stream"}
            except Exception:
                self.bus = InMemoryTruthLinkBus()
        if hasattr(self.bus, "publish"):
            result = self.bus.publish(topic, payload)
            result["backend"] = "memory"
            return result
        return {"published": False, "topic": topic}

    def _default_bus(self) -> Any:
        if self.redis_url and not self.desktop_mode:
            try:
                import redis

                return redis.from_url(self.redis_url, decode_responses=True)
            except Exception:
                return InMemoryTruthLinkBus()
        return InMemoryTruthLinkBus()

    @staticmethod
    def _desktop_mode() -> bool:
        return os.environ.get("IS_DESKTOP_APP", "false").lower() in {"1", "true", "yes", "on"}

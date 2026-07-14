"""Content-free Redis live state for governed MCP connectors."""

from __future__ import annotations

import json
import time
from typing import Any


class MCPLiveStateUnavailable(RuntimeError):
    """Raised when required Redis MCP live state cannot be reached."""


class RedisMCPLiveState:
    """Mirror non-authoritative connector lifecycle and execution state."""

    def __init__(self, redis_client: Any, *, prefix: str = "mcp:live") -> None:
        if redis_client is None:
            raise MCPLiveStateUnavailable("Redis MCP live-state client is unavailable")
        self.redis = redis_client
        self.prefix = str(prefix).strip() or "mcp:live"

    @classmethod
    def from_url(cls, redis_url: str) -> "RedisMCPLiveState":
        try:
            import redis

            client = redis.Redis.from_url(
                redis_url,
                socket_connect_timeout=1,
                socket_timeout=1,
                decode_responses=True,
            )
            client.ping()
        except Exception as exc:
            raise MCPLiveStateUnavailable("Required Redis MCP live state is unavailable") from exc
        return cls(client)

    @property
    def events_key(self) -> str:
        return f"{self.prefix}:events"

    def record_lifecycle(self, server_id: str, event_type: str, status: str) -> None:
        event = {
            "kind": "lifecycle",
            "server_id": str(server_id),
            "event_type": str(event_type),
            "status": str(status),
            "updated_at_epoch": str(int(time.time())),
        }
        self._record(f"{self.prefix}:server:{server_id}:state", event)

    def record_execution(self, server_id: str, execution_id: str, status: str) -> None:
        event = {
            "kind": "execution",
            "server_id": str(server_id),
            "execution_id": str(execution_id),
            "status": str(status),
            "updated_at_epoch": str(int(time.time())),
        }
        self._record(f"{self.prefix}:execution:{execution_id}:state", event)

    def _record(self, state_key: str, event: dict[str, str]) -> None:
        try:
            pipe = self.redis.pipeline(transaction=True)
            pipe.set(state_key, json.dumps(event, sort_keys=True), ex=86_400)
            pipe.xadd(self.events_key, event, maxlen=10_000, approximate=True)
            pipe.execute()
        except Exception as exc:
            raise MCPLiveStateUnavailable("Redis MCP live-state update failed") from exc

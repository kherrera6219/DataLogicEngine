"""MCP resource subscription tracking with SSE-compatible notifications."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
import uuid
from flask import current_app, has_app_context
from werkzeug.local import LocalProxy

from backend.truth_engine.truth_link.transport import SSETransport


class MCPSubscriptionManager:
    """Track resource subscriptions and fan out update notifications."""

    def __init__(self):
        self.subscriptions: dict[str, dict[str, Any]] = {}
        self.transport = SSETransport()

    def subscribe(self, uri: str, *, client_id: str | None = None) -> dict[str, Any]:
        subscription_id = str(uuid.uuid4())
        client = client_id or subscription_id
        self.subscriptions[subscription_id] = {
            "subscription_id": subscription_id,
            "client_id": client,
            "uri": uri,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self.transport.register_client(client)
        return self.subscriptions[subscription_id]

    def unsubscribe(self, subscription_id: str) -> bool:
        subscription = self.subscriptions.pop(subscription_id, None)
        if not subscription:
            return False
        self.transport.unregister_client(subscription["client_id"])
        return True

    def notify(self, uri: str, payload: dict[str, Any] | None = None) -> int:
        sent = 0
        for subscription in list(self.subscriptions.values()):
            if subscription["uri"] != uri:
                continue
            if self.transport.send_event(
                subscription["client_id"],
                "resources/updated",
                {
                    "uri": uri,
                    "payload": payload or {},
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            ):
                sent += 1
        return sent

    def stream(self, client_id: str):
        yield from self.transport.stream_events(client_id)

    def stats(self) -> dict[str, Any]:
        return {
            "subscription_count": len(self.subscriptions),
            "sse": self.transport.get_stats(),
        }


_fallback_subscription_manager: MCPSubscriptionManager | None = None


def get_subscription_manager() -> MCPSubscriptionManager:
    if has_app_context():
        manager = current_app.extensions.get("dle_mcp_subscription_manager")
        if manager is None:
            manager = MCPSubscriptionManager()
            current_app.extensions["dle_mcp_subscription_manager"] = manager
        return manager
    global _fallback_subscription_manager
    if _fallback_subscription_manager is None:
        _fallback_subscription_manager = MCPSubscriptionManager()
    return _fallback_subscription_manager


subscription_manager = LocalProxy(get_subscription_manager)

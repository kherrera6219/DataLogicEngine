"""
In-process resource governor for API request concurrency caps.
"""

from __future__ import annotations

import os
import threading
from collections import defaultdict

from flask import g, jsonify, request
from flask_login import current_user


def _env_truthy(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


class ResourceGovernor:
    """Simple tenant/user scoped concurrency guard."""

    def __init__(
        self,
        *,
        enabled: bool = True,
        default_limit: int = 40,
        admin_limit: int = 10,
    ) -> None:
        self.enabled = enabled
        self.default_limit = max(1, int(default_limit))
        self.admin_limit = max(1, int(admin_limit))
        self._lock = threading.Lock()
        self._inflight: defaultdict[str, int] = defaultdict(int)

    def _request_key(self) -> str:
        tenant = request.headers.get("X-Tenant-ID")
        if tenant:
            return f"tenant:{tenant.strip().lower()}"

        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key[:12]}"

        if getattr(current_user, "is_authenticated", False):
            user_id = getattr(current_user, "id", None) or getattr(current_user, "username", "user")
            return f"user:{user_id}"

        return f"ip:{request.remote_addr or 'unknown'}"

    def _limit_for_request(self) -> int:
        if request.path.startswith("/api/v1/admin"):
            return self.admin_limit
        return self.default_limit

    def acquire_or_reject(self):
        if not self.enabled:
            return None

        if request.method == "OPTIONS":
            return None

        if not (request.path.startswith("/api/") or request.path.startswith("/graphql")):
            return None

        request_key = self._request_key()
        limit = self._limit_for_request()

        with self._lock:
            current = self._inflight[request_key]
            if current >= limit:
                return jsonify(
                    {
                        "success": False,
                        "error": {
                            "code": "RESOURCE_GOVERNOR_LIMIT_EXCEEDED",
                            "message": "Too many concurrent requests for this client scope.",
                            "details": {
                                "limit": limit,
                                "scope": request_key.split(":", 1)[0],
                            },
                        },
                    }
                ), 429

            self._inflight[request_key] = current + 1

        g.resource_governor_key = request_key
        return None

    def release(self) -> None:
        request_key = getattr(g, "resource_governor_key", None)
        if not request_key:
            return

        with self._lock:
            current = self._inflight.get(request_key, 0)
            if current <= 1:
                self._inflight.pop(request_key, None)
            else:
                self._inflight[request_key] = current - 1


def configure_resource_governor(app) -> ResourceGovernor:
    enabled = _env_truthy("RESOURCE_GOVERNOR_ENABLED", True)
    if app.config.get("TESTING"):
        enabled = False

    governor = ResourceGovernor(
        enabled=enabled,
        default_limit=int(os.environ.get("RESOURCE_GOVERNOR_DEFAULT_CONCURRENCY", "40")),
        admin_limit=int(os.environ.get("RESOURCE_GOVERNOR_ADMIN_CONCURRENCY", "10")),
    )

    @app.before_request
    def _acquire_governor_slot():
        return governor.acquire_or_reject()

    @app.after_request
    def _release_governor_slot(response):
        governor.release()
        return response

    return governor


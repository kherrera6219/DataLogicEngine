"""Per-application operational metrics."""

from __future__ import annotations

import time
from threading import Condition


class RequestMetrics:
    """Thread-safe counters owned by one Flask application instance."""

    def __init__(self) -> None:
        self.started_at = time.time()
        self.total_requests = 0
        self.inflight_requests = 0
        self.route_status_totals: dict[tuple[str, str, str], int] = {}
        self.route_latency_ms: dict[tuple[str, str], dict[str, float | int]] = {}
        self._condition = Condition()

    def begin_request(self) -> None:
        with self._condition:
            self.total_requests += 1
            self.inflight_requests += 1

    def record_request(self, method: str, route: str, status_code: int, duration_ms: float) -> None:
        status_family = f"{status_code // 100}xx"
        with self._condition:
            self.inflight_requests = max(0, self.inflight_requests - 1)
            status_key = (method.upper(), route, status_family)
            self.route_status_totals[status_key] = self.route_status_totals.get(status_key, 0) + 1
            latency_key = (method.upper(), route)
            latency = self.route_latency_ms.setdefault(
                latency_key,
                {"count": 0, "sum_ms": 0.0, "max_ms": 0.0},
            )
            latency["count"] = int(latency["count"]) + 1
            latency["sum_ms"] = float(latency["sum_ms"]) + max(0.0, duration_ms)
            latency["max_ms"] = max(float(latency["max_ms"]), max(0.0, duration_ms))
            self._condition.notify_all()

    def wait_for_inflight_at_most(self, limit: int, timeout_seconds: float) -> bool:
        """Wait for admitted requests to drain within the shutdown budget."""
        deadline = time.monotonic() + max(0.0, float(timeout_seconds))
        with self._condition:
            while self.inflight_requests > max(0, int(limit)):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self._condition.wait(timeout=remaining)
            return True

    def snapshot(self) -> dict:
        with self._condition:
            return {
                "started_at": self.started_at,
                "total": self.total_requests,
                "inflight": self.inflight_requests,
                "route_status_totals": dict(self.route_status_totals),
                "route_latency_ms": {
                    key: value.copy()
                    for key, value in self.route_latency_ms.items()
                },
            }

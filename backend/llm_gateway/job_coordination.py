"""Redis coordination state for durable Phase 8 gateway jobs."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any


_RELEASE_LEASE_LUA = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
  return redis.call('DEL', KEYS[1])
end
return 0
"""


class GatewayJobCoordinatorUnavailable(RuntimeError):
    """Raised when required Redis job coordination cannot be reached."""


@dataclass(frozen=True, slots=True)
class GatewayJobCoordinationState:
    job_id: str
    state: str
    updated_at_epoch: int


class RedisGatewayJobCoordinator:
    """Keep content-free leases, cancellation, and event state in Redis."""

    def __init__(self, redis_client: Any, *, prefix: str = "gateway:jobs") -> None:
        if redis_client is None:
            raise GatewayJobCoordinatorUnavailable("Redis gateway job client is unavailable")
        self.redis = redis_client
        self.prefix = str(prefix).strip() or "gateway:jobs"

    @classmethod
    def from_url(cls, redis_url: str) -> "RedisGatewayJobCoordinator":
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
            raise GatewayJobCoordinatorUnavailable(
                "Required Redis gateway job coordination is unavailable"
            ) from exc
        return cls(client)

    def _key(self, job_id: str, suffix: str) -> str:
        normalized = str(job_id).strip()
        if not normalized:
            raise ValueError("Gateway job id is required")
        return f"{self.prefix}:{normalized}:{suffix}"

    def acquire(self, job_id: str, *, worker_id: str, lease_seconds: int) -> bool:
        try:
            return bool(self.redis.set(
                self._key(job_id, "lease"),
                str(worker_id),
                nx=True,
                ex=max(5, int(lease_seconds)),
            ))
        except Exception as exc:
            raise GatewayJobCoordinatorUnavailable("Gateway job lease acquisition failed") from exc

    def release(self, job_id: str, *, worker_id: str) -> bool:
        try:
            return bool(self.redis.eval(
                _RELEASE_LEASE_LUA,
                1,
                self._key(job_id, "lease"),
                str(worker_id),
            ))
        except Exception as exc:
            raise GatewayJobCoordinatorUnavailable("Gateway job lease release failed") from exc

    def record_state(self, job_id: str, state: str, *, retention_seconds: int) -> None:
        event = GatewayJobCoordinationState(
            job_id=str(job_id),
            state=str(state),
            updated_at_epoch=int(time.time()),
        )
        try:
            key = self._key(job_id, "state")
            pipe = self.redis.pipeline(transaction=True)
            pipe.set(key, json.dumps({
                "job_id": event.job_id,
                "state": event.state,
                "updated_at_epoch": event.updated_at_epoch,
            }, sort_keys=True), ex=max(60, int(retention_seconds)))
            pipe.execute()
        except Exception as exc:
            raise GatewayJobCoordinatorUnavailable("Gateway job state update failed") from exc

    def request_cancel(self, job_id: str, *, retention_seconds: int) -> None:
        try:
            self.redis.set(
                self._key(job_id, "cancel"),
                "1",
                ex=max(60, int(retention_seconds)),
            )
        except Exception as exc:
            raise GatewayJobCoordinatorUnavailable("Gateway job cancellation update failed") from exc

    def is_cancel_requested(self, job_id: str) -> bool:
        try:
            return self.redis.exists(self._key(job_id, "cancel")) == 1
        except Exception as exc:
            raise GatewayJobCoordinatorUnavailable("Gateway job cancellation read failed") from exc

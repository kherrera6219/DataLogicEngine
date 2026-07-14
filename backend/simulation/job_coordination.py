"""Content-free Redis coordination for durable simulation jobs."""

from __future__ import annotations

import json
import time
from typing import Any


_RELEASE_LEASE_LUA = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
  return redis.call('DEL', KEYS[1])
end
return 0
"""


class SimulationJobCoordinatorUnavailable(RuntimeError):
    """Raised when required Redis simulation coordination is unavailable."""


class RedisSimulationJobCoordinator:
    """Coordinate queue, lease, control, and content-free progress state."""

    def __init__(self, redis_client: Any, *, prefix: str = "simulation:jobs") -> None:
        if redis_client is None:
            raise SimulationJobCoordinatorUnavailable("Redis simulation client is unavailable")
        self.redis = redis_client
        self.prefix = str(prefix).strip() or "simulation:jobs"

    @classmethod
    def from_url(cls, redis_url: str) -> "RedisSimulationJobCoordinator":
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
            raise SimulationJobCoordinatorUnavailable(
                "Required Redis simulation coordination is unavailable"
            ) from exc
        return cls(client)

    def _key(self, simulation_id: str, suffix: str) -> str:
        normalized = str(simulation_id).strip()
        if not normalized:
            raise ValueError("Simulation id is required")
        return f"{self.prefix}:{normalized}:{suffix}"

    @property
    def queue_key(self) -> str:
        return f"{self.prefix}:queue"

    @property
    def events_key(self) -> str:
        return f"{self.prefix}:events"

    def enqueue(self, simulation_id: str) -> None:
        try:
            self.redis.zadd(self.queue_key, {str(simulation_id): int(time.time())}, nx=True)
            self.record_state(simulation_id, "queued", 0, 0)
        except Exception as exc:
            raise SimulationJobCoordinatorUnavailable("Simulation queue update failed") from exc

    def acquire(self, simulation_id: str, *, worker_id: str, lease_seconds: int) -> bool:
        try:
            acquired = bool(
                self.redis.set(
                    self._key(simulation_id, "lease"),
                    str(worker_id),
                    nx=True,
                    ex=max(5, int(lease_seconds)),
                )
            )
            if acquired:
                self.redis.zrem(self.queue_key, str(simulation_id))
            return acquired
        except Exception as exc:
            raise SimulationJobCoordinatorUnavailable(
                "Simulation lease acquisition failed"
            ) from exc

    def release(self, simulation_id: str, *, worker_id: str) -> bool:
        try:
            return bool(
                self.redis.eval(
                    _RELEASE_LEASE_LUA,
                    1,
                    self._key(simulation_id, "lease"),
                    str(worker_id),
                )
            )
        except Exception as exc:
            raise SimulationJobCoordinatorUnavailable("Simulation lease release failed") from exc

    def record_state(
        self,
        simulation_id: str,
        state: str,
        current: int,
        total: int,
    ) -> None:
        event = {
            "simulation_id": str(simulation_id),
            "state": str(state),
            "current": str(max(0, int(current))),
            "total": str(max(0, int(total))),
            "updated_at_epoch": str(int(time.time())),
        }
        try:
            pipe = self.redis.pipeline(transaction=True)
            pipe.set(
                self._key(simulation_id, "state"),
                json.dumps(event, sort_keys=True),
                ex=86400,
            )
            pipe.xadd(self.events_key, event, maxlen=10_000, approximate=True)
            pipe.execute()
        except Exception as exc:
            raise SimulationJobCoordinatorUnavailable("Simulation state update failed") from exc

    def get_state(self, simulation_id: str) -> dict[str, str] | None:
        try:
            raw = self.redis.get(self._key(simulation_id, "state"))
            payload = json.loads(raw) if raw else None
            return payload if isinstance(payload, dict) else None
        except Exception as exc:
            raise SimulationJobCoordinatorUnavailable("Simulation state read failed") from exc

    def request_control(self, simulation_id: str, action: str) -> None:
        normalized = str(action).strip().lower()
        if normalized not in {"cancel", "pause"}:
            raise ValueError("unsupported_simulation_control")
        try:
            self.redis.set(self._key(simulation_id, normalized), "1", ex=86400)
        except Exception as exc:
            raise SimulationJobCoordinatorUnavailable("Simulation control update failed") from exc

    def requested_control(self, simulation_id: str) -> str | None:
        try:
            if self.redis.exists(self._key(simulation_id, "cancel")) == 1:
                return "cancel"
            if self.redis.exists(self._key(simulation_id, "pause")) == 1:
                return "pause"
            return None
        except Exception as exc:
            raise SimulationJobCoordinatorUnavailable("Simulation control read failed") from exc

    def clear_controls(self, simulation_id: str) -> None:
        try:
            self.redis.delete(
                self._key(simulation_id, "cancel"),
                self._key(simulation_id, "pause"),
            )
        except Exception as exc:
            raise SimulationJobCoordinatorUnavailable("Simulation control cleanup failed") from exc

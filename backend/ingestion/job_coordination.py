"""Content-free Redis coordination for durable ingestion jobs."""

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


class IngestionJobCoordinatorUnavailable(RuntimeError):
    """Raised when required Redis ingestion coordination is unavailable."""


class RedisIngestionJobCoordinator:
    """Coordinate queue membership, leases, controls, state, and progress events."""

    def __init__(self, redis_client: Any, *, prefix: str = "ingestion:jobs") -> None:
        if redis_client is None:
            raise IngestionJobCoordinatorUnavailable(
                "Redis ingestion job client is unavailable"
            )
        self.redis = redis_client
        self.prefix = str(prefix).strip() or "ingestion:jobs"

    @classmethod
    def from_url(cls, redis_url: str) -> "RedisIngestionJobCoordinator":
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
            raise IngestionJobCoordinatorUnavailable(
                "Required Redis ingestion job coordination is unavailable"
            ) from exc
        return cls(client)

    def _key(self, job_id: str, suffix: str) -> str:
        normalized = str(job_id).strip()
        if not normalized:
            raise ValueError("Ingestion job id is required")
        return f"{self.prefix}:{normalized}:{suffix}"

    @property
    def queue_key(self) -> str:
        return f"{self.prefix}:queue"

    @property
    def events_key(self) -> str:
        return f"{self.prefix}:events"

    def enqueue(self, job_id: str) -> None:
        """Idempotently mirror PostgreSQL queued authority in Redis."""
        try:
            self.redis.zadd(self.queue_key, {str(job_id): int(time.time())}, nx=True)
            self.record_state(job_id, "queued")
        except IngestionJobCoordinatorUnavailable:
            raise
        except Exception as exc:
            raise IngestionJobCoordinatorUnavailable(
                "Ingestion job queue update failed"
            ) from exc

    def acquire(self, job_id: str, *, worker_id: str, lease_seconds: int) -> bool:
        try:
            acquired = bool(
                self.redis.set(
                    self._key(job_id, "lease"),
                    str(worker_id),
                    nx=True,
                    ex=max(5, int(lease_seconds)),
                )
            )
            if acquired:
                self.redis.zrem(self.queue_key, str(job_id))
            return acquired
        except Exception as exc:
            raise IngestionJobCoordinatorUnavailable(
                "Ingestion job lease acquisition failed"
            ) from exc

    def release(self, job_id: str, *, worker_id: str) -> bool:
        try:
            return bool(
                self.redis.eval(
                    _RELEASE_LEASE_LUA,
                    1,
                    self._key(job_id, "lease"),
                    str(worker_id),
                )
            )
        except Exception as exc:
            raise IngestionJobCoordinatorUnavailable(
                "Ingestion job lease release failed"
            ) from exc

    def record_state(self, job_id: str, state: str) -> None:
        self.record_progress(job_id, state=state, checkpoint=state)

    def record_progress(
        self,
        job_id: str,
        *,
        state: str,
        checkpoint: str,
        counts: dict[str, int] | None = None,
    ) -> None:
        """Publish content-free state and bounded numeric progress."""
        event = {
            "job_id": str(job_id),
            "state": str(state),
            "checkpoint": str(checkpoint),
            "updated_at_epoch": str(int(time.time())),
        }
        for name, value in (counts or {}).items():
            if name in {
                "files_scanned",
                "files_ingested",
                "files_rejected",
                "chunks_created",
                "chunks_indexed",
                "materializations_pending",
            }:
                event[name] = str(max(0, int(value)))
        try:
            pipe = self.redis.pipeline(transaction=True)
            pipe.set(
                self._key(job_id, "state"),
                json.dumps(event, sort_keys=True),
                ex=86400,
            )
            pipe.xadd(self.events_key, event, maxlen=10_000, approximate=True)
            pipe.execute()
        except Exception as exc:
            raise IngestionJobCoordinatorUnavailable(
                "Ingestion job state update failed"
            ) from exc

    def get_state(self, job_id: str) -> dict[str, str] | None:
        try:
            raw = self.redis.get(self._key(job_id, "state"))
            if not raw:
                return None
            payload = json.loads(raw)
            return payload if isinstance(payload, dict) else None
        except Exception as exc:
            raise IngestionJobCoordinatorUnavailable(
                "Ingestion job state read failed"
            ) from exc

    def request_control(self, job_id: str, action: str) -> None:
        normalized = str(action).strip().lower()
        if normalized not in {"cancel", "pause"}:
            raise ValueError("unsupported_ingestion_job_control")
        try:
            self.redis.set(self._key(job_id, normalized), "1", ex=86400)
            self.record_state(job_id, f"{normalized}_requested")
        except IngestionJobCoordinatorUnavailable:
            raise
        except Exception as exc:
            raise IngestionJobCoordinatorUnavailable(
                "Ingestion job control update failed"
            ) from exc

    def requested_control(self, job_id: str) -> str | None:
        try:
            if self.redis.exists(self._key(job_id, "cancel")) == 1:
                return "cancel"
            if self.redis.exists(self._key(job_id, "pause")) == 1:
                return "pause"
            return None
        except Exception as exc:
            raise IngestionJobCoordinatorUnavailable(
                "Ingestion job control read failed"
            ) from exc

    def clear_controls(self, job_id: str) -> None:
        try:
            self.redis.delete(
                self._key(job_id, "cancel"),
                self._key(job_id, "pause"),
            )
        except Exception as exc:
            raise IngestionJobCoordinatorUnavailable(
                "Ingestion job control cleanup failed"
            ) from exc

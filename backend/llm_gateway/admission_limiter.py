"""Atomic Redis-backed admission limits for external gateway clients."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any


_ADMIT_LUA = """
local current = tonumber(redis.call('GET', KEYS[1]) or '0')
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
if current >= limit then
  local ttl = redis.call('TTL', KEYS[1])
  if ttl < 0 then ttl = window end
  return {0, current, ttl}
end
local next = redis.call('INCR', KEYS[1])
if next == 1 then redis.call('EXPIRE', KEYS[1], window) end
local ttl = redis.call('TTL', KEYS[1])
if ttl < 0 then ttl = window end
return {1, next, ttl}
"""

_ACQUIRE_CONCURRENCY_LUA = """
local now = tonumber(ARGV[1])
local lease_seconds = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local lease_id = ARGV[4]
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
local current = tonumber(redis.call('ZCARD', KEYS[1]) or '0')
if current >= limit then
  local earliest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
  local retry_after = lease_seconds
  if earliest[2] then retry_after = math.max(1, tonumber(earliest[2]) - now) end
  return {0, current, retry_after}
end
redis.call('ZADD', KEYS[1], now + lease_seconds, lease_id)
redis.call('EXPIRE', KEYS[1], lease_seconds + 1)
return {1, current + 1, lease_seconds}
"""

_RELEASE_CONCURRENCY_LUA = """
return redis.call('ZREM', KEYS[1], ARGV[1])
"""


class GatewayLimiterUnavailable(RuntimeError):
    """Raised when required atomic admission state cannot be reached."""


@dataclass(frozen=True, slots=True)
class AdmissionDecision:
    allowed: bool
    count: int
    limit: int
    remaining: int
    retry_after_seconds: int


class AtomicGatewayLimiter:
    """Apply a fixed-window limit with one atomic Redis Lua operation."""

    def __init__(self, redis_client: Any) -> None:
        if redis_client is None:
            raise GatewayLimiterUnavailable("Redis admission client is unavailable")
        self.redis = redis_client

    @classmethod
    def from_url(cls, redis_url: str) -> "AtomicGatewayLimiter":
        try:
            import redis

            client = redis.Redis.from_url(
                redis_url,
                socket_connect_timeout=1,
                socket_timeout=1,
                decode_responses=False,
            )
        except Exception as exc:
            raise GatewayLimiterUnavailable("Redis admission client initialization failed") from exc
        return cls(client)

    def admit(self, bucket: str, *, limit: int, window_seconds: int) -> AdmissionDecision:
        if not str(bucket).strip():
            raise ValueError("Admission bucket is required")
        if int(limit) <= 0 or int(window_seconds) <= 0:
            raise ValueError("Admission limit and window must be positive")
        try:
            result = self.redis.eval(
                _ADMIT_LUA,
                1,
                str(bucket),
                int(limit),
                int(window_seconds),
            )
            allowed_raw, count_raw, ttl_raw = result
            count = max(0, int(count_raw))
            ttl = max(1, int(ttl_raw))
        except Exception as exc:
            raise GatewayLimiterUnavailable("Required Redis admission operation failed") from exc
        return AdmissionDecision(
            allowed=bool(int(allowed_raw)),
            count=count,
            limit=int(limit),
            remaining=max(0, int(limit) - count),
            retry_after_seconds=ttl,
        )

    def acquire_concurrency(
        self,
        bucket: str,
        *,
        lease_id: str,
        limit: int,
        lease_seconds: int,
    ) -> AdmissionDecision:
        """Acquire one expiring request lease with a single Redis operation."""
        if not str(bucket).strip() or not str(lease_id).strip():
            raise ValueError("Concurrency bucket and lease id are required")
        if int(limit) <= 0 or int(lease_seconds) <= 0:
            raise ValueError("Concurrency limit and lease must be positive")
        try:
            result = self.redis.eval(
                _ACQUIRE_CONCURRENCY_LUA,
                1,
                str(bucket),
                int(time.time()),
                int(lease_seconds),
                int(limit),
                str(lease_id),
            )
            allowed_raw, count_raw, retry_raw = result
            count = max(0, int(count_raw))
            retry_after = max(1, int(retry_raw))
        except Exception as exc:
            raise GatewayLimiterUnavailable("Required Redis concurrency operation failed") from exc
        return AdmissionDecision(
            allowed=bool(int(allowed_raw)),
            count=count,
            limit=int(limit),
            remaining=max(0, int(limit) - count),
            retry_after_seconds=retry_after,
        )

    def release_concurrency(self, bucket: str, *, lease_id: str) -> bool:
        """Release a request lease; expiry remains the crash recovery path."""
        if not str(bucket).strip() or not str(lease_id).strip():
            raise ValueError("Concurrency bucket and lease id are required")
        try:
            result = self.redis.eval(
                _RELEASE_CONCURRENCY_LUA,
                1,
                str(bucket),
                str(lease_id),
            )
        except Exception as exc:
            raise GatewayLimiterUnavailable("Required Redis concurrency release failed") from exc
        return bool(result)

"""Phase 8 atomic gateway admission limiter tests."""

from __future__ import annotations

import pytest

from backend.llm_gateway.admission_limiter import (
    AtomicGatewayLimiter,
    GatewayLimiterUnavailable,
)


class FakeRedis:
    def __init__(self, result=None, error: Exception | None = None) -> None:
        self.result = result or [1, 1, 60]
        self.error = error
        self.calls: list[tuple] = []

    def eval(self, *args):
        self.calls.append(args)
        if self.error:
            raise self.error
        return self.result


def test_atomic_limiter_returns_remaining_and_retry_after() -> None:
    client = FakeRedis([1, 3, 42])
    decision = AtomicGatewayLimiter(client).admit("client:key:minute", limit=5, window_seconds=60)
    assert decision.allowed is True
    assert decision.count == 3
    assert decision.remaining == 2
    assert decision.retry_after_seconds == 42
    assert client.calls[0][1] == 1

    denied = AtomicGatewayLimiter(FakeRedis([0, 5, 37])).admit(
        "client:key:minute", limit=5, window_seconds=60
    )
    assert denied.allowed is False
    assert denied.remaining == 0
    assert denied.retry_after_seconds == 37


def test_atomic_limiter_fails_closed_when_redis_is_unavailable() -> None:
    with pytest.raises(GatewayLimiterUnavailable):
        AtomicGatewayLimiter(FakeRedis(error=OSError("redis unavailable"))).admit(
            "client:key:minute", limit=5, window_seconds=60
        )


def test_atomic_concurrency_lease_is_acquired_and_released() -> None:
    client = FakeRedis([1, 2, 11])
    limiter = AtomicGatewayLimiter(client)

    decision = limiter.acquire_concurrency(
        "gateway:client:active",
        lease_id="request-1",
        limit=3,
        lease_seconds=30,
    )

    assert decision.allowed is True
    assert decision.count == 2
    assert decision.remaining == 1
    assert decision.retry_after_seconds == 11
    assert limiter.release_concurrency(
        "gateway:client:active",
        lease_id="request-1",
    ) is True
    assert len(client.calls) == 2


def test_atomic_concurrency_lease_denies_at_limit_and_fails_closed() -> None:
    denied = AtomicGatewayLimiter(FakeRedis([0, 3, 9])).acquire_concurrency(
        "gateway:client:active",
        lease_id="request-2",
        limit=3,
        lease_seconds=30,
    )
    assert denied.allowed is False
    assert denied.remaining == 0

    with pytest.raises(GatewayLimiterUnavailable):
        AtomicGatewayLimiter(FakeRedis(error=OSError("redis unavailable"))).acquire_concurrency(
            "gateway:client:active",
            lease_id="request-3",
            limit=3,
            lease_seconds=30,
        )


@pytest.mark.parametrize("limit,window", [(0, 60), (10, 0), (-1, 1)])
def test_atomic_limiter_rejects_invalid_server_policy(limit: int, window: int) -> None:
    with pytest.raises(ValueError):
        AtomicGatewayLimiter(FakeRedis()).admit("bucket", limit=limit, window_seconds=window)

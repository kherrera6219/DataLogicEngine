"""Phase 8 Redis gateway job coordination contract tests."""

from unittest.mock import MagicMock

import pytest

from backend.llm_gateway.job_coordination import (
    GatewayJobCoordinatorUnavailable,
    RedisGatewayJobCoordinator,
)


def test_gateway_job_coordination_uses_content_free_expiring_keys() -> None:
    redis = MagicMock()
    redis.set.return_value = True
    redis.exists.return_value = 1
    redis.eval.return_value = 1
    redis.pipeline.return_value.execute.return_value = [True]
    coordinator = RedisGatewayJobCoordinator(redis)

    assert coordinator.acquire('job-1', worker_id='worker-1', lease_seconds=300)
    coordinator.record_state('job-1', 'running', retention_seconds=3600)
    coordinator.request_cancel('job-1', retention_seconds=3600)
    assert coordinator.is_cancel_requested('job-1')
    assert coordinator.release('job-1', worker_id='worker-1')

    acquire = redis.set.call_args_list[0]
    assert acquire.args == ('gateway:jobs:job-1:lease', 'worker-1')
    assert acquire.kwargs == {'nx': True, 'ex': 300}
    state_call = redis.pipeline.return_value.set.call_args
    assert 'running' in state_call.args[1]
    assert 'prompt' not in state_call.args[1]
    assert 'response' not in state_call.args[1]


def test_gateway_job_coordination_fails_closed_when_redis_errors() -> None:
    redis = MagicMock()
    redis.set.side_effect = RuntimeError('redis unavailable')
    coordinator = RedisGatewayJobCoordinator(redis)

    with pytest.raises(GatewayJobCoordinatorUnavailable):
        coordinator.acquire('job-1', worker_id='worker-1', lease_seconds=300)

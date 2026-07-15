from __future__ import annotations

from backend.observability.context import (
    bound_observation_context,
    correlation_headers,
    current_correlation_id,
    current_run_id,
)


def test_bound_observation_context_propagates_and_restores_ids():
    assert current_correlation_id() == "startup"
    assert current_run_id() is None

    with bound_observation_context("corr-123", run_id="run-456"):
        assert current_correlation_id() == "corr-123"
        assert current_run_id() == "run-456"
        assert correlation_headers() == {
            "X-Correlation-ID": "corr-123",
            "X-Request-ID": "corr-123",
        }

    assert current_correlation_id() == "startup"
    assert current_run_id() is None

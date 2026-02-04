
import pytest
import sys
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, UTC

# Mocking the UKG SDK components before importing gateway
# This is crucial because gateway.py tries to import from 'models' which might not be set up
sys.modules["models"] = MagicMock()
sys.modules["models.LLMProvider"] = MagicMock()
sys.modules["models.LLMProviderUsage"] = MagicMock()
sys.modules["models.ChatSession"] = MagicMock()
sys.modules["models.ChatMessage"] = MagicMock()

# Now import the module under test
from backend.llm_gateway.gateway import CircuitBreaker, GatewayRequest, GatewayResponse

class TestCircuitBreaker:
    def test_initial_state(self):
        cb = CircuitBreaker("test_provider")
        assert cb.state == "CLOSED"
        assert cb.failures == 0
        assert cb.can_execute() is True

    def test_failure_threshold_trips_breaker(self):
        cb = CircuitBreaker("test_provider", failure_threshold=3)
        
        # Record 2 failures (limit is 3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "CLOSED"
        assert cb.can_execute() is True
        
        # 3rd failure trips it
        cb.record_failure()
        assert cb.state == "OPEN"
        assert cb.can_execute() is False

    def test_recovery_timeout(self):
        cb = CircuitBreaker("test_provider", failure_threshold=1, recovery_timeout=1)
        cb.record_failure()
        assert cb.state == "OPEN"
        
        # Initial check, still open
        assert cb.can_execute() is False
        
        # Mock time passing
        cb.last_failure_time = datetime.now(UTC) - timedelta(seconds=2)
        
        # Should switch to HALF_OPEN
        assert cb.can_execute() is True
        assert cb.state == "HALF_OPEN"
        
        # Success resets it
        cb.record_success()
        assert cb.state == "CLOSED"
        assert cb.failures == 0

class TestGatewayRequest:
    def test_initialization(self):
        req = GatewayRequest(
            messages=[{"role": "user", "content": "hello"}],
            model="gpt-4",
            temperature=0.5
        )
        assert req.mode == "chat"
        assert req.run_ukg_pipeline is True
        assert req.temperature == 0.5
        assert req.messages == [{"role": "user", "content": "hello"}]

class TestGatewayResponse:
    def test_structure(self):
        resp = GatewayResponse(
            content="response",
            run_id="run_123",
            provider_used="openai",
            model_used="gpt-4",
            usage={"total_tokens": 100}
        )
        assert resp.ok is True
        assert resp.content == "response"
        assert resp.usage["total_tokens"] == 100
        assert resp.error is None

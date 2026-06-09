# ruff: noqa: E402

import pytest
import sys
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta, UTC

# Mocking the UKG SDK components before importing gateway
# This is crucial because gateway.py tries to import from 'models' which might not be set up
_original_models_module = sys.modules.get("models")
_original_llm_provider = sys.modules.get("models.LLMProvider")
_original_llm_provider_usage = sys.modules.get("models.LLMProviderUsage")
_original_chat_session = sys.modules.get("models.ChatSession")
_original_chat_message = sys.modules.get("models.ChatMessage")

sys.modules["models"] = MagicMock()
sys.modules["models.LLMProvider"] = MagicMock()
sys.modules["models.LLMProviderUsage"] = MagicMock()
sys.modules["models.ChatSession"] = MagicMock()
sys.modules["models.ChatMessage"] = MagicMock()

# Now import the module under test
from backend.llm_gateway.gateway import CircuitBreaker, GatewayRequest, GatewayResponse, LLMGateway
from backend.llm_gateway.model_defaults import (
    ANTHROPIC_PRIMARY_MODEL,
    GOOGLE_PRIMARY_MODEL,
    OPENAI_LATEST_MODEL,
    default_model_for_provider,
)

# Restore global import state to avoid polluting unrelated tests.
if _original_models_module is not None:
    sys.modules["models"] = _original_models_module
else:
    sys.modules.pop("models", None)

if _original_llm_provider is not None:
    sys.modules["models.LLMProvider"] = _original_llm_provider
else:
    sys.modules.pop("models.LLMProvider", None)

if _original_llm_provider_usage is not None:
    sys.modules["models.LLMProviderUsage"] = _original_llm_provider_usage
else:
    sys.modules.pop("models.LLMProviderUsage", None)

if _original_chat_session is not None:
    sys.modules["models.ChatSession"] = _original_chat_session
else:
    sys.modules.pop("models.ChatSession", None)

if _original_chat_message is not None:
    sys.modules["models.ChatMessage"] = _original_chat_message
else:
    sys.modules.pop("models.ChatMessage", None)

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


class TestModelDefaults:
    def test_provider_defaults_use_current_primary_models(self):
        assert default_model_for_provider("openai") == OPENAI_LATEST_MODEL
        assert default_model_for_provider("anthropic") == ANTHROPIC_PRIMARY_MODEL
        assert default_model_for_provider("google") == GOOGLE_PRIMARY_MODEL
        assert default_model_for_provider("gemini") == GOOGLE_PRIMARY_MODEL

    def test_gateway_resolves_missing_model_from_provider_family(self):
        provider = MagicMock()
        provider.provider_type = "anthropic"
        provider.model_id = None

        model = LLMGateway._resolve_model(
            GatewayRequest(messages=[{"role": "user", "content": "hello"}]),
            provider,
        )

        assert model == ANTHROPIC_PRIMARY_MODEL

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


class TestHasActiveCloudProviders:
    """Unit tests for LLMGateway._has_active_cloud_providers().

    The helper is purely DB-driven: True iff at least one active Google/OpenAI
    provider record with a stored api_key_encrypted exists.  We patch the
    gateway module's LLMProvider binding directly so no Flask app context or
    real database is needed.
    """

    @staticmethod
    def _make_provider(provider_type: str, api_key_encrypted=b"enc_key"):
        p = MagicMock()
        p.provider_type = provider_type
        p.api_key_encrypted = api_key_encrypted
        return p

    def test_returns_false_when_no_active_providers(self):
        from unittest.mock import patch
        with patch("backend.llm_gateway.gateway.LLMProvider") as mock_lp:
            mock_lp.query.filter_by.return_value.all.return_value = []
            assert LLMGateway._has_active_cloud_providers() is False

    def test_returns_true_for_active_google_provider_with_key(self):
        from unittest.mock import patch
        provider = self._make_provider("google")
        with patch("backend.llm_gateway.gateway.LLMProvider") as mock_lp:
            mock_lp.query.filter_by.return_value.all.return_value = [provider]
            assert LLMGateway._has_active_cloud_providers() is True

    def test_returns_true_for_active_openai_provider_with_key(self):
        from unittest.mock import patch
        provider = self._make_provider("openai")
        with patch("backend.llm_gateway.gateway.LLMProvider") as mock_lp:
            mock_lp.query.filter_by.return_value.all.return_value = [provider]
            assert LLMGateway._has_active_cloud_providers() is True

    def test_returns_false_when_cloud_provider_has_no_key(self):
        """A Google record without a stored key must NOT unlock cloud routing."""
        from unittest.mock import patch
        provider = self._make_provider("google", api_key_encrypted=None)
        with patch("backend.llm_gateway.gateway.LLMProvider") as mock_lp:
            mock_lp.query.filter_by.return_value.all.return_value = [provider]
            assert LLMGateway._has_active_cloud_providers() is False

    def test_returns_false_for_ollama_only(self):
        """A local Ollama provider must NOT count as a cloud provider."""
        from unittest.mock import patch
        provider = self._make_provider("ollama")
        with patch("backend.llm_gateway.gateway.LLMProvider") as mock_lp:
            mock_lp.query.filter_by.return_value.all.return_value = [provider]
            assert LLMGateway._has_active_cloud_providers() is False

    def test_returns_false_for_local_slm_only(self):
        from unittest.mock import patch
        provider = self._make_provider("local_slm")
        with patch("backend.llm_gateway.gateway.LLMProvider") as mock_lp:
            mock_lp.query.filter_by.return_value.all.return_value = [provider]
            assert LLMGateway._has_active_cloud_providers() is False

    def test_returns_false_on_db_exception(self):
        """A DB error must silently return False — never raise."""
        from unittest.mock import patch
        with patch("backend.llm_gateway.gateway.LLMProvider") as mock_lp:
            mock_lp.query.filter_by.side_effect = Exception("DB unavailable")
            assert LLMGateway._has_active_cloud_providers() is False

    def test_gemini_provider_type_also_unlocks_cloud(self):
        """provider_type='gemini' (alternative spelling) must also be recognised."""
        from unittest.mock import patch
        provider = self._make_provider("gemini")
        with patch("backend.llm_gateway.gateway.LLMProvider") as mock_lp:
            mock_lp.query.filter_by.return_value.all.return_value = [provider]
            assert LLMGateway._has_active_cloud_providers() is True


class TestGatewayStreaming:
    @pytest.mark.asyncio
    async def test_process_stream_emits_chunks_and_done(self):
        gateway = LLMGateway()
        request = GatewayRequest(messages=[{"role": "user", "content": "hello"}], model="gpt-4")
        gateway.process = AsyncMock(return_value=GatewayResponse(
            content="abcdefghijklmnopqrstuvwxyz",
            run_id="run_1",
            provider_used="openai",
            model_used="gpt-4",
            usage={"tokens_in": 1, "tokens_out": 1},
            ok=True,
        ))

        chunks = [chunk async for chunk in gateway.process_stream(request)]
        assert chunks[0]["type"] == "chunk"
        assert chunks[-1]["type"] == "done"
        assert chunks[-1]["run_id"] == "run_1"

    @pytest.mark.asyncio
    async def test_process_stream_emits_error_event_on_failure(self):
        gateway = LLMGateway()
        request = GatewayRequest(messages=[{"role": "user", "content": "hello"}], model="gpt-4")
        gateway.process = AsyncMock(return_value=GatewayResponse(
            content="",
            run_id="run_2",
            provider_used="none",
            model_used="gpt-4",
            usage={},
            ok=False,
            error="provider timeout",
        ))

        chunks = [chunk async for chunk in gateway.process_stream(request)]
        assert len(chunks) == 1
        assert chunks[0]["type"] == "error"
        assert chunks[0]["error"] == "provider timeout"

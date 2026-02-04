import pytest
import asyncio
import uuid
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch
from backend.llm_gateway.gateway import LLMGateway, GatewayRequest, GatewayResponse, CircuitBreaker

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def gateway(mock_db):
    return LLMGateway(db_session=mock_db)

@pytest.mark.asyncio
async def test_gateway_failover(gateway, mock_db):
    """Test that gateway fails over to second provider if first fails."""
    
    # Mock eligible providers
    provider1 = MagicMock()
    provider1.id = uuid.uuid4()
    provider1.name = "Primary"
    provider1.provider_type = "openai"
    provider1.priority = 1
    provider1.model_id = "gpt-4"
    
    provider2 = MagicMock()
    provider2.id = uuid.uuid4()
    provider2.name = "Secondary"
    provider2.provider_type = "google"
    provider2.priority = 2
    provider2.model_id = "gemini-pro"
    
    with patch.object(gateway, '_get_eligible_providers', AsyncMock(return_value=[provider1, provider2])), \
         patch.object(gateway, '_create_sdk_provider') as mock_create_sdk, \
         patch.object(gateway, '_record_usage', AsyncMock()), \
         patch.object(gateway, '_save_chat_message', AsyncMock()):
        
        # Provider 1 fails (3 retries)
        mock_sdk1 = AsyncMock()
        mock_sdk1.complete.side_effect = Exception("API Down")
        
        # Provider 2 succeeds
        mock_sdk2 = AsyncMock()
        mock_sdk2.complete.return_value = MagicMock(text="Secondary Response", usage={"prompt_tokens": 10, "completion_tokens": 20})
        
        # _create_sdk_provider is called inside the retry loop (max_retries=3)
        # So it's called 3 times for provider1, then 1 time for provider2
        mock_create_sdk.side_effect = [mock_sdk1, mock_sdk1, mock_sdk1, mock_sdk2]
        
        request = GatewayRequest(
            messages=[{"role": "user", "content": "Hello"}],
            run_ukg_pipeline=False # Direct call for simplicity
        )
        
        response = await gateway.process(request)
        
        assert response.ok is True
        assert response.content == "Secondary Response"
        assert response.provider_used == "google"
        assert mock_create_sdk.call_count == 4

@pytest.mark.asyncio
async def test_circuit_breaker_logic():
    """Test standalone circuit breaker logic."""
    cb = CircuitBreaker("test_provider", failure_threshold=2, recovery_timeout=1)
    
    assert cb.can_execute() is True
    
    # First failure
    cb.record_failure()
    assert cb.state == "CLOSED"
    assert cb.can_execute() is True
    
    # Second failure -> OPEN
    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.can_execute() is False
    
    # Wait for recovery
    await asyncio.sleep(1.1)
    assert cb.can_execute() is True
    assert cb.state == "HALF_OPEN"
    
    # Success -> CLOSED
    cb.record_success()
    assert cb.state == "CLOSED"
    assert cb.failures == 0

@pytest.mark.asyncio
async def test_gateway_circuit_breaker_integration(gateway, mock_db):
    """Test that gateway respects an open circuit breaker."""
    
    provider1 = MagicMock(id=uuid.uuid4(), name="Primary", provider_type="openai", priority=1)
    provider2 = MagicMock(id=uuid.uuid4(), name="Secondary", provider_type="google", priority=2)
    
    # Manually open circuit for provider 1
    cb1 = gateway._get_circuit_breaker(str(provider1.id))
    cb1.record_failure()
    cb1.record_failure()
    cb1.record_failure()
    cb1.record_failure()
    cb1.record_failure() # Threshold is 5 by default
    assert cb1.state == "OPEN"
    
    with patch.object(gateway, '_get_eligible_providers', AsyncMock(return_value=[provider1, provider2])), \
         patch.object(gateway, '_create_sdk_provider') as mock_create_sdk, \
         patch.object(gateway, '_record_usage', AsyncMock()), \
         patch.object(gateway, '_save_chat_message', AsyncMock()):
        
        mock_sdk2 = AsyncMock()
        mock_sdk2.complete.return_value = MagicMock(text="Secondary Response", usage={"prompt_tokens": 5, "completion_tokens": 5})
        mock_create_sdk.return_value = mock_sdk2
        
        request = GatewayRequest(messages=[{"role": "user", "content": "Hello"}], run_ukg_pipeline=False)
        response = await gateway.process(request)
        
        assert response.ok is True
        assert response.provider_used == "google"
        # Should NOT have called create_sdk for provider 1
        mock_create_sdk.assert_called_once()

@pytest.mark.asyncio
async def test_gateway_usage_tracking(gateway, mock_db):
    """Test that gateway records usage information."""
    
    provider = MagicMock(id=uuid.uuid4(), name="Primary", provider_type="openai", priority=1)
    
    with patch.object(gateway, '_get_eligible_providers', AsyncMock(return_value=[provider])), \
         patch.object(gateway, '_create_sdk_provider') as mock_create_sdk, \
         patch.object(gateway, '_record_usage', AsyncMock()) as mock_usage, \
         patch.object(gateway, '_save_chat_message', AsyncMock()):
        
        mock_sdk = AsyncMock()
        mock_sdk.complete.return_value = MagicMock(text="Hi", usage={"prompt_tokens": 50, "completion_tokens": 100})
        mock_create_sdk.return_value = mock_sdk
        
        request = GatewayRequest(messages=[{"role": "user", "content": "Test Usage"}], run_ukg_pipeline=False)
        await gateway.process(request)
        
        mock_usage.assert_called_once()
        args = mock_usage.call_args[0]
        # order: provider_id, user_id, api_key_id, run_id, model, tokens_in, tokens_out, latency_ms, success
        assert args[0] == provider.id
        assert args[5] == 50 # tokens_in
        assert args[6] == 100 # tokens_out
        assert args[8] is True # success

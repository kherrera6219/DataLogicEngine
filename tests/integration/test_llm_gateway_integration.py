import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.llm_gateway.gateway import CircuitBreaker, GatewayRequest, LLMGateway


@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def gateway(mock_db):
    LLMGateway._circuit_breakers.clear()
    instance = LLMGateway(db_session=mock_db)
    yield instance
    LLMGateway._circuit_breakers.clear()

@pytest.mark.asyncio
async def test_gateway_does_not_cross_provider_failover(gateway, mock_db):
    """A standard request may not silently spend against a second provider."""
    
    # Mock eligible providers
    provider1 = MagicMock()
    provider1.id = uuid.uuid4()
    provider1.name = "Primary"
    provider1.provider_type = "openai"
    provider1.priority = 1
    provider1.model_id = "gpt-5.5"
    provider1.max_retries = 3
    provider1.timeout_seconds = 30
    
    provider2 = MagicMock()
    provider2.id = uuid.uuid4()
    provider2.name = "Secondary"
    provider2.provider_type = "google"
    provider2.priority = 2
    provider2.model_id = "gemini-3.1-pro-preview"
    
    with patch.object(gateway, '_get_eligible_providers', AsyncMock(return_value=[provider1, provider2])), \
         patch.object(gateway, '_create_sdk_provider') as mock_create_sdk, \
         patch.object(gateway, '_record_usage', AsyncMock()), \
         patch.object(gateway, '_save_chat_message', AsyncMock()):
        
        mock_sdk1 = AsyncMock()
        mock_sdk1.complete.side_effect = ConnectionError("network down")
        
        # Provider 2 succeeds
        mock_sdk2 = AsyncMock()
        mock_sdk2.complete.return_value = MagicMock(text="Secondary Response", usage={"prompt_tokens": 10, "completion_tokens": 20})
        
        mock_create_sdk.side_effect = [mock_sdk1, mock_sdk1, mock_sdk1, mock_sdk2]
        
        request = GatewayRequest(
            messages=[{"role": "user", "content": "Hello"}],
            run_ukg_pipeline=False # Direct call for simplicity
        )
        
        response = await gateway.process(request)
        
        assert response.ok is False
        assert response.provider_used == "openai"
        assert mock_create_sdk.call_count == 1
        assert mock_sdk2.complete.await_count == 0

@pytest.mark.asyncio
async def test_legacy_ollama_request_is_not_silently_rewritten(gateway, monkeypatch):
    monkeypatch.setenv("LLM_DEFAULT_PROVIDER", "google")

    provider = MagicMock()
    provider.id = uuid.uuid4()
    provider.name = "google-default"
    provider.provider_type = "google"
    provider.priority = 1
    provider.model_id = "gemini-3.1-pro-preview"
    provider.max_retries = 1
    provider.timeout_seconds = 30
    eligible = AsyncMock(return_value=[provider])

    with patch.object(gateway, "_get_eligible_providers", eligible), \
         patch.object(gateway, "_create_sdk_provider") as mock_create_sdk, \
         patch.object(gateway, "_record_usage", AsyncMock()), \
         patch.object(gateway, "_save_chat_message", AsyncMock()), \
         patch.object(gateway, "_create_trace_run", AsyncMock()):
        mock_sdk = AsyncMock()
        mock_sdk.complete.return_value = MagicMock(
            text="Google response",
            usage={"prompt_tokens": 3, "completion_tokens": 4},
        )
        mock_create_sdk.return_value = mock_sdk

        response = await gateway.process(
            GatewayRequest(
                messages=[{"role": "user", "content": "Hello"}],
                provider="ollama",
                model="gemma4:12b",
                run_ukg_pipeline=False,
            )
        )

    assert eligible.await_args.args[0] == "ollama"
    assert response.ok is False
    mock_create_sdk.assert_not_called()

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
    provider1.model_id = "gpt-5.5"
    provider1.max_retries = 1
    provider1.timeout_seconds = 30
    
    # Manually open circuit for provider 1
    cb1 = gateway._get_circuit_breaker("openai:gpt-5.5")
    cb1.record_failure()
    cb1.record_failure()
    cb1.record_failure()
    cb1.record_failure()
    cb1.record_failure() # Threshold is 5 by default
    assert cb1.state == "OPEN"
    
    with patch.object(gateway, '_get_eligible_providers', AsyncMock(return_value=[provider1])), \
         patch.object(gateway, '_create_sdk_provider') as mock_create_sdk, \
         patch.object(gateway, '_record_usage', AsyncMock()), \
         patch.object(gateway, '_save_chat_message', AsyncMock()):
        
        mock_sdk2 = AsyncMock()
        mock_sdk2.complete.return_value = MagicMock(text="Secondary Response", usage={"prompt_tokens": 5, "completion_tokens": 5})
        mock_create_sdk.return_value = mock_sdk2
        
        request = GatewayRequest(messages=[{"role": "user", "content": "Hello"}], run_ukg_pipeline=False)
        response = await gateway.process(request)
        
        assert response.ok is False
        assert response.provider_used == "none"
        mock_create_sdk.assert_not_called()

@pytest.mark.asyncio
async def test_gateway_usage_tracking(gateway, mock_db):
    """Test that gateway records usage information."""
    
    provider = MagicMock(id=uuid.uuid4(), name="Primary", provider_type="openai", priority=1)
    provider.model_id = "gpt-5.5"
    provider.max_retries = 1
    provider.timeout_seconds = 30
    
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
        # order includes provider type, session, and full ledger metadata.
        assert args[0] == provider.id
        assert args[7] == 50 # tokens_in
        assert args[8] == 100 # tokens_out
        assert args[10] is True # success


@pytest.mark.asyncio
async def test_gateway_respects_provider_retry_configuration(gateway, mock_db):
    """Provider-specific max_retries should control retry attempts."""
    provider = MagicMock()
    provider.id = uuid.uuid4()
    provider.name = "Primary"
    provider.provider_type = "openai"
    provider.model_id = "gpt-5.5"
    provider.max_retries = 2
    provider.timeout_seconds = 30

    with patch.object(gateway, '_get_eligible_providers', AsyncMock(return_value=[provider])), \
         patch.object(gateway, '_create_sdk_provider') as mock_create_sdk, \
         patch.object(gateway, '_record_usage', AsyncMock()), \
         patch.object(gateway, '_save_chat_message', AsyncMock()):

        failing_sdk = AsyncMock()
        failing_sdk.complete.side_effect = ConnectionError("network down")
        mock_create_sdk.return_value = failing_sdk

        request = GatewayRequest(
            messages=[{"role": "user", "content": "retry test"}],
            mode="enhanced",
            run_ukg_pipeline=False,
        )
        response = await gateway.process(request)

        assert response.ok is False
        assert mock_create_sdk.call_count == 2


@pytest.mark.asyncio
async def test_gateway_enforces_provider_timeout(gateway, mock_db):
    """Provider timeout_seconds should bound execution time."""
    provider = MagicMock()
    provider.id = uuid.uuid4()
    provider.name = "TimeoutProvider"
    provider.provider_type = "openai"
    provider.model_id = "gpt-5.5"
    provider.max_retries = 1
    provider.timeout_seconds = 1

    async def slow_complete(*args, **kwargs):
        await asyncio.sleep(2)
        return MagicMock(text="slow", usage={"prompt_tokens": 1, "completion_tokens": 1})

    with patch.object(gateway, '_get_eligible_providers', AsyncMock(return_value=[provider])), \
         patch.object(gateway, '_create_sdk_provider') as mock_create_sdk, \
         patch.object(gateway, '_record_usage', AsyncMock()) as mock_usage, \
         patch.object(gateway, '_save_chat_message', AsyncMock()):

        slow_sdk = AsyncMock()
        slow_sdk.complete.side_effect = slow_complete
        mock_create_sdk.return_value = slow_sdk

        request = GatewayRequest(
            messages=[{"role": "user", "content": "timeout test"}],
            run_ukg_pipeline=False,
        )
        response = await gateway.process(request)

        assert response.ok is False
        assert "request failed" in (response.error or "").lower()
        assert mock_usage.call_count >= 1
        assert mock_usage.call_args[0][10] is False



@pytest.mark.asyncio
async def test_gateway_persists_full_governed_trace_when_legacy_bypass_is_requested(app, monkeypatch):
    from extensions import db
    from models import TraceRun, TraceStage
    monkeypatch.delenv("LLM_DEFAULT_PROVIDER", raising=False)
    monkeypatch.delenv("AI_PROVIDER", raising=False)


    with app.app_context():
        gateway = LLMGateway(db_session=db.session)
        provider = MagicMock()
        provider.id = uuid.uuid4()
        provider.name = "DirectProvider"
        provider.provider_type = "openai"
        provider.model_id = "gpt-5.5"
        provider.max_retries = 1
        provider.timeout_seconds = 30

        with patch.object(gateway, "_get_eligible_providers", AsyncMock(return_value=[provider])), \
             patch.object(gateway, "_create_sdk_provider") as mock_create_sdk, \
             patch.object(gateway, "_record_usage", AsyncMock()), \
             patch.object(gateway, "_save_chat_message", AsyncMock()):
            mock_sdk = AsyncMock()
            mock_sdk.complete.return_value = MagicMock(
                text="Direct trace response",
                usage={"prompt_tokens": 2, "completion_tokens": 3},
                raw={},
            )
            mock_create_sdk.return_value = mock_sdk

            response = await gateway.process(
                GatewayRequest(
                    messages=[{"role": "user", "content": "Persist direct trace"}],
                    run_ukg_pipeline=False,
                )
            )

        run = db.session.get(TraceRun, uuid.UUID(response.run_id))
        assert response.ok is True
        assert run is not None
        assert run.input_message == "Persist direct trace"
        assert run.final_answer == "Direct trace response"
        assert run.model_name == "gpt-5.5"
        assert run.user_id is None
        stages = run.stages.order_by(TraceStage.layer_index).all()
        assert [stage.name for stage in stages] == [
            "admission",
            "dmrf_routing",
            "layer_1_normalize_route",
            "layer_2_retrieve_context",
            "layer_3_evidence_plan",
            "layer_4_persona_context",
            "layer_5_candidate_plan",
            "provider_execution",
            "layer_6_evidence_validation",
            "layer_7_reasoning_boundary",
            "layer_8_trust_policy_gate",
            "layer_9_convergence",
            "layer_10_release_gate",
            "persistence",
        ]
        assert all(stage.status == "completed" for stage in stages)


@pytest.mark.asyncio
async def test_create_trace_run_accepts_anonymous_dmrf_metadata(app):
    from extensions import db
    from models import TraceRun

    with app.app_context():
        gateway = LLMGateway(db_session=db.session)
        run_id = uuid.uuid4()

        await gateway._create_trace_run(
            {
                "ok": True,
                "answer": "DMRF enriched answer",
                "trace": [{"ka_id": "dmrf-route", "status": "pass", "output": {"tier": "high_stakes"}}],
                "metadata": {
                    "provider_used": "google",
                    "dmrf": {
                        "run_id": "dmrf_test",
                        "tier": "high_stakes",
                        "query_digest": "abc123",
                        "axis_vector": {
                            "frost_layer_depth": 7,
                            "truth_engine_mode": "regulatory_strict",
                            "confidence": 0.92,
                        },
                        "gate_result": {"decision": "allow"},
                        "steps": [
                            {
                                "name": "truth_gate",
                                "status": "ok",
                                "outputs": {"gate": {"passed": True}},
                                "started_at": "2026-07-10T17:00:00+00:00",
                                "completed_at": "2026-07-10T17:00:00.025000+00:00",
                                "snapshot_id": "snapshot-1",
                            }
                        ],
                    }
                },
            },
            "Assess finance compliance",
            str(run_id),
            "anonymous",
            "not-a-session-uuid",
            "gpt-5.5",
        )

        run = db.session.get(TraceRun, run_id)
        assert run is not None
        assert run.user_id is None
        assert run.session_id is None
        assert run.tier == "high_stakes"
        assert run.frost_depth == 7
        assert run.truth_engine_mode == "regulatory_strict"
        assert run.truthgate_decision == "allow"
        assert run.data_snapshot["dmrf"]["run_id"] == "dmrf_test"
        assert run.data_snapshot["provider_used"] == "google"
        assert run.coordinate17_id is not None
        assert run.to_dict()["provider_used"] == "google"
        assert run.to_dict()["model_name"] == "gpt-5.5"
        assert run.stages.count() == 1
        assert run.stages.first().status == "completed"


@pytest.mark.asyncio
async def test_create_trace_run_persists_dsqp_personas(app):
    from extensions import db
    from models import TracePersona, TraceRun, TraceStage

    with app.app_context():
        gateway = LLMGateway(db_session=db.session)
        run_id = uuid.uuid4()
        await gateway._create_trace_run(
            {
                "ok": True,
                "answer": "Paris",
                "tier": "T1",
                "latency_ms": 1234,
                "trace": [
                    {
                        "ka_id": "DSQP",
                        "status": "ok",
                        "output": {
                            "constructed_persona_profiles": {
                                "8": {
                                    "axis_number": 8,
                                    "persona_type": "knowledge",
                                    "name": "Historical Knowledge Analyst",
                                    "description": "Checks historical context.",
                                    "coverage_score": 1.0,
                                    "components": {"skills": {"items": ["history"]}},
                                    "metadata": {
                                        "coordinate_path": "axis_8.history",
                                        "construction_mode": "llm_assisted",
                                    },
                                    "validation": {"valid": True, "errors": []},
                                }
                            }
                        },
                    }
                ],
            },
            "Historical question",
            str(run_id),
            "anonymous",
            None,
            "gemini-3.1-pro-preview",
        )

        run = db.session.get(TraceRun, run_id)
        persona = TracePersona.query.filter_by(run_id=run_id).one()
        assert run.latency_ms == 1234
        assert TraceStage.query.filter_by(run_id=run_id).count() == 1
        assert persona.persona_type == "knowledge"
        assert persona.confidence == 1.0



@pytest.mark.asyncio
async def test_gateway_persists_failed_trace_run_for_provider_exhaustion(app):
    from extensions import db
    from models import TraceRun

    with app.app_context():
        gateway = LLMGateway(db_session=db.session)
        with patch.object(gateway, "_get_eligible_providers", AsyncMock(return_value=[])):
            response = await gateway.process(
                GatewayRequest(
                    messages=[{"role": "user", "content": "Persist failed trace"}],
                    model="gpt-5.5",
                    run_ukg_pipeline=False,
                )
            )

        run = db.session.get(TraceRun, uuid.UUID(response.run_id))
        assert response.ok is False
        assert response.provider_used == "none"
        assert run is not None
        assert run.status == "provider_failure"
        assert run.input_message == "Persist failed trace"
        assert run.model_name == "gpt-5.5"
        assert run.data_snapshot["failure"]["message"] == "No active providers found"
        assert "layer_6_evidence_validation" not in [
            stage.name for stage in run.stages.all()
        ]

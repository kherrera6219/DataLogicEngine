
import pytest
from unittest.mock import MagicMock, patch, AsyncMock, ANY

# Import targets
from backend.truth_engine.truth_core.engine import TruthCoreEngine
from backend.truth_engine.truth_core.meta_reasoning_controller import MetaReasoningController, L9Decision, RefinementSeverity
from backend.truth_engine.truth_core.l9_schemas import L9Input
from backend.llm_gateway.gateway import GatewayRequest, CircuitBreaker

@pytest.fixture
def mock_ka_controller():
    controller = MagicMock()
    controller.execute_algorithm.return_value = {"tier": "moderate", "routing_profile": "default"}
    return controller

@pytest.fixture
def truth_engine(mock_ka_controller):
    return TruthCoreEngine(ka_controller=mock_ka_controller)

@pytest.fixture
def meta_controller(mock_ka_controller):
    return MetaReasoningController(ka_controller=mock_ka_controller)

class TestTruthCoreEngine:
    def test_get_workflow_steps(self, truth_engine):
        assert 'intent_parsing' in truth_engine.get_workflow_steps('trivial')
        assert 'final_safety_gate' in truth_engine.get_workflow_steps('trivial')
        
        moderate_steps = truth_engine.get_workflow_steps('moderate')
        assert 'hybrid_retrieval' in moderate_steps
        assert 'multi_persona_reasoning' in moderate_steps
        
        extreme_steps = truth_engine.get_workflow_steps('extreme')
        assert 'deep_research' in extreme_steps
        assert 'agi_planning' in extreme_steps

    @pytest.mark.asyncio
    async def test_determine_tier_ai(self, truth_engine, mock_ka_controller):
        mock_ka_controller.execute_algorithm.return_value = {"suggested_tier": "high_stakes"}
        tier = await truth_engine.determine_tier("Is this legal?")
        assert tier == "high_stakes"
        mock_ka_controller.execute_algorithm.assert_called_with("KA-005", ANY)

    @pytest.mark.asyncio
    async def test_determine_tier_fallback(self, truth_engine, mock_ka_controller):
        mock_ka_controller.execute_algorithm.side_effect = Exception("KA Error")
        tier = await truth_engine.determine_tier("Hi")
        assert tier == "trivial"
        
        tier = await truth_engine.determine_tier("Risk assessment for project X in legal context")
        assert tier == "high_stakes"

    @pytest.mark.asyncio
    async def test_create_session(self, truth_engine):
        session = await truth_engine.create_session("Test query", user_id=1)
        assert session['query'] == "Test query"
        assert session['user_id'] == 1
        assert 'session_id' in session
        assert session['status'] == 'created'
        assert session['session_id'] in truth_engine.active_sessions

class TestMetaReasoningController:
    def test_meta_evaluate_finalize(self, meta_controller, mock_ka_controller):
        # High confidence, no issues
        input_data = L9Input(
            simulation_id="sim-123",
            l8_gate_result={
                "overall_confidence": 0.98,
                "domain_confidences": [{"domain": "legal", "confidence": 0.99}],
                "quantum_summary": "All good"
            },
            reasoning_trace={"layer1": {"output": "ok"}, "layer2": {"output": "ok"}},
            risk_domain="standard"
        )
        
        # Mocking KA results for component evaluations
        mock_ka_controller.execute_algorithm.side_effect = [
            {"issues": []}, # L9-KA-001
            {"drift_detected": False}, # L9-KA-002
            {}, # L9-KA-003
            {"weaknesses": []}, # L9-KA-004
            {"quality_score": 0.99}, # KA-008
            {"bias_detected": False}, # KA-010
            {"drift_score": 0.0}, # KA-022
            {"awareness_score": 0.99}, # KA-025
            {"readiness_score": 0.98}, # L9-KA-006
            {"trigger_refinement": False} # L9-KA-005
        ]
        
        result = meta_controller.evaluate(input_data)
        assert result.decision == L9Decision.FINALIZE
        assert result.readiness_score >= 0.95

    def test_meta_evaluate_refine(self, meta_controller, mock_ka_controller):
        # Low confidence/Disagreement
        input_data = L9Input(
            simulation_id="sim-456",
            l8_gate_result={
                "overall_confidence": 0.7,
                "domain_confidences": [{"domain": "legal", "confidence": 0.6}],
                "quantum_summary": "Inconsistent"
            },
            reasoning_trace={"layer1": {"output": "ok"}},
            risk_domain="high_risk"
        )
        
        mock_ka_controller.execute_algorithm.side_effect = [
            {"issues": [{"type": "missing_output", "layer": 2}]}, # L9-KA-001
            {"drift_detected": True, "drift_score": 0.4}, # L9-KA-002
            {}, # L9-KA-003
            {"weaknesses": [{"area": "general", "description": "Low support"}]}, # L9-KA-004
            {"quality_score": 0.7}, # KA-008
            {"bias_detected": True}, # KA-010
            {"drift_score": 0.4}, # KA-022
            {"awareness_score": 0.6}, # KA-025
            {"readiness_score": 0.6}, # L9-KA-006
            {"trigger_refinement": True, "target_layer": 5} # L9-KA-005
        ]
        
        result = meta_controller.evaluate(input_data)
        if result.refinement_plan is None:
            print(f"DEBUG: disclosure_flags={result.disclosure_flags}")
        assert result.decision == L9Decision.REFINE
        assert result.severity == RefinementSeverity.MAJOR
        assert result.refinement_plan is not None
        assert result.refinement_plan.target_layer == 5

    def test_iteration_limits(self, meta_controller):
        input_data = L9Input(
            simulation_id="sim-789",
            l8_gate_result={},
            iteration_state={"current_iteration": 5, "max_iterations": 5}
        )
        result = meta_controller.evaluate(input_data)
        assert result.decision == L9Decision.FINALIZE
        assert "Max iterations reached" in result.disclosure_flags[0]

class TestLLMGateway:
    def test_circuit_breaker(self):
        cb = CircuitBreaker("TestProvider", failure_threshold=2, recovery_timeout=0.1)
        assert cb.can_execute() == True
        
        cb.record_failure()
        assert cb.can_execute() == True
        
        cb.record_failure()
        assert cb.can_execute() == False
        assert cb.state == "OPEN"
        
        # Test recovery
        import time
        time.sleep(0.15)
        assert cb.can_execute() == True
        assert cb.state == "HALF_OPEN"
        
        cb.record_success()
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_gateway_routing(self):
        from backend.llm_gateway.gateway import LLMGateway
        
        mock_db = MagicMock()
        gateway = LLMGateway(db_session=mock_db)
        
        # Mock provider config
        mock_provider = MagicMock()
        mock_provider.name = "openai"
        mock_provider.id = 1
        mock_provider.provider_type = "openai"
        mock_provider.api_key = "test-key"
        
        # Mock eligible providers
        with patch.object(gateway, "_get_eligible_providers", new_callable=AsyncMock) as mock_get_p:
            mock_get_p.return_value = [mock_provider]
            
            req = GatewayRequest(messages=[{"role": "user", "content": "hi"}], provider="openai")
            
            with patch.object(gateway, '_run_ukg_overlay', new_callable=AsyncMock) as mock_overlay:
                mock_overlay.return_value = {
                    "answer": "UKG Response",
                    "ok": True,
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5}
                }
                
                # Mock record_usage to avoid DB calls
                with patch.object(gateway, '_record_usage', new_callable=AsyncMock):
                    response = await gateway.process(req)
                    assert response.content == "UKG Response"
                    assert response.ok == True

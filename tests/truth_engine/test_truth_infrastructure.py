
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest

# Import targets
from backend.knowledge_algorithms.contracts import (
    KAExecutionResult,
    KAExecutionState,
    KAOutcomeType,
)
from backend.llm_gateway.gateway import CircuitBreaker, GatewayRequest
from backend.truth_engine.truth_core.engine import TruthCoreEngine
from backend.truth_engine.truth_core.l9_schemas import L9Input
from backend.truth_engine.truth_core.meta_reasoning_controller import (
    L9Decision,
    MetaReasoningController,
    RefinementSeverity,
)


def typed_result(ka_id, output):
    return KAExecutionResult(
        canonical_id=ka_id,
        ka_version="1.0.0",
        manifest_version="test",
        state=KAExecutionState.SUCCEEDED,
        outcome_type=KAOutcomeType.VALUE,
        success=True,
        output=output,
        request_id="request-test",
        run_id="run-test",
        trace_id=f"trace-{ka_id}",
    )


@pytest.fixture
def mock_ka_controller():
    controller = MagicMock()
    controller.execute_typed.return_value = typed_result(
        "KA-005",
        {"suggested_tier": "moderate"},
    )
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
        mock_ka_controller.execute_typed.return_value = typed_result(
            "KA-005",
            {"suggested_tier": "high_stakes"},
        )
        tier = await truth_engine.determine_tier("Is this legal?")
        assert tier == "high_stakes"
        mock_ka_controller.execute_typed.assert_called_with("KA-005", ANY)

    @pytest.mark.asyncio
    async def test_determine_tier_fallback(self, truth_engine, mock_ka_controller):
        mock_ka_controller.execute_typed.side_effect = Exception("KA Error")
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
        mock_ka_controller.execute_typed.side_effect = [
            typed_result("L9-KA-001", {"issues": []}),
            typed_result("L9-KA-002", {"drift_detected": False}),
            typed_result("L9-KA-003", {}),
            typed_result(
                "L9-KA-004",
                {"weaknesses": [], "failure_modes": [], "alternatives": []},
            ),
            typed_result("KA-008", {"overall_score": 0.99}),
            typed_result("KA-010", {"is_biased": False}),
            typed_result("KA-022", {"overall_risk_score": 0.0}),
            typed_result("KA-025", {"meta": {"is_dag": True}}),
            typed_result("L9-KA-006", {"readiness_score": 0.98}),
            typed_result("L9-KA-005", {"trigger_refinement": False}),
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
        
        mock_ka_controller.execute_typed.side_effect = [
            typed_result(
                "L9-KA-001",
                {"issues": [{"type": "missing_output", "layer": 2}]},
            ),
            typed_result(
                "L9-KA-002",
                {
                    "drift_detected": True,
                    "drift_score": 0.4,
                    "drift_type": "semantic",
                },
            ),
            typed_result("L9-KA-003", {}),
            typed_result(
                "L9-KA-004",
                {
                    "weaknesses": [
                        {"area": "general", "description": "Low support"}
                    ],
                    "failure_modes": [],
                    "alternatives": [],
                },
            ),
            typed_result("KA-008", {"overall_score": 0.7}),
            typed_result("KA-010", {"is_biased": True}),
            typed_result("KA-022", {"overall_risk_score": 0.4}),
            typed_result("KA-025", {"meta": {"is_dag": True}}),
            typed_result("L9-KA-006", {"readiness_score": 0.6}),
            typed_result(
                "L9-KA-005",
                {
                    "trigger_refinement": True,
                    "target_layer": 5,
                    "reason": "readiness below threshold",
                },
            ),
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
        assert cb.can_execute()
        
        cb.record_failure()
        assert cb.can_execute()
        
        cb.record_failure()
        assert not cb.can_execute()
        assert cb.state == "OPEN"
        
        # Test recovery
        import time
        time.sleep(0.15)
        assert cb.can_execute()
        assert cb.state == "HALF_OPEN"
        
        cb.record_success()
        assert cb.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_gateway_compatibility_request_enters_canonical_execute(self):
        from backend.governed_execution.contracts import GovernedMode, GovernedResult
        from backend.llm_gateway.gateway import LLMGateway

        mock_db = MagicMock()
        gateway = LLMGateway(db_session=mock_db)
        gateway.execute = AsyncMock(
            return_value=GovernedResult(
                trace_id="00000000-0000-0000-0000-000000000001",
                ok=True,
                status="completed",
                mode=GovernedMode.STANDARD,
                answer="Governed response",
                provider_used="openai",
                model_used="gpt-test",
                usage={"prompt_tokens": 10, "completion_tokens": 5},
            )
        )

        req = GatewayRequest(messages=[{"role": "user", "content": "hi"}], provider="openai")
        response = await gateway.process(req)

        gateway.execute.assert_awaited_once_with(req)
        assert response.content == "Governed response"
        assert response.contract_version == "governed.v1"
        assert response.ok is True

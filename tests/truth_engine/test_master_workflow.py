from typing import Any

import pytest

from backend.knowledge_algorithms.contracts import (
    KAExecutionResult,
    KAExecutionState,
    KAOutcomeType,
)
from backend.truth_engine.truth_core.engine import TruthCoreEngine


def typed_result(ka_id: str, output: dict[str, Any]) -> KAExecutionResult:
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

class MockService:
    def validate(self, *args, **kwargs): return {"status": "valid", "confidence": 0.99}
    def plan(self, *args, **kwargs): 
        from types import SimpleNamespace
        return SimpleNamespace(convergence_score=0.98, root_goal=SimpleNamespace(depth=3))

class MockController:
    def __init__(self):
        self.llm_gateway = "mock_gateway"
    def execute_typed(self, ka_id: str, inputs: dict[str, Any]) -> KAExecutionResult:
        return typed_result(
            ka_id,
            {
                "result": f"Result from {ka_id}",
                "passed": True,
                "confidence": 0.95,
            },
        )
    def authorize(self, *args, **kwargs):
        from types import SimpleNamespace
        return SimpleNamespace(decision=SimpleNamespace(value="RELEASE"), final_answer="Safety Approved Output", model_dump=dict)
    def evaluate(self, *args, **kwargs):
        from types import SimpleNamespace
        return SimpleNamespace(decision=SimpleNamespace(value="FINALIZE"), readiness_score=0.99, model_dump=dict)
    def validate(self, *args, **kwargs):
        from types import SimpleNamespace
        return SimpleNamespace(status=SimpleNamespace(value="PASS"), overall_confidence=0.98, model_dump=dict)

@pytest.fixture
def engine():
    eng = TruthCoreEngine(ka_controller=MockController())
    eng.quant_service = MockService()
    eng.agi_planner = MockService()
    eng.trust_gateway = MockController()
    eng.meta_reasoning = MockController()
    eng.emergence_gate = MockController()
    return eng

@pytest.mark.asyncio
async def test_trivial_tier_express_lane(engine):
    """Test L1 -> L10 express lane."""
    result = await engine._execute_workflow(
        "How are you?", {}, engine.get_workflow_steps("trivial"), "trivial"
    )
    
    steps = [s['step'] for s in result['steps_executed']]
    assert 'intent_parsing' in steps
    assert 'final_safety_gate' in steps
    assert len(steps) == 2
    assert result['tier'] == 'trivial'

@pytest.mark.asyncio
async def test_moderate_tier_workflow(engine):
    """Test L1, L2, L5, L10 workflow."""
    result = await engine._execute_workflow(
        "What is UKG?", {}, engine.get_workflow_steps("moderate"), "moderate"
    )
    
    steps = [s['step'] for s in result['steps_executed']]
    assert steps == ['intent_parsing', 'hybrid_retrieval', 'multi_persona_reasoning', 'final_safety_gate']
    assert result['tier'] == 'moderate'

@pytest.mark.asyncio
async def test_high_stakes_tier_full_audit(engine):
    """Test workflow with L8 trust gate and L9 meta-reasoning."""
    result = await engine._execute_workflow(
        "Financial forecast for 2026",
        {},
        engine.get_workflow_steps("high_stakes"),
        "high_stakes",
    )
    
    steps = [s['step'] for s in result['steps_executed']]
    assert 'trust_validation' in steps
    assert 'meta_reasoning' in steps
    assert 'final_safety_gate' in steps
    assert result['tier'] == 'high_stakes'

@pytest.mark.asyncio
async def test_extreme_tier_full_stack(engine):
    """Test all 10 layers."""
    result = await engine._execute_workflow(
        "Solve autonomous fusion", {}, engine.get_workflow_steps("extreme"), "extreme"
    )
    
    steps = [s['step'] for s in result['steps_executed']]
    assert len(steps) == 10
    assert steps[0] == 'intent_parsing'
    assert steps[-1] == 'final_safety_gate'
    assert 'agi_planning' in steps
    assert 'deep_research' in steps

@pytest.mark.asyncio
async def test_sentinel_safety_enforced_on_all_tiers(engine):
    """Ensure L10 is always the last step."""
    for tier in ['trivial', 'moderate', 'high_stakes', 'extreme']:
        result = await engine._execute_workflow(
            "test", {}, engine.get_workflow_steps(tier), tier
        )
        assert result['steps_executed'][-1]['step'] == 'final_safety_gate'

import pytest
import uuid
from typing import Dict, Any
from backend.truth_engine.truth_core.engine import TruthCoreEngine

class MockService:
    def validate(self, *args, **kwargs): return {"status": "valid", "confidence": 0.99}
    def plan(self, *args, **kwargs): 
        from types import SimpleNamespace
        return SimpleNamespace(convergence_score=0.98, root_goal=SimpleNamespace(depth=3))

class MockController:
    def __init__(self):
        self.llm_gateway = "mock_gateway"
    def execute_algorithm(self, ka_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return {"output": f"Result from {ka_id}", "passed": True, "confidence": 0.95}
    def authorize(self, *args, **kwargs):
        from types import SimpleNamespace
        return SimpleNamespace(decision=SimpleNamespace(value="RELEASE"), final_answer="Safety Approved Output", model_dump=lambda: {})
    def evaluate(self, *args, **kwargs):
        from types import SimpleNamespace
        return SimpleNamespace(decision=SimpleNamespace(value="FINALIZE"), readiness_score=0.99, model_dump=lambda: {})
    def validate(self, *args, **kwargs):
        from types import SimpleNamespace
        return SimpleNamespace(status=SimpleNamespace(value="PASS"), overall_confidence=0.98, model_dump=lambda: {})

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
    session = await engine.create_session("How are you?", tier="trivial")
    result = await engine.process(session['session_id'])
    
    steps = [s['step'] for s in result['workflow_steps']]
    assert 'intent_parsing' in steps
    assert 'final_safety_gate' in steps
    assert len(steps) == 2
    assert result['tier'] == 'trivial'

@pytest.mark.asyncio
async def test_moderate_tier_workflow(engine):
    """Test L1, L2, L5, L10 workflow."""
    session = await engine.create_session("What is UKG?", tier="moderate")
    result = await engine.process(session['session_id'])
    
    steps = [s['step'] for s in result['workflow_steps']]
    assert steps == ['intent_parsing', 'hybrid_retrieval', 'multi_persona_reasoning', 'final_safety_gate']
    assert result['tier'] == 'moderate'

@pytest.mark.asyncio
async def test_high_stakes_tier_full_audit(engine):
    """Test workflow with L8 trust gate and L9 meta-reasoning."""
    session = await engine.create_session("Financial forecast for 2026", tier="high_stakes")
    result = await engine.process(session['session_id'])
    
    steps = [s['step'] for s in result['workflow_steps']]
    assert 'trust_validation' in steps
    assert 'meta_reasoning' in steps
    assert 'final_safety_gate' in steps
    assert result['tier'] == 'high_stakes'

@pytest.mark.asyncio
async def test_extreme_tier_full_stack(engine):
    """Test all 10 layers."""
    session = await engine.create_session("Solve autonomous fusion", tier="extreme")
    result = await engine.process(session['session_id'])
    
    steps = [s['step'] for s in result['workflow_steps']]
    assert len(steps) == 10
    assert steps[0] == 'intent_parsing'
    assert steps[-1] == 'final_safety_gate'
    assert 'agi_planning' in steps
    assert 'deep_research' in steps

@pytest.mark.asyncio
async def test_sentinel_safety_enforced_on_all_tiers(engine):
    """Ensure L10 is always the last step."""
    for tier in ['trivial', 'moderate', 'high_stakes', 'extreme']:
        session = await engine.create_session("test", tier=tier)
        result = await engine.process(session['session_id'])
        assert result['workflow_steps'][-1]['step'] == 'final_safety_gate'

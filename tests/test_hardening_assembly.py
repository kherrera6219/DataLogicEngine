import pytest
from backend.truth_engine.truth_core.engine import TruthCoreEngine
from core.persona.quad.persona_scaling.sufficiency import GatewayPersonaSufficiencyTool as PersonaSufficiencyTool, SufficiencyMode

class MockKAController:
    def __init__(self):
        self.llm_gateway = None

    def execute_algorithm(self, ka_id, context):
        return {"output": {"personas": {}}, "confidence": 0.9, "status": "completed"}
    
    def process_with_persona(self, query, persona, context):
        return {"response": f"Persona {persona} response", "confidence": 0.85, "status": "completed"}

@pytest.fixture
def engine():
    ka_ctrl = MockKAController()
    e = TruthCoreEngine(ka_controller=ka_ctrl)
    # Disable service overrides for integration testing of core loops
    e.quant_service = None
    e.agi_planner = None
    e.trust_gateway = None
    e.meta_reasoning = None
    e.emergence_gate = None
    return e

@pytest.mark.asyncio
async def test_refinement_resilience_recovery():
    from backend.truth_engine.truth_core.refinement_orchestrator import RefinementOrchestrator
    ka_ctrl = MockKAController()
    orchestrator = RefinementOrchestrator(ka_controller=ka_ctrl)
    
    # Mock a failing KA step that drops confidence
    async def failing_step(step, content, context):
        return {"confidence": 0.1, "content": "Adversarial sabotage"}
    
    orchestrator._execute_step = failing_step
    
    initial_response = {"content": "Initial answer", "confidence": 0.8}
    refined = await orchestrator.refine(initial_response, {})
    
    # Should revert to initial state due to confidence drop
    assert refined['final_confidence'] == 0.8
    assert "Adversarial" not in refined['content']

@pytest.mark.asyncio
async def test_persona_sufficiency_adversarial_input():
    tool = PersonaSufficiencyTool()
    
    # Attack: Massive axis mapping
    result = tool.evaluate("query", [1]*100, {}, {})
    assert result['mode'] == SufficiencyMode.QUAD_ONLY.value
    assert "Fail-safe triggered" in result['reasons'][0]
    
    # Attack: Massive query
    result = tool.evaluate("A" * 20000, [], {}, {})
    assert result['mode'] == SufficiencyMode.QUAD_ONLY.value

@pytest.mark.asyncio
async def test_parallel_pod_execution(engine):
    # This verifies the engine can handle multiple lanes scaling simultaneously
    query = "Critical defense infrastructure audit"
    context = {"force_tier": "high_stakes", "tags": ["defense"]}
    
    result = await engine._execute_workflow(
        query,
        context,
        engine.get_workflow_steps('high_stakes'),
        'high_stakes',
    )
    
    # Debug info
    print(f"\nSession Tier: {result['tier']}")
    print(f"Workflow Steps: {result.get('steps_executed')}")
    persona_results = result.get('context', {}).get('persona_results', {})
    print(f"Persona Results Keys: {persona_results.keys()}")

    assert result['response'] is not None
    
    pod_keys = [k for k in persona_results.keys() if "_pod" in k]
    assert len(pod_keys) > 0, f"No persona pods were triggered. Results: {persona_results.keys()}"
    assert persona_results[pod_keys[0]]['specialist_count'] > 0

# (test_api_middleware_hardening removed: it exercised the dead
# backend/api_gateway/unified_middleware.UnifiedMiddleWare, which the api_gateway
# service never used — it applies middleware/asgi_security instead. See ORPH-2.)

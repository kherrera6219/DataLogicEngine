import pytest
from backend.truth_engine.truth_core.engine import TruthCoreEngine
from core.persona.quad.persona_scaling.sufficiency import GatewayPersonaSufficiencyTool as PersonaSufficiencyTool, SufficiencyMode

class MockKAController:
    def __init__(self):
        self.llm_gateway = None

    def execute_algorithm(self, ka_id, context):
        if "step_name" in context.get("step_metadata", {}):
            return {"output": "Refined by Mock", "refined_content": "Refined by Mock KA", "confidence": 0.99}
        return {"output": "Mock output", "confidence": 0.9}
    
    def process_with_persona(self, query, persona, context):
        return {"response": f"Persona {persona} response", "confidence": 0.85}

@pytest.fixture
def engine():
    ka_ctrl = MockKAController()
    e = TruthCoreEngine(ka_controller=ka_ctrl)
    # Disable service overrides to test the assembly logic in isolation
    e.quant_service = None
    e.agi_planner = None
    e.trust_gateway = None
    e.meta_reasoning = None
    e.emergence_gate = None
    return e

def test_persona_sufficiency_trigger():
    tool = PersonaSufficiencyTool()
    
    # Test High-Stakes trigger
    metadata = {"tags": ["defense"]}
    query = "Analyze the impact of electronic warfare on avionics."
    mapped_axes = [1, 2, 3, 4, 5, 8, 9] # Many axes
    initial_outputs = {"knowledge": {"confidence": 0.7}}
    
    result = tool.evaluate(query, mapped_axes, initial_outputs, metadata)
    assert result['mode'] == SufficiencyMode.EXPANDED_COMMITTEE.value
    assert result['spawn']['knowledge'] > 0
    assert "High stakes/assurance detected" in result['reasons'][0]

@pytest.mark.asyncio
async def test_refinement_orchestrator_flow():
    from backend.truth_engine.truth_core.refinement_orchestrator import RefinementOrchestrator
    ka_ctrl = MockKAController()
    orchestrator = RefinementOrchestrator(ka_controller=ka_ctrl)
    
    initial_response = {"content": "Initial answer", "confidence": 0.8}
    refined = await orchestrator.refine(initial_response, {})
    
    assert refined['final_confidence'] > 0.8
    assert len(refined['refinement_history']) == 12
    # Increased gain in mock or lower threshold
    assert refined['final_confidence'] >= 0.98

@pytest.mark.asyncio
async def test_engine_integration_high_stakes(engine):
    # High stakes should trigger refinement and pod scaling
    query = "defense strategy for autonomous systems"
    context = {"force_tier": "high_stakes", "tags": ["defense"]}
    
    result = await engine._execute_workflow(
        query,
        context,
        engine.get_workflow_steps('high_stakes'),
        'high_stakes',
    )
    assert result['tier'] == 'high_stakes'
    
    steps = result['steps_executed']
    refinement_step = next((s for s in steps if s['step'] == 'final_safety_gate'), None)
    assert refinement_step is not None
    # Check if refinement actually happened
    assert "Refined by" in refinement_step.get('final_answer', '')

def test_persona_pod_synthesis():
    from backend.truth_engine.truth_core.personas import PersonaPod
    specialists = [
        {"role": "Spec1", "response": "Answer 1", "confidence": 0.9},
        {"role": "Spec2", "response": "Answer 2", "confidence": 0.8}
    ]
    pod = PersonaPod("knowledge", specialists)
    # Mock execute results
    pod.results = specialists
    synthesis = pod.synthesize()
    
    assert synthesis['lane'] == "knowledge"
    assert "Answer 1" in synthesis['content']
    assert synthesis['confidence'] == pytest.approx(0.85)
    assert synthesis['specialist_count'] == 2

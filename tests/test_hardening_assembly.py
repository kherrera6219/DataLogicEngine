import pytest
import asyncio
from typing import Dict, Any
from backend.truth_engine.truth_core.engine import TruthCoreEngine
from backend.truth_engine.truth_core.personas import PersonaEnhancer, PersonaPod
from backend.truth_engine.truth_core.persona_sufficiency import PersonaSufficiencyTool, SufficiencyMode
from backend.api_gateway.unified_middleware import UnifiedMiddleWare

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
    
    session = await engine.create_session(query, context=context)
    result_session = await engine.process(session['session_id'])
    
    # Debug info
    print(f"\nSession Tier: {result_session['tier']}")
    print(f"Workflow Steps: {result_session.get('workflow_steps')}")
    persona_results = result_session.get('context', {}).get('persona_results', {})
    print(f"Persona Results Keys: {persona_results.keys()}")

    result = result_session['result']
    assert result_session['status'] == 'completed'
    
    pod_keys = [k for k in persona_results.keys() if "_pod" in k]
    assert len(pod_keys) > 0, f"No persona pods were triggered. Results: {persona_results.keys()}"
    assert persona_results[pod_keys[0]]['specialist_count'] > 0

@pytest.mark.asyncio
async def test_api_middleware_hardening():
    # We test the middleware logic in isolation
    from fastapi import Request, Response
    from starlette.datastructures import Headers
    
    middleware = UnifiedMiddleWare(None)
    
    class MockApp:
        async def __call__(self, scope, receive, send):
            pass # Not used for isolation test
            
    async def call_next(request):
        return Response(content="OK", status_code=200)

    # Test Header Sanitization
    headers = Headers({"X-UKG-Axis": "8:9:INVALID", "X-Nurnburg-Alias": "TEST!@#$ALIAS"})
    # Mock FastAPI request
    scope = {"type": "http", "method": "GET", "path": "/", "headers": headers.raw}
    request = Request(scope)
    
    response = await middleware.dispatch(request, call_next)
    
    # Check Security Headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "hardened_v2" in response.headers["X-Nurnburg-Compliance"]
    
    # Check trace context (internal state)
    assert request.state.ukg_metadata["axis"] == "8:9:" # Sanitized
    assert request.state.ukg_metadata["nurnburg_alias"] == "TESTALIAS" # Sanitized

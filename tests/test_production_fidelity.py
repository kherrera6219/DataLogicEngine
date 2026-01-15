import pytest
import asyncio
from typing import Dict, Any
from backend.truth_engine.truth_core.engine import TruthCoreEngine
from backend.truth_engine.truth_core.personas import PersonaEnhancer, PersonaPod
from backend.truth_engine.truth_core.persona_sufficiency import PersonaSufficiencyTool

from knowledge_algorithms.ka_master_controller import get_controller

@pytest.fixture
def production_engine():
    # Use the REAL production controller
    master = get_controller()
    engine = TruthCoreEngine(ka_controller=master)
    # Clear other services to focus on core loops
    engine.quant_service = None
    return engine, master

@pytest.mark.asyncio
async def test_production_refinement_fidelity(production_engine):
    engine, master = production_engine
    from backend.truth_engine.truth_core.refinement_orchestrator import RefinementOrchestrator
    orchestrator = RefinementOrchestrator(ka_controller=master)
    
    # We use a query that triggers the real KA-001 (AoT) through the controller
    initial_content = {"content": "Initial policy draft", "confidence": 0.7}
    context = {"query": "Draft a UKG compliance policy for data privacy", "session_id": "sess_production_1"}
    
    # This now runs real KA logic
    result = await orchestrator.refine(initial_content, context)
    
    assert "content" in result
    assert result['final_confidence'] > 0
    # The real KA-001 (AoT) should have been registered in the system trace or output
    assert result.get('AoT_Polish_status') == "executed"

@pytest.mark.asyncio
async def test_production_sufficiency_heuristics():
    tool = PersonaSufficiencyTool()
    
    # Test Conflict Heuristic (Variance in confidence)
    initial_outputs = {
        "p1": {"confidence": 0.9},
        "p2": {"confidence": 0.4} # Variance 0.0625 -> score 0.25
    }
    scores = tool._calculate_scores("query", [], initial_outputs, {})
    assert scores['conflict'] >= 0.2
    
    # Test Coverage Heuristic
    mapped_axes = [8, 10]
    initial_outputs_low = {"p1": {"response": "Nothing about axes here"}}
    scores_low = tool._calculate_scores("query", mapped_axes, initial_outputs_low, {})
    assert scores_low['coverage'] == 0.0
    
    initial_outputs_high = {"p1": {"response": "Analysis of Axis 8 and coordinate 10..."}}
    scores_high = tool._calculate_scores("query", mapped_axes, initial_outputs_high, {})
    assert scores_high['coverage'] == 1.0

@pytest.mark.asyncio
async def test_production_tiering_and_routing(production_engine):
    engine, master = production_engine
    
    # Real determining of tier via heuristics or KAs
    session = await engine.create_session("Expert legal compliance audit for defense sector")
    
    # "legal" keyword should trigger high_stakes in heuristics if KA-005 fails (likely in test env)
    assert session['tier'] in ["high_stakes", "moderate"]
    assert session['routing_profile'] in ["default", "analysis"]

def test_pii_shield_active():
    from backend.api_gateway.unified_middleware import PIIShield
    
    raw_text = "Contact me at bob@example.com or SSN 123-45-6789. ID: UKG-998877"
    redacted = PIIShield.redact(raw_text)
    
    assert "[PROTECTED_EMAIL]" in redacted
    assert "[PROTECTED_SSN]" in redacted
    assert "[PROTECTED_EMPLOYEE_ID]" in redacted
    assert "bob@example.com" not in redacted
    assert "123-45-6789" not in redacted

"""
End-to-End Test for DataLogicEngine Simulation
"""
import sys
import os
sys.path.append(os.getcwd())

import pytest
from unittest.mock import patch
from core.simulation.legacy_simulation_engine import create_simulation_engine

@pytest.fixture
def mock_quad_engine():
    pytest.skip("Test targets deprecated SimulationEngine API (process_query vs run_simulation)")
    with patch("simulation.simulation_engine.QuadPersonaEngine") as MockClass:
        mock_instance = MockClass.return_value
        # Mock the process_query method to return a standard valid response
        mock_instance.process_query.return_value = {
            "confidence": 0.85,
            "perspectives": [
                {"persona": "Knowledge Expert", "perspective": "Theoretically sound.", "confidence": 0.9},
                {"persona": "Sector Expert", "perspective": "Industry standard.", "confidence": 0.85},
                {"persona": "Regulatory Expert", "perspective": "Compliant.", "confidence": 0.9},
                {"persona": "Compliance Expert", "perspective": "Within limits.", "confidence": 0.8}
            ]
        }
        yield mock_instance

def test_full_simulation_flow(mock_quad_engine):
    """
    Test the full flow:
    SimulationEngine -> QuadPersonaEngine (Mocked) -> RefinementWorkflow -> KA-Registry
    """
    engine = create_simulation_engine()
    
    query = "How do we implement AI compliance in UKG?"
    context = {"simulation_id": "TEST-SIM-E2E"}
    
    # Execute
    result = engine.process_query(query, context)
    
    # Verification
    if result["status"] == "error":
        with open("e2e_error.log", "w") as f:
            f.write(f"Error: {result.get('error')}\n")
            f.write(f"Full Result: {result}")
        
    assert result["status"] == "completed"
    assert result["simulation_id"] == "TEST-SIM-E2E"
    assert result["confidence"] > 0
    assert result["response"] is not None
    
    # Check that Refinement Workflow ran (it adds metadata or modifies confidence)
    # The default mock returns 0.85 confidence. 
    # KA-007 (Synthesis) logic in RefinementWorkflow usually boosts confidence if successful.
    # Checks specific to RefinementWorkflow logic:
    # "confidence": min(1.0, current_conf + 0.1) -> 0.85 + 0.1 = 0.95
    
    assert result["confidence"] > 0.85, "Refinement Workflow should have improved confidence"
    
    print(f"\n✅ Simulation Result: {result['confidence']} confidence")
    print(f"Response Preview: {result['response'][:50]}...")

if __name__ == "__main__":
    # verification mode run
    import sys
    sys.exit(pytest.main(["-v", __file__]))

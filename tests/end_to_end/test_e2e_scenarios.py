import pytest
from unittest.mock import MagicMock
from backend.truth_engine.truth_core.refinement_orchestrator import RefinementOrchestrator, RefinementStep

@pytest.fixture
def orchestrator():
    mock_controller = MagicMock()
    # RefinementStep(name, ka_id, description)
    steps = [
        RefinementStep(name="Regulatory Mapping", ka_id="KA-016", description="Test"),
        RefinementStep(name="Schema Mapping", ka_id="KA-075", description="Test")
    ]
    orchestrator = RefinementOrchestrator(ka_controller=mock_controller)
    # Override STEPS for the test to avoid running all 12
    orchestrator.STEPS = steps
    return orchestrator

@pytest.mark.asyncio
async def test_simulated_user_journey(orchestrator):
    """
    Simulates a users journey:
    1. Initial query received.
    2. Orchestrator executes multiple KA steps.
    3. Final refined response generated with history.
    """
    initial_response = {
        "content": "Initial raw data",
        "confidence": 0.5
    }
    context = {
        "user_id": "user_123",
        "tenant_id": "tenant_abc",
        "session_id": "sess_999"
    }

    # We mock execute_algorithm directly to avoid complex KA registry loading
    orchestrator.ka_controller.execute_algorithm.side_effect = [
        {"refined_content": "Step 1: Mapping found", "confidence": 0.7, "audit_meta": {"ka": "KA-016"}},
        {"refined_content": "Step 2: Nurnburg naming applied", "confidence": 0.9, "audit_meta": {"ka": "KA-075"}}
    ]

    refined_output = await orchestrator.refine(initial_response, context)

    # Assertions
    assert refined_output["content"] == "Step 2: Nurnburg naming applied"
    assert refined_output["confidence"] == 0.9
    assert len(refined_output["refinement_history"]) == 2
    
    # Verify history structure
    history = refined_output["refinement_history"]
    assert history[0]["step"] == "Regulatory Mapping"
    assert history[1]["step"] == "Schema Mapping"
    assert refined_output["content"] == "Step 2: Nurnburg naming applied"

def test_export_flow():
    """Verifies the logic that would be used for exporting the results."""
    from backend.utils.responses import success_response
    from flask import Flask
    
    app = Flask(__name__)
    with app.app_context():
        # Simulate final payload for export
        final_data = {
            "report_id": "REP-2026",
            "content": "Full Compliance Report...",
            "metadata": {"generated_at": "2026-02-02"}
        }
        
        resp, code = success_response(final_data, "Export successful")
        data = resp.get_json()
        
        assert data['success'] is True
        assert data['data']['report_id'] == "REP-2026"
        assert code == 200

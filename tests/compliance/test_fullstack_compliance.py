import pytest
from unittest.mock import MagicMock
from backend.knowledge_algorithms.contracts import (
    KAExecutionResult,
    KAExecutionState,
    KAOutcomeType,
)
from backend.truth_engine.truth_core.refinement_orchestrator import RefinementOrchestrator
from backend.knowledge_algorithms.ka_16_regulatory_mapping import KA016RegulatoryMapping, KA016Input
from backend.knowledge_algorithms.ka_75_schema_mapping import KA075SchemaMapping, KA075MappingInput

@pytest.fixture
def mock_ka_controller():
    return MagicMock()

@pytest.fixture
def orchestrator(mock_ka_controller):
    return RefinementOrchestrator(ka_controller=mock_ka_controller)


def _typed_result(ka_id, output):
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

@pytest.mark.asyncio
async def test_refinement_orchestrator_loop(orchestrator, mock_ka_controller):
    """Verify that orchestrator executes all 12 steps and handles success/failure."""
    initial_response = {"content": "Initial answer", "confidence": 0.8}
    context = {"query": "Test compliance query", "session_id": "test-session"}
    
    # Mock execute_algorithm to return improving results
    def mock_execute(ka_id, ka_input):
        return _typed_result(
            ka_id,
            {
                "refined_content": f"Refined by {ka_id}",
                "confidence": min(
                    0.999,
                    0.82
                    + (
                        0.01
                        * int(
                            ka_id.split('-')[-1]
                            if '-' in ka_id
                            else 1
                        )
                    ),
                ),
                "audit_meta": {"status": "ok"},
            },
        )
    
    # Need to handle both synchronous and asynchronous calls if run_in_executor is used
    mock_ka_controller.execute_typed.side_effect = mock_execute
    
    result = await orchestrator.refine(initial_response, context)
    
    assert "refinement_history" in result
    assert len(result["refinement_history"]) == 12
    assert result["final_confidence"] >= 0.82
    assert mock_ka_controller.execute_typed.call_count == 12

@pytest.mark.asyncio
async def test_refinement_orchestrator_recovery(orchestrator, mock_ka_controller):
    """Verify that orchestrator reverts on a drastic confidence drop."""
    initial_response = {"content": "Good answer", "confidence": 0.9}
    context = {"query": "Recovery test"}
    
    # Step 1: Small improvement
    # Step 2: Drastic drop
    # Others: Normal
    
    call_count = 0
    def mock_execute(ka_id, ka_input):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            return _typed_result(
                ka_id,
                {"confidence": 0.5, "refined_content": "Garbage"},
            )
        return _typed_result(
            ka_id,
            {"confidence": 0.91, "refined_content": "Better"},
        )

    mock_ka_controller.execute_typed.side_effect = mock_execute
    
    result = await orchestrator.refine(initial_response, context)
    
    # Step 2 should have been rejected (confidence < 0.9 - 0.15 = 0.75)
    # The history should show the anomaly warning if we could capture logs, 
    # but we can check that Step 2's content wasn't committed to the final result.
    assert result["content"] != "Garbage"
    # Even if step 2 failed, we still have 12 entries in history (it continues to next step)
    assert len(result["refinement_history"]) == 11 # Wait, _execute_step is called, then state update is skipped.
    # Actually looking at the code:
    # if new_confidence < prev_confidence - 0.15:
    #     current_response = last_good_state.copy()
    #     continue
    # history.append(...) is AFTER the continue.
    # So history will have 11 items.
    assert len(result["refinement_history"]) == 11

def test_ka_016_regulatory_mapping():
    """Verify KA-016 maps only an explicitly requested governed framework."""
    context = {"tenant_id": "test"}
    ka = KA016RegulatoryMapping(context)
    
    ka.catalog = {
        "GDPR": {"obligations": ["PII Protection"], "risk_score": 0.8},
        "HIPAA": {"obligations": ["Health Data Privacy"], "risk_score": 0.9},
    }

    input_data = KA016Input(
        query="Tell me about requirements",
        frameworks=["GDPR"],
    )
    result = ka._run_logic(input_data)

    assert result["success"] is True
    assert any(m["framework"] == "GDPR" for m in result["mappings"])
    assert result["highest_risk"] == 0.8
    assert result["query_content_inspected"] is False

def test_ka_075_schema_mapping():
    """Verify KA-075 aligns source data to canonical schema."""
    context = {"tenant_id": "test"}
    ka = KA075SchemaMapping(context)
    
    ka.config = {
        "canonical_schemas": {
            "user_profile": ["full_name", "email", "job_title"]
        }
    }
    
    records = [
        {"src_full_name": "John Doe", "email": "john@example.com", "extra": "trash"},
        {"full_name": "Jane Smith", "job_title": "Engineer"}
    ]
    
    input_data = KA075MappingInput(records=records, target_schema="user_profile")
    result = ka._run_logic(input_data)
    
    assert result["success"] is True
    assert result["records_mapped"] == 2
    assert result["fields_aligned"] == ["full_name", "email", "job_title"]
    assert result["records_mapped"] == 2
    assert "email" in result["fields_aligned"]

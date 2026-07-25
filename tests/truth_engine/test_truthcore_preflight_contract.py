import pytest

from backend.knowledge_algorithms.contracts import (
    KAExecutionResult,
    KAExecutionState,
    KAOutcomeType,
)
from backend.truth_engine.truth_core.engine import TruthCoreEngine


class _Controller:
    def execute_typed(
        self,
        ka_id,
        input_data,
        *,
        production_workflow=False,
    ):
        assert input_data["_production_workflow"] is True
        assert production_workflow is True
        return KAExecutionResult(
            canonical_id=ka_id,
            ka_version="1.0.0",
            manifest_version="test",
            state=KAExecutionState.SUCCEEDED,
            outcome_type=KAOutcomeType.VALUE,
            success=True,
            output={"ka_id": ka_id},
            request_id="request-test",
            run_id="run-test",
            trace_id=f"trace-{ka_id}",
        )


@pytest.mark.asyncio
async def test_governed_preflight_has_exact_state_and_failure_contract():
    engine = object.__new__(TruthCoreEngine)
    engine.ka_controller = _Controller()

    result = await engine.execute_governed_preflight(
        "Assess the evidence",
        {"evidence": []},
        mode="enhanced",
    )

    assert result["contract_version"] == "truthcore-preflight.v1"
    assert result["ok"] is True
    assert result["state"] == "completed"
    assert result["failure"] is None
    assert [item["ka_id"] for item in result["steps_executed"]] == ["KA-113", "KA-001"]
    assert result["state_transitions"][-1]["to"] == "completed"


def test_truthcore_has_no_product_specific_model_routing_constants():
    assert not hasattr(TruthCoreEngine, "ROUTING_PROFILES")

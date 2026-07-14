import pytest

from backend.truth_engine.truth_core.engine import TruthCoreEngine


class _Controller:
    def execute_algorithm(self, ka_id, input_data):
        assert input_data["_production_workflow"] is True
        return {"success": True, "output": {"ka_id": ka_id}}


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

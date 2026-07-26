import pytest

from backend.dmrf.truth_integration.core_adapter import TruthCoreDMRFAdapter
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


@pytest.mark.asyncio
async def test_governed_layer_plan_uses_manifest_selector_and_typed_results():
    result = await TruthCoreDMRFAdapter().execute(
        "Assess the evidence",
        tier="moderate",
        axis17_context={"value": "default"},
        context={
            "request_id": "request-cp19d",
            "trace_id": "trace-cp19d",
            "ka_deadline_ms": 10_000,
        },
        mode="enhanced",
    )

    assert result["contract_version"] == "truthcore-layer-plan.v1"
    assert result["ok"] is True
    assert result["selection_plan"]["valid"] is True
    assert result["selection_plan"]["selected_ids"] == [
        "KA-001",
        "KA-004",
        "KA-061",
    ]
    assert result["selection_plan"]["execution_order"] == [
        ["KA-004"],
        ["KA-001", "KA-061"],
    ]
    assert all(
        item["status"] == "completed"
        for item in result["steps_executed"]
    )


@pytest.mark.asyncio
async def test_governed_layer_plan_expands_for_high_risk_standard_request():
    result = await TruthCoreDMRFAdapter().execute(
        "Assess the control boundary",
        tier="moderate",
        axis17_context={"value": "default"},
        context={
            "request_id": "request-cp19d-risk",
            "trace_id": "trace-cp19d-risk",
            "risk_domain": "high_stakes",
            "ka_deadline_ms": 10_000,
        },
        mode="standard",
    )

    assert result["ok"] is True
    assert result["selection_plan"]["requested_ids"] == [
        "KA-004",
        "KA-061",
        "KA-001",
    ]


@pytest.mark.asyncio
async def test_regulatory_axis_context_does_not_select_unqualified_kas():
    result = await TruthCoreDMRFAdapter().execute(
        "What are HIPAA requirements for cloud PHI?",
        tier="high_stakes",
        axis17_context={
            "truth_engine_mode": "regulatory_strict",
            "tier": "high_stakes",
        },
        context={
            "request_id": "request-cp19d-regulatory",
            "trace_id": "trace-cp19d-regulatory",
            "risk_domain": "standard",
            "ka_deadline_ms": 10_000,
        },
        mode="local_review",
    )

    assert result["ok"] is True
    assert result["selection_plan"]["selected_ids"] == [
        "KA-001",
        "KA-004",
        "KA-061",
    ]
    assert result["selection_plan"]["validation_errors"] == []

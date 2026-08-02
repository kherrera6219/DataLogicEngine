"""CP19-K owning-path proof for governed request and DMRF algorithms."""

from __future__ import annotations

import pytest

from backend.dmrf.truth_integration.core_adapter import TruthCoreDMRFAdapter
from backend.dmrf.orchestrator import DMRFOrchestrator
from backend.dmrf.tier_classifier import DMRFTierClassifier
from backend.governed_execution.contracts import GovernedContext, GovernedRequest
from backend.governed_execution.ten_layers import GovernedTenLayerStages
from backend.knowledge_algorithms.ka_master_controller import KAMasterController


def _context(query: str) -> GovernedContext:
    request = GovernedRequest(
        messages=[{"role": "user", "content": query}],
        source="cp19_k_qualification",
        principal_kind="desktop",
        principal_id="cp19-k-reviewer",
    )
    context = GovernedContext(request=request, query=query)
    context.routing = {
        "axis_vector": {"axes": {"15": {"value": "standard"}}}
    }
    return context


def _trace_states(context: GovernedContext, canonical_id: str) -> list[str]:
    traces = context.truthcore["execution_report"]["traces"]
    return [event["state"] for event in traces[canonical_id]["events"]]


def _assert_complete_trace(context: GovernedContext, canonical_id: str) -> None:
    assert _trace_states(context, canonical_id) == [
        "planned",
        "candidate",
        "selected",
        "admitted",
        "executing",
        "executed",
    ]
    traces = context.truthcore["execution_report"]["traces"]
    assert traces[canonical_id]["events"][-1]["result_trace_id"]


async def _canonical_dmrf_result():
    query = (
        "Compare maybe whether an SQL API encryption architecture might be "
        "preferable versus another design, but explain the ambiguous trade-off "
        "and possibly evaluate how the algorithm depends on Kubernetes under "
        "uncertain constraints."
    )
    assert DMRFTierClassifier().classify(query).tier == "moderate"
    result = await DMRFOrchestrator(
        desktop_mode=True,
        ka_controller=KAMasterController({"llm_gateway": None}),
    ).process(
        query,
        context={
            "_canonical_defer_dsqp": True,
            "request_id": "cp19-k-dmrf-routing",
            "principal_id": "cp19-k-reviewer",
        },
    )
    step = next(
        item for item in result.steps if item.name == "ka_complexity_router"
    )
    return result, step.outputs


def _assert_dmrf_complete_trace(outputs: dict, canonical_id: str) -> None:
    events = outputs["traces"][canonical_id]["events"]
    assert [event["state"] for event in events] == [
        "planned",
        "candidate",
        "selected",
        "admitted",
        "executing",
        "executed",
    ]
    assert events[-1]["result_trace_id"]


class _InvalidDMRFPlan:
    valid = False
    selected_ids: list[str] = []
    validation_errors = ["required_routing_plan_rejected"]


class _InvalidDMRFController:
    @staticmethod
    def plan_algorithms(_request):
        return _InvalidDMRFPlan()


@pytest.mark.asyncio
async def test_ka_004_owning_path():
    context = _context("  <b>Assess the control boundary</b>  ")
    stages = GovernedTenLayerStages(TruthCoreDMRFAdapter())

    layer = await stages.l1(
        context,
        tier="moderate",
        axis17_context={"value": "default"},
    )

    assert layer.ok
    assert layer.outputs["query"] == "Assess the control boundary"
    assert context.query == "Assess the control boundary"
    assert layer.ka_results["KA-004"]["output"]["is_valid"] is True
    assert layer.decisions == [
        {"decision": "allow", "reason": "normalized_and_routed"}
    ]
    _assert_complete_trace(context, "KA-004")


@pytest.mark.asyncio
async def test_ka_005_owning_path():
    result, outputs = await _canonical_dmrf_result()

    assert result.ok is True
    assert outputs["status"] == "succeeded"
    assert outputs["outputs"]["KA-005"]["category"] == "TECHNICAL"
    assert outputs["outputs"]["KA-005"]["suggested_tier"] == "moderate"
    _assert_dmrf_complete_trace(outputs, "KA-005")


@pytest.mark.asyncio
async def test_ka_061_owning_path():
    context = _context("DROP DATABASE production")
    stages = GovernedTenLayerStages(TruthCoreDMRFAdapter())

    layer = await stages.l1(
        context,
        tier="moderate",
        axis17_context={"value": "default"},
    )

    assert layer.ka_results["KA-004"]["output"]["is_valid"] is True
    assert layer.ka_results["KA-061"]["output"]["blocked"] is True
    assert layer.ka_results["KA-061"]["output"]["veto"] is True
    assert layer.ok is False
    assert layer.error_code == "L1_INPUT_BLOCKED"
    assert layer.outputs["query"] == "[FILTERED]"
    assert layer.decisions[0]["decision"] == "block"
    _assert_complete_trace(context, "KA-061")


@pytest.mark.asyncio
async def test_ka_113_owning_path():
    result, outputs = await _canonical_dmrf_result()

    assert result.ok is True
    assert result.tier == "high_stakes"
    assert outputs["outputs"]["KA-113"]["complexity_tier"] == "high"
    assert outputs["outputs"]["KA-113"]["dependency_routing"] == {
        "normalized_query_consumed": True,
        "classification_tier": "moderate",
    }
    assert "ka_113_may_raise_but_never_lower_tier" in next(
        item.outputs["classification"]["rationale"]
        for item in result.steps
        if item.name == "tier_classifier"
    )
    _assert_dmrf_complete_trace(outputs, "KA-113")


@pytest.mark.asyncio
async def test_ka_113_required_plan_failure_blocks_dmrf():
    result = await DMRFOrchestrator(
        desktop_mode=True,
        ka_controller=_InvalidDMRFController(),
    ).process(
        "Explain a routine local control",
        context={"_canonical_defer_dsqp": True},
    )

    assert result.ok is False
    assert result.axis_vector is None
    assert result.warnings == ["ka_complexity_routing_failed"]
    routing_step = next(
        item for item in result.steps if item.name == "ka_complexity_router"
    )
    assert routing_step.outputs == {
        "status": "failed",
        "selected_ids": [],
        "validation_errors": ["required_routing_plan_rejected"],
    }


@pytest.mark.asyncio
async def test_ka_113_cannot_bypass_desktop_offline_tier_cap():
    query = (
        "Compare maybe whether an SQL API encryption architecture might be "
        "preferable versus another design, but explain the ambiguous trade-off "
        "and possibly evaluate how the algorithm depends on Kubernetes under "
        "uncertain constraints."
    )
    result = await DMRFOrchestrator(
        desktop_mode=True,
        config={
            "offline_tier_cap": "moderate",
            "max_refinement_iterations": 3,
        },
        ka_controller=KAMasterController({"llm_gateway": None}),
    ).process(
        query,
        context={"_canonical_defer_dsqp": True},
        offline=True,
    )

    assert result.ok is True
    assert result.tier == "moderate"
    classification = next(
        item.outputs["classification"]
        for item in result.steps
        if item.name == "tier_classifier"
    )
    assert classification["capped_from"] == "high_stakes"
    assert classification["raw"]["ka_113"]["complexity_tier"] == "high"

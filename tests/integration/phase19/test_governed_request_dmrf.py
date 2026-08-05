"""CP19-K owning-path proof for governed request and DMRF algorithms."""

from __future__ import annotations

from typing import ClassVar

import pytest

from backend.dmrf.orchestrator import DMRFOrchestrator
from backend.dmrf.tier_classifier import DMRFTierClassifier
from backend.dmrf.truth_integration.core_adapter import TruthCoreDMRFAdapter
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
    context.routing = {"axis_vector": {"axes": {"15": {"value": "standard"}}}}
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
    step = next(item for item in result.steps if item.name == "ka_complexity_router")
    return result, step.outputs


def _assert_dmrf_complete_trace(outputs: dict, canonical_id: str) -> None:
    events = outputs["traces"][canonical_id]["events"]
    states = [event["state"] for event in events]
    assert [state for state in states if state != "dependency"] == [
        "planned",
        "candidate",
        "selected",
        "admitted",
        "executing",
        "executed",
    ]
    if canonical_id in {"KA-005", "KA-113"}:
        assert "dependency" in states
    assert events[-1]["result_trace_id"]


class _InvalidDMRFPlan:
    valid = False
    selected_ids: ClassVar[list[str]] = []
    validation_errors: ClassVar[list[str]] = ["required_routing_plan_rejected"]


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
    assert layer.decisions == [{"decision": "allow", "reason": "normalized_and_routed"}]
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
async def test_ka_036_owning_path():
    result, outputs = await _canonical_dmrf_result()

    assert result.ok is True
    complexity = outputs["outputs"]["KA-036"]
    assert complexity["status"] == "complexity_estimated"
    assert complexity["database_read_performed"] is False
    _assert_dmrf_complete_trace(outputs, "KA-036")


@pytest.mark.asyncio
async def test_ka_1073_owning_path():
    result, outputs = await _canonical_dmrf_result()

    assert result.ok is True
    intent = outputs["outputs"]["KA-1073"]
    assert intent["status"] in {"intent_resolved", "clarification_required"}
    assert intent["deterministic"] is True
    _assert_dmrf_complete_trace(outputs, "KA-1073")


@pytest.mark.asyncio
async def test_ka_031_owning_path():
    result, outputs = await _canonical_dmrf_result()

    assert result.ok is True
    selection = outputs["outputs"]["KA-031"]
    assert selection["status"] == "algorithm_selection_proposed"
    assert selection["dependencies_consumed"] == [
        "KA-005",
        "KA-036",
        "KA-1073",
        "KA-113",
    ]
    assert selection["execution_started"] is False
    _assert_dmrf_complete_trace(outputs, "KA-031")


@pytest.mark.asyncio
async def test_ka_1107_owning_path():
    result, outputs = await _canonical_dmrf_result()

    assert result.ok is True
    boundary = outputs["outputs"]["KA-1107"]
    assert boundary["plan_allowed"] is True
    assert boundary["execution_started"] is False
    _assert_dmrf_complete_trace(outputs, "KA-1107")


def test_ka_033_owning_path():
    from backend.knowledge_algorithms.controller import get_ka_controller
    from backend.knowledge_algorithms.ka_33_reserved_expansion_slot import run
    from backend.knowledge_algorithms.selection import (
        KASelectionRequest,
        ManifestKASelector,
    )

    descriptor = run({"payload": {"secret": "must-not-return"}})
    assert descriptor["ka_id"] == "KA-033"
    assert descriptor["output"]["status"] == "reserved_disabled"
    assert descriptor["output"]["payload_returned"] is False
    plan = ManifestKASelector(get_ka_controller().manifest).plan(
        KASelectionRequest(requested_ids=["KA-033"], ka_inputs={"KA-033": {}})
    )
    assert plan.valid is False
    assert any(
        "required algorithms not admitted: KA-033" in error
        for error in plan.validation_errors
    )


@pytest.mark.asyncio
async def test_ka_058_owning_path():
    result, outputs = await _canonical_dmrf_result()

    assert result.ok is True
    clarification = outputs["outputs"]["KA-058"]
    assert clarification["dependencies_consumed"] == ["KA-1073", "KA-1102"]
    assert clarification["clarification_dispatched"] is False
    assert clarification["learning_applied"] is False
    _assert_dmrf_complete_trace(outputs, "KA-058")


@pytest.mark.asyncio
async def test_ka_059_owning_path():
    result, outputs = await _canonical_dmrf_result()

    assert result.ok is True
    preemption = outputs["outputs"]["KA-059"]
    assert preemption["dependencies_consumed"] == ["KA-031", "KA-113"]
    assert preemption["preemption_applied"] is False
    assert preemption["skipped_layers"] == []
    assert not set(preemption["blocked_safety_layers"]) - {
        "L6",
        "L7",
        "L8",
        "L9",
        "L10",
    }
    _assert_dmrf_complete_trace(outputs, "KA-059")


@pytest.mark.asyncio
async def test_ka_master_owning_path():
    controller = KAMasterController({"llm_gateway": None})
    descriptor = controller.authority_descriptor()
    result, outputs = await _canonical_dmrf_result()

    assert result.ok is True
    assert descriptor["capability_count"] == 213
    assert descriptor["self_selection_enabled"] is False
    assert descriptor["planning_authority"] == "ManifestKASelector"
    assert descriptor["execution_authority"] == "CanonicalKAController"
    assert "KA-Master" not in outputs["selected_ids"]
    assert "KA-Master" not in outputs["traces"]


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

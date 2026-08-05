"""CP19-K Batch 19 owning-path proof for the five-node DSQP foundation."""

from __future__ import annotations

import pytest

from backend.governed_execution.contracts import GovernedContext, GovernedRequest
from backend.governed_execution.ten_layers import GovernedTenLayerStages
from backend.knowledge_algorithms.contracts import KABudget, KAExecutionContext
from backend.knowledge_algorithms.controller import get_ka_controller
from backend.knowledge_algorithms.selection import (
    KAPlanExecutionStatus,
    KAPlanExecutor,
    KASelectionRequest,
    KATraceState,
    ManifestKASelector,
)

PERSONAS = ("knowledge", "sector", "regulatory", "compliance")


def _profiles() -> dict[str, dict]:
    return {
        persona: {
            "persona_id": f"dsqp-{axis}",
            "axis_number": axis,
            "persona_type": persona,
            "name": f"{persona.title()} Expert",
            "components": {"job_role": {"focus_area": f"{persona} review"}},
            "validation": {"valid": True, "coverage_score": 1.0},
        }
        for axis, persona in zip((8, 9, 10, 11), PERSONAS, strict=True)
    }


async def _run_owner_dag():
    controller = get_ka_controller()
    request = KASelectionRequest(
        requested_ids=["KA-012", "KA-013", "KA-028", "KA-030", "KA-038"],
        service_capabilities={"persona_context_service"},
        ka_inputs={
            "KA-012": {
                "query": "Assess a regulated encryption deployment",
                "active_personas": list(PERSONAS),
                "dsqp_profiles": _profiles(),
            },
            "KA-013": {
                "domain": "REGULATORY",
                "required_personas": list(PERSONAS),
            },
            "KA-028": {
                "query": "Assess a regulated encryption deployment",
                "existing_personas": list(PERSONAS),
            },
            "KA-030": {"query": "Assess a regulated encryption deployment"},
            "KA-038": {"claims": []},
        },
        context=KAExecutionContext(
            request_id="batch-19-persona-foundation",
            run_id="batch-19-persona-run",
            principal_id="owner-1",
            workflow="governed.dsqp_quad_persona.foundation",
            layer="L4-L5",
            budget=KABudget(
                deadline_ms=5_000,
                max_dependency_executions=8,
                max_recursion_depth=5,
                max_selected_algorithms=8,
                max_fan_out=4,
                max_parallelism=2,
                max_effects=4,
            ),
        ),
    )
    plan = ManifestKASelector(controller.manifest).plan(request)
    assert plan.valid
    assert plan.execution_order == [
        ["KA-012", "KA-028"],
        ["KA-013"],
        ["KA-030"],
        ["KA-038"],
    ]
    report = await KAPlanExecutor(controller).execute(plan, request)
    assert report.status is KAPlanExecutionStatus.SUCCEEDED
    return report


def _assert_trace(report, canonical_id: str) -> None:
    states = [event.state for event in report.traces[canonical_id].events]
    assert [
        state
        for state in states
        if state not in {KATraceState.DEPENDENCY, KATraceState.EFFECT_PROPOSED}
    ] == [
        KATraceState.PLANNED,
        KATraceState.CANDIDATE,
        KATraceState.SELECTED,
        KATraceState.ADMITTED,
        KATraceState.EXECUTING,
        KATraceState.EXECUTED,
    ]


@pytest.mark.asyncio
async def test_ka_012_owning_path():
    report = await _run_owner_dag()
    assert len(report.results["KA-012"].output["persona_findings"]) == 4
    assert report.results["KA-012"].output["provider_subcalls_used"] == 0
    _assert_trace(report, "KA-012")


@pytest.mark.asyncio
async def test_ka_013_owning_path():
    report = await _run_owner_dag()
    output = report.results["KA-013"].output
    assert output["sufficiency"]["sufficient"] is True
    assert output["final_consensus_confidence"] is None
    _assert_trace(report, "KA-013")


@pytest.mark.asyncio
async def test_ka_028_owning_path():
    report = await _run_owner_dag()
    output = report.results["KA-028"].output
    assert output["count"] <= 2
    assert output["context_applied"] is False
    _assert_trace(report, "KA-028")


@pytest.mark.asyncio
async def test_ka_030_owning_path():
    report = await _run_owner_dag()
    output = report.results["KA-030"].output
    assert output["all_dissent_preserved"] is True
    assert output["substantive_resolution_claimed"] is False
    _assert_trace(report, "KA-030")


@pytest.mark.asyncio
async def test_ka_038_owning_path():
    report = await _run_owner_dag()
    output = report.results["KA-038"].output
    assert output["dependencies_consumed"] == ["KA-013", "KA-030"]
    assert output["substantive_consensus_claimed"] is False
    assert output["calibrated_confidence"] is None
    _assert_trace(report, "KA-038")


@pytest.mark.asyncio
async def test_persona_context_service_applies_one_bounded_receipt():
    request = GovernedRequest(
        messages=[{"role": "user", "content": "Assess regulated encryption"}],
        source="cp19_k_qualification",
        principal_kind="desktop",
        principal_id="owner-1",
    )
    context = GovernedContext(request=request, query=request.query_text())
    context.reasoning.tier = "moderate"
    context.dsqp["profiles"] = {
        str(profile["axis_number"]): profile for profile in _profiles().values()
    }
    stages = GovernedTenLayerStages(object())
    l4 = await stages.l4(context)
    l5 = await stages.l5(context)

    assert l4.ok and l5.ok
    assert l4.selected_ka_ids == ["KA-012", "KA-028"]
    assert l5.selected_ka_ids == ["KA-013", "KA-030", "KA-038"]
    receipt = context.dsqp["persona_context_receipt"]
    assert receipt["service"] == "PersonaContextService"
    assert receipt["status"] == "applied"
    assert receipt["provider_subcalls_used"] == 0
    assert {id(item["receipt"]) for item in l5.effects} == {id(receipt)}

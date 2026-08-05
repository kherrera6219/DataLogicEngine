"""CP19-K Batch 19 owning-path proof for the five-node DSQP foundation."""

from __future__ import annotations

import pytest

from backend.governed_execution.contracts import GovernedContext, GovernedRequest
from backend.governed_execution.knowledge_lifecycle import KnowledgeLifecycleCoordinator
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


def _batch_29_inputs() -> dict[str, dict]:
    persona_outputs = [
        {
            "persona_id": persona,
            "content": "Retain the governed evidence and recorded dissent.",
            "position": "review",
        }
        for persona in PERSONAS
    ]
    return {
        "KA-012": {
            "query": "Assess a regulated encryption deployment",
            "active_personas": list(PERSONAS),
            "dsqp_profiles": _profiles(),
        },
        "KA-013": {
            "domain": "REGULATORY",
            "required_personas": list(PERSONAS),
        },
        "KA-030": {"query": "Assess a regulated encryption deployment"},
        "KA-010": {"content": "Use balanced and evidence-based language."},
        "KA-1045": {
            "outputs_corpus": [
                {"record_id": "a-1", "group": "a", "outcome": 0.8},
                {"record_id": "a-2", "group": "a", "outcome": 0.7},
                {"record_id": "b-1", "group": "b", "outcome": 0.5},
                {"record_id": "b-2", "group": "b", "outcome": 0.4},
            ]
        },
        "KA-057": {
            "output_object": {"id": "candidate-1", "content": "not inspected"},
            "persona": "end_user",
            "emotional_context": "uncertain",
        },
        "KA-068": {"domain": "legal", "risk_class": "high"},
        "KA-069": {
            "culture": "regional_eu",
            "text": "private source content",
            "numeric_values": {"confidence_index": 0.75},
        },
        "KA-1037": {"persona_outputs": persona_outputs},
        "KA-1075": {
            "records": [
                {"record_id": "a1", "group": "a", "observed_label": "yes"},
                {"record_id": "a2", "group": "a", "observed_label": "no"},
                {"record_id": "b1", "group": "b", "observed_label": "yes"},
            ]
        },
        "KA-1084": {
            "instance_answers": [
                {"instance_id": "a", "answer": "Approved"},
                {"instance_id": "b", "answer": " approved "},
                {"instance_id": "c", "answer": "Rejected"},
            ],
            "consensus_threshold": 0.66,
        },
    }


def _run_batch_29_owner(canonical_id: str) -> dict:
    execution = KnowledgeLifecycleCoordinator(workflow_phase="cp19k").execute_operation_sync(
        owner="dsqp_quad_persona",
        operation="adaptation",
        requested_ids=[canonical_id],
        ka_inputs=_batch_29_inputs(),
        request_id=f"batch-29-{canonical_id}",
        run_id=f"batch-29-run-{canonical_id}",
        max_effects=4,
        principal_id="persona-context-owner",
        layer="L4-L10",
        service_capabilities={"persona_context_service"},
    )
    _assert_trace(execution.report, canonical_id)
    return execution.results[canonical_id]["output"]


def test_ka_057_owning_path():
    output = _run_batch_29_owner("KA-057")
    assert output["adapted_style_plan"]["persona"] == "end_user"
    assert output["content_rewritten"] is False
    assert output["profile_updated"] is False


def test_ka_068_owning_path():
    output = _run_batch_29_owner("KA-068")
    assert output["tuning_proposal"]["validation_strictness"] == "strict"
    assert output["pipeline_weights_changed"] is False
    assert output["search_started"] is False


def test_ka_069_owning_path():
    output = _run_batch_29_owner("KA-069")
    assert output["culture_applied"] == "regional_eu"
    assert output["locale_detected"] is False
    assert output["text_content_returned"] is False


def test_ka_1037_owning_path():
    output = _run_batch_29_owner("KA-1037")
    assert output["owner_context_ready"] is True
    assert output["dependencies_consumed"] == ["KA-012", "KA-030"]
    assert output["causal_norm_emergence_established"] is False


def test_ka_1075_owning_path():
    output = _run_batch_29_owner("KA-1075")
    assert output["proposal_ready"] is True
    assert output["dependencies_consumed"] == ["KA-010", "KA-1045"]
    assert output["mutation_applied"] is False


def test_ka_1084_owning_path():
    output = _run_batch_29_owner("KA-1084")
    assert output["consensus_reached"] is True
    assert output["truth_established"] is False
    assert output["consensus_applied"] is False

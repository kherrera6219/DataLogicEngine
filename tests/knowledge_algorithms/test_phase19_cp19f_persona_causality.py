"""CP19-F causal Quad Persona/DSQP production integration proof."""

from __future__ import annotations

from typing import Any

import pytest

from backend.governed_execution.contracts import EvidenceRecord
from backend.governed_execution.orchestrator import (
    GovernedExecutionOrchestrator,
)
from backend.knowledge_algorithms.controller import get_ka_controller
from backend.knowledge_algorithms.selection import (
    KAPlanExecutionStatus,
    KAPlanExecutor,
    KASelectionRequest,
    KATraceState,
    ManifestKASelector,
)
from tests.governed_execution.test_orchestrator import (
    _DMRF,
    _DSQP,
    _Gateway,
    _request,
    _TruthCore,
)

PERSONAS = ("knowledge", "sector", "regulatory", "compliance")


def _profile(persona: str, axis: int) -> dict[str, Any]:
    return {
        "persona_id": f"dsqp-{axis}",
        "axis_number": axis,
        "persona_type": persona,
        "name": f"{persona.title()} Expert",
        "components": {
            "job_role": {"focus_area": f"{persona} review"},
            "education": {"focus": persona},
            "certifications": {"list": [f"{persona}-cert"]},
            "skills": {"items": [persona]},
            "training": {"modules": [persona]},
            "career_path": {"stages": [persona]},
            "related_jobs": {"overlapping_roles": [persona]},
        },
        "validation": {
            "valid": True,
            "coverage_score": 1.0,
            "process_valid": True,
        },
    }


def _selection_request() -> KASelectionRequest:
    profiles = {
        persona: _profile(persona, axis)
        for axis, persona in zip((8, 9, 10, 11), PERSONAS, strict=True)
    }
    return KASelectionRequest.model_validate(
        {
            "mode": "production",
            "requested_ids": ["KA-012", "KA-013", "KA-030"],
            "service_capabilities": ["persona_context_service"],
            "ka_inputs": {
                "KA-012": {
                    "query": "Assess a regulated encryption deployment",
                    "active_personas": list(PERSONAS),
                    "dsqp_profiles": profiles,
                },
                "KA-013": {
                    "domain": "REGULATORY",
                    "required_personas": list(PERSONAS),
                },
                "KA-030": {
                    "query": "Assess a regulated encryption deployment",
                },
            },
            "context": {
                "request_id": "cp19f-persona-chain",
                "run_id": "cp19f-persona-run",
                "workflow": "governed.v1",
                "layer": "L4-L5",
                "budget": {
                    "deadline_ms": 5_000,
                    "max_dependency_executions": 8,
                    "max_recursion_depth": 4,
                    "max_selected_algorithms": 8,
                    "max_fan_out": 4,
                    "max_parallelism": 2,
                    "max_input_bytes": 1_000_000,
                    "max_output_bytes": 5_000_000,
                    "max_provider_calls": 0,
                    "max_effects": 1,
                },
            },
        }
    )


@pytest.mark.asyncio
async def test_cp19f_persona_dag_executes_once_without_fake_confidence():
    controller = get_ka_controller()
    selector = ManifestKASelector(controller.manifest)
    request = _selection_request()
    plan = selector.plan(request)

    assert plan.valid is True
    assert controller.manifest.status == "cp19_g_refinement_authority"
    assert controller.manifest.entries["KA-012"].contract.dependencies == []
    assert controller.manifest.entries["KA-013"].contract.dependencies == ["KA-012"]
    assert controller.manifest.entries["KA-030"].contract.dependencies == ["KA-013"]
    assert plan.execution_order == [["KA-012"], ["KA-013"], ["KA-030"]]

    report = await KAPlanExecutor(controller).execute(plan, request)

    assert report.status is KAPlanExecutionStatus.SUCCEEDED
    assert set(report.results) == {"KA-012", "KA-013", "KA-030"}
    assert all(
        sum(event.state is KATraceState.EXECUTED for event in trace.events) == 1
        for trace in report.traces.values()
        if trace.canonical_id in report.results
    )
    analysis = report.results["KA-012"].output
    weighting = report.results["KA-013"].output
    disposition = report.results["KA-030"].output
    assert analysis["provider_subcalls_used"] == 0
    assert weighting["sufficiency"]["sufficient"] is True
    assert weighting["final_consensus_confidence"] is None
    assert weighting["silent_dissent_count"] == 0
    assert disposition["all_dissent_preserved"] is True
    assert disposition["confidence_adjustment"] is None
    assert len(disposition["prompt_constraints"]) == len(weighting["dissent"])


class _MarkedDSQP(_DSQP):
    def __init__(self, marker: str):
        self.marker = marker

    async def construct_all(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        payload = await super().construct_all(*args, **kwargs)
        payload["profiles"]["10"]["components"]["job_role"] = {
            "focus_area": self.marker
        }
        payload["profiles"]["10"]["validation"]["coverage_score"] = 1.0
        for profile in payload["profiles"].values():
            profile["validation"].setdefault("coverage_score", 1.0)
        return payload


class _PersonaCausalGateway(_Gateway):
    async def _direct_llm_call(
        self,
        provider: Any,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        self.provider_calls += 1
        self.provider_messages.append(messages)
        system = str(messages[0]["content"])
        marker = (
            "strict-regulatory"
            if "strict-regulatory" in system
            else "balanced-regulatory"
        )
        return {
            "ok": True,
            "answer": f"{marker} alpha evidence [S1]",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }


def _marked_orchestrator(
    gateway: _Gateway,
    marker: str,
) -> GovernedExecutionOrchestrator:
    return GovernedExecutionOrchestrator(
        gateway,
        dmrf_factory=lambda **kwargs: _DMRF(),
        dsqp_factory=lambda **kwargs: _MarkedDSQP(marker),
        truthcore=_TruthCore(),
    )


@pytest.mark.asyncio
async def test_cp19f_persona_output_changes_prompt_and_single_candidate(
    monkeypatch: pytest.MonkeyPatch,
):
    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(
        module,
        "retrieve_evidence",
        lambda *args, **kwargs: (
            [
                EvidenceRecord(
                    source_id="source-alpha",
                    citation_label="S1",
                    text="alpha evidence",
                )
            ],
            [],
        ),
    )
    first_gateway = _PersonaCausalGateway()
    second_gateway = _PersonaCausalGateway()
    first = await _marked_orchestrator(
        first_gateway,
        "strict-regulatory",
    ).execute(_request())
    second = await _marked_orchestrator(
        second_gateway,
        "balanced-regulatory",
    ).execute(_request())

    assert first.ok is True
    assert second.ok is True
    assert first.answer != second.answer
    assert first_gateway.provider_calls == 1
    assert second_gateway.provider_calls == 1
    assert "strict-regulatory" in first_gateway.provider_messages[0][0]["content"]
    assert "balanced-regulatory" in second_gateway.provider_messages[0][0]["content"]
    layers = {
        layer["layer_id"]: layer
        for layer in first.metadata["reasoning_state"]["layers"]
    }
    assert layers["L4"]["selected_ka_ids"] == ["KA-012"]
    assert set(layers["L5"]["selected_ka_ids"]) == {"KA-013", "KA-030"}
    selected = [
        canonical_id
        for layer in layers.values()
        for canonical_id in layer["selected_ka_ids"]
    ]
    assert selected.count("KA-012") == 1
    assert selected.count("KA-013") == 1
    assert selected.count("KA-030") == 1
    assert not set(selected) & {
        "KA-028",
        "KA-038",
        "KA-057",
        "KA-068",
        "KA-069",
        "KA-1037",
        "KA-1075",
        "KA-1084",
    }


@pytest.mark.asyncio
async def test_cp19f_required_weighting_failure_blocks_before_provider(
    monkeypatch: pytest.MonkeyPatch,
):
    import backend.governed_execution.orchestrator as governed_module

    monkeypatch.setattr(
        governed_module,
        "retrieve_evidence",
        lambda *args, **kwargs: (
            [
                EvidenceRecord(
                    source_id="source-alpha",
                    citation_label="S1",
                    text="alpha evidence",
                )
            ],
            [],
        ),
    )
    gateway = _Gateway()
    orchestrator = _marked_orchestrator(
        gateway,
        "strict-regulatory",
    )
    original_invoke = orchestrator.layer_stages.ka_controller._invoke

    def injected_failure(definition: Any, input_data: dict[str, Any]) -> Any:
        if definition.canonical_id == "KA-013":
            return {
                "success": False,
                "status": "injected_weighting_failure",
            }
        return original_invoke(definition, input_data)

    monkeypatch.setattr(
        orchestrator.layer_stages.ka_controller,
        "_invoke",
        injected_failure,
    )
    result = await orchestrator.execute(_request())

    assert result.ok is False
    assert result.failure is not None
    assert result.failure.code == "L5_CANDIDATE_PLAN_FAILURE"
    assert gateway.provider_calls == 0
    layer = result.metadata["reasoning_state"]["layers"][-1]
    assert layer["layer_id"] == "L5"
    assert layer["status"] == "failed"
    assert layer["ka_plan"]["required_failure"] == "KA-013"

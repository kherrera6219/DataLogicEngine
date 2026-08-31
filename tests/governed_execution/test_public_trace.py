from __future__ import annotations

from backend.governed_execution.contracts import (
    GovernedContext,
    GovernedRequest,
    GovernedStage,
    GovernedStageStatus,
)
from backend.governed_execution.public_trace import (
    MAX_PUBLIC_TRACE_NARRATIVE_CHARS,
    present_stage_event,
    trace_unavailable_payload,
)


def test_governed_context_uses_request_id_for_early_run_correlation():
    request = GovernedRequest(
        request_id="15e2f56a-6b7c-4f7b-8d7e-3f227a95ecde",
        messages=[{"role": "user", "content": "Explain the evidence."}],
    )

    context = GovernedContext(request=request)

    assert context.trace_id == "15e2f56a-6b7c-4f7b-8d7e-3f227a95ecde"


def test_public_stage_event_is_stable_ordered_bounded_and_redacted():
    canary = "TRACE-PRIVATE-CANARY-DO-NOT-EXPOSE"
    stage = GovernedStage(
        name="layer_2_retrieve_context",
        stage_type="reasoning_layer",
        inputs={"layer_id": "L2", "query": canary},
    )
    stage.finish(
        GovernedStageStatus.COMPLETED,
        outputs={
            "evidence_ids": ["ev-1", "ev-2"],
            "provider_text": canary,
            "selected_ka_ids": ["KA-018"],
        },
        metrics={"trace_sequence": 4, "tokens_in": 999},
    )

    event = present_stage_event("run-1", stage, sequence=4)
    repeated = present_stage_event("run-1", stage, sequence=4)

    assert event == repeated
    assert event["schema_version"] == "dle.public-trace-event.v1"
    assert event["event_id"] == repeated["event_id"]
    assert event["sequence"] == 4
    assert event["run_id"] == "run-1"
    assert event["stage_id"] == stage.stage_id
    assert event["name"] == "Retrieve context"
    assert event["layer_index"] == 2
    assert event["step_index"] is None
    assert event["status"] == "completed"
    assert "2 evidence records" in event["narrative"]
    assert len(event["narrative"]) <= MAX_PUBLIC_TRACE_NARRATIVE_CHARS
    assert canary not in str(event)
    assert "input" not in event
    assert "output" not in event
    assert "metrics" not in event


def test_public_stage_event_preserves_allowlisted_refinement_receipt_only():
    stage = GovernedStage(
        name="refinement_1",
        stage_type="refinement",
        inputs={"candidate": "private candidate"},
    )
    stage.finish(
        GovernedStageStatus.COMPLETED,
        outputs={
            "refinement": {
                "schema_version": "dle.canonical-refinement-result.v1",
                "registry_version": "2026.08.08-rw12.1",
                "status": "completed",
                "step_count": 12,
                "rewrite_authorized": True,
                "blocked_by_step": None,
                "steps": [
                    {
                        "step": 1,
                        "step_id": "claim_inventory",
                        "name": "Claim inventory",
                        "status": "executed",
                        "findings": [{"private": "do not publish"}],
                    }
                ],
            },
            "candidate": "private candidate",
        },
    )

    event = present_stage_event("run-2", stage, sequence=9)

    assert event["refinement"]["step_count"] == 12
    assert event["refinement"]["steps"] == [
        {
            "step": 1,
            "step_id": "claim_inventory",
            "name": "Claim inventory",
            "status": "executed",
            "reason": None,
        }
    ]
    assert "private" not in str(event)


def test_trace_unavailable_payload_is_typed_and_never_looks_empty_successful():
    payload = trace_unavailable_payload(
        "run-missing",
        code="TRACE_BUNDLE_NOT_FOUND",
        message="Trace bundle is not available yet.",
        retryable=True,
    )

    assert payload == {
        "schema_version": "dle.trace-unavailable.v1",
        "run_id": "run-missing",
        "status": "unavailable",
        "error": {
            "code": "TRACE_BUNDLE_NOT_FOUND",
            "message": "Trace bundle is not available yet.",
            "retryable": True,
        },
    }

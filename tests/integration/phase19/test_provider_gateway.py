"""CP19-K provider/gateway owning-path qualification."""

from __future__ import annotations

import pytest

from backend.governed_execution.extended_subsystems import (
    ExtendedSubsystemCoordinator,
)
from backend.governed_execution.knowledge_lifecycle import (
    KnowledgeLifecycleError,
)


def _assert_complete_trace(execution, canonical_id: str) -> None:
    events = execution.report.traces[canonical_id].events
    assert [event.state.value for event in events] == [
        "planned",
        "candidate",
        "selected",
        "admitted",
        "executing",
        "executed",
    ]
    executed = next(event for event in events if event.state.value == "executed")
    assert executed.result_trace_id


@pytest.mark.asyncio
async def test_ka_1072_owning_path():
    coordinator = ExtendedSubsystemCoordinator()
    execution = await coordinator.plan_provider_request(
        request_id="provider-ka-1072",
        trace_id="provider-trace-ka-1072",
        principal_id="owner-1",
        messages=[
            {"role": "system", "content": "Follow governed policy."},
            {"role": "user", "content": "Summarize the evidence."},
        ],
        token_budget=1_000,
    )
    output = coordinator.execution_outputs(execution)["KA-1072"]
    receipt = coordinator.bind_effect_receipt(
        service="ProviderGatewayService",
        operation="answer:provider_call",
        resource_id="provider-trace-ka-1072:1",
        request_payload={"message_sha256": "a" * 64},
        result_payload={"answer_sha256": "b" * 64},
        idempotency_key="provider-ka-1072:answer:1",
        ka_execution=execution,
    )

    assert output["status"] == "context_selected"
    assert output["selected_element_ids"] == ["message-0", "message-1"]
    assert receipt.ka_plan_id == execution.plan.plan_id
    assert receipt.ka_proposal_ids == []
    _assert_complete_trace(execution, "KA-1072")

    with pytest.raises(KnowledgeLifecycleError):
        await coordinator.plan_provider_request(
            request_id="provider-ka-1072-blocked",
            trace_id="provider-trace-ka-1072-blocked",
            principal_id="owner-1",
            messages=[
                {"role": "system", "content": "Required system policy."},
                {"role": "user", "content": "Required user request."},
            ],
            token_budget=1,
        )


@pytest.mark.asyncio
async def test_ka_084_owning_path():
    coordinator = ExtendedSubsystemCoordinator()
    execution = await coordinator.monitor_provider_result(
        request_id="provider-ka-084",
        trace_id="provider-trace-ka-084",
        principal_id="owner-1",
        duration_ms=350,
    )
    decision = coordinator.provider_monitoring_decision(execution)

    assert decision["status"] == "measured"
    assert decision["drift_detected"] is True
    assert decision["anomalies"] == ["LATENCY_SPIKE"]
    assert decision["alert_recommended"] is True
    assert decision["notification_applied"] is False
    _assert_complete_trace(execution, "KA-084")

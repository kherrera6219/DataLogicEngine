"""CP19-K owning-path proofs for MCP security and access decisions."""

from __future__ import annotations

import pytest

from backend.governed_execution.extended_subsystems import (
    ExtendedSubsystemCoordinator,
    ExtendedSubsystemError,
)


def _admit(*, execution_id: str, arguments: dict):
    return ExtendedSubsystemCoordinator().admit_mcp_tool(
        execution_id=execution_id,
        principal_id="owner-1",
        server_id="local-connector",
        tool_name="read_data",
        arguments=arguments,
        required_scopes={"mcp:execute", "connector:local-connector:read"},
        consent_approved=True,
    )


def _assert_complete_trace(execution, canonical_id: str) -> None:
    events = execution.report.traces[canonical_id].events
    required = [
        "planned",
        "candidate",
        "selected",
        "admitted",
        "executing",
        "executed",
    ]
    states = [event.state.value for event in events]
    assert [state for state in states if state in required] == required
    executed = next(event for event in events if event.state.value == "executed")
    assert executed.result_trace_id


def test_ka_137_owning_path():
    admitted = _admit(execution_id="mcp-ka-137-safe", arguments={"record": 1})
    output = admitted.results["KA-137"]["output"]

    assert output["findings"] == []
    assert output["matched_values_returned"] is False
    _assert_complete_trace(admitted, "KA-137")

    with pytest.raises(
        ExtendedSubsystemError,
        match="credential_in_tool_arguments",
    ):
        _admit(
            execution_id="mcp-ka-137-blocked",
            arguments={"api_key": "abcdefghijklmnop"},
        )


def test_ka_179_owning_path():
    coordinator = ExtendedSubsystemCoordinator()
    admitted = coordinator.admit_mcp_tool(
        execution_id="mcp-ka-179",
        principal_id="owner-1",
        server_id="local-connector",
        tool_name="read_data",
        arguments={"record": 1},
        required_scopes={"mcp:execute", "connector:local-connector:read"},
        consent_approved=True,
    )
    output = admitted.results["KA-179"]["output"]
    receipt = coordinator.bind_effect_receipt(
        service="MCPConnectorService",
        operation="tools/call:read_data",
        resource_id="mcp-ka-179",
        request_payload={"name": "read_data", "arguments": {"record": 1}},
        result_payload={"sha256": "a" * 64},
        idempotency_key="mcp-ka-179",
        ka_execution=admitted,
        proposal_ids=["KA-177", "KA-179"],
    )

    assert output["decision"] == "allow"
    assert output["access_applied"] is False
    assert receipt.ka_plan_id == admitted.plan.plan_id
    assert receipt.ka_proposal_ids == ["KA-177", "KA-179"]
    _assert_complete_trace(admitted, "KA-179")

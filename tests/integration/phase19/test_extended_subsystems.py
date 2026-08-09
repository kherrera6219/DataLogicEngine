"""CP19-I simulation, MCP, provider, operations, and effect-port proof."""

from __future__ import annotations

import pytest

from backend.governed_execution.extended_subsystems import (
    AuthoritativeEffectReceipt,
    ExtendedSubsystemCoordinator,
    ExtendedSubsystemError,
)
from backend.governed_execution.knowledge_lifecycle import KnowledgeLifecycleError
from backend.knowledge_algorithms.controller import get_ka_controller
from backend.simulation.contracts import SimulationDepth, SimulationScenario
from scripts.build_ka_runtime_manifest import (
    CP19_I_ADDITIONAL_ADMISSION_IDS,
    CP19_I_OWNER_IDS,
)


def test_cp19i_manifest_preserves_one_identity_and_admits_extended_owners():
    manifest = get_ka_controller().manifest

    assert manifest.status == "cp19_j_product_workflow_authority"
    assert manifest.manifest_version == "2026.08.08-cp19k.24"
    assert manifest.capability_count == 213
    assert len(manifest.entries) == len(set(manifest.entries)) == 213
    assert (
        sum(
            definition.admission.production_enabled
            for definition in manifest.entries.values()
        )
        == 211
    )
    assert CP19_I_OWNER_IDS | CP19_I_ADDITIONAL_ADMISSION_IDS <= set(
        manifest.authority["production_admission_ids"]
    )
    registry = manifest.authority["extended_subsystem_execution_registry"]
    assert set(registry["owners"]) == {
        "simulation",
        "mcp_connectors",
        "provider_gateway",
        "security_operations_lifecycle",
    }


def test_cp19i_effect_receipt_requires_real_hashes_and_applied_state():
    with pytest.raises(ExtendedSubsystemError, match="SHA-256"):
        AuthoritativeEffectReceipt(
            service="service",
            operation="operation",
            resource_id="resource",
            request_sha256="not-a-hash",
            result_sha256="b" * 64,
            idempotency_key="request-1",
        )
    with pytest.raises(ExtendedSubsystemError, match="status=applied"):
        AuthoritativeEffectReceipt(
            service="service",
            operation="operation",
            resource_id="resource",
            request_sha256="a" * 64,
            result_sha256="b" * 64,
            idempotency_key="request-1",
            status="proposed",
        )


def test_cp19i_effect_proposal_budget_blocks_before_execution():
    coordinator = ExtendedSubsystemCoordinator()

    with pytest.raises(
        KnowledgeLifecycleError,
        match="effect proposal budget exceeded",
    ):
        coordinator.execute_operation_sync(
            owner="simulation",
            operation="outcome_archive",
            requested_ids=["KA-1091"],
            ka_inputs={
                "KA-1091": {
                    "outcomes": [
                        {
                            "scenario_id": "simulation-budget",
                            "outcome_id": "result",
                            "status": "completed",
                            "significance": 1,
                            "summary": "bounded result",
                            "artifact_refs": [],
                        }
                    ],
                    "minimum_significance": 0,
                }
            },
            request_id="effect-budget",
            run_id="effect-budget",
            max_effects=0,
            principal_id="owner-1",
            service_capabilities={"simulation_job_service"},
        )


def test_cp19i_mcp_admission_runs_security_and_operations_before_effect():
    coordinator = ExtendedSubsystemCoordinator()

    execution = coordinator.admit_mcp_tool(
        execution_id="mcp-execution-1",
        principal_id="owner-1",
        server_id="local-connector",
        tool_name="read_data",
        arguments={"record_id": "record-1"},
        required_scopes={"mcp:execute", "connector:local-connector:read"},
        consent_approved=True,
    )

    assert execution.ok is True
    assert {
        "KA-022",
        "KA-136",
        "KA-137",
        "KA-177",
        "KA-179",
    } <= set(execution.executed_ids)
    assert coordinator.execution_outputs(execution)["KA-179"]["decision"] == "allow"


def test_cp19i_mcp_admission_rejects_inline_credentials():
    coordinator = ExtendedSubsystemCoordinator()

    with pytest.raises(
        ExtendedSubsystemError,
        match="credential_in_tool_arguments",
    ):
        coordinator.admit_mcp_tool(
            execution_id="mcp-execution-2",
            principal_id="owner-1",
            server_id="local-connector",
            tool_name="read_data",
            arguments={"api_key": "abcdefghijklmnop"},
            required_scopes={
                "mcp:execute",
                "connector:local-connector:read",
            },
            consent_approved=True,
        )


@pytest.mark.asyncio
async def test_cp19i_provider_governance_and_monitoring_are_trace_accounted():
    coordinator = ExtendedSubsystemCoordinator()

    request_execution = await coordinator.plan_provider_request(
        request_id="provider-request-1",
        trace_id="provider-trace-1",
        principal_id="owner-1",
        messages=[
            {"role": "system", "content": "Follow governed policy."},
            {"role": "user", "content": "Summarize the evidence."},
        ],
        token_budget=1_000,
    )
    monitor_execution = await coordinator.monitor_provider_result(
        request_id="provider-request-1",
        trace_id="provider-trace-1",
        principal_id="owner-1",
        duration_ms=125,
    )
    monitoring_decision = coordinator.provider_monitoring_decision(monitor_execution)
    receipt = coordinator.bind_effect_receipt(
        service="ProviderGatewayService",
        operation="answer:provider_call",
        resource_id="provider-trace-1:1",
        request_payload={"model": "fixture-model"},
        result_payload={"answer_sha256": "a" * 64},
        idempotency_key="provider-request-1:answer:1",
        ka_execution=request_execution,
    )

    assert request_execution.executed_ids == ["KA-1072"]
    assert monitor_execution.executed_ids == ["KA-084"]
    assert receipt.status == "applied"
    assert receipt.ka_plan_id == request_execution.plan.plan_id
    assert receipt.request_sha256 != receipt.result_sha256
    assert monitoring_decision["status"] == "measured"
    assert monitoring_decision["notification_applied"] is False


def test_cp19i_simulation_plan_executes_and_effect_remains_service_owned():
    coordinator = ExtendedSubsystemCoordinator()
    scenario = SimulationScenario(
        query="Evaluate a bounded local counterfactual.",
        depth=SimulationDepth.QUICK,
        execution_mode="fixed_seed_local",
    )

    execution = coordinator.plan_simulation(
        simulation_id="simulation-cp19i-1",
        principal_id="owner-1",
        scenario=scenario,
    )
    allowed, blockers = coordinator.simulation_plan_allowed(
        execution,
        scenario=scenario,
    )

    assert execution.ok is True
    assert allowed is True
    assert blockers == []
    assert {"KA-032", "KA-037", "KA-1080", "KA-1081"} <= set(execution.executed_ids)
    assert execution.plan.effect_proposal_count >= 1

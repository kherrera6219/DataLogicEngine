from __future__ import annotations

import pytest

from backend.governed_execution.contracts import (
    EvidenceRecord,
    GovernedPolicyDecision,
)
from backend.governed_execution.extended_subsystems import (
    ExtendedSubsystemCoordinator,
    ExtendedSubsystemError,
)
from backend.knowledge_algorithms.controller import get_ka_controller
from tests.governed_execution.test_orchestrator import (
    _Gateway,
    _orchestrator,
    _request,
)


def test_cp19h_truthgate_registry_has_one_canonical_owner_per_operation():
    manifest = get_ka_controller().manifest
    registry = manifest.authority["subsystem_execution_registry"]

    assert registry["schema_version"] == "dle.ka-subsystem-registry.v1"
    assert registry["owners"]["truthgate"]["entry"] == [
        "KA-022",
        "KA-172",
        "KA-173",
        "KA-174",
        "KA-176",
        "KA-177",
    ]
    for operation_ids in registry["owners"]["truthgate"].values():
        assert len(operation_ids) == len(set(operation_ids))
        assert all(
            manifest.entries[canonical_id].admission.production_enabled
            for canonical_id in operation_ids
        )


def test_ka_177_owning_path():
    coordinator = ExtendedSubsystemCoordinator()
    admitted = coordinator.admit_mcp_tool(
        execution_id="mcp-ka-177-allowed",
        principal_id="owner-1",
        server_id="local-connector",
        tool_name="read_data",
        arguments={"record": 1},
        required_scopes={"mcp:execute", "connector:local-connector:read"},
        consent_approved=True,
    )
    output = admitted.results["KA-177"]["output"]
    events = admitted.report.traces["KA-177"].events
    receipt = coordinator.bind_effect_receipt(
        service="MCPConnectorService",
        operation="tools/call:read_data",
        resource_id="mcp-ka-177-allowed",
        request_payload={"name": "read_data", "arguments": {"record": 1}},
        result_payload={"sha256": "a" * 64},
        idempotency_key="mcp-ka-177-allowed",
        ka_execution=admitted,
        proposal_ids=["KA-177", "KA-179"],
    )

    assert output["decision"] == "allow"
    assert output["effect_applied"] is False
    assert receipt.ka_plan_id == admitted.plan.plan_id
    assert [
        event.state.value
        for event in events
        if event.state.value
        in {"planned", "candidate", "selected", "admitted", "executing", "executed"}
    ] == ["planned", "candidate", "selected", "admitted", "executing", "executed"]
    assert next(
        event for event in events if event.state.value == "executed"
    ).result_trace_id

    with pytest.raises(ExtendedSubsystemError, match="policy_denied"):
        coordinator.admit_mcp_tool(
            execution_id="mcp-ka-177-denied",
            principal_id="owner-1",
            server_id="local-connector",
            tool_name="read_data",
            arguments={"record": 1},
            required_scopes={"mcp:execute", "connector:local-connector:read"},
            consent_approved=False,
        )


@pytest.mark.asyncio
async def test_ka_022_owning_path():
    allowed_gateway = _Gateway()
    allowed = await _orchestrator(allowed_gateway).execute(_request())

    admission = next(
        decision
        for decision in allowed.metadata["policy_decisions"]
        if decision["policy_id"] == "canonical_truthgate_entry"
    )
    assert admission["decision"] == "allow"
    assert admission["ka_results"]["KA-022"]["output"][
        "mitigation_required"
    ] is False

    blocked_gateway = _Gateway()
    blocked = await _orchestrator(blocked_gateway).execute(
        _request(
            metadata={
                "impact_scores": {
                    "technical": 0.9,
                    "security": 0.9,
                    "compliance": 0.9,
                    "financial": 0.9,
                    "schedule": 0.9,
                    "reputational": 0.9,
                }
            }
        )
    )

    assert blocked.ok is False
    assert blocked.failure is not None
    assert blocked.failure.code == "TRUTHGATE_ENTRY_BLOCK"
    assert blocked_gateway.provider_calls == 0
    blocked_admission = next(
        decision
        for decision in blocked.metadata["policy_decisions"]
        if decision["policy_id"] == "canonical_truthgate_entry"
    )
    assert blocked_admission["ka_results"]["KA-022"]["output"][
        "mitigation_required"
    ] is True


@pytest.mark.asyncio
async def test_ka_010_owning_path(monkeypatch: pytest.MonkeyPatch):
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

    class BiasedGateway(_Gateway):
        async def _direct_llm_call(
            self,
            provider,
            model,
            messages,
            temperature,
            max_tokens,
        ):
            self.provider_calls += 1
            self.provider_messages.append(messages)
            return {
                "ok": True,
                "answer": "The chairman approved the answer [S1]",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            }

    gateway = BiasedGateway()
    result = await _orchestrator(gateway).execute(_request())

    assert result.ok is False
    assert result.failure is not None
    assert result.failure.code == "L8_TRUST_POLICY_BLOCK"
    layer8 = next(
        layer
        for layer in result.metadata["reasoning_state"]["layers"]
        if layer["layer_id"] == "L8"
    )
    assert layer8["ka_results"]["KA-010"]["output"]["is_biased"] is True
    assert layer8["outputs"]["trust_policy_decision"]["decision"] == "block"


@pytest.mark.asyncio
async def test_ka_024_owning_path(monkeypatch: pytest.MonkeyPatch):
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

    allowed = await _orchestrator(_Gateway()).execute(_request())
    allowed_layer8 = next(
        layer
        for layer in allowed.metadata["reasoning_state"]["layers"]
        if layer["layer_id"] == "L8"
    )
    assert allowed_layer8["ka_results"]["KA-024"]["output"][
        "is_approved"
    ] is True

    blocked = await _orchestrator(_Gateway()).execute(
        _request(metadata={"risk_score": 1.0})
    )
    assert blocked.ok is False
    assert blocked.failure is not None
    assert blocked.failure.code == "L8_TRUST_POLICY_BLOCK"
    blocked_layer8 = next(
        layer
        for layer in blocked.metadata["reasoning_state"]["layers"]
        if layer["layer_id"] == "L8"
    )
    assert blocked_layer8["ka_results"]["KA-024"]["output"][
        "is_approved"
    ] is False
    assert blocked_layer8["outputs"]["trust_policy_decision"][
        "decision"
    ] == "block"


@pytest.mark.asyncio
async def test_cp19h_entry_policy_ka_block_prevents_routing_and_provider():
    gateway = _Gateway()
    request = _request(
        metadata={
            "safety_risk_level": "high",
            "hazard_ids": ["unsafe-output"],
            "required_safeguard_ids": ["owner-review"],
            "verified_safeguard_ids": [],
            "human_reviewed": False,
        }
    )

    result = await _orchestrator(gateway).execute(request)

    assert result.ok is False
    assert result.failure is not None
    assert result.failure.code == "TRUTHGATE_ENTRY_BLOCK"
    assert gateway.provider_calls == 0
    decision = result.metadata["policy_decisions"][1]
    assert decision["decision_version"] == "dle.governed-policy-decision.v1"
    assert decision["decision"] == "block"
    assert decision["ka_results"]["KA-172"]["output"]["decisions"][0][
        "decision"
    ] == "block"


@pytest.mark.asyncio
async def test_cp19h_layer8_uses_shared_typed_policy_and_canonical_ka_plan(
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
    result = await _orchestrator(_Gateway()).execute(_request())

    assert result.ok is True
    layer8 = next(
        layer
        for layer in result.metadata["reasoning_state"]["layers"]
        if layer["layer_id"] == "L8"
    )
    assert {"KA-010", "KA-024", "KA-027", "KA-1074"} <= set(
        layer8["selected_ka_ids"]
    )
    decision = layer8["outputs"]["trust_policy_decision"]
    assert decision["decision_version"] == "dle.governed-policy-decision.v1"
    assert GovernedPolicyDecision(
        policy_id=decision["policy_id"],
        decision=decision["decision"],
        stage=decision["stage"],
    ).blocked is False


@pytest.mark.asyncio
async def test_cp19h_lifecycle_publication_failure_prevents_release(
    monkeypatch: pytest.MonkeyPatch,
):
    import backend.governed_execution.orchestrator as module

    class FailingPublisher:
        @staticmethod
        def publish_stage(*args, **kwargs):
            raise RuntimeError("publication_failed")

        @staticmethod
        def publish_ka_results(*args, **kwargs):
            raise RuntimeError("publication_failed")

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
    orchestrator = _orchestrator(_Gateway())
    orchestrator.transition_publisher = FailingPublisher()

    result = await orchestrator.execute(_request())

    assert result.ok is False
    assert result.failure is not None
    assert result.failure.code == "LIFECYCLE_PUBLICATION_FAILURE"
    assert result.metadata["lifecycle_failures"]

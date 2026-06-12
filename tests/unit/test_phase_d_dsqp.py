from backend.dsqp import COMPONENT_KEYS, DSQPChain, DSQPOrchestrator, DSQPValidator
from core.system.persona_construction_service import PersonaConstructionService
from sdk.UKG_Python_SDK.ukg_sdk.overlay import UKGOverlay
from sdk.UKG_Python_SDK.ukg_sdk.audit import FileAuditStore
from sdk.UKG_Python_SDK.ukg_sdk.providers import LLMResponse


class _Provider:
    async def complete(self, *, messages, model, temperature=0.2, max_tokens=1024):
        return LLMResponse(
            text="Provider-backed answer",
            raw={},
            model=model,
            usage={"total_tokens": 8},
        )


def test_dsqp_chain_returns_seven_component_json_serializable_persona():
    persona = DSQPChain().construct(
        "Assess healthcare AI audit controls",
        {"active_axes": [8]},
        axis_number=8,
        coordinate_path="healthcare.audit",
        context={"risk_domain": "healthcare"},
    )

    payload = persona.to_dict()
    assert set(payload["components"]) == set(COMPONENT_KEYS)
    assert len(payload["dsqp_chain"]) == 7
    assert payload["coverage_score"] >= 0.70
    assert payload["metadata"]["local_slm_audit"]["mode"] == "LOCAL_MODEL"
    assert DSQPValidator().validate(payload)["valid"] is True


def test_dsqp_orchestrator_constructs_four_persona_axes():
    result = DSQPOrchestrator(timeout_seconds=5).construct_all_sync(
        "Review a regulated AI workflow",
        {"active_axes": [8, 9, 10, 11]},
        active_axes=[8, 9, 10, 11],
        context={"query": "Review a regulated AI workflow", "risk_domain": "finance"},
    )

    assert result["failures"] == {}
    assert set(result["profiles"]) == {"8", "9", "10", "11"}
    for profile in result["profiles"].values():
        assert profile["validation"]["valid"] is True
        assert len(profile["dsqp_chain"]) == 7


def test_persona_construction_service_uses_dsqp_with_static_fallback_available():
    service = PersonaConstructionService()
    profile = service.construct_persona(
        10,
        "regulatory.ai",
        {"query": "Check an AI workflow for EU AI Act risk", "dsqp_mode": True},
    )

    assert profile.metadata["construction_mode"] == "dsqp"
    assert profile.metadata["dsqp_coverage_score"] >= 0.70
    assert len(profile.metadata["dsqp_chain"]) == 7
    assert profile.components["job_role"]["query_mission"]


async def test_sdk_overlay_trace_includes_dsqp_chain(tmp_path):
    overlay = UKGOverlay(
        provider=_Provider(),
        model="test-model",
        audit=FileAuditStore(tmp_path / "audit.jsonl"),
    )

    result = await overlay.run(
        query="Assess finance AI release controls",
        tier_override="T2",
        meta={"risk_domain": "finance"},
    )

    dsqp_stage = next(stage for stage in result["trace"] if stage["ka_id"] == "DSQP")
    assert dsqp_stage["status"] == "ok"
    assert set(dsqp_stage["output"]["dsqp_chain"]["profiles"]) == {"8", "9", "10", "11"}
    assert dsqp_stage["output"]["dsqp_chain"]["failures"] == {}


def test_dsqp_validator_requires_self_questioning_process():
    """A2: the validator must confirm the seven-step chain ran, not just that
    components are populated. A persona with full components but no chain is
    NOT a valid DSQP construction."""
    persona = DSQPChain().construct(
        "Evaluate regulatory filing controls",
        {"active_axes": [10]},
        axis_number=10,
        coordinate_path="regulatory.filing",
        context={"risk_domain": "finance"},
    )
    payload = persona.to_dict()

    # Real construction: coverage + process both valid.
    result = DSQPValidator().validate(payload)
    assert result["valid"] is True
    assert result["process_valid"] is True
    assert result["process_issues"] == []

    # Components present but chain stripped → process invalid → overall invalid.
    no_chain = dict(payload)
    no_chain["dsqp_chain"] = []
    stripped = DSQPValidator().validate(no_chain)
    assert stripped["process_valid"] is False
    assert stripped["valid"] is False
    assert "dsqp_chain_missing" in stripped["process_issues"] or any(
        "missing_chain_steps" in issue for issue in stripped["process_issues"]
    )


def test_dsqp_validator_flags_incomplete_chain_steps():
    """A chain step with an empty question or answer fails process validation."""
    persona = DSQPChain().construct(
        "Assess sector supply chain risk",
        {"active_axes": [9]},
        axis_number=9,
        coordinate_path="sector.supply_chain",
        context={"risk_domain": "standard"},
    )
    payload = persona.to_dict()
    payload["dsqp_chain"][2]["question"] = ""  # corrupt one step

    result = DSQPValidator().validate(payload)
    assert result["process_valid"] is False
    assert result["valid"] is False
    assert any("empty_question" in issue for issue in result["process_issues"])

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

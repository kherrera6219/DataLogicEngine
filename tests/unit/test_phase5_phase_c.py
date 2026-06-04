import json
from types import SimpleNamespace

import pytest

from backend.knowledge_algorithms.ka_38_consensus_engine import KA038ConsensusEngine, KA038Input, PersonaClaim
from backend.llm_gateway.gateway import LLMGateway
from backend.truth_engine.truth_core.engine import TruthCoreEngine
from backend.truth_engine.truth_core.personas import PersonaEnhancer
from backend.truth_engine.truth_core.refinement_orchestrator import RefinementOrchestrator
from core.persona.quad.mathematical_framework import DynamicWeightFunctions


class FakeQuadEngine:
    async def run_quad_analysis(self, query, context):
        return {
            "synthesis": "base synthesis",
            "perspectives": {
                "knowledge": {"response": "Axis 8 analysis", "confidence": 0.82},
                "sector": {"response": "Axis 9 analysis", "confidence": 0.8},
                "regulatory": {"response": "Axis 10 analysis", "confidence": 0.86},
                "compliance": {"response": "Axis 11 analysis", "confidence": 0.84},
            },
            "metadata": {"confidence": 0.83},
        }


class FakeController:
    llm_gateway = None

    def execute_algorithm(self, ka_id, inputs):
        if ka_id == "KA-012":
            return {
                "personas": {
                    "knowledge": {"response": "Axis 8 claim", "confidence": 0.9},
                    "sector": {"response": "Axis 9 claim", "confidence": 0.8},
                    "regulatory": {"response": "Axis 10 claim", "confidence": 0.85},
                    "compliance": {"response": "Axis 11 claim", "confidence": 0.82},
                },
                "claims": [{"claim_id": "c1", "content": "claim"}],
                "confidence": 0.86,
            }
        return {"output": {"ok": True}, "confidence": 0.9}


class FakePersonaConstruction:
    def construct_persona(self, axis_number, coordinate_path, context):
        components = {
            "job_role": {"title": f"Axis {axis_number} Expert"},
            "education": {"degree": "Advanced Degree"},
            "certifications": {"list": ["Local Certification"]},
            "skills": {"items": ["Analysis"]},
            "training": {"modules": ["Recursive Learning"]},
            "career_path": {"stages": ["SME"]},
            "related_jobs": {"overlapping_roles": ["Advisor"]},
        }
        return SimpleNamespace(
            persona_type={8: "knowledge", 9: "sector", 10: "regulatory", 11: "compliance"}[axis_number],
            to_dict=lambda: {
                "axis_number": axis_number,
                "persona_type": {8: "knowledge", 9: "sector", 10: "regulatory", 11: "compliance"}[axis_number],
                "components": components,
            },
        )


@pytest.mark.asyncio
async def test_gateway_quad_analysis_reaches_pod_orchestrator(monkeypatch):
    import backend.quad_persona.quad_engine as quad_engine

    monkeypatch.setattr(quad_engine, "create_quad_persona_engine", lambda: FakeQuadEngine())
    gateway = LLMGateway()

    result = await gateway._run_quad_analysis(
        "Assess legal compliance risk",
        {"tags": ["legal"], "force_expanded_committee": True},
    )

    pod_trace = next(item for item in result["trace"] if item["ka_id"] == "PodOrchestrator")
    assert result["ok"] is True
    assert pod_trace["output"]["pod_count"] > 0
    assert "collective_confidence" in pod_trace["output"]
    assert LLMGateway.get_quad_analysis_status()["pod_count"] == pod_trace["output"]["pod_count"]


@pytest.mark.asyncio
async def test_gateway_desktop_adds_local_slm_fallback(monkeypatch):
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    providers = await LLMGateway()._get_eligible_providers(meta={"tier": "high_stakes"})

    assert providers[-1].provider_type == "local_slm"
    assert providers[-1].endpoint == "http://localhost:11434/v1"


@pytest.mark.asyncio
async def test_truthcore_l5_constructs_profiles_and_uses_pod_orchestrator():
    engine = TruthCoreEngine(ka_controller=FakeController())
    engine.persona_construction = FakePersonaConstruction()

    result = await engine._execute_workflow(
        "Evaluate legal and compliance risk",
        {
            "tags": ["legal"],
            "coordinate_vector": {
                "active_axes": [8, 9, 10, 11],
                "axes": {8: "pillar.defense", 9: "sector.software", 10: "reg.far", 11: "control.audit"},
            },
        },
        ["multi_persona_reasoning"],
        "moderate",
    )

    context = result["context"]
    assert set(context["constructed_persona_profiles"].keys()) == {"8", "9", "10", "11"}
    for profile in context["constructed_persona_profiles"].values():
        assert set(profile["components"]) == {
            "job_role",
            "education",
            "certifications",
            "skills",
            "training",
            "career_path",
            "related_jobs",
        }
    assert context["pod_orchestration_summary"]["pod_count"] > 0


def test_persona_enhancer_uses_integration_function():
    enhancer = PersonaEnhancer()
    synthesized = enhancer._synthesize_responses(
        {
            "knowledge_expert": {"role": "Knowledge Expert", "response": "Knowledge view", "confidence": 0.8},
            "sector_expert": {"role": "Sector Expert", "response": "Sector view", "confidence": 0.8},
            "regulatory_expert": {"role": "Regulatory Expert", "response": "Regulatory view", "confidence": 0.8},
            "compliance_expert": {"role": "Compliance Expert", "response": "Compliance view", "confidence": 0.8},
        },
        {
            "knowledge_expert": 0.3,
            "sector_expert": 0.3,
            "regulatory_expert": 0.2,
            "compliance_expert": 0.2,
        },
    )

    assert synthesized["synthesis_method"] == "quad_integration_function"
    assert "dynamic_weights" in synthesized
    assert "Knowledge Expert" in synthesized["content"]


@pytest.mark.asyncio
async def test_refinement_orchestrator_adds_drl_convergence():
    orchestrator = RefinementOrchestrator(ka_controller=FakeController())
    orchestrator.STEPS = []

    result = await orchestrator.refine({"content": "draft", "confidence": 0.4}, {"session_id": "s1"})

    assert result["drl_convergence"]["threshold_met"] is True
    assert result["final_confidence"] >= orchestrator.target_confidence


def test_dynamic_weights_and_ka038_are_json_serializable():
    weights_engine = DynamicWeightFunctions()
    weights = weights_engine.compute_all_weights({"regulatory_urgency": 1.0, 12: "axis-key"})
    json.dumps(weights)
    json.dumps(weights_engine.get_serializable_weight_history())

    ka = KA038ConsensusEngine({})
    result = ka._run_logic(
        KA038Input(
            claims=[
                PersonaClaim(claim_id="c1", content="claim", persona_type="knowledge", confidence=0.8),
                PersonaClaim(claim_id="c1", content="claim", persona_type="regulatory", confidence=0.9),
            ],
            context={"regulatory_urgency": 1.0},
        )
    )
    json.dumps(result["metadata"]["weights_used"])

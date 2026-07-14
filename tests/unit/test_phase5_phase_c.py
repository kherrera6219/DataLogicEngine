import json
from types import SimpleNamespace

import pytest

from backend.knowledge_algorithms.ka_38_consensus_engine import KA038ConsensusEngine, KA038Input, PersonaClaim
from backend.llm_gateway.gateway import LLMGateway
from backend.truth_engine.truth_core.engine import TruthCoreEngine
from backend.truth_engine.truth_core.personas import PersonaEnhancer
from backend.truth_engine.truth_core.refinement_orchestrator import RefinementOrchestrator
from core.persona.quad.mathematical_framework import DynamicWeightFunctions


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


def test_gateway_has_no_duplicate_quad_or_overlay_pipeline():
    assert not hasattr(LLMGateway, "_run_quad_analysis")
    assert not hasattr(LLMGateway, "_run_ukg_overlay")


@pytest.mark.asyncio
async def test_quad_engine_returns_gateway_contract_without_live_provider():
    from backend.quad_persona.quad_engine import create_quad_persona_engine

    analysis = await create_quad_persona_engine().run_quad_analysis(
        "Assess compliance risk",
        {"tags": ["legal"], "risk_domain": "compliance"},
    )

    assert set(analysis["perspectives"]) == {"knowledge", "sector", "regulatory", "compliance"}
    assert isinstance(analysis["synthesis"], str)
    assert analysis["metadata"]["successful_personas"] == 4
    assert analysis["metadata"]["confidence"] > 0
    for persona_result in analysis["perspectives"].values():
        assert persona_result["status"] == "success"
        assert "ImportError" not in persona_result["response"]


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
async def test_refinement_orchestrator_requires_explicit_validator_convergence():
    orchestrator = RefinementOrchestrator(ka_controller=FakeController())
    orchestrator.STEPS = []

    result = await orchestrator.refine({"content": "draft", "confidence": 0.4}, {"session_id": "s1"})

    assert result["drl_convergence"]["action"] == "abstain"
    assert result["drl_convergence"]["support_ratio"] is None
    assert result["drl_convergence"]["missing_inputs"] == ["validator_results"]
    assert result["final_confidence"] == 0.4


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

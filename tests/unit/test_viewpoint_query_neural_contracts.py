"""Contracts for governed viewpoints, legacy query personas, and neural synthesis."""

from core.simulation.layer6_neural_analysis import Layer6NeuralAnalysis
from core.simulation.query_persona_engine import QueryPersonaEngine
from core.simulation.viewpoint_registry import (
    ExpertProfile,
    RedactionPolicy,
    ViewpointProfile,
    create_viewpoint_registry,
)


class Memory:
    def __init__(self, fail=False):
        self.entries = []
        self.fail = fail

    def add_memory_entry(self, **entry):
        if self.fail:
            raise RuntimeError("memory failed")
        self.entries.append(entry)
        return f"memory-{len(self.entries)}"

    def update_memory_entry(self, **entry):
        if self.fail:
            raise RuntimeError("memory failed")
        self.entries.append(entry)


class Execution:
    def __init__(self, output): self.output = output
    def require_output(self): return self.output


class Loader:
    def __init__(self, fail=False): self.calls = []; self.fail = fail
    def execute_typed(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail: raise RuntimeError("KA failed")
        return Execution({
            "confidence": 0.7,
            "extracted_entities": [{"text": "DataLogic"}, {}],
            "identified_topics": [{"topic": "coverage"}, {}],
        })


def test_viewpoint_models_domain_rules_and_round_trip():
    expert = ExpertProfile(job_role={"title": "Engineer"}, skills={"items": ["testing"]})
    redaction = RedactionPolicy(redact_pii=False, allowed_classification_levels=["PUBLIC"])
    profile = ViewpointProfile(
        id="custom",
        name="Custom Reviewer",
        lane="knowledge",
        allowed_domains=["Technology"],
        blocked_domains=["Defense"],
        required_evidence_types=["test_report"],
        redaction_policy=redaction,
        expert_profile=expert,
    )
    assert profile.is_allowed_for_domain("technology")
    assert not profile.is_allowed_for_domain("defense")
    assert not profile.is_allowed_for_domain("finance")
    unrestricted = ViewpointProfile(id="open", name="Open", lane="stakeholder")
    assert unrestricted.is_allowed_for_domain("anything")
    restored = ViewpointProfile.from_dict(profile.to_dict())
    assert restored.expert_profile.to_dict()["job_role"]["title"] == "Engineer"
    assert restored.redaction_policy.to_dict()["redact_pii"] is False
    assert restored.created_at and restored.updated_at


def test_viewpoint_registry_builtins_crud_query_audit_export_and_import():
    registry = create_viewpoint_registry({"governed": True})
    assert registry.get_profile("radar_sme").name == "Radar Systems SME"
    assert registry.get_profile("missing") is None
    assert registry.list_profiles(lane="knowledge")
    assert registry.list_profiles(domain="aviation")
    assert registry.get_profiles_by_lane("compliance")
    assert registry.get_profiles_for_domain("technology")
    assert registry.search_profiles("radar")
    assert registry.search_profiles("acquisition")
    assert registry.search_profiles("aesa")

    profile = ViewpointProfile(id="new", name="New Reviewer", lane="stakeholder")
    assert registry.add_profile(profile, "owner")
    assert not registry.add_profile(profile, "owner")
    assert registry.get_profile("new").status == "pending_review"
    assert registry.update_profile("new", {"description": "updated", "unknown": "ignored"}, "editor")
    assert not registry.update_profile("missing", {}, "editor")
    assert registry.approve_profile("new", "approver")
    assert not registry.approve_profile("missing", "approver")
    assert registry.deprecate_profile("new", "owner")
    audit = registry.get_audit_log("new", 2)
    assert len(audit) == 2
    exported = registry.export_profiles()
    assert any(item["id"] == "new" for item in exported)

    imported = create_viewpoint_registry()
    assert imported.import_profiles(
        [
            {"id": "imported", "name": "Imported", "lane": "knowledge"},
            {"name": "broken"},
            {"id": "radar_sme", "name": "Duplicate", "lane": "knowledge"},
        ],
        "importer",
    ) == 1
    assert imported.get_profile("imported").created_by == "importer"


def test_query_persona_engine_runs_all_personas_and_records_results():
    memory = Memory()
    loader = Loader()
    engine = QueryPersonaEngine({}, object(), memory, object(), loader)
    result = engine.run(
        "How should coverage be qualified?",
        "topic",
        {"Axis8": 0.8, "Axis9": 0.7, "Axis10": 0.6, "Axis11": 0.5},
        ["US"],
        "session",
        1,
    )
    assert result["status"] == "success"
    assert set(result["personas_output"]) == {"KE", "SE", "RE", "CE"}
    assert result["overall_confidence"] > 0.7
    assert len(loader.calls) == 4
    assert len(memory.entries) == 6
    for output in result["personas_output"].values():
        assert "DataLogic" in output["answer"]
        assert "coverage" in output["answer"]
        assert "Contextual Considerations" in output["answer"]


def test_query_persona_invalid_failure_answer_and_confidence_boundaries():
    engine = QueryPersonaEngine(
        {"layer2_qpe_ro": {"personas": ["UNKNOWN"]}}, object(), Memory(), object(), Loader()
    )
    result = engine.run("q", "topic", {}, [], "", 1)
    assert result["overall_confidence"] == 0.0
    assert result["personas_output"]["UNKNOWN"]["status"] == "error"
    assert engine._get_persona_model("UNKNOWN") == {}

    no_components = {"name": "Minimal", "knowledge_focus": "facts", "components": []}
    answer = engine._generate_persona_answer("KE", no_components, "q", {}, {}, [])
    assert "Based on my expertise" in answer
    assert engine._calculate_persona_confidence("KE", {"confidence": "unknown"}, 10, {}) == 0.0
    assert engine._calculate_persona_confidence("KE", {"confidence": 0.9}, 3000, {"Axis8": 1}) == 1.0
    assert engine._calculate_persona_confidence("UNKNOWN", {"confidence": 0.1}, 300, {}) == 0.2

    broken = QueryPersonaEngine({}, object(), Memory(), object(), Loader(fail=True))
    assert broken._run_persona("KE", "q", "topic", {}, [], "session", 1)["status"] == "error"
    memory_failure = QueryPersonaEngine({}, object(), Memory(fail=True), object(), Loader())
    assert memory_failure.run("q", "topic", {}, [], "session", 1)["status"] == "error"


def test_neural_analysis_patterns_gaps_synthesis_and_readiness_branches():
    engine = Layer6NeuralAnalysis({"mode": "test"}, object())
    rich = {
        "consensus_score": 0.9,
        "content": "risk danger warning compliance violation",
        "covered_axes": [6],
    }
    result = engine.process(rich, {"session": "one"})
    assert result["status"] == "success"
    assert result["embeddings_generated"] == 5
    assert len(result["patterns_detected"]) == 2
    assert [gap["axis_id"] for gap in result["gaps_identified"]] == [7, 14]
    assert result["synthesis"]["recommendation"] == "RECURSE"

    complete = engine.synthesis({}, [{"description": "one"}, {"description": "two"}, {"description": "three"}], [])
    assert complete["recommendation"] == "PROCEED"
    assert complete["readiness_score"] == 0.8
    empty = engine.process({"covered_axes": [6, 7, 14]})
    assert empty["patterns_detected"] == []
    assert empty["gaps_identified"] == []

"""Behavioral contracts for the non-production 12-step simulation reference."""

from core.simulation.refinement_orchestrator import SimulationRefinementOrchestrator


class MemoryManager:
    def __init__(self, fail=False):
        self.fail = fail
        self.added = []
        self.updated = []

    def add_memory_entry(self, **entry):
        if self.fail:
            raise RuntimeError("memory unavailable")
        self.added.append(entry)
        return f"memory-{len(self.added)}"

    def update_memory_entry(self, **entry):
        self.updated.append(entry)
        return True


def _qpe_output():
    long_answer = (
        "The release architecture requires documented evidence and verified sources. "
        "Because the policy applies, the system must retain audit records and protect personal data. "
        "For example, the qualification report provides a source and citation. "
        "However, assumptions and risks should be stated clearly. "
    ) * 4
    return {
        "status": "success",
        "overall_confidence": 0.82,
        "personas_output": {
            "knowledge": {
                "status": "success",
                "confidence": 0.9,
                "answer": long_answer,
                "persona_model": {"name": "Knowledge", "knowledge_focus": "architecture"},
            },
            "regulatory": {
                "status": "success",
                "confidence": 0.8,
                "answer": long_answer + " GDPR CCPA regulation compliance.",
                "persona_model": {"name": "Regulatory", "knowledge_focus": "law"},
            },
            "failed": {"status": "error", "confidence": 0.1, "error": "not available"},
        },
    }


def _orchestrator(memory=None):
    return SimulationRefinementOrchestrator(
        {"layer2_qpe_ro": {}}, None, memory or MemoryManager(), None, None
    )


def test_simulation_refinement_all_twelve_steps_success():
    memory = MemoryManager()
    orchestrator = _orchestrator(memory)
    result = orchestrator.run(
        _qpe_output(),
        "How should release architecture evidence satisfy GDPR policy?",
        "topic-1",
        {"a1": 0.8, "a11": 0.9},
        ["LOC_COUNTRY_USA"],
        "session-1",
        1,
    )

    assert result["status"] == "success"
    assert len(result["refinement_steps_log"]) == 12
    assert result["refined_answer_text"].startswith("#")
    assert "Universal Knowledge Graph" in result["refined_answer_text"]
    assert 0 <= result["final_confidence"] <= 0.95
    assert result["final_scoring_factors_from_s11"]
    assert len(memory.added) == 13
    assert len(memory.updated) == 1


def test_simulation_refinement_validation_top_level_error_and_step_fallbacks():
    orchestrator = _orchestrator()
    invalid = orchestrator.run({}, "query", "topic", {}, [], "", 1)
    assert invalid == {"status": "error", "error": "Invalid QPE output: Unknown error"}

    failed_memory = _orchestrator(MemoryManager(fail=True))
    failed = failed_memory.run(_qpe_output(), "query", "topic", {}, [], "session", 1)
    assert failed["status"] == "error"
    assert "memory unavailable" in failed["error"]

    state = {
        "query_text": "query",
        "query_topic_uid": "topic",
        "qpe_output": {"status": "success", "personas_output": {}},
        "initial_axis_context_scores": {},
        "active_location_context": [],
        "session_id": "session",
        "pass_num": 1,
        "refinement_steps_log": {},
        "current_draft": "",
        "step_confidence_scores": {},
        "research_needs": [],
    }
    state = orchestrator._execute_step_1_analysis_of_qpe_outputs(state)
    assert state["step_confidence_scores"]["S1_Analysis_of_QPE_Outputs"] == 0.3
    state = orchestrator._execute_step_2_initial_synthesis(state)
    assert state["current_draft"].startswith("# Response to Query")


def test_simulation_refinement_helpers_and_weighted_confidence_fallback():
    orchestrator = _orchestrator()
    personas = _qpe_output()["personas_output"]
    assert orchestrator._identify_commonalities(personas)[0]["type"] == "shared_perspective"
    assert {item["persona"] for item in orchestrator._identify_differences(personas)} == {
        "knowledge",
        "regulatory",
    }
    assert orchestrator._get_term_context("Before GDPR after", "gdpr") == "Before GDPR after"
    assert orchestrator._get_term_context("text", "missing") == ""
    assert {item["id"] for item in orchestrator._get_applicable_regulations([])} == {"GDPR", "CCPA"}

    confidence = orchestrator._calculate_final_confidence(
        {
            "refinement_steps_log": {},
            "step_confidence_scores": {
                "S1_Analysis_of_QPE_Outputs": 0.8,
                "S10_Answer_Quality_Evaluation": 1.0,
                "unknown": 1.0,
            },
        }
    )
    assert 0 < confidence <= 0.95
    assert orchestrator._calculate_final_confidence(
        {"refinement_steps_log": {}, "step_confidence_scores": {}}
    ) == 0

"""Contract coverage for SEKRE analysis, enhancement, and feedback paths."""

from types import SimpleNamespace

from core.self_evolving.sekre_engine import SekreEngine


class Memory:
    def __init__(self, fail=False):
        self.entries = []
        self.fail = fail

    def store_memory(self, **entry):
        if self.fail:
            raise RuntimeError("memory failed")
        self.entries.append(entry)


class Execution:
    def __init__(self, success=True):
        self.success = success
        self.trace_id = "trace"

    def require_output(self):
        return {"enhanced": True}


class KAEngine:
    def __init__(self, algorithms):
        self.algorithms = algorithms
        self.calls = []

    def list_algorithms(self):
        return [{"ka_id": value} for value in self.algorithms]

    def execute_typed(self, ka_id, payload):
        self.calls.append((ka_id, payload))
        return Execution()


class USM:
    def __init__(self, components):
        self.components = components

    def get_component(self, name):
        return self.components.get(name)


def low_simulation():
    return {
        "simulation_id": "sim",
        "query": "qualify release",
        "confidence": {"overall": 0.4},
        "passes": [
            {
                "persona_results": {
                    "knowledge": {
                        "confidence": 0.4,
                        "components": {
                            "job_role": {"confidence": 0.2},
                            "education": {"confidence": 0.9},
                        },
                    }
                }
            }
        ],
    }


def test_analysis_specific_general_high_confidence_and_auto_improve():
    memory = Memory()
    engine = SekreEngine(
        {"sekre": {"auto_improve": True, "improvement_threshold": 0.75}},
        memory_manager=memory,
    )
    specific = engine.analyze_simulation_results(low_simulation())
    assert specific["suggestions"][0]["target"] == "knowledge.job_role"
    assert engine.stats["improvement_suggestions"] == 1
    assert engine.stats["improvements_applied"] == 1
    assert memory.entries

    general = engine.analyze_simulation_results(
        {"simulation_id": "general", "query": "q", "confidence": {"overall": 0.2}}
    )
    assert general["suggestions"][0]["type"] == "general_enhancement"
    high = engine.analyze_simulation_results(
        {"simulation_id": "high", "confidence": {"overall": 0.95}}
    )
    assert high["suggestions"] == []


def test_apply_improvements_uses_specific_fallback_general_and_basic_paths():
    memory = Memory()
    specific_ka = KAEngine(["KA_ENHANCE_KNOWLEDGE_JOB_ROLE"])
    engine = SekreEngine(memory_manager=memory, united_system_manager=USM({"ka_engine": specific_ka}))
    result = engine.apply_improvements(
        [
            {
                "type": "knowledge_enhancement",
                "target": "knowledge.job_role",
                "query_pattern": "q",
                "confidence": 0.2,
            },
            {"type": "knowledge_enhancement", "target": "invalid"},
            {"type": "ignored", "target": "none"},
        ]
    )
    assert result["suggestions_applied"] == 1
    assert specific_ka.calls[0][0] == "KA_ENHANCE_KNOWLEDGE_JOB_ROLE"

    fallback_ka = KAEngine(["KA_ENHANCE_GENERAL"])
    fallback = SekreEngine(memory_manager=memory, united_system_manager=USM({"ka_engine": fallback_ka}))
    assert fallback._enhance_knowledge("knowledge", "skills", "q", 0.1)["success"]
    assert fallback._enhance_general_knowledge("q", 0.1)["success"]

    none_available = SekreEngine(
        memory_manager=memory, united_system_manager=USM({"ka_engine": KAEngine([])})
    )
    assert none_available._enhance_knowledge("knowledge", "skills", "q", 0.1)["success"]
    assert none_available._enhance_general_knowledge("q", 0.1)["success"]
    no_engine = SekreEngine(memory_manager=memory, united_system_manager=USM({}))
    assert no_engine._enhance_knowledge("knowledge", "skills", "q", 0.1)["success"]
    assert no_engine._enhance_general_knowledge("q", 0.1)["success"]


def test_basic_enhancement_and_error_paths_are_fail_closed():
    engine = SekreEngine()
    assert not engine._apply_basic_enhancement("p", "c", "q")
    assert not engine._apply_basic_general_enhancement("q")
    failing = SekreEngine(memory_manager=Memory(fail=True))
    assert not failing._apply_basic_enhancement("p", "c", "q")
    assert not failing._apply_basic_general_enhancement("q")

    class BrokenUSM:
        def get_component(self, _name):
            raise RuntimeError("component failed")

    broken = SekreEngine(united_system_manager=BrokenUSM())
    assert "error" in broken._enhance_knowledge("p", "c", "q", 0.2)
    assert "error" in broken._enhance_general_knowledge("q", 0.2)

    original = engine._enhance_general_knowledge
    engine._enhance_general_knowledge = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("x"))
    result = engine.apply_improvements(
        [{"type": "general_enhancement", "target": "overall", "query_pattern": "q"}]
    )
    assert result["error"] == "x"
    engine._enhance_general_knowledge = original


def test_feedback_storage_negative_analysis_positive_and_validation():
    memory = Memory()
    simulation_engine = SimpleNamespace(get_simulation=lambda _simulation_id: low_simulation())
    engine = SekreEngine(
        {"sekre": {"auto_improve": True}},
        memory_manager=memory,
        united_system_manager=USM({"simulation_engine": simulation_engine}),
    )
    assert not engine.process_feedback({})["processed"]
    negative = engine.process_feedback(
        {"feedback_id": "feedback", "simulation_id": "sim", "rating": 1, "query": "q"}
    )
    assert negative["processed"]
    assert "analysis_id" in negative
    assert "improvement_id" in negative
    positive = engine.process_feedback({"simulation_id": "sim", "rating": 5})
    assert positive["processed"]
    assert engine.stats["feedback_processed"] == 2
    assert len(memory.entries) >= 3

    broken = SekreEngine(memory_manager=Memory(fail=True))
    failed = broken.process_feedback({"simulation_id": "sim", "rating": 5})
    assert failed["error"] == "memory failed"


def test_conflicts_history_stats_and_toggle_contracts():
    engine = SekreEngine(graph_manager=object())
    engine.improvement_suggestions = [{"id": 1}, {"id": 2}, {"id": 3}]
    assert engine.identify_knowledge_conflicts() == []
    resolved = engine.resolve_knowledge_conflict("conflict", "prefer_newer")
    assert resolved["resolved"]
    assert engine.get_improvement_history(1, 1) == [{"id": 2}]
    assert engine.get_stats()["knowledge_conflicts_resolved"] == 1
    assert engine.set_auto_improve(True)
    assert engine.auto_improve

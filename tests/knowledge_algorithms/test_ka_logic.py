import pytest
from backend.knowledge_algorithms.ka_01_algorithm_of_thought import KA001AlgorithmOfThought, KA001Input
from backend.knowledge_algorithms.ka_07_recursive_reasoning_control import KA007RecursiveReasoningControl, KA007Input
from backend.knowledge_algorithms.ka_26_contradiction_detection import KA026ContradictionDetection, KA026Input
from backend.knowledge_algorithms.ka_43_causal_inference import KA043CausalInference, KA043Input

@pytest.fixture
def empty_context():
    return {}

class TestKA01AoT:
    def test_simple_strategy(self, empty_context):
        ka = KA001AlgorithmOfThought(empty_context)
        result = ka.run(KA001Input(query="What is 1+1?"))
        assert result["success"]
        assert result["output"]["strategy"] == "simple"
        assert len(result["output"]["tasks"]) > 0

    def test_research_strategy(self, empty_context):
        ka = KA001AlgorithmOfThought(empty_context)
        result = ka.run(KA001Input(query="Deep research into quantum gravity in black holes"))
        assert result["success"]
        assert result["output"]["strategy"] == "research"
        assert any(t["step_type"] == "search" for t in result["output"]["tasks"])

class TestKA07RecursionControl:
    def test_max_depth_termination(self, empty_context):
        ka = KA007RecursiveReasoningControl(empty_context)
        # Mock config max depth to 2 if possible, otherwise use default
        ka.config["max_recursion_depth"] = 2
        
        result = ka.run(KA007Input(current_depth=2, confidence=1.0))
        assert result["success"]
        assert result["output"]["allow_recursion"] is False
        assert "depth" in result["output"]["reason"]

    def test_loop_detection(self, empty_context):
        ka = KA007RecursiveReasoningControl(empty_context)
        state = {"val": 100}
        # pre-calculate history hash for loop detection
        import json, hashlib
        state_str = json.dumps(state, sort_keys=True)
        state_hash = hashlib.sha256(state_str.encode()).hexdigest()
        
        result = ka.run(KA007Input(current_depth=0, current_state=state, state_history=[state_hash]))
        assert result["success"]
        assert result["output"]["allow_recursion"] is False
        assert "loop detected" in result["output"]["reason"]

    def test_confidence_decay(self, empty_context):
        ka = KA007RecursiveReasoningControl(empty_context)
        ka.config["termination_threshold"] = 0.5
        ka.config["confidence_decay_factor"] = 0.1
        
        result = ka.run(KA007Input(current_depth=1, confidence=1.0))
        assert result["success"]
        assert result["output"]["allow_recursion"] is False
        assert "Effective confidence" in result["output"]["reason"]

class TestKA26ContradictionDetection:
    def test_direct_negation(self, empty_context):
        ka = KA026ContradictionDetection(empty_context)
        findings = [
            {"id": "f1", "content": "The sky is blue"},
            {"id": "f2", "content": "The sky is not blue"}
        ]
        result = ka.run(KA026Input(findings=findings))
        assert result["success"]
        assert result["output"]["has_contradictions"] is True
        assert any(c["type"] == "DIRECT_NEGATION" for c in result["output"]["conflicts"])

    def test_persona_stance_clash(self, empty_context):
        ka = KA026ContradictionDetection(empty_context)
        findings = [
            {"id": "f1", "persona": "engineer", "subject": "deadline", "content": "We need 2 months"},
            {"id": "f2", "persona": "manager", "subject": "deadline", "content": "We need 2 weeks"}
        ]
        result = ka.run(KA026Input(findings=findings))
        assert result["success"]
        assert result["output"]["has_contradictions"] is True
        assert any(c["type"] == "STANCE_CLASH" for c in result["output"]["conflicts"])

class TestKA43CausalInference:
    def test_basic_causality(self, empty_context):
        ka = KA043CausalInference(empty_context)
        result = ka.run(KA043Input(effect="Ground is wet", candidates=["It rained", "Sprinklers were on"]))
        assert result["success"]
        assert result["output"]["likely_cause"] == "It rained"

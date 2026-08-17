"""Deterministic contract tests for Layer 8 quantum-style simulation helpers."""

import numpy as np

from core.simulation.layer8_quantum_computer import (
    FidelityProjectionModule,
    QuantumCollapseSimulator,
    QuantumEntanglementManager,
    SchrodingerConfidenceProcessor,
    SimQOSKernel,
    SimulatedQuantumComputer,
    SuperpositionLogicEngine,
)


def _quantum_context():
    return {
        "simulation_id": "sim-coverage",
        "layer8_escalation": True,
        "confidence_score": 0.4,
        "entropy": 0.6,
        "simulation_pass": 2,
        "beliefs": [
            {"id": "fact", "content": "release architecture policy", "type": "fact", "confidence": 0.9},
            {"content": "release architecture evidence", "type": "analysis", "confidence": 0.8},
            {"id": "reg", "content": "release regulatory evidence", "type": "regulation", "confidence": 0.7},
            {"id": "comp", "content": "release compliance evidence", "type": "compliance", "confidence": 0.6},
        ],
        "goals": [
            {"id": "goal-release", "content": "release architecture evidence policy"},
            {"id": "goal-none", "content": "completely unrelated tokens"},
        ],
        "persona_results": {
            "knowledge": {"confidence": 0.8, "beliefs": []},
            "regulatory": {"confidence": 0.7},
        },
    }


def test_quantum_computer_activation_extraction_and_end_to_end_processing():
    np.random.seed(7)
    computer = SimulatedQuantumComputer(
        {"qubit_register_size": 8, "collapse_iterations": 5, "confidence_threshold": 0.8}
    )

    high_confidence = {"confidence_score": 0.9, "entropy": 0.1, "role_conflicts": 0}
    assert computer.process(high_confidence) is high_confidence
    assert computer._should_activate({"confidence_score": 0.7}) is True
    assert computer._should_activate({"confidence_score": 1, "entropy": 0.5}) is True
    assert computer._should_activate({"confidence_score": 1, "role_conflicts": 2}) is True

    context = _quantum_context()
    result = computer.process(context)

    assert result["quantum_processing_applied"] is True
    assert result["quantum_trust_fidelity"] >= context["confidence_score"]
    assert result["confidence_source"] == "quantum_simulation"
    assert result["collapsed_beliefs"]
    assert result["quantum_entanglement_map"]
    assert result["layer8_processing"]["processed_beliefs"] >= 1
    assert result["processing_time_ms"] >= 0

    persona_beliefs = computer._extract_belief_vectors(
        {"persona_results": {"one": {"beliefs": [{"content": "from persona"}]}}}
    )
    synthesis_beliefs = computer._extract_belief_vectors(
        {"synthesis": {"key_beliefs": [{"content": "from synthesis"}]}}
    )
    assert persona_beliefs[0]["id"] == "b0"
    assert synthesis_beliefs[0]["id"] == "b0"
    assert computer._extract_confidence_scores({"persona_results": {"one": {}}})["personas"] == {}


def test_quantum_computer_internal_branches_and_result_templates():
    np.random.seed(3)
    computer = SimulatedQuantumComputer({"qubit_register_size": 2, "collapse_iterations": 2})
    beliefs = [
        {"id": "a", "content": "shared policy words", "type": "fact", "confidence": 1.0},
        {"id": "b", "content": "shared policy words", "type": "analysis", "confidence": 0.0},
        {"id": "ignored", "content": "over register", "confidence": 0.5},
    ]
    computer._initialize_belief_states(beliefs, {})
    entanglements = computer._create_entanglements(beliefs[:2])
    assert set(entanglements) == {"q0", "q1"}

    no_roles = computer._calculate_fidelity({"confidence_score": 0.5, "entropy": 0.1})
    assert no_roles["qtf"] == 1.0
    collapsed = computer._simulate_collapse(
        {
            "empty": {"qubits": []},
            "zero": {"qubits": ["q1"]},
        },
        {"individual_fidelities": {"q1": 0.0}, "qtf": 0.4},
    )
    assert "empty" not in collapsed
    assert collapsed["zero"]["qubit"] == "q1"

    computer.quantum_register.update(
        {
            "q-fact": {"belief_id": "fact", "type": "fact", "entangled_with": []},
            "q-analysis": {"belief_id": "analysis", "type": "analysis", "entangled_with": []},
            "q-reg": {"belief_id": "reg", "type": "regulation", "entangled_with": []},
            "q-comp": {"belief_id": "comp", "type": "compliance", "entangled_with": []},
            "q-other": {"belief_id": "other", "type": "other", "entangled_with": []},
            "q-low": {"belief_id": "low", "type": "fact", "entangled_with": []},
        }
    )
    collapsed_templates = {
        "g1": {"qubit": "q-fact", "content": "fact", "probability": 0.9},
        "g2": {"qubit": "q-analysis", "content": "analysis", "probability": 0.9},
        "g3": {"qubit": "q-reg", "content": "regulation", "probability": 0.9},
        "g4": {"qubit": "q-comp", "content": "compliance", "probability": 0.9},
        "g5": {"qubit": "q-other", "content": "other", "probability": 0.9},
        "g6": {"qubit": "q-low", "content": "low", "probability": 0.4},
        "g7": {"qubit": "q-fact", "content": "fact", "probability": 0.9},
    }
    generated = computer._generate_results(collapsed_templates, {"qtf": 0.9})
    assert len(generated["quantum_insights"]) == 5
    assert generated["collapsed_beliefs"]["fact"]["supporting_goals"] == ["g1", "g7"]
    unchanged = computer._update_context(
        {"confidence_score": 0.99},
        {
            "quantum_trust_fidelity": 0.5,
            "quantum_insights": [],
            "quantum_summary": "summary",
            "collapsed_beliefs": {},
        },
    )
    assert unchanged["confidence_score"] == 0.99


def test_quantum_helper_components_cover_normalization_and_defaults():
    np.random.seed(11)
    entanglement = QuantumEntanglementManager()
    entanglement.create_entanglement("a", "b", 0.5, "causal")
    assert entanglement.get_entangled_nodes("a")[0]["node"] == "b"
    assert entanglement.get_entangled_nodes("missing") == []
    assert entanglement.propagate_change("a", 0.8) == {"b": 0.4}

    fidelity = FidelityProjectionModule()
    assert fidelity.calculate_qtf({"knowledge": 0.8}, 0.5, 0.9) > 0
    assert fidelity.calculate_qtf({}, 0, 1, {}) == 0
    assert len(fidelity.get_projection_history()) == 2

    processor = SchrodingerConfidenceProcessor()
    assert processor.sample_confidence("missing") == 0.5
    processor.update_distribution("missing", 0.8, 0.2)
    processor.create_distribution("node", 0.7, 0.01)
    sample = processor.sample_confidence("node")
    assert 0 <= sample <= 1
    processor.update_distribution("node", new_mean=0.8)
    processor.update_distribution("node", new_variance=0.02)
    assert processor.confidence_distributions["node"]["mean"] == 0.8
    assert processor.confidence_distributions["node"]["variance"] == 0.02

    collapse = QuantumCollapseSimulator()
    assert collapse.simulate_collapse({"a": 0, "b": 0}, 4)["iterations"] == 4
    assert collapse.simulate_collapse({"a": 1, "b": 3}, 4)["most_probable_state"] in {"a", "b"}
    assert len(collapse.get_collapse_history()) == 2

    superposition = SuperpositionLogicEngine()
    zero_states = [{"id": "a", "probability": 0}, {"id": "b", "probability": 0}]
    superposition.create_superposition("zero", zero_states)
    assert sum(item["probability"] for item in zero_states) == 1
    weighted_states = [{"id": "a", "probability": 1}, {"id": "b", "probability": 3}]
    superposition.create_superposition("weighted", weighted_states)
    assert weighted_states[1]["probability"] == 0.75
    assert superposition.get_superposition("missing") == {}
    assert superposition.collapse_superposition("missing", collapse) == {}
    assert superposition.collapse_superposition("weighted", collapse)["id"] in {"a", "b"}


def test_simqos_kernel_full_operator_contract():
    np.random.seed(13)
    kernel = SimQOSKernel({"decoherence_threshold": 0.1})
    kernel.boot()
    kernel.boot()
    assert kernel.is_running is True
    kernel.qubit_init(4)
    assert len(kernel.quantum_registers) == 4

    assert kernel.fidelity_project({"knowledge": 0.8}, 0.4, 0.9) > 0
    kernel.state_superpose("decision", [{"id": "go", "probability": 0.8}, {"id": "stop", "probability": 0.2}])
    kernel.entangle("go", "policy", 0.5)
    assert kernel.observe("decision")["id"] in {"go", "stop"}
    assert kernel.observe("missing") == {}

    assert kernel.simulate_decoherence([])["is_decoherent"] is False
    assert kernel.simulate_decoherence(
        [{"confidence_score": 0.9, "entropy": 0.1}, {"confidence_score": 0.5, "entropy": 0.4}]
    )["is_decoherent"] is True
    dispatch = kernel.dispatch_to_layer9(
        {"quantum_trust_fidelity": 0.9, "collapsed_beliefs": {"a": {}}}
    )
    assert dispatch["quantum_trust_fidelity"] == 0.9
    assert kernel.get_system_logs()

    kernel.shutdown()
    kernel.shutdown()
    assert kernel.is_running is False

"""Layer entry classification and gatekeeper activation contracts."""

from core.simulation.gatekeeper_agent import GatekeeperAgent
from core.simulation.layer1_entry import Layer1EntryEngine


def test_gatekeeper_defaults_reset_and_range_checks():
    gatekeeper = GatekeeperAgent()
    assert gatekeeper.get_active_layers() == []
    assert gatekeeper.should_halt() is False
    assert gatekeeper.check_layer_conditions({}, 3)["activate"] is False
    assert gatekeeper.check_layer_conditions({}, 11)["activate"] is False

    decision = gatekeeper.evaluate({"confidence_score": 1, "entropy_score": 0})
    assert all(not item["activate"] for item in decision["layer_activations"].values())
    assert gatekeeper.get_decision_log() == gatekeeper.decision_log
    assert gatekeeper.get_decision_log(1) == gatekeeper.decision_log[-1:]
    gatekeeper.reset()
    assert gatekeeper.current_decision == {}
    assert gatekeeper.decision_log == []


def test_gatekeeper_all_trigger_paths_and_parameter_adaptation():
    gatekeeper = GatekeeperAgent()
    context = {
        "simulation_id": "gate-test",
        "simulation_pass": 5,
        "confidence_score": 0.5,
        "entropy_score": 0.8,
        "uncertainty_level": 0.5,
        "historical_confidence": [0.9, 0.8],
        "roles_triggered": [
            "multirole",
            "knowledge_gap",
            "role_conflict",
            "uncertainty",
            "low_cohesion",
            "recursive_contradiction",
            "emergence_indicator",
            "goal_conflict",
            "trust_entropy",
            "convergence_failure",
            "cross_agent_instability",
        ],
        "regulatory_flags": ["validation_needed", "emergence"],
        "high_priority": True,
        "viewpoint_count": 7,
    }
    decision = gatekeeper.evaluate(context)
    assert gatekeeper.should_halt() is True
    assert gatekeeper.get_active_layers() == list(range(4, 11))
    assert decision["layer_activations"]["layer_4"]["triggered_by"] == ["Multiple viewpoints detected"]
    assert "high_uncertainty" in decision["layer_activations"]["layer_5"]["triggered_by"]
    assert "confidence_decay" in decision["layer_activations"]["layer_7"]["triggered_by"]
    assert "high_entropy" in decision["layer_activations"]["layer_7"]["triggered_by"]
    assert "multiple_passes_low_confidence" in decision["layer_activations"]["layer_7"]["triggered_by"]

    layer5 = gatekeeper.get_layer5_integration_parameters(context)
    assert layer5["active"] is True
    assert layer5["verification_cycles"] == 4
    assert layer5["refinement_depth"] == 3
    assert layer5["uncertainty_threshold"] == 0.1

    layer7 = gatekeeper.get_layer7_agi_parameters(context)
    assert layer7["active"] is True
    assert layer7["goal_expansion_depth"] == 4
    assert layer7["conflict_resolution_iterations"] == 7
    assert layer7["goal_convergence_threshold"] == 0.85
    assert layer7["belief_realignment_threshold"] == 0.1
    assert layer7["pov_expansion"] is True
    assert layer7["viewpoint_count"] == 7
    assert layer7["context_metrics"]["confidence_decay"] == 0.4
    assert gatekeeper.check_layer_conditions(context, 7)["activate"] is True


def test_gatekeeper_trigger_reason_fallbacks_and_invalid_layer_key():
    gatekeeper = GatekeeperAgent(
        {
            "layer_5_threshold": 0,
            "layer_7_threshold": 0,
            "layer_8_threshold": 0,
            "layer_10_threshold": 0,
        }
    )
    layer5 = gatekeeper.evaluate({"confidence_score": 1, "roles_triggered": ["role_conflict"]})
    assert layer5["layer_activations"]["layer_5"]["activate"] is True

    layer7 = gatekeeper.evaluate({"confidence_score": 1, "roles_triggered": ["recursive_contradiction"]})
    assert layer7["layer_activations"]["layer_7"]["activate"] is True

    layer8 = gatekeeper.evaluate({"confidence_score": 1, "entropy_score": 0.7})
    assert layer8["layer_activations"]["layer_8"]["triggered_by"] == ["High entropy or trust issues detected"]

    layer10 = gatekeeper.evaluate({"confidence_score": 0.5})
    assert layer10["layer_activations"]["layer_10"]["triggered_by"] == [
        "Very low confidence or emergence indicators"
    ]

    gatekeeper.current_decision["layer_activations"]["bad"] = {"activate": True}
    assert gatekeeper.get_active_layers() == [4, 6, 9, 10]

    fresh = GatekeeperAgent()
    simple5 = fresh.get_layer5_integration_parameters({"confidence_score": 1})
    simple7 = fresh.get_layer7_agi_parameters({"confidence_score": 1, "critical": True})
    assert simple5["active"] is False
    assert simple7["goal_expansion_depth"] == 4
    assert simple7["context_metrics"]["confidence_decay"] == 0


def test_layer1_entry_classifies_axes_pillars_roles_and_stats():
    engine = Layer1EntryEngine()
    query = (
        "How should a defense technology acquisition contract address legal compliance, "
        "risk, ethical AI performance, and learning feedback?"
    )
    result = engine.process({"query": query, "request_id": "one"})

    assert result["request_id"] == "one"
    assert result["layer1_entry"]["layer"] == 1
    assert result["axis_scores"][4] > 0
    assert result["axis_scores"][11] > 0
    assert result["pillar_context"]["primary_pillar"] in {"acquisition", "technology", "defense", "legal"}
    assert result["expert_roles"]
    assert result["layer1_entry"]["knowledge_expansion"]["query_tokens"]
    assert 0 <= result["layer1_entry"]["layer_confidence"] <= 0.95
    assert engine.get_stats()["queries_processed"] == 1


def test_layer1_entry_default_axis_general_pillar_and_expansion_edges():
    engine = Layer1EntryEngine()
    scores = engine._identify_relevant_axes("hello")
    assert scores[3] == 0.4
    assert scores[4] == 0.3
    context = engine._assign_pillar_context("hello", scores)
    assert context["primary_pillar"] == "general"
    assert context["confidence"] == 0.3
    assert engine._assign_expert_roles(context) == []

    expansion = engine._prepare_knowledge_expansion("One Two", {1: 0.5, 2: 0.6, 3: 0.7, 4: 0.8}, context)
    assert expansion["expansion_depth"] == 2
    assert expansion["include_cross_domain"] is True
    assert expansion["query_tokens"] == ["one", "two"]
    assert engine._calculate_layer_confidence({}, {}) == 0.15

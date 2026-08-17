"""Behavioral contracts for Layer 7 AGI support components."""

import pytest

from core.simulation.layer7_agi_system import (
    ConfidenceDriftMonitor,
    EntropyScorer,
    LayerLinkHandler,
    MemoryPatchEngine,
    MultiRoleCoordinator,
    POVExpansionModule,
)


def test_confidence_drift_decay_patterns_and_history():
    monitor = ConfidenceDriftMonitor()
    assert monitor.compute_drift([], [1]) == 0.0
    assert monitor.recursive_confidence_decay([], 1) == 0.0
    assert monitor.recursive_confidence_decay([0.9], 1) == 0.0
    assert monitor.get_historical_drift_pattern()["pattern"] == "insufficient_data"
    assert monitor.compute_drift([0.9], [0.8]) == pytest.approx(0.1)
    assert monitor.compute_drift([0.8], [0.4]) == pytest.approx(0.4)
    assert monitor.compute_drift([0.4], [0.5]) == pytest.approx(0.1)
    assert monitor.recursive_confidence_decay([1.0, 0.8, 0.7], 20) > 0
    assert monitor._is_oscillating([0.1, 0.4, 0.1, 0.4])
    assert monitor._is_diverging([0.1, 0.2, 0.3, 0.4])
    assert monitor.get_historical_drift_pattern()["trend"] in {"increasing", "decreasing", "stable"}


def test_layer_links_feedback_escalation_thresholds_and_history():
    links = LayerLinkHandler()
    for drift, factor in ((0.0, 1.0), (0.2, 1.2), (0.4, 1.5), (0.6, 2.0)):
        assert links.feedback_to_layer6(drift)["adjustment_factor"] == factor
    assert links.feedback_history[0]["suggestions"] == []
    assert len(links.feedback_history[-1]["suggestions"]) == 2
    cases = [
        (0.1, 0.9, "critical"),
        (0.1, 0.7, "high"),
        (0.8, 0.5, "medium"),
        (0.1, 0.2, "low"),
    ]
    for entropy, emergence, priority in cases:
        assert links.escalate_to_layer8(entropy, emergence)["priority"] == priority
    assert len(links.get_feedback_history()) == 4
    assert len(links.get_escalation_history()) == 4


def test_entropy_scores_empty_invalid_normalized_and_history_limits():
    scorer = EntropyScorer()
    assert scorer.compute_goal_entropy([]) == 0.0
    assert scorer.compute_goal_entropy([0, -1]) == 0.0
    assert scorer.compute_goal_entropy([1]) == 0.0
    assert scorer.compute_goal_entropy([0.5, 0.5]) == 1.0
    assert scorer.compute_belief_entropy([]) == 0.0
    belief_entropy = scorer.compute_belief_entropy(
        [{"confidence": 0.1, "realigned": True}, {"confidence": 0.9}]
    )
    assert belief_entropy > 0
    assert scorer.compute_conflict_entropy([]) == 0.0
    conflict_entropy = scorer.compute_conflict_entropy(
        [
            {"resolved": False, "resolution_iterations": 5, "probability": 0.1},
            {"resolved": True, "resolution_iterations": 1, "probability": 0.9},
        ]
    )
    assert conflict_entropy > 0
    for _ in range(12):
        scorer.compute_goal_entropy([0.4, 0.6])
        scorer.compute_belief_entropy([{"confidence": 0.5}])
        scorer.compute_conflict_entropy([{"resolved": False}])
    assert all(len(values) == 10 for values in scorer.recent_scores.values())


def test_multi_role_coordination_default_selected_skip_and_resolution_variants():
    coordinator = MultiRoleCoordinator()
    conflict = {
        "id": "c1",
        "resolved": True,
        "goal_content": "qualify coverage",
        "belief_content": "tests pass",
    }
    results = coordinator.coordinate_roles([conflict, {**conflict, "id": "skip", "resolved": False}], {})
    assert results[0]["success"]
    assert set(results[0]["roles_involved"]) == {"knowledge", "sector", "regulatory", "compliance"}
    selected = coordinator.coordinate_roles([conflict], {"persona_results": {"knowledge": {}, "sector": {}}})
    assert selected[0]["roles_involved"] == ["knowledge", "sector"]
    generic = coordinator._generate_role_resolution("other", conflict, {})
    assert not generic["success"]
    assert not coordinator._determine_final_resolution([])["success"]
    assert coordinator.resolution_history


def test_pov_expansion_real_missing_failing_and_simulated_paths():
    module = POVExpansionModule()
    simulated = module.expand_context(None, {"content": "query"})
    assert simulated["pov_expanded"]
    assert simulated["pov_expanded_content"] == "query"

    class Real:
        def process(self, context): return {**context, "real": True}

    assert module.expand_context(Real(), {"x": 1})["real"]
    assert module.expand_context(object(), {"x": 1})["pov_expanded"]

    class Failing:
        def process(self, _context): raise RuntimeError("failed")

    assert module.expand_context(Failing(), {})["pov_expanded"]
    for _ in range(55):
        module._record_expansion({}, {})
    assert len(module.expansion_history) == 50


def test_memory_patch_engine_initializes_applies_limits_and_tracks_history():
    engine = MemoryPatchEngine()
    context = {"query": "q"}
    assert engine.apply_patches(context, []) is context
    patches = [
        {"type": "add_key_goals", "content": [{"id": "g1", "content": "goal", "probability": 0.8}] * 25},
        {"type": "add_conflict_resolutions", "content": [{"id": "c1", "goal_content": "g", "belief_content": "b", "resolution": "r"}] * 25},
        {"type": "update_beliefs", "content": [{"content": "belief", "original_confidence": 0.4, "confidence": 0.8, "source": "test"}] * 25},
        {"type": "ignored", "content": [1]},
        {"type": "add_key_goals", "content": []},
    ]
    updated = engine.apply_patches(context, patches)
    memory = updated["memory"]["agi_memory"]
    assert len(memory["key_goals"]) == 20
    assert len(memory["conflict_resolutions"]) == 20
    assert len(memory["belief_updates"]) == 20
    assert set(engine.get_patch_history()[0]["patch_types"]) == {
        "add_key_goals",
        "add_conflict_resolutions",
        "update_beliefs",
    }

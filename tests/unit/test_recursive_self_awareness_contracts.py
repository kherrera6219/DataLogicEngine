"""Contracts for recursive processing and final self-monitoring controls."""

import random

import pytest

from core.simulation.layer9_recursive_agi import RecursiveAGICore
from core.simulation.layer10_self_awareness import SelfAwarenessEngine


def _recursive_context():
    return {
        "simulation_id": "recursive-test",
        "query": "Qualify the release architecture",
        "confidence_score": 0.5,
        "quantum_trust_fidelity": 0.6,
        "goals": [
            {"id": "parent", "content": "Release", "probability": 0.6, "depth": 0},
            {"id": "child", "content": "Evidence", "probability": 0.7, "depth": 1},
        ],
        "persona_results": {
            "one": {
                "beliefs": [
                    {"id": "must", "content": "The control must be enabled", "confidence": 0.9}
                ]
            },
            "two": {
                "beliefs": [
                    {"id": "not", "content": "The control should not be enabled", "confidence": 0.4}
                ]
            },
        },
    }


def test_recursive_core_end_to_end_and_threshold_short_circuit():
    random.seed(5)
    core = RecursiveAGICore(
        {"confidence_threshold": 0.99, "max_recursive_passes": 2, "inject_new_personas": True}
    )
    result = core.process(_recursive_context())

    assert result["recursive_passes"] >= 1
    assert result["recursive_confidence_score"] > 0
    assert result["memory_alignments"]
    assert result["contradiction_count"] >= 1
    assert result["planning_trace"]["edges"]
    assert result["persona_results"]
    assert result["recursive_summary"].startswith("[Layer 9 Recursive AGI Summary]")
    assert result["layer9_processing_time_ms"] >= 0
    assert core.get_processing_history()

    short = RecursiveAGICore({"confidence_threshold": 0.9, "max_recursive_passes": 3})
    short_result = short.process({"confidence_score": 1.0})
    assert short_result["recursive_passes"] == 1
    assert short.get_processing_history() == []


def test_recursive_planning_roles_and_injection_exhaustion():
    random.seed(9)
    core = RecursiveAGICore()
    planned = core._apply_recursive_planning(
        {"goals": [{"content": "unnamed"}, {"id": "deep", "content": "deep", "depth": 2}]},
        2,
    )
    assert planned["temporal_scope"] == 2.0
    assert planned["planning_trace"]["nodes"][0]["id"] == "g0"
    assert planned["planning_trace"]["edges"]

    roles = [
        "financial_expert",
        "technology_expert",
        "ethics_expert",
        "legal_expert",
        "data_privacy_expert",
        "risk_management_expert",
        "compliance_officer",
        "industry_analyst",
        "custom_expert",
    ]
    for role in roles:
        assert "Qualify" in core._generate_role_response({"query": "Qualify"}, role)
        beliefs = core._generate_role_beliefs({}, role)
        assert len(beliefs) == 3
        assert all("id" in belief for belief in beliefs)

    core.injected_roles = [
        {"role": role}
        for role in roles
        if role != "custom_expert"
    ]
    original = {"persona_results": {"base": {}}}
    assert core._inject_new_roles(original, 2) is original

    disabled = RecursiveAGICore({"inject_new_personas": False})
    processed = disabled._execute_recursive_pass({"confidence_score": 0.5}, 1)
    assert "persona_results" in processed
    assert disabled.injected_roles == []


def test_recursive_contradiction_resolution_confidence_and_math_edges():
    core = RecursiveAGICore()
    beliefs = [
        {"id": "required", "content": "This is required", "confidence": 0.9, "persona": "a"},
        {"id": "optional", "content": "This is optional", "confidence": 0.2, "persona": "b"},
        {"id": "always", "content": "This is always beneficial", "confidence": 0.1, "persona": "c"},
        {"id": "never", "content": "This is never harmful", "confidence": 0.8, "persona": "d"},
    ]
    contradictions = core._identify_contradictions(beliefs)
    assert len(contradictions) >= 2
    aligned = core._resolve_contradictions([item.copy() for item in beliefs], contradictions)
    assert sum("reconciled_with" in item for item in aligned) >= 2
    assert core._calculate_memory_alignment_score(beliefs, aligned) < 1
    assert core._calculate_memory_alignment_score([], []) == 1

    unchanged = core._resolve_contradictions(
        [item.copy() for item in beliefs],
        [{"belief1_id": "missing", "belief2_id": "also-missing"}],
    )
    assert unchanged == beliefs

    assert core.recursive_confidence_score() == 0
    core.add_recursive_pass(0, 1)
    assert core.recursive_confidence_score() == 0
    core.add_recursive_pass(1, 0.8)
    assert core.recursive_confidence_score() == 0.8
    assert core.entropy_monitor(0.9, 0.1) is True
    assert core.entropy_monitor(0.2, 0.1) is False

    assert core._is_converged(1) is False
    core.confidence_history = [{"updated": 0.8}, {"updated": 0.805}]
    assert core._is_converged(2) is True
    core.confidence_history[-1]["updated"] = 0.9
    assert core._is_converged(2) is False

    high = core._update_confidence({"confidence_score": 0.99, "memory_alignment_score": 1}, 5)
    low = core._update_confidence({"confidence_score": 0.01, "memory_alignment_score": 0}, 1)
    assert high["confidence_score"] == 1
    assert low["confidence_score"] == 0


def _awareness_context():
    return {
        "simulation_id": "aware-test",
        "query": "Release coverage",
        "simulation_pass": 5,
        "confidence_score": 0.4,
        "recursive_passes": 9,
        "entropy": 0.8,
        "prior_entropy": 0.1,
        "rcs_plateau_count": 3,
        "injected_roles": list(range(6)),
        "goals": [{"content": "Coverage goal"}],
        "persona_results": {
            "one": {
                "beliefs": [
                    {"id": "plain", "content": "Plain belief", "confidence": 0.9},
                    {"id": "reinforced", "content": "Stable belief", "confidence": 0.9, "reinforced": True},
                ]
            }
        },
    }


def test_self_awareness_end_to_end_critical_containment():
    engine = SelfAwarenessEngine({"lambda_decay": 0.5})
    result = engine.process(_awareness_context())

    assert result["belief_decay_avg"] > 0.05
    assert result["persona_results"]["one"]["beliefs"][0]["decayed"] is True
    assert result["identity_consistency_score"] == 0
    assert result["layer9_realignment_needed"] is True
    assert result["critical_emergence"] is True
    assert result["limit_recursion"] is True
    assert result["containment_needed"] is True
    assert result["containment_action"] == "halt"
    assert result["human_review_required"] is True
    assert "ACTIVE - HALT" in result["self_awareness_summary"]
    assert result["layer10_processing_time_ms"] >= 0
    assert engine.get_containment_events()
    assert engine.get_emergence_alerts()


def test_self_awareness_identity_growth_helpers_and_inactive_containment():
    engine = SelfAwarenessEngine()
    assert engine.identity_consistency_score(0, 0) == 1
    assert engine.identity_consistency_score(2, 4) == 0.5
    assert engine.belief_decay(1, 1) < 1
    assert engine.belief_decay(1, 1, 0) == 1
    assert 0 < engine.metacognitive_energy_limit(0.2, 0.8) < 1
    assert all(engine.emergence_detection(0.1, 1, 0.1, 3).values())

    assert engine._extract_memory_anchors({}) == set()
    first = engine._track_identity_consistency({"query": "one"})
    second = engine._track_identity_consistency(
        {
            "query": "one",
            "goals": [{"content": "two"}],
            "persona_results": {"p": {"beliefs": [{"content": "three"}, {}]}},
        }
    )
    assert first["identity_consistency_score"] == 0
    assert second["shared_memory_anchors"] == 1
    assert engine._check_persistent_memory({}) is True
    assert engine._check_agent_independence({"injected_roles": []}) is False
    assert engine._check_entropy_drift({"entropy": 0.2}) is False
    assert engine._check_rcs_plateau({}) is False
    assert engine._check_self_replication({}) is False

    inactive = engine._check_containment(
        {
            "identity_consistency_score": 1,
            "entropy": 0,
            "belief_decay_avg": 0.3,
            "critical_emergence": False,
            "limit_recursion": False,
        }
    )
    assert inactive["containment_needed"] is False
    assert inactive["containment_action"] is None
    assert "INACTIVE" in engine._generate_self_awareness_summary(inactive)


def test_self_awareness_disabled_controls_and_empty_beliefs():
    engine = SelfAwarenessEngine(
        {
            "emergence_monitoring": False,
            "metacognitive_limiter": False,
            "containment_protocol": False,
        }
    )
    result = engine.process({"persona_results": {"empty": {}}, "confidence_score": 0.9})
    assert result["belief_decay_avg"] == 0
    assert "emergence_score" not in result
    assert "metacognitive_energy_limit" not in result
    assert "containment_needed" not in result
    assert "Self-Awareness Summary" in result["self_awareness_summary"]

    limited = SelfAwarenessEngine()._apply_metacognitive_limits(
        {"entropy": 0, "confidence_score": 1, "recursive_passes": 0}
    )
    assert limited["limit_recursion"] is False

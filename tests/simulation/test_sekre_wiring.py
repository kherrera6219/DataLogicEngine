"""SEKRE post-L10 wiring tests (N1).

Verifies the Self-Evolving Knowledge Refinement Engine is instantiated by the
live SimulationEngine and invoked on completed runs, with the Tier-3+ gate,
fail-safe behavior, and read-only-by-default semantics.
"""

from unittest.mock import MagicMock

from core.simulation.simulation_engine import SimulationEngine
from core.self_evolving.sekre_engine import SekreEngine


def test_sekre_engine_initialized_by_default():
    engine = SimulationEngine(config={})
    assert isinstance(engine.sekre_engine, SekreEngine)
    assert engine.sekre_enabled is True
    # Read-only by default — auto_improve must be off.
    assert engine.sekre_engine.auto_improve is False


def test_sekre_can_be_disabled_via_config():
    engine = SimulationEngine(config={"simulation": {"enable_sekre": False}})
    assert engine.sekre_enabled is False
    assert engine.sekre_engine is None


def test_qualifies_for_sekre_tier_gate():
    # No tier marker → run (SEKRE self-gates on confidence).
    assert SimulationEngine._qualifies_for_sekre({"context": {}, "params": {}}) is True
    # Explicit low tier → skip.
    assert SimulationEngine._qualifies_for_sekre({"context": {"tier": "trivial"}}) is False
    assert SimulationEngine._qualifies_for_sekre({"context": {"tier": "moderate"}}) is False
    # High tier → run.
    for tier in ("high_stakes", "extreme", "autonomous", "3", "4", "5"):
        assert SimulationEngine._qualifies_for_sekre({"context": {"tier": tier}}) is True
    # Tier in params also honored.
    assert SimulationEngine._qualifies_for_sekre({"params": {"tier": "extreme"}}) is True


def test_run_sekre_analysis_attaches_result_and_increments_stat():
    engine = SimulationEngine(config={})
    engine.sekre_engine = MagicMock()
    engine.sekre_engine.analyze_simulation_results.return_value = {"suggestions": [], "confidence": 0.9}

    sim = {"status": "completed", "context": {"tier": "extreme"}, "passes": []}
    engine._run_sekre_analysis(sim)

    assert sim["sekre_analysis"] == {"suggestions": [], "confidence": 0.9}
    assert engine.stats["sekre_analyses"] == 1
    engine.sekre_engine.analyze_simulation_results.assert_called_once_with(sim)


def test_run_sekre_analysis_skips_incomplete_run():
    engine = SimulationEngine(config={})
    engine.sekre_engine = MagicMock()

    sim = {"status": "started", "context": {"tier": "extreme"}}
    engine._run_sekre_analysis(sim)

    assert "sekre_analysis" not in sim
    engine.sekre_engine.analyze_simulation_results.assert_not_called()


def test_run_sekre_analysis_skips_low_tier():
    engine = SimulationEngine(config={})
    engine.sekre_engine = MagicMock()

    sim = {"status": "completed", "context": {"tier": "trivial"}}
    engine._run_sekre_analysis(sim)

    assert "sekre_analysis" not in sim
    engine.sekre_engine.analyze_simulation_results.assert_not_called()


def test_run_sekre_analysis_is_failsafe():
    engine = SimulationEngine(config={})
    engine.sekre_engine = MagicMock()
    engine.sekre_engine.analyze_simulation_results.side_effect = RuntimeError("boom")

    sim = {"status": "completed", "context": {}, "passes": []}
    # Must not raise.
    engine._run_sekre_analysis(sim)
    assert "sekre_analysis" not in sim


def test_run_sekre_analysis_noop_when_engine_absent():
    engine = SimulationEngine(config={"simulation": {"enable_sekre": False}})
    sim = {"status": "completed", "context": {}}
    engine._run_sekre_analysis(sim)  # no engine → no-op, no crash
    assert "sekre_analysis" not in sim


def test_sekre_analyze_generates_suggestion_on_low_confidence():
    """The real SEKRE produces a suggestion when overall confidence is low."""
    sekre = SekreEngine(config={})
    result = sekre.analyze_simulation_results({
        "simulation_id": "sim-1",
        "query": "complex regulatory question",
        "passes": [],
        "confidence": {"overall": 0.4},  # below default 0.75 threshold
    })
    assert result["suggestions"]
    assert result["suggestions"][0]["type"] == "general_enhancement"

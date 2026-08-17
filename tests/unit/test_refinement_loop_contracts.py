"""Contract coverage for the bounded refinement workflow."""

from unittest.mock import patch

from core.simulation.refinement_loop_handler import RefinementLoopHandler


class StubGatekeeper:
    def __init__(self, halt=False):
        self.halt = halt
        self.inputs = []

    def evaluate(self, context):
        self.inputs.append(context)
        return {"decision": "halt" if self.halt else "continue"}

    def get_active_layers(self):
        return [1, 2]

    def should_halt(self):
        return self.halt


def test_refinement_full_lifecycle_and_lookup():
    gatekeeper = StubGatekeeper()
    handler = RefinementLoopHandler(
        {"max_refinement_passes": 2, "convergence_threshold": 0.99}, gatekeeper=gatekeeper
    )
    started = handler.start_refinement("Qualify release", {"scope": "desktop"})
    simulation_id = started["simulation_id"]
    assert handler.get_simulation(simulation_id)["status"] == "initialized"

    result = handler.run_refinement()

    assert result["status"] == "completed"
    assert result["metrics"]["total_passes"] == 2
    assert result["metrics"]["total_layers_activated"] == 4
    assert result["metrics"]["processing_time"] >= 0
    assert len(result["passes"][0]["refinement_workflow"]["steps_completed"]) == 12
    assert result["passes"][0]["cross_persona_conflicts"]
    assert result["passes"][1]["cross_persona_conflicts"] == []
    assert result["passes"][0]["confidence"]["overall"] > 0
    assert handler.get_simulation(simulation_id) is result
    assert simulation_id not in handler.active_simulations
    assert len(gatekeeper.inputs) == 2


def test_refinement_errors_halt_convergence_and_delay():
    handler = RefinementLoopHandler(gatekeeper=StubGatekeeper())
    assert handler.run_refinement() == {"error": "No simulation ID specified or available"}
    assert handler.run_refinement("missing") == {"error": "Simulation missing not found"}
    assert handler.get_simulation("missing") is None

    halted = RefinementLoopHandler(gatekeeper=StubGatekeeper(halt=True))
    halt_id = halted.start_refinement("halt")["simulation_id"]
    halt_result = halted.run_refinement(halt_id)
    assert halt_result["status"] == "halted"
    assert halt_result["passes"][0]["halt_reason"] == "Entropy threshold exceeded"

    converged = RefinementLoopHandler(
        {"convergence_threshold": 0.5, "max_refinement_passes": 3}, gatekeeper=StubGatekeeper()
    )
    converge_id = converged.start_refinement("converge")["simulation_id"]
    assert converged.run_refinement(converge_id)["status"] == "converged"

    delayed = RefinementLoopHandler(
        {"pass_delay": 0.01, "max_refinement_passes": 2, "convergence_threshold": 1},
        gatekeeper=StubGatekeeper(),
    )
    delay_id = delayed.start_refinement("delay")["simulation_id"]
    with patch("core.simulation.refinement_loop_handler.time.sleep") as sleep:
        delayed.run_refinement(delay_id)
    sleep.assert_called_once_with(0.01)


def test_prepare_pass_context_trend_plateau_and_oscillation_flags():
    handler = RefinementLoopHandler(gatekeeper=StubGatekeeper())
    simulation_id = handler.start_refinement("trend")["simulation_id"]
    simulation = handler.active_simulations[simulation_id]
    first = handler._prepare_pass_context(simulation, 1)
    assert first["previous_passes"] == 0

    simulation["confidence"]["overall"] = 0.4
    simulation["passes"] = [
        {"confidence": {"overall": 0.8}, "roles_triggered": ["prior"], "regulatory_flags": ["flag"]}
    ]
    decreasing = handler._prepare_pass_context(simulation, 2)
    assert "confidence_decreasing" in decreasing["roles_triggered"]
    assert decreasing["regulatory_flags"] == ["flag"]

    simulation["confidence"]["overall"] = 0.51
    simulation["passes"] = [
        {"confidence": {"overall": 0.8}},
        {"confidence": {"overall": 0.5}},
    ]
    plateau = handler._prepare_pass_context(simulation, 3)
    assert "confidence_plateau" in plateau["roles_triggered"]
    assert "confidence_oscillation" in plateau["roles_triggered"]


def test_refinement_workflow_error_and_invalid_timestamp_are_fail_closed():
    handler = RefinementLoopHandler(gatekeeper=StubGatekeeper())
    simulation_id = handler.start_refinement("error")["simulation_id"]
    context = handler._prepare_pass_context(handler.active_simulations[simulation_id], 1)

    def fail(_context):
        raise RuntimeError("step failed")

    handler.workflow_steps = [handler._initial_analysis, fail, handler._final_synthesis]
    context["start_time"] = "not-a-time"
    result = handler._execute_refinement_workflow(context)
    assert result["status"] == "error"
    assert result["processing_time"] == 0
    assert result["refinement_workflow"]["step_results"]["fail"] == {
        "error": "step failed",
        "status": "failed",
    }


def test_refinement_step_edge_branches():
    handler = RefinementLoopHandler(gatekeeper=StubGatekeeper())
    simulation_id = handler.start_refinement("edges")["simulation_id"]
    context = handler._prepare_pass_context(handler.active_simulations[simulation_id], 2)

    handler._initial_analysis(context)
    handler._knowledge_processing(context)
    handler._sector_processing(context)
    handler._regulatory_processing(context)
    handler._compliance_processing(context)
    cross = handler._cross_persona_analysis(context)
    assert cross["conflicts_detected"] == []
    assert cross["harmony_score"] == 0.8
    assert handler._conflict_resolution(context)["confidence_adjustment"] == 0
    assert handler._confidence_assessment(context)["confidence_factors"]["conflict_resolution"] == 0.9

    context["previous_confidence"] = context["confidence"]["overall"]
    determination = handler._refinement_determination(context)
    assert determination["diminishing_returns"] is True
    assert determination["recommendation"] == "stop"
    assert handler._fact_verification(context)["confidence_adjustment"] == 0.02

    context["confidence"]["overall"] = 1.0
    context["cross_persona_conflicts"] = [{"id": str(i)} for i in range(10)]
    assessment = handler._confidence_assessment(context)
    assert assessment["entropy"] <= 1
    assert assessment["confidence_factors"]["conflict_resolution"] == 0.7
    assert handler._final_synthesis(context)["final_confidence"] == context["confidence"]["overall"]

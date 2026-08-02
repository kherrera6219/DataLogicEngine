"""CP19-K owning-path proof for canonical simulation algorithms."""

from __future__ import annotations

import pytest

from backend.governed_execution.extended_subsystems import (
    ExtendedSubsystemCoordinator,
)
from backend.simulation.contracts import SimulationDepth, SimulationScenario


@pytest.fixture(scope="module")
def simulation_owning_path():
    coordinator = ExtendedSubsystemCoordinator()
    scenario = SimulationScenario(
        query="Evaluate a bounded capacity counterfactual.",
        context={
            "counterfactual": {
                "baseline": {"capacity": 10, "latency": 100},
                "change": {"capacity": 20},
                "relationships": {"capacity": {"latency": -2}},
                "graph": {"capacity": {"latency": 0.5}},
            }
        },
        depth=SimulationDepth.QUICK,
        execution_mode="fixed_seed_local",
    )
    planning = coordinator.plan_simulation(
        simulation_id="simulation-cp19k-3",
        principal_id="owner-1",
        scenario=scenario,
    )
    counterfactual = coordinator.plan_simulation_counterfactual(
        simulation_id="simulation-cp19k-3",
        principal_id="owner-1",
        scenario=scenario,
    )
    outcome = coordinator.plan_simulation_outcome(
        simulation_id="simulation-cp19k-3",
        principal_id="owner-1",
        status="completed",
        summary="Bounded capacity counterfactual completed.",
        significance=0.9,
    )
    return coordinator, scenario, planning, counterfactual, outcome


def _output(execution, canonical_id: str) -> dict:
    return dict(execution.results[canonical_id].get("output") or {})


def _assert_complete_trace(execution, canonical_id: str) -> None:
    events = execution.report.traces[canonical_id].events
    required = [
        "planned",
        "candidate",
        "selected",
        "admitted",
        "executing",
        "executed",
    ]
    states = [event.state.value for event in events]
    assert [state for state in states if state in required] == required
    executed = next(event for event in events if event.state.value == "executed")
    assert executed.result_trace_id


def test_ka_032_owning_path(simulation_owning_path):
    coordinator, scenario, planning, _, _ = simulation_owning_path
    allowed, blockers = coordinator.simulation_plan_allowed(
        planning,
        scenario=scenario,
    )
    output = _output(planning, "KA-032")
    receipt = coordinator.bind_effect_receipt(
        service="SimulationJobRunner",
        operation="admit_simulation_plan",
        resource_id="simulation-cp19k-3",
        request_payload=scenario.plan.to_dict(),
        result_payload={"status": "running"},
        idempotency_key="simulation-cp19k-3:admission",
        ka_execution=planning,
        proposal_ids=["simulation-cp19k-3:plan"],
    )

    assert allowed is True
    assert blockers == []
    assert output["final_status"] == "COMPLETED"
    assert receipt.status == "applied"
    assert receipt.ka_plan_id == planning.plan.plan_id
    _assert_complete_trace(planning, "KA-032")


def test_ka_037_owning_path(simulation_owning_path):
    coordinator, scenario, planning, _, _ = simulation_owning_path
    limits = coordinator.simulation_resource_limits(
        planning,
        scenario=scenario,
    )
    output = _output(planning, "KA-037")

    assert limits["max_total_tokens"] == output["token_budget"]
    assert scenario.plan.max_output_tokens <= limits["max_total_tokens"]
    assert limits["max_total_tokens"] < scenario.max_total_tokens
    assert limits["execution_queue"] == output["execution_queue"]
    _assert_complete_trace(planning, "KA-037")


def test_ka_042_owning_path(simulation_owning_path):
    coordinator, _, _, counterfactual, _ = simulation_owning_path
    context = coordinator.simulation_counterfactual_context(counterfactual)
    output = _output(counterfactual, "KA-042")

    assert context["local_projection"] == output
    assert output["projected_state"] == {"capacity": 20, "latency": 80.0}
    assert context["ka_lifecycle"]["owner"] == "simulation"
    _assert_complete_trace(counterfactual, "KA-042")


def test_ka_070_owning_path(simulation_owning_path):
    coordinator, scenario, _, counterfactual, _ = simulation_owning_path
    context = coordinator.simulation_counterfactual_context(counterfactual)
    output = _output(counterfactual, "KA-070")
    receipt = coordinator.bind_effect_receipt(
        service="SimulationJobRunner",
        operation="apply_counterfactual_context",
        resource_id="simulation-cp19k-3",
        request_payload={"query": scenario.query},
        result_payload=context,
        idempotency_key="simulation-cp19k-3:counterfactual",
        ka_execution=counterfactual,
        proposal_ids=["simulation-cp19k-3:counterfactual"],
    )

    assert context["graph_projection"] == output
    assert output["local_projection_consumed"] is True
    assert output["simulated_outcomes"][0]["changed_node"] == "capacity"
    assert receipt.ka_plan_id == counterfactual.plan.plan_id
    _assert_complete_trace(counterfactual, "KA-070")


def test_ka_1080_owning_path(simulation_owning_path):
    _, scenario, planning, _, _ = simulation_owning_path
    estimate = _output(planning, "KA-1080")["estimate"]
    admission = _output(planning, "KA-1081")

    assert estimate["tokens"] == scenario.plan.max_output_tokens
    assert estimate["step_count"] == scenario.plan.max_provider_calls
    assert admission["estimate_source"] == "KA-1080_dependency"
    _assert_complete_trace(planning, "KA-1080")


def test_ka_1081_owning_path(simulation_owning_path):
    coordinator, scenario, planning, _, _ = simulation_owning_path
    allowed, blockers = coordinator.simulation_plan_allowed(
        planning,
        scenario=scenario,
    )
    output = _output(planning, "KA-1081")

    assert allowed is True
    assert blockers == []
    assert output["allowed"] is True
    assert output["violations"] == []
    assert output["estimate_source"] == "KA-1080_dependency"
    _assert_complete_trace(planning, "KA-1081")


def test_ka_1091_owning_path(simulation_owning_path):
    coordinator, _, _, _, outcome = simulation_owning_path
    output = _output(outcome, "KA-1091")
    receipt = coordinator.bind_effect_receipt(
        service="SimulationJobRunner",
        operation="persist_simulation_artifacts",
        resource_id="simulation-cp19k-3",
        request_payload={"scenario_revision": "a" * 64},
        result_payload={"artifacts": ["result", "transcript"]},
        idempotency_key="simulation-cp19k-3:artifacts",
        ka_execution=outcome,
        proposal_ids=["simulation-cp19k-3:result"],
    )

    assert output["archive_count"] == 1
    assert output["artifacts_written"] == 0
    assert receipt.ka_plan_id == outcome.plan.plan_id
    assert receipt.ka_proposal_ids == ["simulation-cp19k-3:result"]
    _assert_complete_trace(outcome, "KA-1091")

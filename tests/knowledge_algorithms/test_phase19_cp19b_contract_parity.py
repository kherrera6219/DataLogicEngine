"""CP19-B real-controller and production-caller contract regressions."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from backend.knowledge_algorithms.consumer import execute_required_ka
from backend.knowledge_algorithms.contracts import (
    KAExecutionContractError,
    KAExecutionError,
    KAExecutionResult,
    KAExecutionState,
    KAFailureCode,
    KAOutcomeType,
)
from backend.knowledge_algorithms.ka_master_controller import (
    KAMasterController,
)
from backend.truth_engine.truth_core.emergence_controller import (
    EmergenceDetectionController,
)
from backend.truth_engine.truth_core.l10_schemas import (
    L10Decision,
    L10Input,
)
from backend.truth_engine.truth_core.l9_schemas import L9Decision, L9Input
from backend.truth_engine.truth_core.meta_reasoning_controller import (
    MetaReasoningController,
)
from core.engine.ka_engine import KAEngine
from core.knowledge_algorithm.ka_loader import KALoader
from core.simulation.pov_engine import POVEngine
from core.simulation.simulation_engine import SimulationEngine
from scripts.verify_ka_contract_parity import verify as verify_contract_parity

REPO_ROOT = Path(__file__).resolve().parents[2]


def _failed_result() -> KAExecutionResult:
    return KAExecutionResult(
        canonical_id="KA-004",
        ka_version="1.0.0",
        manifest_version="test",
        state=KAExecutionState.INVALID,
        outcome_type=KAOutcomeType.INVALID_INPUT,
        success=False,
        error=KAExecutionError(
            code=KAFailureCode.INVALID_INPUT,
            message="invalid test input",
        ),
        request_id="request-test",
        run_id="run-test",
        trace_id="trace-test",
    )


def test_required_consumer_rejects_legacy_and_failed_results():
    class LegacyOnly:
        @staticmethod
        def execute_algorithm(ka_id, payload):
            return {"success": True, "output": {}}

    class FailedTyped:
        @staticmethod
        def execute_typed(ka_id, payload):
            return _failed_result()

    with pytest.raises(TypeError, match="execute_typed"):
        execute_required_ka(LegacyOnly(), "KA-004", {"query": "test"})
    with pytest.raises(KAExecutionContractError, match="KA_INVALID_INPUT"):
        execute_required_ka(FailedTyped(), "KA-004", {"query": "test"})


def test_compatibility_facades_offer_canonical_typed_results():
    engine_result = KAEngine().execute_typed("KA-004", {"query": "validate"})
    loader_result = KALoader().execute_typed(
        "KA-004",
        {"query": "validate"},
    )

    assert engine_result.require_output()["is_valid"] is True
    assert loader_result.require_output()["is_valid"] is True
    assert engine_result.schema_version == "dle.ka-execution-result.v1"
    assert loader_result.schema_version == "dle.ka-execution-result.v1"


def test_real_controller_layer9_consumes_actual_canonical_outputs():
    controller = KAMasterController({})
    result = MetaReasoningController(controller).evaluate(
        L9Input(
            simulation_id="cp19-b-l9",
            problem_spec={
                "original_query": "How should this deployment be validated?"
            },
            l8_gate_result={
                "overall_confidence": 0.98,
                "domain_confidences": [
                    {"domain": "operations", "confidence": 0.99}
                ],
                "quantum_summary": (
                    "Validate the deployment with bounded tests."
                ),
            },
            reasoning_trace={
                f"layer{number}": {"output": "ok"}
                for number in range(1, 9)
            },
            risk_domain="standard",
        )
    )

    assert result.decision == L9Decision.FINALIZE
    assert {
        "KA-008",
        "KA-010",
        "KA-022",
        "KA-025",
    }.issubset(result.kas_invoked)
    assert not result.disclosure_flags


def test_real_controller_layer10_uses_corrected_canonical_identities():
    controller = KAMasterController({})
    result = EmergenceDetectionController(controller).authorize(
        L10Input(
            simulation_id="cp19-b-l10",
            problem_spec={"original_query": "Provide a safe answer"},
            l9_result={
                "readiness_score": 0.99,
                "epistemic_report": {
                    "current_output": (
                        "Use a staged and validated deployment."
                    )
                },
            },
            risk_domain="standard",
            reasoning_trace={"steps": ["L1", "L9"]},
        )
    )

    assert result.decision == L10Decision.RELEASE
    assert {
        "KA-1108",
        "KA-1109",
        "KA-1079",
        *EmergenceDetectionController.L10_KAS,
    }.issubset(result.kas_invoked)
    assert {"KA-108", "KA-109", "KA-079"}.isdisjoint(
        result.kas_invoked
    )


def test_real_simulation_consumers_read_typed_outputs():
    ka_engine = KAEngine()
    simulation_engine = SimulationEngine(
        config={"simulation": {"enable_sekre": False}},
        ka_engine=ka_engine,
    )
    simulation = {
        "simulation_id": "cp19-b-simulation",
        "query": "Validate a secure deployment",
        "context": {},
    }
    pass_record = {}

    simulation_engine._run_routing_step(simulation, pass_record)
    component = simulation_engine._run_component_simulation(
        "knowledge",
        "job_role",
        simulation["query"],
        {},
        simulation["simulation_id"],
        1,
    )

    assert pass_record["routing"]["complexity"]["complexity_tier"]
    assert pass_record["routing"]["pipeline"]
    assert component["status"] == "completed"
    assert component["ka_id"] == "KA-012"
    assert component["ka_execution_id"]
    assert component["confidence"] == 0.0


def test_real_pov_consumers_read_named_canonical_outputs():
    engine = POVEngine(
        config={"confidence_threshold": 0.0},
        ka_controller=KAMasterController({}),
    )
    result = engine.expand_context(
        "Validate a secure deployment",
        {
            "simulation_id": "cp19-b-pov",
            "initial_data": [],
        },
    )

    assert len(result["ka028_perspectives"]) == 2
    assert result["emotional_context"]["persona_applied"] == "general"
    assert result["pov_stats"]["passes"] == 1


def test_production_callers_do_not_invoke_legacy_result_methods():
    forbidden = re.compile(
        r"\.(?:execute_algorithm|execute_legacy|execute_ka)\s*\("
    )
    findings = []
    for source_root in ("backend", "core"):
        for path in (REPO_ROOT / source_root).rglob("*.py"):
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(),
                start=1,
            ):
                if forbidden.search(line):
                    findings.append(
                        f"{path.relative_to(REPO_ROOT)}:{line_number}"
                    )

    assert findings == []


def test_contract_parity_verifier_accepts_governed_plan_execution_boundary():
    evidence = verify_contract_parity()

    assert evidence["status"] == "pass", evidence["errors"]
    assert evidence["caller_status"]["api"]["typed_boundary_present"] is True

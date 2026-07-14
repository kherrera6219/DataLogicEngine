"""Explicit validators for simulation results and confidence reporting."""

from __future__ import annotations

from typing import Any

from backend.simulation.contracts import SimulationScenario


def validate_simulation_result(
    *,
    scenario: SimulationScenario,
    result: dict[str, Any],
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return measured confidence only when source evidence is verified."""

    events = [item for item in result.get("events") or [] if isinstance(item, dict)]
    observed_agents = {
        str(item.get("agent"))
        for item in events
        if str(item.get("action")) == "ARGUE"
    }
    required_agents = set(scenario.plan.participants)
    usage = result.get("budget") or {}
    provider_calls = int(usage.get("provider_calls_used") or 0)
    validators = [
        {
            "id": "required_participant_coverage",
            "status": "passed" if required_agents <= observed_agents else "failed",
        },
        {
            "id": "bounded_provider_calls",
            "status": (
                "passed"
                if 0 < provider_calls <= scenario.plan.max_provider_calls
                else "failed"
            ),
        },
        {
            "id": "nonempty_synthesis",
            "status": "passed" if str(result.get("final_conclusion") or "").strip() else "failed",
        },
    ]
    requested = set(scenario.input_corpus)
    verified = {
        str(item.get("source_uid"))
        for item in evidence
        if item.get("validation_state") == "verified"
    }
    evidence_ready = bool(requested) and requested <= verified
    validators.append(
        {
            "id": "source_evidence_verified",
            "status": "passed" if evidence_ready else "not_measured",
            "verified": len(requested & verified),
            "required": len(requested),
        }
    )
    structural_passed = all(
        item["status"] == "passed" for item in validators[:3]
    )
    if scenario.execution_mode == "fixed_seed_local":
        return {
            "status": "qualification_only",
            "confidence_score": None,
            "formula_version": "simulation-evidence-coverage.v1",
            "reason": "fixed_seed_output_is_not_external_evidence",
            "validators": validators,
        }
    if not evidence_ready:
        return {
            "status": "insufficient_evidence",
            "confidence_score": None,
            "formula_version": "simulation-evidence-coverage.v1",
            "reason": "verified_input_corpus_required",
            "validators": validators,
        }
    confidence = 1.0 if structural_passed else 0.0
    return {
        "status": "measured",
        "confidence_score": confidence,
        "formula_version": "simulation-evidence-coverage.v1",
        "reason": "all_declared_validators_evaluated",
        "explanation": (
            "Coverage of declared structural validators and verified cited evidence; "
            "not a probability that the conclusion is correct."
        ),
        "validators": validators,
    }

"""Fail-closed security controls for product Layer 8 (TruthGate candidate trust).

These controls were absorbed from TrustValidationGateway so the single product
L8 authority (GovernedTenLayerStages.l8) is the more secure path:

- optional enhanced model screening (TRUTH_GATE_ENHANCED_SCREENING)
- OPA/Rego policy evaluation with deterministic Python fallback

Both are fail-closed on evaluation errors.
"""

from __future__ import annotations

from typing import Any


def evaluate_model_screening(
    text: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Screen candidate text; errors block (fail-closed)."""
    try:
        from backend.truth_engine.truth_gate.model_screening import (
            TruthGateModelScreening,
        )

        return TruthGateModelScreening().screen(text or "", metadata=metadata or {})
    except Exception as exc:  # noqa: BLE001 - security boundary
        return {
            "enabled": False,
            "allowed": False,
            "risks": ["model_screening_error"],
            "action": "block",
            "backend": "error",
            "error": str(exc),
        }


def evaluate_opa_policy(
    *,
    risk_domain: str,
    overall_confidence: float,
    minimum_confidence: float,
    axis_17_requires_human: bool = False,
    human_reviewed: bool = False,
    simulation_id: str | None = None,
) -> dict[str, Any]:
    """Evaluate TruthGate OPA policy; errors deny (fail-closed)."""
    try:
        from backend.truth_engine.truth_gate.opa_policy import OPAPolicyEvaluator

        return OPAPolicyEvaluator().evaluate(
            {
                "simulation_id": simulation_id or "governed-l8",
                "risk_domain": risk_domain or "standard",
                "overall_confidence": float(overall_confidence),
                "minimum_confidence": float(minimum_confidence),
                "status": "pass",
                "axis_17_requires_human": bool(axis_17_requires_human),
                "human_reviewed": bool(human_reviewed),
            }
        )
    except Exception as exc:  # noqa: BLE001 - security boundary
        return {
            "available": False,
            "backend": "error",
            "allow": False,
            "violations": ["opa_evaluation_error"],
            "error": str(exc),
        }


def risk_domain_threshold(risk_domain: str) -> float:
    """Domain thresholds aligned with TrustValidationGateway RISK_THRESHOLDS."""
    thresholds = {
        "standard": 0.95,
        "healthcare": 0.995,
        "finance": 0.995,
        "legal": 0.995,
        "safety": 0.995,
        "high": 0.995,
        "critical": 0.995,
        "high_risk": 0.995,
    }
    return thresholds.get(str(risk_domain or "standard").lower(), 0.95)

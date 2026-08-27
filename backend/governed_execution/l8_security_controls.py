"""Fail-closed security controls for product Layer 8 (TruthGate candidate trust).

These controls were absorbed from TrustValidationGateway so the single product
L8 authority (GovernedTenLayerStages.l8) is the more secure path:

- optional enhanced model screening (TRUTH_GATE_ENHANCED_SCREENING)
- OPA/Rego policy evaluation with deterministic Python fallback

Both are fail-closed on evaluation errors.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.truth_engine.truth_gate.model_screening import TruthGateModelScreening
from backend.truth_engine.truth_gate.opa_policy import OPAPolicyEvaluator

logger = logging.getLogger(__name__)


def evaluate_model_screening(
    text: str,
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Screen candidate text; errors block (fail-closed)."""
    try:
        return TruthGateModelScreening().screen(text or "", metadata=metadata or {})
    except Exception:  # noqa: BLE001 - CU-2 fail-closed boundary; see tests/governed_execution/test_l8_security_controls.py
        logger.exception("Layer 8 model screening failed closed")
        return {
            "enabled": False,
            "allowed": False,
            "risks": ["model_screening_error"],
            "action": "block",
            "backend": "error",
            "error": "model_screening_failed",
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
    except Exception:  # noqa: BLE001 - CU-2 fail-closed boundary; see tests/governed_execution/test_l8_security_controls.py
        logger.exception("Layer 8 OPA policy evaluation failed closed")
        return {
            "available": False,
            "backend": "error",
            "allow": False,
            "violations": ["opa_evaluation_error"],
            "error": "opa_evaluation_failed",
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

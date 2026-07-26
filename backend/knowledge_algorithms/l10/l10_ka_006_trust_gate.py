"""L10-KA-006: terminal trust gate with belief decay."""

from __future__ import annotations

from typing import Any

BELIEF_DECAY_FACTOR = 0.98


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    confidence_value = inputs.get("confidence", inputs.get("readiness_score"))
    threshold = float(inputs.get("threshold", 0.95) or 0.95)
    decay = float(
        inputs.get("decay_factor", BELIEF_DECAY_FACTOR) or BELIEF_DECAY_FACTOR
    )
    allow_not_measured = bool(inputs.get("allow_not_measured"))
    if not 0.0 <= threshold <= 1.0 or not 0.0 <= decay <= 1.0:
        raise ValueError("threshold and decay_factor must be between 0 and 1")
    if confidence_value is None:
        return {
            "success": True,
            "original_confidence": None,
            "decayed_confidence": None,
            "decay_factor": decay,
            "threshold": threshold,
            "status": "not_measured",
            "passed": allow_not_measured,
            "limitation": "No measured confidence was supplied.",
        }
    confidence = float(confidence_value)
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0 and 1")
    decayed = round(confidence * decay, 6)
    return {
        "success": True,
        "original_confidence": confidence,
        "decayed_confidence": decayed,
        "decay_factor": decay,
        "threshold": threshold,
        "status": "pass" if decayed >= threshold else "fail",
        "passed": decayed >= threshold,
    }

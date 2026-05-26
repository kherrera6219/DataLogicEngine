"""L10-KA-006: terminal trust gate with belief decay."""

from __future__ import annotations

from typing import Any

BELIEF_DECAY_FACTOR = 0.98


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    confidence = float(inputs.get("confidence", inputs.get("readiness_score", 1.0)) or 0.0)
    threshold = float(inputs.get("threshold", 0.95) or 0.95)
    decay = float(inputs.get("decay_factor", BELIEF_DECAY_FACTOR) or BELIEF_DECAY_FACTOR)
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

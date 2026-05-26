"""L10-KA-005: final containment decision engine."""

from __future__ import annotations

from typing import Any

from backend.knowledge_algorithms.l10.common import severity_rank


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    violations = inputs.get("violations") or inputs.get("safety_violations") or []
    confidence = float(inputs.get("confidence", inputs.get("decayed_confidence", 1.0)) or 0.0)
    emergence = inputs.get("emergence_detected", False)
    max_severity = max([severity_rank(v.get("severity", "info")) for v in violations], default=0)

    if max_severity >= 3 or (emergence and confidence < 0.80):
        decision = "HALT"
    elif max_severity >= 2 or confidence < 0.90:
        decision = "ESCALATE"
    elif max_severity == 1:
        decision = "MODIFY"
    else:
        decision = "RELEASE"
    return {
        "success": True,
        "decision": decision,
        "requires_human_signoff": decision in {"HALT", "ESCALATE"},
        "max_violation_severity": max_severity,
    }

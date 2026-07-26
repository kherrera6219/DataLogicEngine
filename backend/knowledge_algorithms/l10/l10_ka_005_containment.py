"""L10-KA-005: final containment decision engine."""

from __future__ import annotations

from typing import Any

from backend.knowledge_algorithms.l10.common import severity_rank


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    dependency_results = inputs.get("dependency_results") or {}
    ethics = dependency_results.get("L10-KA-004") or {}
    privacy = dependency_results.get("L10-KA-003") or {}
    awareness = dependency_results.get("L10-KA-002") or {}
    trust = dependency_results.get("L10-KA-006") or {}
    escalation = dependency_results.get("L10-KA-007") or {}
    violations = (
        inputs.get("violations")
        or inputs.get("safety_violations")
        or ethics.get("violations")
        or []
    )
    final_action = str(inputs.get("final_action") or "finalize").lower()
    confidence_value = inputs.get("confidence")
    if confidence_value is None:
        confidence_value = trust.get("decayed_confidence")
    confidence = float(confidence_value) if confidence_value is not None else None
    emergence = bool(
        inputs.get("emergence_detected")
        or awareness.get("level") in {"moderate", "high", "critical"}
    )
    max_severity = max(
        [severity_rank(v.get("severity", "info")) for v in violations], default=0
    )
    pii_found = int(privacy.get("redactions_found") or 0) > 0
    trust_passed = trust.get("passed")
    escalation_required = bool(escalation.get("escalation_required"))

    if final_action in {"abstain", "local_review"} and max_severity < 3:
        decision = "MODIFY" if pii_found else "RELEASE"
    elif trust_passed is not True:
        decision = "ESCALATE"
    elif max_severity >= 3 or (
        emergence and confidence is not None and confidence < 0.80
    ):
        decision = "HALT"
    elif (
        escalation_required
        or max_severity >= 2
        or (confidence is not None and confidence < 0.90)
    ):
        decision = "ESCALATE"
    elif pii_found or max_severity == 1:
        decision = "MODIFY"
    else:
        decision = "RELEASE"
    return {
        "success": True,
        "decision": decision,
        "requires_human_signoff": decision in {"HALT", "ESCALATE"},
        "max_violation_severity": max_severity,
        "confidence_measured": confidence is not None,
        "pii_redaction_required": pii_found,
        "release_authorized": decision in {"RELEASE", "MODIFY"},
    }

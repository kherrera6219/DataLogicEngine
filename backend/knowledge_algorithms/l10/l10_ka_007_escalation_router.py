"""L10-KA-007: deterministic human-review escalation proposal."""

from __future__ import annotations

import hashlib
from typing import Any

HIGH_TOUCH_DOMAINS = {"healthcare", "finance", "legal", "high_risk", "regulated"}


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    dependency_results = inputs.get("dependency_results") or {}
    trust = dependency_results.get("L10-KA-006") or {}
    ethics = dependency_results.get("L10-KA-004") or {}
    domain = str(
        inputs.get("risk_domain") or inputs.get("domain") or "standard"
    ).lower()
    confidence_value = inputs.get("confidence", inputs.get("decayed_confidence"))
    if confidence_value is None:
        confidence_value = trust.get("decayed_confidence")
    confidence = float(confidence_value) if confidence_value is not None else None
    violations = inputs.get("violations") or ethics.get("violations") or []
    consequential = bool(inputs.get("consequential_decision"))
    should_escalate = (
        bool(violations)
        or (confidence is None and not inputs.get("allow_not_measured"))
        or (confidence is not None and confidence < 0.90)
        or (domain in HIGH_TOUCH_DOMAINS and consequential)
    )
    proposal = None
    if should_escalate:
        stable_source = "|".join(
            [
                str(inputs.get("request_id") or "unknown"),
                domain,
                str(confidence),
                str(len(violations)),
            ]
        )
        proposal = {
            "proposal_id": (
                "hitl_" + hashlib.sha256(stable_source.encode()).hexdigest()[:12]
            ),
            "queue": "human_review",
            "risk_domain": domain,
            "reason": inputs.get("reason") or "Layer 10 escalation policy",
            "applied": False,
        }
    return {
        "success": True,
        "escalation_required": should_escalate,
        "review_proposal": proposal,
        "reviews_dispatched": 0,
        "deterministic": True,
    }

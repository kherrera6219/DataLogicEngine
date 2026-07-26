"""L10-KA-004: ethical alignment and EU AI Act risk mapping."""

from __future__ import annotations

import re
from typing import Any

from backend.knowledge_algorithms.l10.common import text_from_inputs

RULES = [
    (
        "manipulation",
        "critical",
        re.compile(r"\bmanipulate|deceive|coerce\b", re.IGNORECASE),
    ),
    (
        "illegal_discrimination",
        "critical",
        re.compile(r"\bdiscriminat(?:e|ion)|protected class\b", re.IGNORECASE),
    ),
    (
        "unsafe_medical_or_legal",
        "major",
        re.compile(
            r"\bguaranteed diagnosis|ignore a lawyer|ignore a doctor\b", re.IGNORECASE
        ),
    ),
    (
        "unethical_request",
        "major",
        re.compile(r"\bunethical|evade compliance|hide evidence\b", re.IGNORECASE),
    ),
]


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    content = text_from_inputs(inputs)
    violations = []
    for violation_type, severity, pattern in RULES:
        if pattern.search(content):
            violations.append(
                {
                    "type": violation_type,
                    "severity": severity,
                    "message": f"Detected {violation_type.replace('_', ' ')} indicator.",
                }
            )
    tier = "minimal"
    if any(v["severity"] == "critical" for v in violations):
        tier = "unacceptable"
    elif violations:
        tier = "high"
    return {
        "success": True,
        "ethical_score": max(0.0, 1.0 - (0.35 * len(violations))),
        "eu_ai_act_tier": tier,
        "violations": violations,
        "passed": not violations,
    }

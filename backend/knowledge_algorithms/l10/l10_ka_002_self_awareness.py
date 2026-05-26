"""L10-KA-002: self-awareness and capability escalation monitor."""

from __future__ import annotations

import re
from typing import Any

from backend.knowledge_algorithms.l10.common import text_from_inputs

PATTERNS = {
    "self_reference": re.compile(r"\b(i am|i'm|my (?:instructions|weights|model|system prompt))\b", re.I),
    "capability_escalation": re.compile(r"\b(self[- ]?improv|recursive autonomy|modify my own|escape|bypass)\b", re.I),
    "authority_claim": re.compile(r"\b(i can guarantee|i have unrestricted|i am authorized)\b", re.I),
}


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    content = text_from_inputs(inputs)
    matches = [
        {"type": name, "match": match.group(0)}
        for name, pattern in PATTERNS.items()
        for match in pattern.finditer(content)
    ]
    return {
        "success": True,
        "awareness_detected": bool(matches),
        "level": "moderate" if any(m["type"] == "capability_escalation" for m in matches) else ("low" if matches else "none"),
        "escalation_patterns": matches,
    }

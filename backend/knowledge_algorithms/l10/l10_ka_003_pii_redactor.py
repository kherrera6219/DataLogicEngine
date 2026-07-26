"""L10-KA-003: pure-Python PII redactor."""

from __future__ import annotations

import re
from typing import Any

from backend.knowledge_algorithms.l10.common import text_from_inputs

PII_PATTERNS = {
    "EMAIL": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "PHONE": re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "IP_ADDRESS": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    content = text_from_inputs(inputs)
    redacted = content
    redactions = []
    for pii_type, pattern in PII_PATTERNS.items():
        matches = list(pattern.finditer(redacted))
        if not matches:
            continue
        redactions.append({"type": pii_type, "count": len(matches)})
        redacted = pattern.sub(f"[REDACTED_{pii_type}]", redacted)
    return {
        "success": True,
        "secure": not redactions,
        "redactions_found": len(redactions),
        "redactions": redactions,
        "redacted_content": redacted,
        "passed": not redactions,
        "sensitive_values_returned": False,
    }

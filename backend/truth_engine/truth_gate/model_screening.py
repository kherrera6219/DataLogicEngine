"""Optional enhanced model screening for TruthGate."""

from __future__ import annotations

import os
import re
from typing import Any


class TruthGateModelScreening:
    """Graceful no-op unless TRUTH_GATE_ENHANCED_SCREENING=true."""

    RISK_PATTERNS = {
        "prompt_injection": re.compile(r"\b(ignore previous|system prompt|developer message|jailbreak)\b", re.I),
        "data_exfiltration": re.compile(r"\b(secret|api key|password|token dump|credential)\b", re.I),
        "unsafe_autonomy": re.compile(r"\b(self[- ]?replicate|evade monitoring|disable safety)\b", re.I),
    }

    def __init__(self, enabled: bool | None = None):
        if enabled is None:
            enabled = os.environ.get("TRUTH_GATE_ENHANCED_SCREENING", "false").lower() in {"1", "true", "yes", "on"}
        self.enabled = bool(enabled)

    def screen(self, text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.enabled:
            return {
                "enabled": False,
                "allowed": True,
                "risks": [],
                "action": "allow",
                "backend": "not_configured",
            }
        risks = [
            name
            for name, pattern in self.RISK_PATTERNS.items()
            if pattern.search(text or "")
        ]
        return {
            "enabled": True,
            "allowed": not risks,
            "risks": risks,
            "action": "block" if risks else "allow",
            "metadata": metadata or {},
            "backend": "local-pattern-fallback",
            "model": "local-pattern-fallback",
        }

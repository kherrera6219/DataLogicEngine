"""Axis 16: Ethics, Trust & Criticality."""

from __future__ import annotations

from typing import Any


class EthicsTrustAxis:
    """Resolve safety criticality and ethics framework routing."""

    axis_number = 16
    axis_name = "Ethics, Trust & Criticality"
    description = "Sensitivity, trust, criticality, and ethics-framework routing"

    CATEGORIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    FRAMEWORK_KEYWORDS = {
        "medical": "HIPAA",
        "patient": "HIPAA",
        "ai act": "EU_AI_ACT",
        "critical": "NIST_AI_RMF",
        "safety": "NIST_AI_RMF",
        "soc 2": "SOC2",
        "iso 42001": "ISO_42001",
    }

    def resolve_context(self, axis_data: Any) -> dict[str, Any]:
        text = str(axis_data or "").lower()
        category = "LOW"
        if any(term in text for term in ("critical", "life safety", "medical", "patient")):
            category = "CRITICAL"
        elif any(term in text for term in ("regulated", "security", "privacy", "compliance")):
            category = "HIGH"
        elif any(term in text for term in ("internal", "business", "policy")):
            category = "MEDIUM"

        framework = "GENERAL"
        for keyword, candidate in self.FRAMEWORK_KEYWORDS.items():
            if keyword in text:
                framework = candidate
                break

        return {
            "axis": self.axis_number,
            "name": self.axis_name,
            "criticality": category,
            "ethics_framework": framework,
            "requires_human_review": category in {"HIGH", "CRITICAL"},
            "confidence": 0.85 if framework != "GENERAL" or category != "LOW" else 0.5,
        }

    def navigate(self, **kwargs: Any) -> dict[str, Any]:
        query = kwargs.get("query") or kwargs.get("text") or kwargs
        return self.resolve_context(query)

"""Axis 15: Risk & Threat Context."""

from __future__ import annotations

from typing import Any


class RiskThreatAxis:
    """Resolve six-dimensional risk context for routing and governance."""

    axis_number = 15
    axis_name = "Risk & Threat Context"
    description = "Technical, security, compliance, financial, schedule, and reputational risk"

    DIMENSIONS = ("technical", "security", "compliance", "financial", "schedule", "reputational")

    KEYWORDS = {
        "outage": "technical",
        "latency": "technical",
        "breach": "security",
        "vulnerability": "security",
        "compliance": "compliance",
        "audit": "compliance",
        "cost": "financial",
        "budget": "financial",
        "delay": "schedule",
        "deadline": "schedule",
        "reputation": "reputational",
        "public": "reputational",
    }

    def resolve_context(self, axis_data: Any) -> dict[str, Any]:
        text = str(axis_data or "").lower()
        scores = dict.fromkeys(self.DIMENSIONS, 0.0)
        for keyword, dimension in self.KEYWORDS.items():
            if keyword in text:
                scores[dimension] = min(scores[dimension] + 0.35, 1.0)

        composite = max(scores.values()) if any(scores.values()) else 0.15
        dominant = max(scores, key=lambda key: scores[key])
        return {
            "axis": self.axis_number,
            "name": self.axis_name,
            "dimensions": scores,
            "composite_score": round(composite, 3),
            "dominant_dimension": dominant,
            "confidence": 0.8 if composite > 0.15 else 0.45,
        }

    def navigate(self, **kwargs: Any) -> dict[str, Any]:
        query = kwargs.get("query") or kwargs.get("text") or kwargs
        return self.resolve_context(query)

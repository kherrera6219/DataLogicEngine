"""DSQP quality gate."""

from __future__ import annotations

from typing import Any

from backend.dsqp.dsqp_chain import COMPONENT_KEYS


class DSQPValidator:
    """Validate seven-component persona coverage."""

    def __init__(self, minimum_coverage: float = 0.70):
        self.minimum_coverage = minimum_coverage

    def validate(self, persona: Any) -> dict[str, Any]:
        payload = persona.to_dict() if hasattr(persona, "to_dict") else dict(persona or {})
        components = payload.get("components") or {}
        missing = [
            key
            for key in COMPONENT_KEYS
            if not isinstance(components.get(key), dict)
            or not any(value not in (None, "", [], {}) for value in components[key].values())
        ]
        coverage_score = round((len(COMPONENT_KEYS) - len(missing)) / len(COMPONENT_KEYS), 4)
        return {
            "valid": coverage_score >= self.minimum_coverage,
            "coverage_score": coverage_score,
            "missing_components": missing,
            "minimum_coverage": self.minimum_coverage,
        }

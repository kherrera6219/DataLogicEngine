"""
L9-KA-006: Readiness Scorer

Calculates composite readiness score from multiple dimensions:
- L8 confidence
- Trace integrity
- Belief alignment
- Persona agreement
- Meta evaluation
"""

import logging
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class ReadinessScorerKA:
    """KA for calculating readiness score."""

    KA_ID = "L9-KA-006"
    NAME = "Readiness Scorer"

    # Default weights for readiness calculation
    DEFAULT_WEIGHTS: ClassVar[dict[str, float]] = {
        "l8_confidence": 0.30,
        "trace_integrity": 0.15,
        "belief_alignment": 0.20,
        "persona_agreement": 0.25,
        "meta_evaluation": 0.10,
    }

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.weights = self.config.get("weights", self.DEFAULT_WEIGHTS)

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate composite readiness score.

        Args:
            inputs: Dict with component scores

        Returns:
            {"readiness_score": float, "components": Dict}
        """
        dependency_results = inputs.get("dependency_results") or {}
        candidates = {
            "l8_confidence": inputs.get("l8_confidence"),
            "trace_integrity": inputs.get("trace_integrity"),
            "belief_alignment": inputs.get("belief_alignment"),
            "persona_agreement": inputs.get("persona_agreement"),
            "meta_evaluation": inputs.get("meta_evaluation"),
        }
        trace_result = dependency_results.get("L9-KA-001") or {}
        drift_result = dependency_results.get("L9-KA-002") or {}
        persona_result = dependency_results.get("L9-KA-003") or {}
        meta_result = dependency_results.get("L9-KA-004") or {}
        candidates["trace_integrity"] = (
            trace_result.get("integrity_score")
            if trace_result.get("integrity_score") is not None
            else candidates["trace_integrity"]
        )
        candidates["belief_alignment"] = (
            1.0 - float(drift_result["drift_score"])
            if drift_result.get("drift_score") is not None
            else candidates["belief_alignment"]
        )
        candidates["persona_agreement"] = (
            persona_result.get("min_score")
            if persona_result.get("measured")
            else candidates["persona_agreement"]
        )
        candidates["meta_evaluation"] = (
            meta_result.get("evaluation_score")
            if meta_result.get("evaluation_score") is not None
            else candidates["meta_evaluation"]
        )
        components = {
            name: float(value)
            for name, value in candidates.items()
            if value is not None
        }
        if any(not 0.0 <= value <= 1.0 for value in components.values()):
            raise ValueError("readiness components must be between 0 and 1")
        measured_weight = sum(self.weights[name] for name in components)
        readiness = (
            sum(self.weights[name] * value for name, value in components.items())
            / measured_weight
            if measured_weight
            else None
        )

        # Calculate weighted score
        if readiness is not None:
            readiness = round(max(0.0, min(1.0, readiness)), 4)
        logger.info("L9-KA-006: Readiness score = %s", readiness)

        return {
            "readiness_score": readiness,
            "components": components,
            "weights_used": {name: self.weights[name] for name in components},
            "measurement_coverage": round(
                measured_weight / sum(self.weights.values()), 4
            ),
            "status": "measured" if readiness is not None else "not_measured",
        }


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    return ReadinessScorerKA({}).execute(inputs)

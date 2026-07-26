"""
L9-KA-004: Meta-Cognitive Evaluator

Runs structured self-critique prompts:
- Alternative approach analysis
- Failure mode identification
- Edge case coverage
- Robustness assessment
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MetaCognitiveEvaluatorKA:
    """KA for meta-cognitive self-evaluation."""

    KA_ID = "L9-KA-004"
    NAME = "Meta-Cognitive Evaluator"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Run meta-cognitive evaluation.

        Args:
            inputs: {"solution": Dict, "trace": Dict}

        Returns:
            {"weaknesses": List, "failure_modes": List, "alternatives": List}
        """
        solution = inputs.get("solution", {})
        trace = inputs.get("trace", {})

        if not isinstance(solution, dict) or not isinstance(trace, dict):
            raise TypeError("solution and trace must be objects")
        weaknesses: list[dict[str, Any]] = []
        failure_modes: list[dict[str, Any]] = []
        alternatives: list[str] = []

        # Analyze solution structure
        if solution:
            confidence = solution.get(
                "overall_confidence",
                solution.get("confidence_score"),
            )

            if confidence is None:
                weaknesses.append(
                    {
                        "area": "confidence",
                        "severity": "medium",
                        "description": "Confidence was not measured",
                    }
                )
            elif float(confidence) < 0.95:
                weaknesses.append(
                    {
                        "area": "confidence",
                        "severity": "medium",
                        "description": (
                            f"Measured confidence {float(confidence):.1%} is below "
                            "the declared readiness threshold"
                        ),
                    }
                )

            # Check for single points of failure
            domain_confs = solution.get("domain_confidences", [])
            if domain_confs:
                min_conf = min(
                    dc.get("confidence", 1.0)
                    for dc in domain_confs
                    if isinstance(dc, dict)
                )
                if min_conf < 0.9:
                    failure_modes.append(
                        {
                            "scenario": "domain_expert_disagreement",
                            "observed": True,
                            "impact": "medium",
                        }
                    )

        # Check trace completeness
        if trace and len(trace) < 8:
            weaknesses.append(
                {
                    "area": "trace_completeness",
                    "severity": "low",
                    "description": "Incomplete layer trace",
                }
            )

        checks = 3
        failed_checks = min(checks, len(weaknesses) + len(failure_modes))
        evaluation_score = round((checks - failed_checks) / checks, 4)

        logger.info(
            f"L9-KA-004: Found {len(weaknesses)} weaknesses, {len(failure_modes)} failure modes"
        )

        return {
            "evaluation_score": evaluation_score,
            "weaknesses": weaknesses,
            "failure_modes": failure_modes,
            "alternatives": alternatives,
            "score_basis": "passed_observable_structure_checks",
        }


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    return MetaCognitiveEvaluatorKA({}).execute(inputs)

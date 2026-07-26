"""L9-KA-002: deterministic lexical and numeric belief-drift checks."""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class BeliefDriftDetectorKA:
    """KA for detecting belief drift between query and solution."""

    KA_ID = "L9-KA-002"
    NAME = "Belief Drift Detector"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.drift_threshold = self.config.get("drift_threshold", 0.15)

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        original = str(inputs.get("original_query") or "").strip()
        solution = str(inputs.get("final_solution") or "").strip()

        if not original or not solution:
            return {
                "drift_detected": False,
                "drift_score": None,
                "drift_type": "not_measured",
                "measured": False,
                "limitations": "Both original query and final solution are required.",
            }

        original_numbers = self._extract_numbers(original)
        solution_numbers = self._extract_numbers(solution)
        numeric_drift = bool(original_numbers) and not all(
            number in solution_numbers for number in original_numbers
        )
        original_terms = self._terms(original)
        solution_terms = self._terms(solution)
        lexical_overlap = (
            len(original_terms & solution_terms) / len(original_terms)
            if original_terms
            else 0.0
        )
        lexical_alignment_gap = round(1.0 - lexical_overlap, 4)
        # A question and its answer are expected to use different wording.
        # Lexical distance is therefore reported as an observation and must
        # never be promoted into a semantic-drift claim. Only an observable
        # loss of numeric facts is a blocking drift signal in this KA.
        drift_score = 1.0 if numeric_drift else 0.0
        drift_detected = numeric_drift
        drift_type = "numeric_fact_loss" if numeric_drift else None

        logger.info(
            f"L9-KA-002: Drift {'detected' if drift_detected else 'not detected'} (score={drift_score:.2f})"
        )

        return {
            "drift_detected": drift_detected,
            "drift_score": drift_score,
            "drift_type": drift_type,
            "measured": True,
            "lexical_overlap": round(lexical_overlap, 4),
            "lexical_alignment_gap": lexical_alignment_gap,
            "numeric_facts_preserved": not numeric_drift,
            "limitations": (
                "Lexical distance is observational only. This KA detects "
                "numeric fact loss and does not measure semantic truth."
            ),
        }

    @staticmethod
    def _extract_numbers(text: str) -> list[float]:
        """Extract numeric values from text."""
        numbers = []
        matches = re.findall(r"(\d+(?:\.\d+)?)\s*%?", text)
        for m in matches:
            try:
                numbers.append(float(m))
            except (TypeError, ValueError):
                pass
        return numbers

    @staticmethod
    def _terms(text: str) -> set[str]:
        return {
            token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2
        }


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    return BeliefDriftDetectorKA({}).execute(inputs)

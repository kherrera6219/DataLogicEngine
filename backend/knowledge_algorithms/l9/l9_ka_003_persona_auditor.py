"""
L9-KA-003: Persona Agreement Auditor

Audits persona agreement matrix for:
- Silent dissent (experts who disagree but were overruled)
- Below-threshold satisfaction
- Unresolved concerns
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PersonaAgreementAuditorKA:
    """KA for auditing persona agreement."""

    KA_ID = "L9-KA-003"
    NAME = "Persona Agreement Auditor"

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.default_threshold = self.config.get("default_threshold", 0.95)

    def execute(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Audit persona agreement for silent dissent.

        Args:
            inputs: {"domain_confidences": List[Dict]}

        Returns:
            {"min_score": float, "flagged": List[Dict], "consensus": bool}
        """
        domain_confs = inputs.get("domain_confidences", [])
        threshold = inputs.get("threshold", self.default_threshold)

        if not isinstance(domain_confs, list):
            raise TypeError("domain_confidences must be a list")
        threshold = float(threshold)
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")

        measured_scores: list[float] = []
        flagged: list[dict[str, Any]] = []

        for dc in domain_confs:
            if isinstance(dc, dict):
                if dc.get("confidence") is None:
                    continue
                confidence = float(dc["confidence"])
                if not 0.0 <= confidence <= 1.0:
                    raise ValueError("persona confidence must be between 0 and 1")
                domain = dc.get("domain", "unknown")
                measured_scores.append(confidence)

                if confidence < threshold:
                    flagged.append(
                        {
                            "persona": domain,
                            "score": confidence,
                            "gap": threshold - confidence,
                            "concern": f"Below threshold by {(threshold - confidence) * 100:.1f}%",
                        }
                    )

        measured = bool(measured_scores)
        min_score = min(measured_scores) if measured else None
        consensus = measured and len(flagged) == 0

        logger.info(
            "L9-KA-003: Min score %s, %s flagged, consensus=%s",
            min_score,
            len(flagged),
            consensus,
        )

        return {
            "min_score": min_score,
            "flagged": flagged,
            "consensus": consensus,
            "threshold_applied": threshold,
            "measured": measured,
            "measured_personas": len(measured_scores),
            "status": "measured" if measured else "not_measured",
        }


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    return PersonaAgreementAuditorKA({}).execute(inputs)

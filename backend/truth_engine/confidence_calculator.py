"""F-CONF-01 Confidence Calculator (spec Section 13).

Computes a canonical confidence score for a completed reasoning run using four
weighted dimensions:

  C = w_e * evidence_quality
    + w_k * ka_consensus
    + w_p * persona_agreement
    + w_g * gate_factor

Weights (sum to 1.0):
  w_e = 0.35  evidence quality  — completeness and corroboration of evidence
  w_k = 0.30  KA consensus      — agreement across knowledge algorithms
  w_p = 0.20  persona agreement — cross-persona synthesis alignment
  w_g = 0.15  gate factor       — TruthGate security/regulatory outcome

All component scores are clamped to [0.0, 1.0] before weighting.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_W_EVIDENCE = 0.35
_W_KA = 0.30
_W_PERSONA = 0.20
_W_GATE = 0.15

_GATE_SCORES = {
    "allow": 1.0,
    "escalate": 0.6,
    "hitl": 0.4,
    "block": 0.0,
    None: 0.8,  # no gate decision recorded — assume neutral pass
}


class ConfidenceCalculator:
    """Compute F-CONF-01 canonical confidence score."""

    def calculate(
        self,
        run: Any,
        ka_results: Optional[list] = None,
        gate_decision: Optional[str] = None,
    ) -> float:
        """
        Parameters
        ----------
        run : TraceRun
            Completed TraceRun with linked evidence_items, personas, ka_invocations.
        ka_results : list, optional
            Raw KA result dicts (from SDK trace). Used when TraceRun relationships
            are not yet loaded.
        gate_decision : str, optional
            TruthGate outcome: 'allow' | 'block' | 'escalate' | 'hitl'.
            Falls back to run.truthgate_decision if omitted.

        Returns
        -------
        float
            Canonical confidence in [0.0, 1.0].
        """
        try:
            evidence_score = self._evidence_quality(run)
            ka_score = self._ka_consensus(run, ka_results)
            persona_score = self._persona_agreement(run)
            gate_score = self._gate_factor(gate_decision or getattr(run, "truthgate_decision", None))

            confidence = (
                _W_EVIDENCE * evidence_score
                + _W_KA * ka_score
                + _W_PERSONA * persona_score
                + _W_GATE * gate_score
            )
            result = max(0.0, min(1.0, confidence))
            logger.debug(
                "F-CONF-01: evidence=%.3f ka=%.3f persona=%.3f gate=%.3f → %.3f",
                evidence_score, ka_score, persona_score, gate_score, result,
            )
            return result
        except Exception as exc:
            logger.warning("ConfidenceCalculator fallback (%.2f): %s", 0.5, exc)
            return 0.5

    @staticmethod
    def _evidence_quality(run) -> float:
        """Score based on evidence count and pass/fail corroboration."""
        try:
            items = list(run.evidence_items) if run.evidence_items else []
        except Exception:
            return 0.5

        if not items:
            return 0.5  # neutral when no evidence recorded

        total = len(items)
        passed = sum(
            1 for e in items
            if getattr(e, "status", "pass") in ("pass", "corroborated", "verified")
        )
        # Completeness bonus — more evidence = more trustworthy up to a cap
        completeness = min(1.0, total / 10.0)
        corroboration = passed / total if total else 0.0
        return 0.6 * corroboration + 0.4 * completeness

    @staticmethod
    def _ka_consensus(run, ka_results: Optional[list]) -> float:
        """Agreement across KA invocations — fraction that passed."""
        try:
            invocations = list(run.ka_invocations) if run.ka_invocations else []
        except Exception:
            invocations = []

        if invocations:
            passed = sum(1 for k in invocations if getattr(k, "status", "pass") in ("pass", "success"))
            return passed / len(invocations)

        if ka_results:
            passed = sum(1 for k in ka_results if k.get("status") in ("pass", "success"))
            return passed / len(ka_results) if ka_results else 0.5

        return 0.5  # neutral when no KA data

    @staticmethod
    def _persona_agreement(run) -> float:
        """Cross-persona synthesis alignment — fraction of personas that reached consensus."""
        try:
            personas = list(run.personas) if run.personas else []
        except Exception:
            return 0.5

        if not personas:
            return 0.5

        agreed = sum(
            1 for p in personas
            if getattr(p, "consensus_reached", None) is not False
        )
        return agreed / len(personas)

    @staticmethod
    def _gate_factor(gate_decision: Optional[str]) -> float:
        """TruthGate outcome mapped to a confidence multiplier."""
        key = (gate_decision or "").lower().strip() or None
        return _GATE_SCORES.get(key, _GATE_SCORES.get(None))

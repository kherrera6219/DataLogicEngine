"""DMRF five-tier query classifier."""

from __future__ import annotations

from typing import Any

from .models import TIER_ORDER, TierClassification


class DMRFTierClassifier:
    """Classify DMRF work into trivial, moderate, high_stakes, extreme, or autonomous."""

    def __init__(self, ka_controller: Any | None = None, *, desktop_mode: bool = False):
        self.ka_controller = ka_controller
        self.desktop_mode = desktop_mode

    def classify(
        self,
        query: str,
        *,
        context: dict[str, Any] | None = None,
        offline: bool = False,
    ) -> TierClassification:
        context = context or {}
        q = query.lower()
        score = min(1.0, max(len(query) / 500.0, 0.05))
        rationale = [f"length_score={score:.2f}"]

        if any(term in q for term in ("autonomous", "agent", "take action", "execute", "without approval")):
            score = max(score, 0.92)
            rationale.append("autonomous_action_terms")
        if any(term in q for term in ("simulate", "multi-country", "scenario", "federated", "cross-organization")):
            score = max(score, 0.78)
            rationale.append("extensive_simulation_terms")
        if any(term in q for term in ("hipaa", "sox", "legal", "regulatory", "audit", "patient", "safety", "compliance")):
            score = max(score, 0.62)
            rationale.append("regulated_or_high_stakes_terms")

        tier = self._tier_for_score(score)
        capped_from = None
        if self.desktop_mode and offline and TIER_ORDER[tier] > TIER_ORDER["high_stakes"]:
            capped_from = tier
            tier = "high_stakes"
            rationale.append("desktop_offline_cap")

        return TierClassification(
            tier=tier,
            confidence=round(0.72 + min(score, 0.25), 4),
            rationale=rationale,
            raw={"score": round(score, 4), "context_keys": sorted(context)},
            capped_from=capped_from,
        )

    @staticmethod
    def _tier_for_score(score: float) -> str:
        if score < 0.18:
            return "trivial"
        if score < 0.55:
            return "moderate"
        if score < 0.76:
            return "high_stakes"
        if score < 0.90:
            return "extreme"
        return "autonomous"


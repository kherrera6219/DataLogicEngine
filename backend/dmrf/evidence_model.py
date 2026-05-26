"""Domain-specific evidence freshness model for DMRF."""

from __future__ import annotations

from datetime import UTC, datetime
from math import exp
from typing import Any

from .convergence_policy import ConvergencePolicy


class EvidenceModel:
    """Score evidence freshness with the same domain lambdas as KA-023."""

    def __init__(self, domain: str = "general"):
        self.domain = domain or "general"
        self.policy = ConvergencePolicy(self.domain)

    def score(self, evidence: dict[str, Any]) -> dict[str, Any]:
        age_days = self._age_days(evidence)
        decay_lambda = self.policy.domain_lambdas.get(
            self.domain,
            self.policy.domain_lambdas.get("general", 0.001),
        )
        freshness_score = exp(-decay_lambda * age_days)
        return {
            "domain": self.domain,
            "age_days": round(age_days, 4),
            "decay_lambda": decay_lambda,
            "freshness_score": round(freshness_score, 4),
            "stale": freshness_score < 0.80,
        }

    @staticmethod
    def _age_days(evidence: dict[str, Any]) -> float:
        value = evidence.get("observed_at") or evidence.get("timestamp") or evidence.get("created_at")
        if isinstance(value, datetime):
            observed = value if value.tzinfo else value.replace(tzinfo=UTC)
        elif isinstance(value, str) and value:
            observed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            observed = observed if observed.tzinfo else observed.replace(tzinfo=UTC)
        else:
            return 0.0
        return max((datetime.now(UTC) - observed).total_seconds() / 86400, 0.0)


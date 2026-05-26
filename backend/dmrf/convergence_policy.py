"""Convergence policy for DMRF refinement loops."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConvergencePolicy:
    """Use KA-023 domain lambdas to decide whether DMRF should refine."""

    def __init__(self, domain: str = "general", *, config_path: str | Path | None = None):
        self.domain = domain or "general"
        self.config_path = Path(config_path) if config_path else (
            Path(__file__).resolve().parents[1]
            / "knowledge_algorithms"
            / "config"
            / "ka_23_config.json"
        )
        self.domain_lambdas = self._load_lambdas()

    def should_refine(
        self,
        *,
        confidence: float,
        target_confidence: float,
        iteration: int,
        max_iterations: int = 3,
        evidence_age_days: float = 0.0,
    ) -> dict[str, Any]:
        decay_lambda = self.domain_lambdas.get(self.domain, self.domain_lambdas.get("general", 0.001))
        stale_penalty = min(0.20, max(evidence_age_days, 0.0) * decay_lambda)
        adjusted_confidence = max(0.0, confidence - stale_penalty)
        refine = adjusted_confidence < target_confidence and iteration < max_iterations
        return {
            "should_refine": refine,
            "domain": self.domain,
            "decay_lambda": decay_lambda,
            "confidence": confidence,
            "adjusted_confidence": round(adjusted_confidence, 4),
            "target_confidence": target_confidence,
            "iteration": iteration,
            "max_iterations": max_iterations,
            "reason": "below_target" if refine else "converged_or_limit",
        }

    def _load_lambdas(self) -> dict[str, float]:
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            lambdas = data.get("domain_lambdas") or {}
            return {str(key): float(value) for key, value in lambdas.items()}
        except Exception:
            return {"healthcare": 0.05, "finance": 0.02, "general": 0.001}


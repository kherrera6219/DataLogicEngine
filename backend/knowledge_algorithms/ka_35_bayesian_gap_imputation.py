"""
KA-035: Bayesian Gap Imputation
Purpose: Probabilistically fill missing data gaps using uncertainty bounds and Bayesian priors.
"""

import json
import logging
import os
import statistics
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA035Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    gaps: list[str] = Field(default_factory=list, description="Gaps to impute")
    priors: dict[str, float] = Field(
        default_factory=dict, description="Prior values for gaps"
    )
    observations: dict[str, list[float]] = Field(default_factory=dict)
    evidence_weights: dict[str, float] = Field(default_factory=dict)


class KA035BayesianGapImputation(KnowledgeAlgorithm):
    """
    KA-035: Bayesian imputation and gap-filling engine for missing data.
    """

    input_schema = KA035Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-035"
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        try:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "ka_35_config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return {}

    def _run_logic(self, input_data: KA035Input) -> dict[str, Any]:
        gaps = input_data.gaps or sorted(
            set(input_data.priors) | set(input_data.observations)
        )
        self.log_execution_step("Imputing Gaps", {"gap_count": len(gaps)})

        sigma = float(self.config.get("uncertainty_sigma", 0.2))
        imputed_values = {
            gap: self._posterior_for_gap(
                gap,
                input_data.priors,
                input_data.observations,
                input_data.evidence_weights,
                sigma,
            )
            for gap in gaps
        }
        overall_uncertainty = (
            statistics.mean(item["uncertainty"] for item in imputed_values.values())
            if imputed_values
            else sigma
        )
        return {
            "success": True,
            "imputed_data": imputed_values,
            "overall_uncertainty": round(overall_uncertainty, 4),
            "method": self.config.get("imputation_method", "bayesian_posterior_mean"),
            "imputations_applied": False,
            "deterministic": True,
            "limitations": (
                "Posterior values use caller-declared priors, observations, and "
                "weights. They are bounded proposals, not learned distributions "
                "or replacements for missing evidence."
            ),
        }

    @staticmethod
    def _posterior_for_gap(
        gap: str,
        priors: dict[str, float],
        observations: dict[str, list[float]],
        evidence_weights: dict[str, float],
        sigma: float,
    ) -> dict[str, Any]:
        prior = float(priors.get(gap, 0.5))
        observed = [
            float(value)
            for value in observations.get(gap, [])
            if isinstance(value, (int, float))
        ]
        evidence_mean = statistics.mean(observed) if observed else prior
        weight = max(
            0.0,
            min(
                1.0,
                float(
                    evidence_weights.get(gap, len(observed) / max(1, len(observed) + 2))
                ),
            ),
        )
        posterior = prior * (1 - weight) + evidence_mean * weight
        posterior = max(0.0, min(1.0, posterior))
        uncertainty = max(0.01, sigma * (1 - min(0.8, weight * 0.8)))
        return {
            "value": round(posterior, 4),
            "confidence": round(max(0.0, min(1.0, 1.0 - uncertainty)), 4),
            "uncertainty": round(uncertainty, 4),
            "prior": round(prior, 4),
            "evidence_mean": round(evidence_mean, 4),
            "evidence_count": len(observed),
            "method": "posterior_weighted_mean",
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA035BayesianGapImputation(context).run(context)

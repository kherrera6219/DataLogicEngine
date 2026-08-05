"""
KA-014: Confidence Scoring
Purpose: Aggregate multi-factor confidence metrics to certify system outputs.
"""

import json
import logging
import os
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA014Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_score: float = Field(1.0, ge=0.0, le=1.0)
    persona_consensus_score: float = Field(1.0, ge=0.0, le=1.0)
    truth_score: float = Field(1.0, ge=0.0, le=1.0)
    relevance_score: float = Field(1.0, ge=0.0, le=1.0)
    has_contradictions: bool = Field(False)
    domain_scores: dict[str, float] = Field(default_factory=dict)
    risk_domain: str = Field("standard")
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA014ConfidenceScoring(KnowledgeAlgorithm):
    """
    KA-014: Master confidence engine for system output certification.
    """

    input_schema = KA014Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-014"
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        try:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "ka_14_config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return {}

    def _run_logic(self, input_data: KA014Input) -> dict[str, Any]:
        dependencies = input_data.dependency_results
        evidence_rows = dependencies.get("KA-009", {}).get("results") or []
        normalized_rows = (
            dependencies.get("KA-1041", {}).get("normalized_confidence") or []
        )
        entropy = dependencies.get("KA-1102", {}).get("normalized_entropy")
        contradiction = dependencies.get("KA-026", {}).get("has_contradictions")
        measured_evidence = (
            sum(float(row.get("score") or 0.0) for row in evidence_rows)
            / len(evidence_rows)
            if evidence_rows
            else input_data.evidence_score
        )
        measured_normalized = (
            sum(
                float(row.get("normalized_confidence") or 0.0)
                for row in normalized_rows
            )
            / len(normalized_rows)
            if normalized_rows
            else input_data.truth_score
        )
        metrics = {
            "evidence_validation": measured_evidence,
            "persona_consensus": input_data.persona_consensus_score,
            "normalized_declared_confidence": measured_normalized,
            "context_relevance": input_data.relevance_score,
            "distribution_certainty": (
                1.0 - float(entropy) if entropy is not None else 1.0
            ),
        }
        has_conflict = (
            bool(contradiction)
            if contradiction is not None
            else input_data.has_contradictions
        )

        self.log_execution_step(
            "Confidence Benchmarking", {"metrics": metrics, "conflict": has_conflict}
        )

        configured_weights = self.config.get("weights", {})
        aliases = {
            "normalized_declared_confidence": "truth_score",
            "distribution_certainty": "truth_score",
        }
        weights = {
            key: max(
                0.0,
                float(
                    configured_weights.get(
                        key, configured_weights.get(aliases.get(key), 1.0)
                    )
                ),
            )
            for key in metrics
        }
        weight_total = sum(weights.values()) or float(len(metrics))
        total_score = sum(metrics[key] * weights[key] for key in metrics) / weight_total

        if input_data.domain_scores:
            domain_values = [
                max(0.0, min(1.0, float(value)))
                for value in input_data.domain_scores.values()
            ]
            domain_mean = sum(domain_values) / len(domain_values)
            # Platt-style logistic proxy centered at 0.5, blended with weighted evidence.
            import math

            calibrated = 1.0 / (1.0 + math.exp(-6.0 * (domain_mean - 0.5)))
            total_score = (0.65 * total_score) + (0.35 * calibrated)

        risk_adjustments = self.config.get(
            "risk_domain_adjustments",
            {"high_risk": -0.05, "healthcare": -0.03, "finance": -0.02},
        )
        total_score += risk_adjustments.get(input_data.risk_domain, 0.0)

        if has_conflict:
            total_score *= self.config.get("conflict_penalty_multiplier", 0.8)

        total_score = max(0.0, min(1.0, total_score))

        thresholds = self.config.get("thresholds", {})
        status = "risky"
        if total_score >= thresholds.get("certified", 0.85):
            status = "certified"
        elif total_score >= thresholds.get("provisional", 0.6):
            status = "provisional"

        return {
            "success": True,
            "confidence_index": round(total_score, 8),
            "calibrated_confidence": None,
            "risk_domain": input_data.risk_domain,
            "domain_scores": input_data.domain_scores,
            "status_tier": status,
            "metrics_breakdown": metrics,
            "is_certified": False,
            "certification_recommendation": status,
            "dependencies_consumed": sorted(dependencies),
            "deterministic": True,
            "limitations": (
                "The confidence index is a configured decision heuristic over "
                "supplied measurements. It is not a calibrated probability or "
                "release certification."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA014ConfidenceScoring(context).run(context)

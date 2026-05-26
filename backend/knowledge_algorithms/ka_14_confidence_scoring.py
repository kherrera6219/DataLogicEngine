"""
KA-014: Confidence Scoring
Purpose: Aggregate multi-factor confidence metrics to certify system outputs.
"""
import logging
import json
import os
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA014Input(BaseModel):
    evidence_score: float = Field(1.0, ge=0.0, le=1.0)
    persona_consensus_score: float = Field(1.0, ge=0.0, le=1.0)
    truth_score: float = Field(1.0, ge=0.0, le=1.0)
    relevance_score: float = Field(1.0, ge=0.0, le=1.0)
    has_contradictions: bool = Field(False)
    domain_scores: Dict[str, float] = Field(default_factory=dict)
    risk_domain: str = Field("standard")

class KA014ConfidenceScoring(KnowledgeAlgorithm):
    """
    KA-014: Master confidence engine for system output certification.
    """
    input_schema = KA014Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-014"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_14_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA014Input) -> Dict[str, Any]:
        metrics = {
            "evidence_validation": input_data.evidence_score,
            "persona_consensus": input_data.persona_consensus_score,
            "truth_score": input_data.truth_score,
            "context_relevance": input_data.relevance_score
        }
        has_conflict = input_data.has_contradictions
        
        self.log_execution_step("Confidence Benchmarking", {"metrics": metrics, "conflict": has_conflict})
        
        weights = self.config.get("weights", {})
        total_score = 0.0
        for key, val in metrics.items():
            total_score += val * weights.get(key, 0.25)
            
        if input_data.domain_scores:
            domain_values = [max(0.0, min(1.0, float(value))) for value in input_data.domain_scores.values()]
            domain_mean = sum(domain_values) / len(domain_values)
            # Platt-style logistic proxy centered at 0.5, blended with weighted evidence.
            import math

            calibrated = 1.0 / (1.0 + math.exp(-6.0 * (domain_mean - 0.5)))
            total_score = (0.65 * total_score) + (0.35 * calibrated)

        risk_adjustments = self.config.get("risk_domain_adjustments", {"high_risk": -0.05, "healthcare": -0.03, "finance": -0.02})
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
            "final_confidence": total_score,
            "calibrated_confidence": total_score,
            "risk_domain": input_data.risk_domain,
            "domain_scores": input_data.domain_scores,
            "status_tier": status,
            "metrics_breakdown": metrics,
            "is_certified": status == "certified"
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA014ConfidenceScoring(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-014 Failed: {e}")
        return {"success": False, "error": str(e)}

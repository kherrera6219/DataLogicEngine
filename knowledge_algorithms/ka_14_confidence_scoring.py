"""
KA-014: Confidence Scoring
Purpose: Aggregate multi-factor confidence metrics to certify system outputs.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA014ConfidenceScoring(KnowledgeAlgorithm):
    """
    KA-014: Master confidence engine.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
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

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        metrics = {
            "evidence_validation": input_data.get("evidence_score", 1.0),
            "persona_consensus": input_data.get("persona_consensus_score", 1.0),
            "truth_score": input_data.get("truth_score", 1.0),
            "context_relevance": input_data.get("relevance_score", 1.0)
        }
        
        has_conflict = input_data.get("has_contradictions", False)
        
        self.log_execution_step("Confidence Benchmarking", {"metrics": metrics, "conflict": has_conflict})
        
        # 1. Weighted Average
        weights = self.config.get("weights", {})
        total_score = 0.0
        for key, val in metrics.items():
            total_score += val * weights.get(key, 0.25)
            
        # 2. Conflict Penalty
        if has_conflict:
            total_score *= self.config.get("conflict_penalty_multiplier", 0.8)
            
        # 3. Certification Tier
        thresholds = self.config.get("thresholds", {})
        status = "risky"
        if total_score >= thresholds.get("certified", 0.85):
            status = "certified"
        elif total_score >= thresholds.get("provisional", 0.6):
            status = "provisional"
            
        return {
            "ka_id": "KA-014",
            "ka_name": "Confidence Scoring",
            "success": True,
            "final_confidence": total_score,
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

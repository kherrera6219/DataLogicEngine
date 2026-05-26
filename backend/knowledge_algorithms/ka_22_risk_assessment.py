"""
KA-022: Risk Assessment
Purpose: Compute operational, financial, legal, and reputational risk of proposed recommendations.
"""
import logging
import json
import os
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA022Input(BaseModel):
    recommendation: str = Field(..., description="The recommendation to assess for risk")
    impact_scores: Dict[str, float] = Field(default_factory=dict, description="Impact scores across categories")

class KA022RiskAssessment(KnowledgeAlgorithm):
    """
    KA-022: Risk profile calculation engine.
    """
    input_schema = KA022Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-022"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_22_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA022Input) -> Dict[str, Any]:
        recommendation = input_data.recommendation
        impact_areas = input_data.impact_scores
        
        self.log_execution_step("Risk Profiling", {"recommendation": recommendation[:50]})
        
        dimensions = ("technical", "security", "compliance", "financial", "schedule", "reputational")
        keyword_map = {
            "technical": ("outage", "latency", "failure", "integration", "scale"),
            "security": ("breach", "vulnerability", "secret", "attack", "token"),
            "compliance": ("compliance", "audit", "regulation", "policy", "legal"),
            "financial": ("cost", "budget", "revenue", "invoice", "finance"),
            "schedule": ("delay", "deadline", "timeline", "blocked", "late"),
            "reputational": ("reputation", "public", "customer", "trust", "press"),
        }
        text = recommendation.lower()
        risk_factors = self.config.get("risk_factors", {})
        total_risk = 0.0
        details = {}
        for area in dimensions:
            config_weight = risk_factors.get(area, risk_factors.get(area.upper(), 1 / len(dimensions)))
            keyword_score = min(1.0, sum(0.2 for keyword in keyword_map[area] if keyword in text))
            area_score = max(float(impact_areas.get(area, impact_areas.get(area.upper(), 0.0)) or 0.0), keyword_score)
            weight = float(config_weight)
            weighted_score = area_score * weight
            total_risk += weighted_score
            details[area] = {
                "input_score": area_score,
                "weighted_risk": weighted_score
            }
        total_weight = sum(float(risk_factors.get(area, risk_factors.get(area.upper(), 1 / len(dimensions)))) for area in dimensions)
        if total_weight > 0:
            total_risk = total_risk / total_weight
            
        status = "LOW"
        if total_risk >= self.config.get("critical_threshold", 0.75):
            status = "CRITICAL"
        elif total_risk >= self.config.get("warning_threshold", 0.4):
            status = "WARNING"
            
        return {
            "success": True,
            "overall_risk_score": total_risk,
            "risk_status": status,
            "axis15_dimensions": details,
            "dominant_dimension": max(details, key=lambda key: details[key]["input_score"]),
            "area_details": details,
            "mitigation_required": status != "LOW"
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA022RiskAssessment(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-022 Failed: {e}")
        return {"success": False, "error": str(e)}

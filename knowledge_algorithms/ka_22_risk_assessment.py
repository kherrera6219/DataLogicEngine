"""
KA-022: Risk Assessment
Purpose: Compute operational, financial, legal, and reputational risk of proposed recommendations.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA022RiskAssessment(KnowledgeAlgorithm):
    """
    KA-022: Risk profile calculation engine.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
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

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        recommendation = input_data.get("recommendation", "")
        impact_areas = input_data.get("impact_scores", {}) # e.g. {"FINANCIAL": 0.5, "OPERATIONAL": 0.2}
        
        self.log_execution_step("Risk Profiling", {"recommendation": recommendation[:50]})
        
        risk_factors = self.config.get("risk_factors", {})
        
        total_risk = 0.0
        details = {}
        
        for area, weight in risk_factors.items():
            area_score = impact_areas.get(area, 0.0)
            weighted_score = area_score * weight
            total_risk += weighted_score
            details[area] = {
                "input_score": area_score,
                "weighted_risk": weighted_score
            }
            
        status = "LOW"
        if total_risk >= self.config.get("critical_threshold", 0.75):
            status = "CRITICAL"
        elif total_risk >= self.config.get("warning_threshold", 0.4):
            status = "WARNING"
            
        return {
            "ka_id": "KA-022",
            "ka_name": "Risk Assessment",
            "success": True,
            "overall_risk_score": total_risk,
            "risk_status": status,
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

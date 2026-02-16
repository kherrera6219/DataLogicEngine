"""
KA-027: Ethical Impact Analysis
Purpose: Evaluate draft recommendations for ethical implications, bias, and potential harm.
"""
import logging
import json
import os
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

class KA027Input(BaseModel):
    recommendation: str = Field(..., description="The recommendation to evaluate for ethical impact")
    has_linguistic_bias: bool = Field(False, description="Whether linguistic bias was flagged by earlier KAs")

class KA027EthicalImpactAnalysis(KnowledgeAlgorithm):
    """
    KA-027: Ethical assessment engine for evaluating recommendations.
    """
    input_schema = KA027Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-027"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_27_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA027Input) -> Dict[str, Any]:
        recommendation = input_data.recommendation
        self.log_execution_step("Ethical Review", {"content_len": len(recommendation)})
        
        score = 0.0
        findings = []
        harm_keywords = self.config.get("harm_keywords", [])
        for kw in harm_keywords:
            if kw.lower() in recommendation.lower():
                score += 0.25
                findings.append(f"Potential Harm Category: {kw}")
                
        if input_data.has_linguistic_bias:
            score += 0.2
            findings.append("Linguistic bias flagged by KA-010 integration")
            
        status = "PASSED"
        if score >= self.config.get("critical_threshold", 0.7):
             status = "CRITICAL_FAILURE"
             
        return {
            "success": True,
            "ethics_score": min(1.0, score),
            "findings": findings,
            "status": status,
            "review_recommended": score > 0.3
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA027EthicalImpactAnalysis(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-027 Failed: {e}")
        return {"success": False, "error": str(e)}

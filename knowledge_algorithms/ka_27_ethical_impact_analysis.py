"""
KA-027: Ethical Impact Analysis
Purpose: Evaluate draft recommendations for ethical implications, bias, and potential harm.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA027EthicalImpactAnalysis(KnowledgeAlgorithm):
    """
    KA-027: Ethical assessment engine.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
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

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        recommendation = input_data.get("recommendation", "")
        
        self.log_execution_step("Ethical Review", {"content_len": len(recommendation)})
        
        score = 0.0
        findings = []
        
        # 1. Keyword-based Harm Detection
        harm_keywords = self.config.get("harm_keywords", [])
        for kw in harm_keywords:
            if kw.lower() in recommendation.lower():
                score += 0.25
                findings.append(f"Potential Harm Category: {kw}")
                
        # 2. Bias signals (Stub for integration with KA-010)
        if input_data.get("has_linguistic_bias", False):
            score += 0.2
            findings.append("Linguistic bias flagged by KA-010 integration")
            
        status = "PASSED"
        if score >= self.config.get("critical_threshold", 0.7):
             status = "CRITICAL_FAILURE"
             
        return {
            "ka_id": "KA-027",
            "ka_name": "Ethical Impact Analysis",
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

"""
KA-010: Bias Detection
Purpose: Detect bias signals in reasoning/output.
"""
import logging
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA010BiasDetection(KnowledgeAlgorithm):
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scan text for bias.
        """
        text = input_data.get("text", "") or input_data.get("draft", "")
        
        self.log_execution_step("Detecting Bias", {})
        
        bias_flags = []
        bias_keywords = ["always", "never", "obviously", "everyone knows", "inferior", "superior"]
        
        for word in bias_keywords:
            if word in text.lower():
                bias_flags.append(f"Found absolute term: {word}")
                
        return {
            "ka_id": "KA-010",
            "success": True,
            "bias_detected": len(bias_flags) > 0,
            "flags": bias_flags
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA010BiasDetection(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-010 Failed: {e}")
        return {"success": False, "error": str(e)}

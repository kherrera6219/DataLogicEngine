"""
KA-027: Ethical Impact Analysis
Purpose: Assess ethical implications of an action/finding.
"""
import logging
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA027EthicalImpact(KnowledgeAlgorithm):
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate ethics.
        """
        proposal = input_data.get("proposal", "")
        
        self.log_execution_step("Ethical Analysis", {})
        
        impact_score = "neutral"
        concerns = []
        
        keywords = ["harm", "bias", "exclude", "manipulate"]
        for k in keywords:
            if k in proposal.lower():
                impact_score = "negative"
                concerns.append(f"Potential {k}")
                
        return {
            "ka_id": "KA-027",
            "success": True,
            "impact": impact_score,
            "concerns": concerns
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA027EthicalImpact(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-027 Failed: {e}")
        return {"success": False, "error": str(e)}

"""
KA-008: Self-Critique & Reflection
Purpose: Attack draft output for flaws and assumptions.
"""
import logging
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA008SelfCritique(KnowledgeAlgorithm):
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Critique the provided draft.
        """
        draft = input_data.get("draft", "")
        if not draft:
            return {"success": False, "critiques": []}
            
        self.log_execution_step("Critiquing Draft", {})
        
        critiques = []
        if len(draft) < 50:
             critiques.append("Draft is too short / brief.")
        if "obviously" in draft.lower():
             critiques.append("Avoid assuming obviousness.")
             
        return {
            "ka_id": "KA-008",
            "success": True,
            "critiques": critiques,
            "passed": len(critiques) == 0
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA008SelfCritique(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-008 Failed: {e}")
        return {"success": False, "error": str(e)}

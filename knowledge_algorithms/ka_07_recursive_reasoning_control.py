"""
KA-007: Recursive Reasoning Control
Purpose: Control recursion depth/breadth; prevent runaway loops.
"""
import logging
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA007RecursiveControl(KnowledgeAlgorithm):
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine if recursion should continue.
        """
        current_depth = input_data.get("current_depth", 0)
        max_depth = input_data.get("max_depth", 5)
        entropy = input_data.get("entropy", 0.0)
        
        self.log_execution_step("Checking Recursion", {"depth": current_depth, "entropy": entropy})
        
        should_stop = False
        reason = ""
        
        if current_depth >= max_depth:
            should_stop = True
            reason = "Max depth reached"
        elif entropy < 0.1:
            should_stop = True
            reason = "Entropy sufficiently low"
            
        return {
            "ka_id": "KA-007",
            "success": True,
            "decision": "STOP" if should_stop else "CONTINUE",
            "reason": reason
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA007RecursiveControl(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-007 Failed: {e}")
        return {"success": False, "error": str(e)}

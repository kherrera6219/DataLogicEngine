"""
KA-020: Loopback Trigger
Purpose: Force loopback to earlier layers when thresholds fail.
"""
import logging
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA020LoopbackTrigger(KnowledgeAlgorithm):
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check triggers for loopback.
        """
        confidence = input_data.get("confidence", 1.0)
        threshold = input_data.get("threshold", 0.8)
        
        self.log_execution_step("Checking Loopback", {"conf": confidence, "thresh": threshold})
        
        loopback = False
        target_layer = None
        
        if confidence < threshold:
            loopback = True
            target_layer = "L2"
            
        return {
            "ka_id": "KA-020",
            "success": True,
            "loopback_required": loopback,
            "target_layer": target_layer
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA020LoopbackTrigger(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-020 Failed: {e}")
        return {"success": False, "error": str(e)}

"""
KA-023: Belief Decay
Purpose: Model the decay of belief/confidence over time.
"""
import logging
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA023BeliefDecay(KnowledgeAlgorithm):
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply decay function to belief.
        """
        initial_confidence = input_data.get("confidence", 1.0)
        time_delta = input_data.get("time_delta", 0) # hours
        
        self.log_execution_step("Applying Decay", {"delta": time_delta})
        
        # Simple exponential decay
        decay_rate = 0.01
        new_confidence = initial_confidence * ((1 - decay_rate) ** time_delta)
        
        return {
            "ka_id": "KA-023",
            "success": True,
            "original_confidence": initial_confidence,
            "decayed_confidence": max(0.0, new_confidence)
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA023BeliefDecay(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-023 Failed: {e}")
        return {"success": False, "error": str(e)}

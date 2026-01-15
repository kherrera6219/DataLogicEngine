"""
KA-015: Temporal Reasoning
Purpose: Reason across time; timelines; validity windows.
"""
import logging
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA015TemporalReasoning(KnowledgeAlgorithm):
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze temporal aspects.
        """
        events = input_data.get("events", [])
        
        self.log_execution_step("Temporal Analysis", {"events": len(events)})
        
        timeline = sorted(events, key=lambda x: x.get("timestamp", 0))
        validity = {"start": 0, "end": 9999999999}
        if timeline:
            validity["start"] = timeline[0].get("timestamp", 0)
            validity["end"] = timeline[-1].get("timestamp", 0)
            
        return {
            "ka_id": "KA-015",
            "success": True,
            "timeline": timeline,
            "validity_window": validity
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA015TemporalReasoning(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-015 Failed: {e}")
        return {"success": False, "error": str(e)}

"""
KA-020: Loopback Trigger
Purpose: Evaluate state and decide whether to initiate a recursive reasoning loopback pass.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA020LoopbackTrigger(KnowledgeAlgorithm):
    """
    KA-020: Control gate for recursive system loopbacks.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_20_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        current_pass = input_data.get("pass_count", 1)
        confidence = input_data.get("final_confidence", 1.0)
        entropy = input_data.get("entropy_level", 0.0)
        unresolved_gaps = input_data.get("gap_count", 0)
        
        self.log_execution_step("Loopback Evaluation", {
            "pass": current_pass,
            "conf": confidence,
            "entropy": entropy
        })
        
        max_passes = self.config.get("max_passes", 3)
        conf_threshold = self.config.get("confidence_threshold", 0.85)
        entropy_threshold = self.config.get("entropy_threshold", 0.4)
        
        should_loop = False
        reason = []
        
        if current_pass < max_passes:
            if confidence < conf_threshold:
                should_loop = True
                reason.append(f"Confidence {confidence:.2f} below threshold {conf_threshold}")
            
            if entropy > entropy_threshold:
                should_loop = True
                reason.append(f"Entropy {entropy:.2f} above threshold {entropy_threshold}")
                
            if unresolved_gaps > 0:
                should_loop = True
                reason.append(f"Unresolved gaps: {unresolved_gaps}")
        else:
            reason.append(f"Max passes ({max_passes}) reached.")
            
        return {
            "ka_id": "KA-020",
            "ka_name": "Loopback Trigger",
            "success": True,
            "should_loopback": should_loop,
            "reasoning": "; ".join(reason),
            "next_pass": current_pass + 1 if should_loop else current_pass
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA020LoopbackTrigger(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-020 Failed: {e}")
        return {"success": False, "error": str(e)}

"""
KA-007: Recursive Reasoning Control
Purpose: Manage and throttle recursive reasoning loops to ensure termination and focus.
"""
import logging
import json
import os
import hashlib
from typing import Dict, Any, List, Set
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA007RecursiveReasoningControl(KnowledgeAlgorithm):
    """
    KA-007: Controller for recursive processes. Tracks depth and state to prevent infinite loops.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_07_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        current_depth = input_data.get("current_depth", 0)
        state_history = input_data.get("state_history", [])
        current_state = input_data.get("current_state", {})
        
        self.log_execution_step("Checking Recursion Bounds", {"depth": current_depth})
        
        # 1. Depth Check
        max_depth = self.config.get("max_recursion_depth", 5)
        if current_depth >= max_depth:
            return {
                "ka_id": "KA-007",
                "success": True,
                "allow_recursion": False,
                "reason": f"Maximum recursion depth {max_depth} reached"
            }
            
        # 2. State Loop Detection
        if self._is_looping(current_state, state_history):
             return {
                "ka_id": "KA-007",
                "success": True,
                "allow_recursion": False,
                "reason": "Recursion loop detected (duplicate state)"
            }
            
        # 3. Confidence/Entropy check (Optional integration)
        confidence = input_data.get("confidence", 1.0)
        decay = self.config.get("confidence_decay_factor", 0.9)
        threshold = self.config.get("termination_threshold", 0.05)
        
        effective_confidence = confidence * (decay ** current_depth)
        
        if effective_confidence < threshold:
            return {
                "ka_id": "KA-007",
                "success": True,
                "allow_recursion": False,
                "reason": f"Effective confidence {effective_confidence:.4f} below threshold {threshold}"
            }

        return {
            "ka_id": "KA-007",
            "ka_name": "Recursive Reasoning Control",
            "success": True,
            "allow_recursion": True,
            "next_depth": current_depth + 1,
            "effective_confidence": effective_confidence
        }

    def _is_looping(self, current_state: Dict[str, Any], history: List[str]) -> bool:
        if not current_state: return False
        
        # Serialize state for comparison
        state_str = json.dumps(current_state, sort_keys=True)
        state_hash = hashlib.md5(state_str.encode()).hexdigest()
        
        return state_hash in history

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA007RecursiveReasoningControl(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-007 Failed: {e}")
        return {"success": False, "error": str(e)}

"""
KA-007: Recursive Reasoning Control
Purpose: Manage and throttle recursive reasoning loops to ensure termination and focus.
"""
import logging
import json
import os
import hashlib
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

class KA007Input(BaseModel):
    current_depth: int = Field(0, ge=0)
    state_history: List[str] = Field(default_factory=list)
    current_state: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(1.0, ge=0.0, le=1.0)

class KA007RecursiveReasoningControl(KnowledgeAlgorithm):
    """
    KA-007: Controller for recursive processes. Tracks depth and state to prevent infinite loops.
    """
    input_schema = KA007Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-007"
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

    def _run_logic(self, input_data: KA007Input) -> Dict[str, Any]:
        current_depth = input_data.current_depth
        state_history = input_data.state_history
        current_state = input_data.current_state
        
        self.log_execution_step("Checking Recursion Bounds", {"depth": current_depth})
        
        # 1. Depth Check
        max_depth = self.config.get("max_recursion_depth", 5)
        if current_depth >= max_depth:
            return {
                "success": True,
                "allow_recursion": False,
                "reason": f"Maximum recursion depth {max_depth} reached"
            }
            
        # 2. State Loop Detection
        if self._is_looping(current_state, state_history):
             return {
                "success": True,
                "allow_recursion": False,
                "reason": "Recursion loop detected (duplicate state)"
            }
            
        # 3. Confidence/Entropy check
        confidence = input_data.confidence
        decay = self.config.get("confidence_decay_factor", 0.9)
        threshold = self.config.get("termination_threshold", 0.05)
        
        effective_confidence = confidence * (decay ** current_depth)
        
        if effective_confidence < threshold:
            return {
                "success": True,
                "allow_recursion": False,
                "reason": f"Effective confidence {effective_confidence:.4f} below threshold {threshold}"
            }

        return {
            "success": True,
            "allow_recursion": True,
            "next_depth": current_depth + 1,
            "effective_confidence": effective_confidence
        }

    def _is_looping(self, current_state: Dict[str, Any], history: List[str]) -> bool:
        if not current_state:
            return False
        state_str = json.dumps(current_state, sort_keys=True)
        state_hash = hashlib.sha256(state_str.encode()).hexdigest()
        return state_hash in history

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA007RecursiveReasoningControl(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-007 Failed: {e}")
        return {"success": False, "error": str(e)}

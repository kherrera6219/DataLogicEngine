"""
L9-KA-007: Loop Controller

Controls recursive iteration:
- Iteration counting
- Diminishing returns detection
- Infinite loop prevention
- Breadcrumb memory
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class LoopControllerKA:
    """KA for controlling recursion loops."""
    
    KA_ID = "L9-KA-007"
    NAME = "Loop Controller"
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.max_iterations = self.config.get("max_iterations", 5)
        self.min_improvement = self.config.get("min_improvement", 0.03)
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Control recursion loop.
        
        Args:
            inputs: {"iteration": int, "previous_scores": List[float]}
            
        Returns:
            {"continue": bool, "reason": str}
        """
        iteration = inputs.get("iteration", 1)
        prev_scores = inputs.get("previous_scores", [])
        prior_fixes = inputs.get("prior_fixes", [])
        
        # Check max iterations
        if iteration >= self.max_iterations:
            logger.info(f"L9-KA-007: Max iterations ({self.max_iterations}) reached")
            return {
                "continue": False,
                "reason": "max_iterations_reached",
                "force_finalize": True
            }
        
        # Check diminishing returns
        if len(prev_scores) >= 2:
            improvement = prev_scores[-1] - prev_scores[-2]
            if improvement < self.min_improvement:
                logger.info(f"L9-KA-007: Diminishing returns (improvement={improvement:.3f})")
                return {
                    "continue": False,
                    "reason": "diminishing_returns",
                    "improvement": improvement
                }
        
        # Check for repeated fix attempts
        if len(prior_fixes) > 2:
            # Simple check: if last 3 fixes target same layer, might be stuck
            if len(set(f.get("target_layer") for f in prior_fixes[-3:])) == 1:
                logger.warning("L9-KA-007: Possible loop detected (same layer targeted 3x)")
                return {
                    "continue": False,
                    "reason": "possible_loop_detected"
                }
        
        logger.info(f"L9-KA-007: Continue allowed (iteration {iteration})")
        
        return {
            "continue": True,
            "iteration": iteration,
            "remaining": self.max_iterations - iteration
        }

"""
L9-KA-005: Recursion Trigger

Determines when and why to trigger recursive refinement:
- Threshold violations
- Critical issue detection
- Quality gaps
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class RecursionTriggerKA:
    """KA for determining recursion triggers."""
    
    KA_ID = "L9-KA-005"
    NAME = "Recursion Trigger"
    
    # Issue type to target layer mapping
    ROUTING_TABLE = {
        "knowledge_gap": 2,
        "missing_perspective": 4,
        "persona_disagreement": 5,
        "low_quantitative_support": 6,
        "robustness_issues": 7,
        "trust_gate_fail": 8
    }
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.readiness_threshold = self.config.get("readiness_threshold", 0.95)
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine if recursion should be triggered.
        
        Args:
            inputs: {"readiness": float, "issues": List}
            
        Returns:
            {"trigger_refinement": bool, "target_layer": int, "reason": str}
        """
        readiness = inputs.get("readiness", 1.0)
        issues = inputs.get("issues", [])
        
        trigger = False
        target_layer = 5  # Default
        reason = ""
        
        # Check readiness threshold
        if readiness < self.readiness_threshold:
            trigger = True
            reason = f"Readiness {readiness:.3f} below threshold {self.readiness_threshold}"
        
        # Check for critical issues
        if issues:
            trigger = True
            # Pick target layer from first issue
            if len(issues) > 0 and len(issues[0]) >= 2:
                issue_type = issues[0][0] if isinstance(issues[0], tuple) else issues[0].get("type", "")
                target_layer = self.ROUTING_TABLE.get(issue_type, 5)
                reason = issues[0][2] if len(issues[0]) > 2 else str(issues[0])
        
        logger.info(f"L9-KA-005: Trigger={trigger}, target_layer={target_layer}")
        
        return {
            "trigger_refinement": trigger,
            "target_layer": target_layer,
            "reason": reason
        }

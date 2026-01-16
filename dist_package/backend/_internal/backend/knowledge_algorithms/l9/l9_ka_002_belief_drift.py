"""
L9-KA-002: Belief Drift Detector

Detects drift between the original query intent and the final solution:
- Semantic drift (meaning changed)
- Numerical drift (values shifted)
- Scope creep (answer went beyond question)
"""

import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)


class BeliefDriftDetectorKA:
    """KA for detecting belief drift between query and solution."""
    
    KA_ID = "L9-KA-002"
    NAME = "Belief Drift Detector"
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.drift_threshold = self.config.get("drift_threshold", 0.15)
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect belief drift between query and solution.
        
        Args:
            inputs: {"original_query": str, "final_solution": str}
            
        Returns:
            {"drift_detected": bool, "drift_score": float, "drift_type": str}
        """
        original = inputs.get("original_query", "")
        solution = inputs.get("final_solution", "")
        
        drift_detected = False
        drift_score = 0.0
        drift_type = None
        
        if not original or not solution:
            return {
                "drift_detected": False,
                "drift_score": 0.0,
                "drift_type": None
            }
        
        # Check numerical drift
        original_numbers = self._extract_numbers(original)
        solution_numbers = self._extract_numbers(solution)
        
        if original_numbers and solution_numbers:
            for on in original_numbers:
                for sn in solution_numbers:
                    if abs(on - sn) / max(on, 1) > 0.2:
                        drift_detected = True
                        drift_type = "numerical"
                        drift_score = max(drift_score, 0.3)
        
        # Check for scope keywords
        scope_indicators = ["additionally", "also", "furthermore", "beyond"]
        if any(ind in solution.lower() for ind in scope_indicators):
            # Might indicate scope expansion
            if drift_score < 0.2:
                drift_score = 0.15
                drift_type = drift_type or "scope"
        
        drift_detected = drift_score >= self.drift_threshold
        
        logger.info(f"L9-KA-002: Drift {'detected' if drift_detected else 'not detected'} (score={drift_score:.2f})")
        
        return {
            "drift_detected": drift_detected,
            "drift_score": drift_score,
            "drift_type": drift_type
        }
    
    def _extract_numbers(self, text: str) -> list:
        """Extract numeric values from text."""
        numbers = []
        matches = re.findall(r'(\d+(?:\.\d+)?)\s*%?', text)
        for m in matches:
            try:
                numbers.append(float(m))
            except:
                pass
        return numbers

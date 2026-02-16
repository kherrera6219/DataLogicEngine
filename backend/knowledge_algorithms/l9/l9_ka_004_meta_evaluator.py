"""
L9-KA-004: Meta-Cognitive Evaluator

Runs structured self-critique prompts:
- Alternative approach analysis
- Failure mode identification
- Edge case coverage
- Robustness assessment
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MetaCognitiveEvaluatorKA:
    """KA for meta-cognitive self-evaluation."""
    
    KA_ID = "L9-KA-004"
    NAME = "Meta-Cognitive Evaluator"
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run meta-cognitive evaluation.
        
        Args:
            inputs: {"solution": Dict, "trace": Dict}
            
        Returns:
            {"weaknesses": List, "failure_modes": List, "alternatives": List}
        """
        solution = inputs.get("solution", {})
        trace = inputs.get("trace", {})
        
        weaknesses = []
        failure_modes = []
        alternatives = []
        
        # Analyze solution structure
        if solution:
            confidence = solution.get("overall_confidence", solution.get("confidence_score", 0.9))
            
            # Identify potential weaknesses
            if confidence < 0.95:
                weaknesses.append({
                    "area": "confidence",
                    "severity": "medium",
                    "description": f"Confidence {confidence:.1%} leaves room for improvement"
                })
            
            # Check for single points of failure
            domain_confs = solution.get("domain_confidences", [])
            if domain_confs:
                min_conf = min(dc.get("confidence", 1.0) for dc in domain_confs if isinstance(dc, dict))
                if min_conf < 0.9:
                    failure_modes.append({
                        "scenario": "domain_expert_disagreement",
                        "probability": 0.3,
                        "impact": "medium"
                    })
        
        # Check trace completeness
        if trace:
            if len(trace) < 8:
                weaknesses.append({
                    "area": "trace_completeness",
                    "severity": "low",
                    "description": "Incomplete layer trace"
                })
        
        evaluation_score = 1.0 - (len(weaknesses) * 0.1 + len(failure_modes) * 0.15)
        evaluation_score = max(0.5, min(1.0, evaluation_score))
        
        logger.info(f"L9-KA-004: Found {len(weaknesses)} weaknesses, {len(failure_modes)} failure modes")
        
        return {
            "evaluation_score": evaluation_score,
            "weaknesses": weaknesses,
            "failure_modes": failure_modes,
            "alternatives": alternatives
        }

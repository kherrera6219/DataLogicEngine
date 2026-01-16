"""
KA-31: Emergence Probability Engine

This algorithm calculates the probability of emergent behaviors in complex knowledge
systems, based on complexity scores and feedback loop counts.
"""

import logging
from typing import Dict, List, Any, Optional
import time
import math

logger = logging.getLogger(__name__)

class EmergenceProbabilityEngine:
    """
    KA-31: Calculates emergence probability in complex knowledge systems.
    
    This algorithm analyzes system complexity and feedback loops to estimate
    the probability of emergent behaviors and self-organizing patterns.
    """
    
    def __init__(self):
        """Initialize the Emergence Probability Engine."""
        self.complexity_factors = self._initialize_complexity_factors()
        self.feedback_types = self._initialize_feedback_types()
        logger.info("KA-31: Emergence Probability Engine initialized")
    
    def _initialize_complexity_factors(self) -> Dict[str, float]:
        """Initialize complexity factors for different system aspects."""
        return {
            "connectivity_density": 0.15,
            "knowledge_diversity": 0.12,
            "temporal_dynamics": 0.09,
            "cross_domain_linkage": 0.18,
            "abstraction_levels": 0.14,
            "semantic_richness": 0.11,
            "structural_coherence": 0.10,
            "adaptive_capacity": 0.11
        }
    
    def _initialize_feedback_types(self) -> Dict[str, Dict[str, Any]]:
        """Initialize feedback loop types and their impact on emergence."""
        return {
            "reinforcing": {
                "description": "Self-amplifying feedback that strengthens patterns",
                "emergence_multiplier": 0.15,
                "examples": ["Belief reinforcement", "Concept strengthening", "Pattern amplification"]
            },
            "balancing": {
                "description": "Stabilizing feedback that maintains equilibrium",
                "emergence_multiplier": 0.08,
                "examples": ["Error correction", "Confidence calibration", "Stability maintenance"]
            },
            "adaptive": {
                "description": "Feedback that modifies system behavior based on outcomes",
                "emergence_multiplier": 0.12,
                "examples": ["Learning adjustments", "Response optimization", "Context adaptation"]
            },
            "delayed": {
                "description": "Feedback with time lag between action and response",
                "emergence_multiplier": 0.05,
                "examples": ["Long-term memory reinforcement", "Gradual insight formation"]
            },
            "cross_level": {
                "description": "Feedback that crosses abstraction levels or domains",
                "emergence_multiplier": 0.18,
                "examples": ["Cross-domain insights", "Hierarchy-spanning connections"]
            }
        }
    
    def calculate_emergence_probability(self, complexity_score: Optional[float] = None, 
                                    feedback_loops: Optional[int] = None,
                                    system_factors: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate the probability of emergent behavior.
        
        Args:
            complexity_score: Optional overall complexity score (0-1)
            feedback_loops: Optional count of feedback loops
            system_factors: Optional detailed system factors
            
        Returns:
            Dictionary with emergence probability and factors
        """
        # Default values
        if complexity_score is None:
            if system_factors:
                complexity_score = self._calculate_complexity_from_factors(system_factors)
            else:
                complexity_score = 0.75  # Default moderate-high complexity
        
        if feedback_loops is None:
            feedback_loops = 2  # Default moderate feedback
        
        # Calculate base probability
        base_probability = self._calculate_base_probability(complexity_score, feedback_loops)
        
        # Apply sigmoid transformation to ensure bounds and non-linearity
        transformed_probability = self._apply_probability_transformation(base_probability)
        
        # Calculate critical threshold
        critical_threshold = self._calculate_critical_threshold(complexity_score, feedback_loops)
        
        # Determine emergence characteristics
        characteristics = self._determine_emergence_characteristics(transformed_probability, 
                                                              complexity_score, 
                                                              feedback_loops)
        
        # Prepare result
        result = {
            "emergence_probability": round(transformed_probability, 3),
            "complexity_score": complexity_score,
            "feedback_loops": feedback_loops,
            "critical_threshold": round(critical_threshold, 3),
            "proximity_to_threshold": round(abs(transformed_probability - critical_threshold), 3),
            "emergence_regime": self._determine_emergence_regime(transformed_probability, critical_threshold),
            "characteristics": characteristics
        }
        
        return result
    
    def _calculate_complexity_from_factors(self, factors: Dict[str, Any]) -> float:
        """
        Calculate complexity score from detailed system factors.
        
        Args:
            factors: Dictionary of system complexity factors
            
        Returns:
            Calculated complexity score (0-1)
        """
        complexity_score = 0.0
        factors_used = 0
        
        # Process each known complexity factor
        for factor, weight in self.complexity_factors.items():
            if factor in factors:
                # Get factor value, ensuring it's between 0-1
                factor_value = min(1.0, max(0.0, float(factors[factor])))
                complexity_score += factor_value * weight
                factors_used += 1
        
        # If no factors matched, return default complexity
        if factors_used == 0:
            return 0.75
        
        # Normalize based on weights used
        return min(1.0, complexity_score)
    
    def _calculate_base_probability(self, complexity: float, feedback_loops: int) -> float:
        """
        Calculate base emergence probability.
        
        Args:
            complexity: System complexity score (0-1)
            feedback_loops: Number of feedback loops
            
        Returns:
            Base probability before transformation
        """
        # Simple model: complexity * (1 + feedback_effect)
        feedback_effect = 0.1 * feedback_loops
        
        # Cap feedback effect to avoid unrealistic values
        capped_feedback = min(0.5, feedback_effect)
        
        return complexity * (1 + capped_feedback)
    
    def _apply_probability_transformation(self, base_probability: float) -> float:
        """
        Apply sigmoid transformation to ensure probability bounds.
        
        Args:
            base_probability: The raw calculated probability
            
        Returns:
            Transformed probability between 0 and 1
        """
        # Sigmoid function to transform value to 0-1 range with non-linear scaling
        # Adjust parameters to center sigmoid around relevant probability range
        return 1.0 / (1.0 + math.exp(-10 * (base_probability - 0.5)))
    
    def _calculate_critical_threshold(self, complexity: float, feedback_loops: int) -> float:
        """
        Calculate critical threshold for emergence.
        
        Args:
            complexity: System complexity score
            feedback_loops: Number of feedback loops
            
        Returns:
            Critical threshold for emergence
        """
        # Base threshold depends inversely on complexity
        base_threshold = 0.7 - (0.2 * complexity)
        
        # Feedback loops lower the threshold
        feedback_adjustment = 0.05 * min(4, feedback_loops)
        
        return max(0.3, base_threshold - feedback_adjustment)
    
    def _determine_emergence_regime(self, probability: float, threshold: float) -> str:
        """
        Determine the emergence regime based on probability and threshold.
        
        Args:
            probability: Calculated emergence probability
            threshold: Critical threshold
            
        Returns:
            Emergence regime description
        """
        difference = probability - threshold
        
        if difference < -0.2:
            return "subcritical_stable"
        elif difference < -0.05:
            return "subcritical_near_threshold"
        elif difference < 0.05:
            return "critical_transition"
        elif difference < 0.2:
            return "supercritical_emerging"
        else:
            return "supercritical_established"
    
    def _determine_emergence_characteristics(self, probability: float, 
                                          complexity: float, 
                                          feedback_loops: int) -> Dict[str, Any]:
        """
        Determine characteristics of potential emergence.
        
        Args:
            probability: Emergence probability
            complexity: System complexity
            feedback_loops: Number of feedback loops
            
        Returns:
            Dictionary of emergence characteristics
        """
        # Stability is inversely related to proximity to critical threshold
        stability = 1.0 - min(1.0, probability / 0.7)
        
        # Predictability decreases with complexity
        predictability = 1.0 - complexity
        
        # Self-organization tendency
        self_organization = 0.3 + (0.4 * complexity) + (0.1 * min(3, feedback_loops))
        
        # Novelty generation
        novelty = 0.2 + (0.5 * complexity) + (0.1 * min(3, feedback_loops))
        
        return {
            "stability": round(stability, 2),
            "predictability": round(predictability, 2),
            "self_organization": round(min(1.0, self_organization), 2),
            "novelty_potential": round(min(1.0, novelty), 2),
            "boundary_definition": "well_defined" if complexity < 0.6 else "fuzzy",
            "response_character": "linear" if probability < 0.4 else "non_linear"
        }


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Emergence Probability Engine (KA-31) on the provided data.
    
    Args:
        data: A dictionary containing complexity score and feedback loop information
        
    Returns:
        Dictionary with emergence probability analysis
    """
    complexity_score = data.get("complexity")
    feedback_loops = data.get("feedback_loops")
    system_factors = data.get("system_factors")
    
    engine = EmergenceProbabilityEngine()
    result = engine.calculate_emergence_probability(complexity_score, feedback_loops, system_factors)
    
    return {
        "algorithm": "KA-31",
        **result,
        "timestamp": time.time(),
        "success": True
    }
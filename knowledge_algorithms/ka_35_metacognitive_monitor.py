"""
KA-35: Metacognitive Loop Monitor

This algorithm monitors metacognitive reasoning processes, detecting reflective thinking
patterns and self-referential reasoning loops in the simulation.
"""

import logging
from typing import Dict, List, Any, Optional, Set
import time
import re

logger = logging.getLogger(__name__)

class MetacognitiveLoopMonitor:
    """
    KA-35: Monitors metacognitive and reflective thinking in simulations.
    
    This algorithm analyzes reasoning chains for metacognitive patterns,
    tracking reflection depth, self-assessment, and recursive thought patterns.
    """
    
    def __init__(self):
        """Initialize the Metacognitive Loop Monitor."""
        self.reflection_patterns = self._initialize_reflection_patterns()
        self.metacognitive_indicators = self._initialize_metacognitive_indicators()
        self.recursion_types = self._initialize_recursion_types()
        logger.info("KA-35: Metacognitive Loop Monitor initialized")
    
    def _initialize_reflection_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns that indicate reflective thinking."""
        return {
            "self_assessment": {
                "patterns": [
                    r"(?:assess|evaluate|review)(?:ing)? (?:my|the) (?:own|previous|prior) (?:reasoning|analysis|thinking|conclusion|decision)",
                    r"(?:reflect|reflecting|reflection) on (?:my|the) (?:own|previous|prior) (?:reasoning|analysis|thinking)",
                    r"(?:reconsider|reconsidering|reconsideration) of (?:my|the) (?:own|previous|prior) (?:assumption|conclusion|premise)"
                ],
                "weight": 0.8,
                "reflection_type": "explicit_self_assessment"
            },
            "confidence_calibration": {
                "patterns": [
                    r"(?:adjust|adjusting|recalibrate|recalibrating) (?:my|the) confidence",
                    r"confidence (?:in this|in the|about this) (?:reasoning|analysis|conclusion) is (?:too high|too low|miscalibrated)",
                    r"(?:over|under)(?:confident|estimating) (?:in|about) (?:my|the) (?:reasoning|analysis|conclusion)"
                ],
                "weight": 0.7,
                "reflection_type": "confidence_adjustment"
            },
            "assumption_examination": {
                "patterns": [
                    r"(?:examine|examining|question|questioning) (?:my|the) (?:own|underlying|implicit|explicit) assumptions",
                    r"(?:implicit|explicit|unstated|hidden) assumptions (?:underlying|behind) (?:my|the) (?:reasoning|analysis)",
                    r"assumptions that (?:led to|resulted in|produced) (?:this|the) (?:conclusion|outcome|result)"
                ],
                "weight": 0.75,
                "reflection_type": "assumption_analysis"
            },
            "alternative_perspectives": {
                "patterns": [
                    r"(?:consider|considering|explore|exploring) alternative (?:perspectives|viewpoints|approaches)",
                    r"(?:from|taking) a different (?:perspective|viewpoint|angle)",
                    r"(?:how|what) would (?:someone else|others|another person|an expert) (?:think|conclude|reason) about this"
                ],
                "weight": 0.6,
                "reflection_type": "perspective_taking"
            },
            "bias_detection": {
                "patterns": [
                    r"(?:potential|possible|likely) (?:bias|biases) in (?:my|the) (?:reasoning|analysis|thinking)",
                    r"(?:recognize|recognizing|identify|identifying) (?:my|the) (?:own|cognitive|reasoning) biases",
                    r"(?:affected|influenced|distorted) by (?:confirmation|recency|anchoring|availability) bias"
                ],
                "weight": 0.7,
                "reflection_type": "bias_awareness"
            }
        }
    
    def _initialize_metacognitive_indicators(self) -> Dict[str, List[str]]:
        """Initialize indicators of metacognitive processing."""
        return {
            "epistemic_status": [
                "I know that", "I believe that", "I'm certain that", "I'm uncertain about",
                "I'm confident that", "I'm unsure whether", "I need to verify"
            ],
            "reasoning_about_reasoning": [
                "thinking about how I'm approaching", "analyzing my process for", 
                "considering how I reached this conclusion", "reviewing my chain of reasoning"
            ],
            "knowledge_assessment": [
                "I know enough to", "I don't have sufficient information", 
                "my knowledge is limited regarding", "I need to learn more about"
            ],
            "strategy_awareness": [
                "a better approach would be", "this strategy isn't optimal", 
                "changing my approach to", "adopting a different method for"
            ],
            "error_detection": [
                "I made a mistake in", "this reasoning contains an error", 
                "correcting my previous statement", "I need to revise my earlier claim"
            ]
        }
    
    def _initialize_recursion_types(self) -> Dict[str, Dict[str, Any]]:
        """Initialize types of recursive thinking patterns."""
        return {
            "linear_recursion": {
                "description": "Thinking about previous thinking in a linear sequence",
                "depth_potential": "medium",
                "complexity": "low"
            },
            "nested_recursion": {
                "description": "Thinking about thinking about thinking in nested layers",
                "depth_potential": "high",
                "complexity": "high"
            },
            "mutual_recursion": {
                "description": "Interleaved recursive thinking across different aspects",
                "depth_potential": "medium",
                "complexity": "medium"
            },
            "tail_recursion": {
                "description": "Summarizing and building on previous recursive thinking",
                "depth_potential": "low",
                "complexity": "low"
            },
            "explosive_recursion": {
                "description": "Rapidly expanding tree of recursive thinking paths",
                "depth_potential": "very_high",
                "complexity": "very_high"
            }
        }
    
    def analyze_reasoning(self, evaluations: List[str], 
                        threshold: float = 0.5) -> Dict[str, Any]:
        """
        Analyze reasoning chains for metacognitive patterns.
        
        Args:
            evaluations: List of reasoning statements to analyze
            threshold: Minimum score to classify as metacognitive reflection
            
        Returns:
            Dictionary with metacognitive analysis results
        """
        # Initialize results
        metacognitive_instances = []
        reflection_scores = []
        indicator_counts = {category: 0 for category in self.metacognitive_indicators}
        
        # Analyze each evaluation statement
        for i, statement in enumerate(evaluations):
            # Skip empty statements
            if not statement:
                continue
                
            # Calculate reflection score
            reflection_score, reflection_types = self._calculate_reflection_score(statement)
            reflection_scores.append(reflection_score)
            
            # Check for metacognitive indicators
            indicators_found = self._check_metacognitive_indicators(statement)
            
            # Update indicator counts
            for category, count in indicators_found.items():
                indicator_counts[category] += count
            
            # Record metacognitive instances above threshold
            if reflection_score >= threshold or any(indicators_found.values()):
                metacognitive_instances.append({
                    "index": i,
                    "statement": statement,
                    "reflection_score": reflection_score,
                    "reflection_types": reflection_types,
                    "indicators": {k: v for k, v in indicators_found.items() if v > 0}
                })
        
        # Analyze recursion pattern
        recursion_pattern = self._analyze_recursion_pattern(metacognitive_instances)
        
        # Calculate summary statistics
        avg_reflection_score = sum(reflection_scores) / len(reflection_scores) if reflection_scores else 0
        max_reflection_score = max(reflection_scores) if reflection_scores else 0
        
        # Create analysis result
        analysis_result = {
            "reflections_detected": len(metacognitive_instances),
            "total_statements": len(evaluations),
            "reflection_ratio": len(metacognitive_instances) / len(evaluations) if evaluations else 0,
            "average_reflection_score": avg_reflection_score,
            "maximum_reflection_score": max_reflection_score,
            "indicator_counts": indicator_counts,
            "metacognitive_instances": metacognitive_instances,
            "recursion_analysis": recursion_pattern
        }
        
        return analysis_result
    
    def _calculate_reflection_score(self, statement: str) -> tuple:
        """
        Calculate reflection score for a statement.
        
        Args:
            statement: The statement to analyze
            
        Returns:
            Tuple of (reflection_score, reflection_types)
        """
        statement_lower = statement.lower()
        total_score = 0.0
        max_score = 0.0
        detected_types = []
        
        # Check each reflection pattern
        for pattern_name, pattern_info in self.reflection_patterns.items():
            pattern_weight = pattern_info["weight"]
            found_match = False
            
            # Check each regex pattern
            for regex in pattern_info["patterns"]:
                if re.search(regex, statement_lower):
                    found_match = True
                    total_score += pattern_weight
                    max_score = max(max_score, pattern_weight)
                    if pattern_info["reflection_type"] not in detected_types:
                        detected_types.append(pattern_info["reflection_type"])
                    break  # Stop after first match in this pattern group
        
        # Normalize score (0-1)
        normalized_score = min(1.0, total_score / 3.0)  # Normalize assuming max ~3 patterns
        
        return normalized_score, detected_types
    
    def _check_metacognitive_indicators(self, statement: str) -> Dict[str, int]:
        """
        Check for metacognitive indicators in a statement.
        
        Args:
            statement: The statement to analyze
            
        Returns:
            Dictionary with counts of indicator categories
        """
        statement_lower = statement.lower()
        counts = {}
        
        # Check each indicator category
        for category, indicators in self.metacognitive_indicators.items():
            category_count = 0
            
            # Check each indicator phrase
            for indicator in indicators:
                indicator_lower = indicator.lower()
                if indicator_lower in statement_lower:
                    category_count += 1
            
            counts[category] = category_count
        
        return counts
    
    def _analyze_recursion_pattern(self, instances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the pattern of recursion in metacognitive instances.
        
        Args:
            instances: List of metacognitive instances
            
        Returns:
            Dictionary with recursion pattern analysis
        """
        if not instances:
            return {
                "recursion_detected": False,
                "recursion_type": None,
                "recursion_depth": 0,
                "pattern_description": "No metacognitive reflection detected"
            }
        
        # Count consecutive reflections
        max_consecutive = 0
        current_consecutive = 0
        
        for i in range(len(instances) - 1):
            if instances[i + 1]["index"] - instances[i]["index"] == 1:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        # Determine recursion depth based on consecutive reflections and scores
        max_score = max(instance["reflection_score"] for instance in instances)
        avg_score = sum(instance["reflection_score"] for instance in instances) / len(instances)
        
        # Estimated recursion depth
        if max_consecutive >= 3 and max_score > 0.8:
            recursion_depth = 3  # Deep recursion
        elif max_consecutive >= 2 or (max_score > 0.7 and avg_score > 0.5):
            recursion_depth = 2  # Moderate recursion
        elif len(instances) > 2:
            recursion_depth = 1  # Light recursion
        else:
            recursion_depth = 0  # No significant recursion
        
        # Determine recursion type
        if recursion_depth == 0:
            recursion_type = None
            pattern_description = "No significant recursive thinking pattern"
        elif max_consecutive >= 3 and avg_score > 0.7:
            recursion_type = "nested_recursion"
            pattern_description = "Nested recursive thinking with deep reflection"
        elif max_consecutive >= 2:
            recursion_type = "linear_recursion"
            pattern_description = "Linear sequence of recursive thinking"
        elif len(instances) > 4 and avg_score > 0.6:
            recursion_type = "mutual_recursion"
            pattern_description = "Interleaved recursive thinking across different statements"
        elif max_score > 0.8:
            recursion_type = "explosive_recursion"
            pattern_description = "High-intensity but sporadic recursive thinking"
        else:
            recursion_type = "tail_recursion"
            pattern_description = "Basic recursive thinking with summary reflections"
        
        # Get recursion type details if available
        recursion_details = self.recursion_types.get(recursion_type, {}) if recursion_type else {}
        
        return {
            "recursion_detected": recursion_depth > 0,
            "recursion_type": recursion_type,
            "recursion_depth": recursion_depth,
            "pattern_description": pattern_description,
            "consecutive_reflections": max_consecutive,
            "reflection_intensity": {
                "max": max_score,
                "average": avg_score
            },
            "recursion_details": recursion_details
        }


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Metacognitive Loop Monitor (KA-35) on the provided data.
    
    Args:
        data: A dictionary containing evaluations to analyze
        
    Returns:
        Dictionary with metacognitive analysis results
    """
    evaluations = data.get("evaluations", [])
    threshold = data.get("threshold", 0.5)
    
    if not evaluations:
        return {
            "algorithm": "KA-35",
            "error": "No evaluations provided for analysis",
            "success": False
        }
    
    monitor = MetacognitiveLoopMonitor()
    result = monitor.analyze_reasoning(evaluations, threshold)
    
    return {
        "algorithm": "KA-35",
        "reflections_detected": result["reflections_detected"],
        "details": result,
        "timestamp": time.time(),
        "success": True
    }
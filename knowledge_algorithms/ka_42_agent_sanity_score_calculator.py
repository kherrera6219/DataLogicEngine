"""
KA-42: Agent Sanity Score Calculator

This algorithm evaluates the sanity and validity of agent reasoning steps,
assigning a score based on logical consistency and validity markers.
"""

import logging
from typing import Dict, List, Any, Optional
import time
import re

logger = logging.getLogger(__name__)

class AgentSanityScoreCalculator:
    """
    KA-42: Calculates sanity scores for agent reasoning steps.
    
    This algorithm evaluates the logical coherence and validity of agent reasoning,
    providing a quantitative score for the overall sanity of a reasoning chain.
    """
    
    def __init__(self):
        """Initialize the Agent Sanity Score Calculator."""
        self.validity_markers = self._initialize_validity_markers()
        self.invalidity_markers = self._initialize_invalidity_markers()
        logger.info("KA-42: Agent Sanity Score Calculator initialized")
    
    def _initialize_validity_markers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize markers indicating valid reasoning."""
        return {
            "logical_structure": {
                "patterns": [
                    r"(?:therefore|thus|consequently|it follows that|we can conclude)",
                    r"(?:because|since|as|given that|for the reason that)",
                    r"(?:if|when|assuming that|in the case that|on the condition that).*(?:then|we have|it follows)"
                ],
                "weight": 0.7,
                "category": "inference"
            },
            "evidence_citing": {
                "patterns": [
                    r"(?:according to|as stated in|as mentioned in|reference|citation|source)",
                    r"(?:evidence shows|data indicates|research demonstrates|studies support)",
                    r"(?:demonstrated by|illustrated by|exemplified by|supported by)"
                ],
                "weight": 0.8,
                "category": "evidence"
            },
            "qualification": {
                "patterns": [
                    r"(?:however|nevertheless|although|despite|but|yet|on the other hand)",
                    r"(?:to some extent|partially|somewhat|approximately|roughly|about)",
                    r"(?:with the caveat that|with the exception of|excluding|apart from)"
                ],
                "weight": 0.6,
                "category": "nuance"
            },
            "uncertainty_acknowledgment": {
                "patterns": [
                    r"(?:uncertain|unclear|unknown|unproven|undetermined)",
                    r"(?:may|might|could|possibly|potentially|perhaps|probably)",
                    r"(?:confidence level|probability|likelihood|chance)"
                ],
                "weight": 0.5,
                "category": "uncertainty"
            },
            "methodology": {
                "patterns": [
                    r"(?:method|approach|technique|procedure|process)",
                    r"(?:systematically|methodically|step by step|procedurally)",
                    r"(?:analyze|evaluate|assess|measure|quantify|calculate)"
                ],
                "weight": 0.7,
                "category": "process"
            }
        }
    
    def _initialize_invalidity_markers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize markers indicating invalid reasoning."""
        return {
            "logical_fallacies": {
                "patterns": [
                    r"(?:all|every|everyone|nobody|always|never)",
                    r"(?:obviously|clearly|certainly|undoubtedly)",
                    r"(?:must|absolutely|definitely|undeniably)"
                ],
                "weight": 0.8,
                "category": "absolutism"
            },
            "circular_reasoning": {
                "patterns": [
                    r"(?:assumption|presuming|taking for granted|presupposing)",
                    r"(?:is true because it is true|proves itself|self-evident)",
                    r"(?:by definition|tautological|restating)"
                ],
                "weight": 0.9,
                "category": "circularity"
            },
            "inconsistency": {
                "patterns": [
                    r"(?:contradicts|conflicts with|inconsistent with|at odds with)",
                    r"(?:incompatible|mutually exclusive|cannot both be true)",
                    r"(?:contrary to|despite earlier|reversing|changing position)"
                ],
                "weight": 0.7,
                "category": "contradiction"
            },
            "unwarranted_leap": {
                "patterns": [
                    r"(?:suddenly|unexpectedly|surprisingly|without explanation)",
                    r"(?:inexplicably|mysteriously|jumping to|leaping to)",
                    r"(?:non sequitur|doesn't follow|unrelated)"
                ],
                "weight": 0.7,
                "category": "non_sequitur"
            },
            "emotionality": {
                "patterns": [
                    r"(?:outrageous|ridiculous|absurd|ludicrous)",
                    r"(?:shocking|horrifying|devastating|alarming)",
                    r"(?:wonderful|amazing|incredible|miraculous)"
                ],
                "weight": 0.6,
                "category": "emotional_language"
            }
        }
    
    def calculate_sanity_score(self, agent_steps: List[str], 
                            valid_threshold: float = 0.6) -> Dict[str, Any]:
        """
        Calculate sanity score for agent reasoning steps.
        
        Args:
            agent_steps: List of reasoning step strings
            valid_threshold: Threshold score for a step to be considered valid
            
        Returns:
            Dictionary with sanity analysis
        """
        # Skip empty input
        if not agent_steps:
            return {
                "sanity_score": 0.0,
                "valid_step_count": 0,
                "invalid_step_count": 0,
                "total_steps": 0,
                "step_scores": []
            }
        
        # Analyze each step
        step_scores = []
        valid_steps = 0
        invalid_steps = 0
        
        for i, step in enumerate(agent_steps):
            step_analysis = self._analyze_step(step)
            step_score = step_analysis["score"]
            
            # Count valid and invalid steps
            if step_score >= valid_threshold:
                valid_steps += 1
            else:
                invalid_steps += 1
            
            # Record step score
            step_scores.append({
                "step_index": i,
                "score": step_score,
                "valid": step_score >= valid_threshold,
                "analysis": step_analysis
            })
        
        # Calculate overall sanity score
        total_steps = len(agent_steps)
        sanity_score = valid_steps / total_steps if total_steps > 0 else 0.0
        
        # Round scores for readability
        sanity_score = round(sanity_score, 3)
        for step in step_scores:
            step["score"] = round(step["score"], 3)
        
        # Prepare result
        result = {
            "sanity_score": sanity_score,
            "valid_step_count": valid_steps,
            "invalid_step_count": invalid_steps,
            "total_steps": total_steps,
            "valid_threshold": valid_threshold,
            "step_scores": step_scores
        }
        
        return result
    
    def _analyze_step(self, step: str) -> Dict[str, Any]:
        """
        Analyze a single reasoning step.
        
        Args:
            step: The reasoning step string
            
        Returns:
            Dictionary with step analysis
        """
        # Initialize analysis
        validity_matches = {}
        invalidity_matches = {}
        validity_score = 0.0
        invalidity_score = 0.0
        
        # Convert to lowercase for pattern matching
        step_lower = step.lower()
        
        # Check validity markers
        for marker_name, marker_info in self.validity_markers.items():
            marker_matches = []
            
            for pattern in marker_info["patterns"]:
                matches = re.findall(pattern, step_lower)
                marker_matches.extend(matches)
            
            # Record matches if found
            if marker_matches:
                validity_matches[marker_name] = {
                    "count": len(marker_matches),
                    "examples": marker_matches[:3],  # Limit examples
                    "category": marker_info["category"],
                    "weight": marker_info["weight"]
                }
                
                # Add to validity score
                validity_score += marker_info["weight"] * min(1.0, len(marker_matches) / 3)
        
        # Check invalidity markers
        for marker_name, marker_info in self.invalidity_markers.items():
            marker_matches = []
            
            for pattern in marker_info["patterns"]:
                matches = re.findall(pattern, step_lower)
                marker_matches.extend(matches)
            
            # Record matches if found
            if marker_matches:
                invalidity_matches[marker_name] = {
                    "count": len(marker_matches),
                    "examples": marker_matches[:3],  # Limit examples
                    "category": marker_info["category"],
                    "weight": marker_info["weight"]
                }
                
                # Add to invalidity score
                invalidity_score += marker_info["weight"] * min(1.0, len(marker_matches) / 2)
        
        # Normalize scores
        max_validity = sum(info["weight"] for info in self.validity_markers.values())
        max_invalidity = sum(info["weight"] for info in self.invalidity_markers.values())
        
        validity_score = validity_score / max_validity if max_validity > 0 else 0
        invalidity_score = invalidity_score / max_invalidity if max_invalidity > 0 else 0
        
        # Calculate final score
        # Score = validity_score - invalidity_score, bounded to [0, 1]
        final_score = max(0.0, min(1.0, validity_score - (invalidity_score * 0.8)))
        
        # Prepare analysis result
        analysis = {
            "score": final_score,
            "validity_score": validity_score,
            "invalidity_score": invalidity_score,
            "validity_matches": validity_matches,
            "invalidity_matches": invalidity_matches,
            "step_length": len(step),
            "characteristic": self._get_step_characteristic(final_score)
        }
        
        return analysis
    
    def _get_step_characteristic(self, score: float) -> str:
        """
        Get characteristic description for a step based on score.
        
        Args:
            score: The step score
            
        Returns:
            Characteristic description
        """
        if score >= 0.9:
            return "exemplary"
        elif score >= 0.8:
            return "rigorous"
        elif score >= 0.7:
            return "solid"
        elif score >= 0.6:
            return "adequate"
        elif score >= 0.5:
            return "borderline"
        elif score >= 0.4:
            return "problematic"
        elif score >= 0.3:
            return "flawed"
        elif score >= 0.2:
            return "invalid"
        elif score >= 0.1:
            return "severely_flawed"
        else:
            return "nonsensical"


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Agent Sanity Score Calculator (KA-42) on the provided data.
    
    Args:
        data: A dictionary containing agent steps to evaluate
        
    Returns:
        Dictionary with sanity score results
    """
    agent_steps = data.get("agent_steps", [])
    valid_threshold = data.get("valid_threshold", 0.6)
    
    calculator = AgentSanityScoreCalculator()
    result = calculator.calculate_sanity_score(agent_steps, valid_threshold)
    
    return {
        "algorithm": "KA-42",
        "sanity_score": result["sanity_score"],
        "valid_steps": result["valid_step_count"],
        "invalid_steps": result["invalid_step_count"],
        "total_steps": result["total_steps"],
        "timestamp": time.time(),
        "success": True
    }
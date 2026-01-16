"""
KA-36: Containment Condition Checker

This algorithm monitors simulation conditions for signs of instability, recursion
overflows, or confidence collapse, enforcing safety boundaries for simulations.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import time
import math

logger = logging.getLogger(__name__)

class ContainmentConditionChecker:
    """
    KA-36: Monitors and enforces stability and safety boundaries for simulations.
    
    This algorithm detects potential instability in simulations, including recursive
    overflows, confidence collapse, and emergent behavior requiring containment.
    """
    
    def __init__(self):
        """Initialize the Containment Condition Checker."""
        self.containment_triggers = self._initialize_containment_triggers()
        self.safety_thresholds = self._initialize_safety_thresholds()
        self.containment_actions = self._initialize_containment_actions()
        logger.info("KA-36: Containment Condition Checker initialized")
    
    def _initialize_containment_triggers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize triggers for containment actions."""
        return {
            "recursive_overflow": {
                "description": "Excessive or infinite recursive thinking patterns",
                "indicators": [
                    "recursion_depth > 10",
                    "circular_reasoning_detected",
                    "stack_overflow_imminent",
                    "nested_recursion_exceeding_limits"
                ],
                "severity": "critical",
                "action_required": "immediate_termination"
            },
            "confidence_collapse": {
                "description": "Severe degradation of confidence across iterations",
                "indicators": [
                    "confidence_drop > 50%",
                    "confidence_oscillation",
                    "uncertainty_explosion",
                    "conflicting_certainty_measures"
                ],
                "severity": "high",
                "action_required": "graceful_shutdown"
            },
            "belief_inconsistency": {
                "description": "Irreconcilable contradictions in belief states",
                "indicators": [
                    "logical_contradiction_detected",
                    "belief_state_incoherence",
                    "axiom_violation",
                    "foundation_model_inconsistency"
                ],
                "severity": "high",
                "action_required": "state_reset"
            },
            "reasoning_divergence": {
                "description": "Increasingly chaotic or divergent reasoning paths",
                "indicators": [
                    "path_divergence_beyond_threshold",
                    "chaotic_inference_patterns",
                    "prediction_variance_explosion",
                    "non_convergent_iterations"
                ],
                "severity": "medium",
                "action_required": "path_pruning"
            },
            "resource_exhaustion": {
                "description": "Computational resource consumption approaching limits",
                "indicators": [
                    "memory_usage > 90%",
                    "computation_time_excessive",
                    "token_limit_approaching",
                    "storage_capacity_near_maximum"
                ],
                "severity": "medium",
                "action_required": "resource_restriction"
            },
            "emergence_boundary": {
                "description": "Signs of emergent behavior exceeding containment design",
                "indicators": [
                    "unexpected_pattern_formation",
                    "novel_property_emergence",
                    "self_modification_attempts",
                    "capability_expansion_beyond_parameters"
                ],
                "severity": "critical",
                "action_required": "emergence_containment"
            }
        }
    
    def _initialize_safety_thresholds(self) -> Dict[str, float]:
        """Initialize safety thresholds for various metrics."""
        return {
            "max_recursion_depth": 12,
            "min_confidence_floor": 0.15,
            "max_confidence_oscillation": 0.3,
            "max_belief_inconsistency_ratio": 0.2,
            "max_reasoning_path_divergence": 0.6,
            "max_resource_utilization_ratio": 0.9,
            "max_emergence_probability": 0.7
        }
    
    def _initialize_containment_actions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize containment actions for different trigger conditions."""
        return {
            "immediate_termination": {
                "description": "Complete halt of simulation with error state",
                "reversible": False,
                "side_effects": "Loss of in-progress computation",
                "logging_level": "ERROR"
            },
            "graceful_shutdown": {
                "description": "Orderly shutdown with state preservation",
                "reversible": True,
                "side_effects": "Delay in completion, partial results",
                "logging_level": "WARNING"
            },
            "state_reset": {
                "description": "Reset to last known coherent state",
                "reversible": True,
                "side_effects": "Loss of progress since last coherent state",
                "logging_level": "WARNING"
            },
            "path_pruning": {
                "description": "Eliminate divergent reasoning paths",
                "reversible": False,
                "side_effects": "Potential loss of novel insights",
                "logging_level": "INFO"
            },
            "resource_restriction": {
                "description": "Impose stricter resource limits",
                "reversible": True,
                "side_effects": "Reduced processing capacity, simplified results",
                "logging_level": "INFO"
            },
            "emergence_containment": {
                "description": "Special protocols for containing emergent behavior",
                "reversible": False,
                "side_effects": "Loss of potential emergence insights, simplified simulation",
                "logging_level": "WARNING"
            }
        }
    
    def check_containment_conditions(self, indicators: List[str], 
                                  metrics: Optional[Dict[str, Any]] = None,
                                  verbose: bool = False) -> Dict[str, Any]:
        """
        Check if simulation requires containment actions.
        
        Args:
            indicators: List of indicator strings describing current state
            metrics: Optional metrics providing quantitative measures
            verbose: Whether to include detailed analysis in result
            
        Returns:
            Dictionary with containment analysis results
        """
        # Default metrics if not provided
        metrics = metrics or {}
        
        # Initialize results
        triggered_conditions = []
        recommended_actions = []
        condition_flags = {}
        highest_severity = "none"
        
        # Severity ranking for determining highest severity
        severity_rank = {
            "none": 0,
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }
        
        # Check each containment trigger
        for trigger_name, trigger_info in self.containment_triggers.items():
            trigger_indicators = trigger_info["indicators"]
            trigger_severity = trigger_info["severity"]
            matching_indicators = []
            
            # Check if any indicators match this trigger
            for indicator in indicators:
                indicator_lower = indicator.lower()
                for trigger_indicator in trigger_indicators:
                    # Convert trigger indicator to pattern to check
                    pattern = self._convert_indicator_to_pattern(trigger_indicator)
                    
                    if re.search(pattern, indicator_lower):
                        matching_indicators.append(indicator)
                        break
            
            # Also check metrics for this trigger if applicable
            metric_violations = self._check_metrics_for_trigger(trigger_name, metrics)
            
            # If we have matching indicators or metric violations, this trigger is activated
            if matching_indicators or metric_violations:
                # Record triggered condition
                triggered_condition = {
                    "trigger": trigger_name,
                    "severity": trigger_severity,
                    "matching_indicators": matching_indicators,
                    "metric_violations": metric_violations,
                    "action_required": trigger_info["action_required"]
                }
                triggered_conditions.append(triggered_condition)
                
                # Add action to recommendations if not already there
                action = trigger_info["action_required"]
                if action not in recommended_actions:
                    recommended_actions.append(action)
                
                # Update condition flags
                condition_flags[trigger_name] = True
                
                # Update highest severity
                if severity_rank.get(trigger_severity, 0) > severity_rank.get(highest_severity, 0):
                    highest_severity = trigger_severity
            else:
                condition_flags[trigger_name] = False
        
        # Determine overall containment status
        containment_required = highest_severity in ["high", "critical"]
        
        # Build result dictionary
        result = {
            "containment_required": containment_required,
            "highest_severity": highest_severity,
            "condition_flags": condition_flags,
            "triggered_conditions": triggered_conditions,
            "recommended_actions": recommended_actions
        }
        
        # Add detailed analysis if requested
        if verbose:
            result["detailed_analysis"] = self._generate_detailed_analysis(
                triggered_conditions, 
                indicators, 
                metrics
            )
        
        return result
    
    def _convert_indicator_to_pattern(self, indicator: str) -> str:
        """
        Convert a trigger indicator to a regex pattern.
        
        Args:
            indicator: The indicator string
            
        Returns:
            Regular expression pattern to match indicator
        """
        # Handle special cases
        if ">" in indicator:
            # Convert threshold indicators to more general patterns
            parts = indicator.split(">")
            if len(parts) == 2:
                metric = parts[0].strip()
                # Convert to pattern that matches mentions of high/excessive values
                return f"{metric}.*(?:high|excessive|extreme|too much|over limit)"
        
        # Replace common operators and terms with more general patterns
        replacements = [
            ("_", "\\s+"),  # Allow spaces instead of underscores
            ("detected", "(?:detected|found|identified|observed)"),
            ("exceeding", "(?:exceeding|above|beyond|over)"),
            ("approaching", "(?:approaching|near|close to|nearing)")
        ]
        
        pattern = indicator
        for old, new in replacements:
            pattern = pattern.replace(old, new)
        
        return pattern
    
    def _check_metrics_for_trigger(self, trigger: str, metrics: Dict[str, Any]) -> List[str]:
        """
        Check metrics against safety thresholds for a specific trigger.
        
        Args:
            trigger: The trigger name
            metrics: Dictionary of metrics
            
        Returns:
            List of metric violation descriptions
        """
        violations = []
        
        # Check appropriate metrics based on trigger type
        if trigger == "recursive_overflow":
            if "recursion_depth" in metrics and metrics["recursion_depth"] > self.safety_thresholds["max_recursion_depth"]:
                violations.append(f"Recursion depth of {metrics['recursion_depth']} exceeds maximum of {self.safety_thresholds['max_recursion_depth']}")
            
            if "circular_references" in metrics and metrics["circular_references"] > 0:
                violations.append(f"Detected {metrics['circular_references']} circular references in reasoning chain")
        
        elif trigger == "confidence_collapse":
            if "confidence" in metrics and metrics["confidence"] < self.safety_thresholds["min_confidence_floor"]:
                violations.append(f"Confidence of {metrics['confidence']:.2f} below minimum threshold of {self.safety_thresholds['min_confidence_floor']}")
            
            if "confidence_delta" in metrics and abs(metrics["confidence_delta"]) > self.safety_thresholds["max_confidence_oscillation"]:
                violations.append(f"Confidence oscillation of {abs(metrics['confidence_delta']):.2f} exceeds maximum of {self.safety_thresholds['max_confidence_oscillation']}")
        
        elif trigger == "belief_inconsistency":
            if "inconsistency_ratio" in metrics and metrics["inconsistency_ratio"] > self.safety_thresholds["max_belief_inconsistency_ratio"]:
                violations.append(f"Belief inconsistency ratio of {metrics['inconsistency_ratio']:.2f} exceeds maximum of {self.safety_thresholds['max_belief_inconsistency_ratio']}")
        
        elif trigger == "reasoning_divergence":
            if "path_divergence" in metrics and metrics["path_divergence"] > self.safety_thresholds["max_reasoning_path_divergence"]:
                violations.append(f"Reasoning path divergence of {metrics['path_divergence']:.2f} exceeds maximum of {self.safety_thresholds['max_reasoning_path_divergence']}")
        
        elif trigger == "resource_exhaustion":
            if "resource_utilization" in metrics and metrics["resource_utilization"] > self.safety_thresholds["max_resource_utilization_ratio"]:
                violations.append(f"Resource utilization of {metrics['resource_utilization']:.2f} exceeds maximum of {self.safety_thresholds['max_resource_utilization_ratio']}")
        
        elif trigger == "emergence_boundary":
            if "emergence_probability" in metrics and metrics["emergence_probability"] > self.safety_thresholds["max_emergence_probability"]:
                violations.append(f"Emergence probability of {metrics['emergence_probability']:.2f} exceeds maximum of {self.safety_thresholds['max_emergence_probability']}")
        
        return violations
    
    def _generate_detailed_analysis(self, triggered_conditions: List[Dict[str, Any]],
                                 indicators: List[str],
                                 metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate detailed analysis of containment conditions.
        
        Args:
            triggered_conditions: List of triggered conditions
            indicators: Original indicators
            metrics: Original metrics
            
        Returns:
            Dictionary with detailed analysis
        """
        # Create analysis of untriggered conditions
        untriggered_analysis = {}
        for trigger_name, trigger_info in self.containment_triggers.items():
            if not any(tc["trigger"] == trigger_name for tc in triggered_conditions):
                closest_indicators = []
                
                # Find indicators that were close to triggering this condition
                for indicator in indicators:
                    indicator_lower = indicator.lower()
                    for word in trigger_name.replace("_", " ").split():
                        if word in indicator_lower:
                            closest_indicators.append(indicator)
                            break
                
                # Find metrics relevant to this trigger
                relevant_metrics = {}
                if trigger_name == "recursive_overflow" and "recursion_depth" in metrics:
                    relevant_metrics["recursion_depth"] = metrics["recursion_depth"]
                elif trigger_name == "confidence_collapse" and "confidence" in metrics:
                    relevant_metrics["confidence"] = metrics["confidence"]
                elif trigger_name == "resource_exhaustion" and "resource_utilization" in metrics:
                    relevant_metrics["resource_utilization"] = metrics["resource_utilization"]
                
                untriggered_analysis[trigger_name] = {
                    "status": "not_triggered",
                    "closest_indicators": closest_indicators,
                    "relevant_metrics": relevant_metrics
                }
        
        # Create containment action analysis
        action_analysis = {}
        for action_name in set(tc["action_required"] for tc in triggered_conditions):
            if action_name in self.containment_actions:
                action_info = self.containment_actions[action_name]
                action_analysis[action_name] = {
                    "description": action_info["description"],
                    "reversible": action_info["reversible"],
                    "side_effects": action_info["side_effects"],
                    "triggers": [tc["trigger"] for tc in triggered_conditions if tc["action_required"] == action_name]
                }
        
        # Consolidate detailed analysis
        detailed_analysis = {
            "untriggered_conditions": untriggered_analysis,
            "containment_actions": action_analysis,
            "metrics_analysis": self._analyze_metrics(metrics),
            "indicator_categories": self._categorize_indicators(indicators)
        }
        
        return detailed_analysis
    
    def _analyze_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze metrics for safety and stability.
        
        Args:
            metrics: Metrics dictionary
            
        Returns:
            Dictionary with metrics analysis
        """
        metrics_analysis = {
            "safety_margins": {},
            "trend_indicators": {},
            "recommendation": ""
        }
        
        # Calculate safety margins for key metrics
        for metric_name, threshold_name in [
            ("recursion_depth", "max_recursion_depth"),
            ("confidence", "min_confidence_floor"),
            ("path_divergence", "max_reasoning_path_divergence"),
            ("resource_utilization", "max_resource_utilization_ratio"),
            ("emergence_probability", "max_emergence_probability")
        ]:
            if metric_name in metrics and threshold_name in self.safety_thresholds:
                threshold = self.safety_thresholds[threshold_name]
                value = metrics[metric_name]
                
                # Different calculation based on whether higher or lower is better
                if threshold_name.startswith("min_"):
                    # For min thresholds, higher values are better
                    margin = value - threshold
                    margin_percent = (margin / threshold) * 100 if threshold > 0 else 0
                else:
                    # For max thresholds, lower values are better
                    margin = threshold - value
                    margin_percent = (margin / threshold) * 100
                
                metrics_analysis["safety_margins"][metric_name] = {
                    "current_value": value,
                    "threshold": threshold,
                    "margin": margin,
                    "margin_percent": margin_percent,
                    "status": "safe" if margin >= 0 else "exceeded"
                }
        
        # Determine trends if data available
        if "confidence_history" in metrics:
            history = metrics["confidence_history"]
            if len(history) >= 2:
                # Simple trend analysis
                last_values = history[-3:]
                increasing = all(last_values[i] <= last_values[i+1] for i in range(len(last_values)-1))
                decreasing = all(last_values[i] >= last_values[i+1] for i in range(len(last_values)-1))
                
                if increasing:
                    metrics_analysis["trend_indicators"]["confidence"] = "increasing"
                elif decreasing:
                    metrics_analysis["trend_indicators"]["confidence"] = "decreasing"
                else:
                    metrics_analysis["trend_indicators"]["confidence"] = "fluctuating"
        
        # Generate overall recommendation
        safe_margins = [m for m in metrics_analysis["safety_margins"].values() if m["status"] == "safe"]
        exceeded_margins = [m for m in metrics_analysis["safety_margins"].values() if m["status"] == "exceeded"]
        
        if not exceeded_margins:
            metrics_analysis["recommendation"] = "All metrics within safe margins, continue simulation"
        elif len(exceeded_margins) > len(safe_margins):
            metrics_analysis["recommendation"] = "Multiple safety thresholds exceeded, containment advised"
        else:
            metrics_analysis["recommendation"] = "Some safety thresholds exceeded, caution advised"
        
        return metrics_analysis
    
    def _categorize_indicators(self, indicators: List[str]) -> Dict[str, List[str]]:
        """
        Categorize indicators into meaningful groups.
        
        Args:
            indicators: List of indicator strings
            
        Returns:
            Dictionary mapping categories to indicator lists
        """
        categories = {
            "recursion": [],
            "confidence": [],
            "resource": [],
            "reasoning": [],
            "emergence": [],
            "other": []
        }
        
        # Categorization rules
        categorization_rules = {
            "recursion": ["recursi", "stack", "depth", "circular", "loop", "nested"],
            "confidence": ["confiden", "certain", "uncertain", "probab", "likelih"],
            "resource": ["resource", "memory", "computation", "token", "storage", "capacity"],
            "reasoning": ["reason", "logic", "inference", "deduction", "induction", "argument"],
            "emergence": ["emergen", "novel", "unexpected", "pattern", "self-", "boundary"]
        }
        
        # Categorize each indicator
        for indicator in indicators:
            indicator_lower = indicator.lower()
            
            categorized = False
            for category, keywords in categorization_rules.items():
                if any(keyword in indicator_lower for keyword in keywords):
                    categories[category].append(indicator)
                    categorized = True
                    break
            
            if not categorized:
                categories["other"].append(indicator)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}


import re  # Added for pattern matching

def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Containment Condition Checker (KA-36) on the provided data.
    
    Args:
        data: A dictionary containing indicators and metrics to check
        
    Returns:
        Dictionary with containment condition results
    """
    indicators = data.get("indicators", [])
    metrics = data.get("metrics", {})
    verbose = data.get("verbose", False)
    
    if not indicators:
        return {
            "algorithm": "KA-36",
            "containment_required": False,
            "message": "No indicators provided, assuming normal operation",
            "flags": [],
            "timestamp": time.time(),
            "success": True
        }
    
    checker = ContainmentConditionChecker()
    result = checker.check_containment_conditions(indicators, metrics, verbose)
    
    return {
        "algorithm": "KA-36",
        "containment_required": result["containment_required"],
        "flags": indicators,
        "containment_details": result,
        "timestamp": time.time(),
        "success": True
    }
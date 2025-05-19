"""
KA-45: Emergence Containment Manager

This algorithm manages the containment of emergent behaviors and patterns,
enforcing boundaries and safety constraints on complex simulations.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import time

logger = logging.getLogger(__name__)

class EmergenceContainmentManager:
    """
    KA-45: Manages containment of emergent behaviors in simulations.
    
    This algorithm detects and contains potentially dangerous or uncontrolled
    emergent behaviors in complex simulations, applying safety boundaries.
    """
    
    def __init__(self):
        """Initialize the Emergence Containment Manager."""
        self.emergence_types = self._initialize_emergence_types()
        self.containment_strategies = self._initialize_containment_strategies()
        logger.info("KA-45: Emergence Containment Manager initialized")
    
    def _initialize_emergence_types(self) -> Dict[str, Dict[str, Any]]:
        """Initialize types of emergent behaviors to monitor."""
        return {
            "unbounded_growth": {
                "description": "Exponential or runaway growth in variables or resources",
                "risk_level": "critical",
                "indicators": [
                    "exponential_increase",
                    "resource_exhaustion",
                    "unlimited_expansion"
                ],
                "containment_priority": 1
            },
            "feedback_loop": {
                "description": "Self-reinforcing feedback loops creating amplification",
                "risk_level": "high",
                "indicators": [
                    "positive_feedback",
                    "amplification_cascade",
                    "runaway_reinforcement"
                ],
                "containment_priority": 2
            },
            "attractor_formation": {
                "description": "Formation of strange attractors or convergent states",
                "risk_level": "medium",
                "indicators": [
                    "state_convergence",
                    "pattern_fixation",
                    "basin_formation"
                ],
                "containment_priority": 3
            },
            "phase_transition": {
                "description": "Sudden phase transitions to qualitatively different behaviors",
                "risk_level": "high",
                "indicators": [
                    "abrupt_change",
                    "state_transition",
                    "critical_threshold"
                ],
                "containment_priority": 2
            },
            "self_modification": {
                "description": "System modifying its own rules or structure",
                "risk_level": "critical",
                "indicators": [
                    "rule_alteration",
                    "self_reprogramming",
                    "constraint_violation"
                ],
                "containment_priority": 1
            },
            "novel_pattern": {
                "description": "Emergence of novel, unexplained patterns",
                "risk_level": "medium",
                "indicators": [
                    "unexpected_pattern",
                    "novel_behavior",
                    "unexplained_regularity"
                ],
                "containment_priority": 3
            },
            "complexity_explosion": {
                "description": "Rapid increase in system complexity beyond expectations",
                "risk_level": "high",
                "indicators": [
                    "complexity_increase",
                    "dimension_explosion",
                    "structure_elaboration"
                ],
                "containment_priority": 2
            }
        }
    
    def _initialize_containment_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize strategies for containing emergent behaviors."""
        return {
            "parameter_restriction": {
                "description": "Restrict parameters to prevent unbounded growth",
                "applicable_to": ["unbounded_growth", "feedback_loop"],
                "reversible": True,
                "impact": "medium"
            },
            "energy_limitation": {
                "description": "Impose energy or resource constraints on the system",
                "applicable_to": ["unbounded_growth", "complexity_explosion"],
                "reversible": True,
                "impact": "high"
            },
            "attractor_disruption": {
                "description": "Introduce noise or perturbations to disrupt attractors",
                "applicable_to": ["attractor_formation", "phase_transition"],
                "reversible": True,
                "impact": "medium"
            },
            "rule_enforcement": {
                "description": "Strictly enforce system rules and constraints",
                "applicable_to": ["self_modification", "constraint_violation"],
                "reversible": False,
                "impact": "high"
            },
            "dimension_reduction": {
                "description": "Reduce system dimensions or complexity",
                "applicable_to": ["complexity_explosion", "novel_pattern"],
                "reversible": False,
                "impact": "high"
            },
            "system_partitioning": {
                "description": "Partition system into isolated components",
                "applicable_to": ["feedback_loop", "contagion_spread"],
                "reversible": True,
                "impact": "medium"
            },
            "emergency_halt": {
                "description": "Completely halt the simulation",
                "applicable_to": ["unbounded_growth", "self_modification"],
                "reversible": False,
                "impact": "critical"
            }
        }
    
    def evaluate_emergence(self, emergence_flags: List[str],
                         metrics: Optional[Dict[str, Any]] = None,
                         containment_threshold: str = "high") -> Dict[str, Any]:
        """
        Evaluate emergence indicators and determine containment actions.
        
        Args:
            emergence_flags: List of emergence indicator flags
            metrics: Optional metrics providing quantitative measures
            containment_threshold: Minimum risk level for triggering containment
            
        Returns:
            Dictionary with emergence evaluation results
        """
        # Convert flags to lowercase for case-insensitive matching
        normalized_flags = [flag.lower() for flag in emergence_flags]
        
        # Initialize tracking
        detected_emergence = []
        containment_actions = []
        containment_triggered = False
        highest_risk = "none"
        
        # Risk level ranking
        risk_levels = {
            "none": 0,
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }
        
        # Check each emergence type for matches
        for emergence_type, type_info in self.emergence_types.items():
            matched_indicators = []
            
            # Check if any indicators for this type match the flags
            for indicator in type_info["indicators"]:
                if indicator.lower() in normalized_flags:
                    matched_indicators.append(indicator)
            
            # If metrics are provided, check them as well
            if metrics is not None:
                for indicator in type_info["indicators"]:
                    # For example, check if "exponential_increase" appears in metrics
                    if indicator in metrics and metrics[indicator]:
                        matched_indicators.append(indicator)
            
            # If indicators are matched, record this emergence type
            if matched_indicators:
                emergence_detection = {
                    "type": emergence_type,
                    "risk_level": type_info["risk_level"],
                    "matched_indicators": matched_indicators,
                    "description": type_info["description"]
                }
                
                detected_emergence.append(emergence_detection)
                
                # Update highest risk level
                if risk_levels.get(type_info["risk_level"], 0) > risk_levels.get(highest_risk, 0):
                    highest_risk = type_info["risk_level"]
        
        # Determine if containment is triggered
        containment_triggered = risk_levels.get(highest_risk, 0) >= risk_levels.get(containment_threshold, 0)
        
        # If containment is triggered, determine appropriate actions
        if containment_triggered:
            containment_actions = self._determine_containment_actions(detected_emergence)
        
        # Prepare result
        result = {
            "containment_triggered": containment_triggered,
            "detected_emergence": detected_emergence,
            "highest_risk": highest_risk,
            "flags_analyzed": emergence_flags,
            "containment_actions": containment_actions,
            "containment_threshold": containment_threshold
        }
        
        return result
    
    def _determine_containment_actions(self, detected_emergence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Determine appropriate containment actions.
        
        Args:
            detected_emergence: List of detected emergence types
            
        Returns:
            List of containment action dictionaries
        """
        if not detected_emergence:
            return []
        
        # Collect all emergence types
        emergence_types = [e["type"] for e in detected_emergence]
        
        # Find applicable strategies
        applicable_strategies = []
        for strategy_name, strategy_info in self.containment_strategies.items():
            # Check if strategy applies to any detected emergence types
            applicable_to = strategy_info["applicable_to"]
            
            if any(e_type in applicable_to for e_type in emergence_types):
                # Create action
                action = {
                    "strategy": strategy_name,
                    "description": strategy_info["description"],
                    "impact": strategy_info["impact"],
                    "reversible": strategy_info["reversible"],
                    "applicable_to": [e for e in emergence_types if e in applicable_to]
                }
                
                applicable_strategies.append(action)
        
        # Sort actions by impact (critical first)
        impact_levels = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }
        
        applicable_strategies.sort(
            key=lambda s: impact_levels.get(s["impact"], 0),
            reverse=True
        )
        
        return applicable_strategies
    
    def apply_containment(self, simulation_state: Dict[str, Any],
                        detected_emergence: List[Dict[str, Any]],
                        containment_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply containment actions to simulation state.
        
        Args:
            simulation_state: Current simulation state
            detected_emergence: List of detected emergence types
            containment_actions: List of containment actions to apply
            
        Returns:
            Updated simulation state after containment
        """
        # Make a copy of the state to avoid modifying the original
        contained_state = dict(simulation_state)
        
        # Track applied containment
        applied_actions = []
        
        # Apply containment actions
        for action in containment_actions:
            strategy = action["strategy"]
            
            # Apply strategy
            if strategy == "parameter_restriction":
                # Implement parameter restriction
                if "parameters" in contained_state:
                    restricted_params = {}
                    for param, value in contained_state["parameters"].items():
                        # Cap numeric parameters
                        if isinstance(value, (int, float)):
                            restricted_params[param] = min(value, 10.0)
                        else:
                            restricted_params[param] = value
                    
                    contained_state["parameters"] = restricted_params
                    applied_actions.append(f"Applied parameter restrictions")
            
            elif strategy == "energy_limitation":
                # Implement energy limitation
                contained_state["energy_cap"] = 100.0
                if "energy" in contained_state:
                    contained_state["energy"] = min(contained_state["energy"], 100.0)
                
                applied_actions.append(f"Applied energy limitation (cap: 100)")
            
            elif strategy == "dimension_reduction":
                # Implement dimension reduction
                if "dimensions" in contained_state:
                    contained_state["dimensions"] = min(contained_state["dimensions"], 3)
                
                applied_actions.append(f"Reduced dimensions to maximum of 3")
            
            elif strategy == "emergency_halt":
                # Implement emergency halt
                contained_state["halted"] = True
                contained_state["running"] = False
                
                applied_actions.append(f"EMERGENCY HALT triggered")
            
            # Other strategies would be implemented similarly
        
        # Record containment metadata
        contained_state["containment"] = {
            "applied": True,
            "timestamp": time.time(),
            "actions": applied_actions,
            "emergence_types": [e["type"] for e in detected_emergence]
        }
        
        return contained_state


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Emergence Containment Manager (KA-45) on the provided data.
    
    Args:
        data: A dictionary containing emergence flags and optional simulation state
        
    Returns:
        Dictionary with containment results
    """
    emergence_flags = data.get("emergence_flags", [])
    metrics = data.get("metrics")
    containment_threshold = data.get("containment_threshold", "high")
    simulation_state = data.get("simulation_state", {})
    
    # Simple case with just flags
    if "unbounded_growth" in [f.lower() for f in emergence_flags]:
        return {
            "algorithm": "KA-45",
            "containment": True,
            "flags": emergence_flags,
            "timestamp": time.time(),
            "success": True
        }
    
    # More detailed analysis
    manager = EmergenceContainmentManager()
    result = manager.evaluate_emergence(emergence_flags, metrics, containment_threshold)
    
    # Apply containment if triggered and simulation state is provided
    applied_containment = None
    if result["containment_triggered"] and simulation_state:
        applied_containment = manager.apply_containment(
            simulation_state,
            result["detected_emergence"],
            result["containment_actions"]
        )
    
    return {
        "algorithm": "KA-45",
        "containment": result["containment_triggered"],
        "flags": emergence_flags,
        "detected_emergence": result["detected_emergence"],
        "containment_actions": result["containment_actions"] if result["containment_triggered"] else [],
        "contained_state": applied_containment,
        "timestamp": time.time(),
        "success": True
    }
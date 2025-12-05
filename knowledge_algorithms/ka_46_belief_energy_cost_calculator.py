"""
KA-46: Belief Energy Cost Calculator

This algorithm calculates the computational and cognitive energy costs of maintaining
and updating belief states during reasoning and decision-making processes.
"""

import logging
from typing import Dict, List, Any, Optional
import time

logger = logging.getLogger(__name__)

class BeliefEnergyCostCalculator:
    """
    KA-46: Calculates energy costs for belief operations.
    
    This algorithm models the computational and cognitive costs of maintaining,
    updating, and reasoning with beliefs, using energy as a unit of measure.
    """
    
    def __init__(self):
        """Initialize the Belief Energy Cost Calculator."""
        self.operation_costs = self._initialize_operation_costs()
        self.belief_complexities = self._initialize_belief_complexities()
        logger.info("KA-46: Belief Energy Cost Calculator initialized")
    
    def _initialize_operation_costs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize energy costs for different belief operations."""
        return {
            "creation": {
                "description": "Creating a new belief",
                "base_cost": 0.8,
                "complexity_factor": 1.2,
                "uncertainty_factor": 0.5
            },
            "update": {
                "description": "Updating an existing belief",
                "base_cost": 0.5,
                "complexity_factor": 1.0,
                "uncertainty_factor": 0.7
            },
            "inference": {
                "description": "Deriving a new belief from existing beliefs",
                "base_cost": 1.2,
                "complexity_factor": 1.5,
                "uncertainty_factor": 1.0
            },
            "consistency_check": {
                "description": "Checking consistency between beliefs",
                "base_cost": 0.3,
                "complexity_factor": 1.3,
                "uncertainty_factor": 0.2
            },
            "revision": {
                "description": "Revising beliefs due to contradictions",
                "base_cost": 1.5,
                "complexity_factor": 1.4,
                "uncertainty_factor": 1.2
            }
        }
    
    def _initialize_belief_complexities(self) -> Dict[str, Dict[str, Any]]:
        """Initialize complexity factors for different belief types."""
        return {
            "atomic": {
                "description": "Simple atomic beliefs with no internal structure",
                "complexity_score": 1.0,
                "example": "The sky is blue"
            },
            "compound": {
                "description": "Beliefs composed of multiple atomic beliefs",
                "complexity_score": 1.5,
                "example": "If it rains, then the ground will be wet"
            },
            "probabilistic": {
                "description": "Beliefs with explicit probability estimates",
                "complexity_score": 1.8,
                "example": "There is an 80% chance of rain tomorrow"
            },
            "temporal": {
                "description": "Beliefs involving time and temporal reasoning",
                "complexity_score": 2.0,
                "example": "After the meeting, we will have lunch"
            },
            "nested": {
                "description": "Beliefs about other beliefs (meta-beliefs)",
                "complexity_score": 2.5,
                "example": "Alice believes that Bob thinks it will rain"
            },
            "counterfactual": {
                "description": "Beliefs about what could have happened",
                "complexity_score": 2.2,
                "example": "If I had left earlier, I would have caught the train"
            },
            "quantified": {
                "description": "Beliefs with quantifiers (all, some, none)",
                "complexity_score": 1.7,
                "example": "All birds can fly"
            }
        }
    
    def calculate_energy_cost(self, decisions: List[Dict[str, Any]],
                           base_rate: float = 0.042) -> Dict[str, Any]:
        """
        Calculate energy costs for a series of decisions or belief operations.
        
        Args:
            decisions: List of decision or belief operation descriptions
            base_rate: Base energy rate per operation
            
        Returns:
            Dictionary with energy cost analysis
        """
        # Initialize costs
        total_cost = 0.0
        operation_costs = {}
        complexity_costs = {}
        
        # Process each decision
        decision_costs = []
        for i, decision in enumerate(decisions):
            # Extract decision info
            operation = decision.get("operation", "inference")
            complexity = decision.get("complexity", "atomic")
            uncertainty = decision.get("uncertainty", 0.5)
            description = decision.get("description", f"Decision {i+1}")
            
            # Get cost factors
            op_info = self.operation_costs.get(operation, self.operation_costs["inference"])
            complexity_info = self.belief_complexities.get(complexity, self.belief_complexities["atomic"])
            
            # Calculate cost components
            base_cost = op_info["base_cost"] * base_rate
            complexity_cost = base_cost * op_info["complexity_factor"] * complexity_info["complexity_score"]
            uncertainty_cost = base_cost * op_info["uncertainty_factor"] * uncertainty
            
            # Calculate total decision cost
            decision_cost = base_cost + complexity_cost + uncertainty_cost
            
            # Track costs
            total_cost += decision_cost
            
            # Update operation costs
            if operation in operation_costs:
                operation_costs[operation] += decision_cost
            else:
                operation_costs[operation] = decision_cost
            
            # Update complexity costs
            if complexity in complexity_costs:
                complexity_costs[complexity] += decision_cost
            else:
                complexity_costs[complexity] = decision_cost
            
            # Record decision cost
            decision_costs.append({
                "index": i,
                "description": description,
                "operation": operation,
                "complexity": complexity,
                "uncertainty": uncertainty,
                "cost": round(decision_cost, 4),
                "components": {
                    "base": round(base_cost, 4),
                    "complexity": round(complexity_cost, 4),
                    "uncertainty": round(uncertainty_cost, 4)
                }
            })
        
        # Round costs for display
        total_cost = round(total_cost, 3)
        operation_costs = {k: round(v, 3) for k, v in operation_costs.items()}
        complexity_costs = {k: round(v, 3) for k, v in complexity_costs.items()}
        
        # Calculate summary statistics
        avg_cost = total_cost / len(decisions) if decisions else 0
        max_cost = max(d["cost"] for d in decision_costs) if decision_costs else 0
        min_cost = min(d["cost"] for d in decision_costs) if decision_costs else 0
        
        # Identify most energy-intensive operations and complexities
        most_expensive_operation = max(operation_costs.items(), key=lambda x: x[1])[0] if operation_costs else None
        most_expensive_complexity = max(complexity_costs.items(), key=lambda x: x[1])[0] if complexity_costs else None
        
        # Prepare result
        result = {
            "total_energy_cost": total_cost,
            "decisions_count": len(decisions),
            "average_cost": round(avg_cost, 3),
            "operation_costs": operation_costs,
            "complexity_costs": complexity_costs,
            "decision_costs": decision_costs,
            "most_expensive_operation": most_expensive_operation,
            "most_expensive_complexity": most_expensive_complexity,
            "cost_range": {
                "min": round(min_cost, 3),
                "max": round(max_cost, 3),
                "spread": round(max_cost - min_cost, 3)
            },
            "base_rate": base_rate
        }
        
        return result
    
    def estimate_from_text(self, text_decisions: List[str],
                         operation_mapping: Optional[Dict[str, str]] = None,
                         base_rate: float = 0.042) -> Dict[str, Any]:
        """
        Estimate energy costs from text descriptions of decisions.
        
        Args:
            text_decisions: List of decision text descriptions
            operation_mapping: Optional mapping of keywords to operations
            base_rate: Base energy rate per operation
            
        Returns:
            Dictionary with energy cost analysis
        """
        # Default operation mapping if not provided
        if operation_mapping is None:
            operation_mapping = {
                "create": "creation",
                "new": "creation",
                "update": "update",
                "revise": "update",
                "modify": "update",
                "infer": "inference",
                "conclude": "inference",
                "deduce": "inference",
                "check": "consistency_check",
                "verify": "consistency_check",
                "validate": "consistency_check",
                "contradict": "revision",
                "correct": "revision",
                "resolve": "revision"
            }
        
        # Default complexity mapping
        complexity_mapping = {
            "simple": "atomic",
            "basic": "atomic",
            "compound": "compound",
            "complex": "compound",
            "probability": "probabilistic",
            "likely": "probabilistic",
            "time": "temporal",
            "when": "temporal",
            "belief about": "nested",
            "thinks that": "nested",
            "would have": "counterfactual",
            "could have": "counterfactual",
            "all": "quantified",
            "every": "quantified",
            "some": "quantified",
            "none": "quantified"
        }
        
        # Convert text decisions to structured decisions
        structured_decisions = []
        
        for i, text in enumerate(text_decisions):
            text_lower = text.lower()
            
            # Determine operation
            operation = "inference"  # Default
            for keyword, op_type in operation_mapping.items():
                if keyword.lower() in text_lower:
                    operation = op_type
                    break
            
            # Determine complexity
            complexity = "atomic"  # Default
            for keyword, comp_type in complexity_mapping.items():
                if keyword.lower() in text_lower:
                    complexity = comp_type
                    break
            
            # Estimate uncertainty based on hedging language
            uncertainty = 0.5  # Default medium uncertainty
            uncertainty_markers = {
                "certain": 0.1,
                "confident": 0.2,
                "likely": 0.4,
                "possibly": 0.6,
                "maybe": 0.7,
                "uncertain": 0.8,
                "doubt": 0.9
            }
            
            for marker, value in uncertainty_markers.items():
                if marker in text_lower:
                    uncertainty = value
                    break
            
            # Create structured decision
            structured_decision = {
                "operation": operation,
                "complexity": complexity,
                "uncertainty": uncertainty,
                "description": text
            }
            
            structured_decisions.append(structured_decision)
        
        # Calculate energy costs using the structured decisions
        return self.calculate_energy_cost(structured_decisions, base_rate)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Belief Energy Cost Calculator (KA-46) on the provided data.
    
    Args:
        data: A dictionary containing decisions to analyze
        
    Returns:
        Dictionary with energy cost results
    """
    # Check for text decisions
    text_decisions = data.get("text_decisions")
    if text_decisions:
        operation_mapping = data.get("operation_mapping")
        base_rate = data.get("base_rate", 0.042)
        
        calculator = BeliefEnergyCostCalculator()
        result = calculator.estimate_from_text(text_decisions, operation_mapping, base_rate)
        
        return {
            "algorithm": "KA-46",
            "energy_cost": result["total_energy_cost"],
            "decisions_count": result["decisions_count"],
            "cost_details": result,
            "timestamp": time.time(),
            "success": True
        }
    
    # Check for structured decisions
    decisions = data.get("decisions", [])
    base_rate = data.get("base_rate", 0.042)
    
    # Simple case with minimal details
    if isinstance(decisions, int):
        # Just a count was provided, create simple decisions
        decisions = [{"operation": "inference", "complexity": "atomic", "uncertainty": 0.5} for _ in range(decisions)]
    
    # Process with full calculator
    calculator = BeliefEnergyCostCalculator()
    result = calculator.calculate_energy_cost(decisions, base_rate)
    
    return {
        "algorithm": "KA-46",
        "energy_cost": result["total_energy_cost"],
        "decisions_count": result["decisions_count"],
        "timestamp": time.time(),
        "success": True
    }
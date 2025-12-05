"""
KA-56: Recursive Planning AGI Core

This algorithm enables recursive planning and goal decomposition,
implementing a hierarchical planning system that breaks complex goals
into manageable sub-goals with dependency tracking.
"""

import logging
from typing import Dict, List, Any, Set, Tuple
import time
import random
import uuid
import copy
from collections import deque

logger = logging.getLogger(__name__)

class RecursivePlanningAGICore:
    """
    KA-56: Recursive Planning AGI Core.
    
    This algorithm implements a hierarchical planning system that recursively
    decomposes complex goals into manageable sub-goals, tracks dependencies,
    and optimizes execution paths while maintaining goal alignment.
    """
    
    def __init__(self):
        """Initialize the Recursive Planning AGI Core."""
        self.planning_strategies = self._initialize_planning_strategies()
        self.goal_types = self._initialize_goal_types()
        self.execution_modes = self._initialize_execution_modes()
        self.dependency_types = self._initialize_dependency_types()
        logger.info("KA-56: Recursive Planning AGI Core initialized")
    
    def _initialize_planning_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize planning strategies for different goal types."""
        return {
            "decomposition": {
                "description": "Break complex goals into simpler sub-goals",
                "applicable_to": ["high_level", "complex_task", "long_term"],
                "max_recursion_depth": 5,
                "branching_factor": [3, 7]  # Min, max number of sub-goals
            },
            "sequential": {
                "description": "Arrange sub-goals in strict sequence",
                "applicable_to": ["procedural", "step_by_step", "linear"],
                "dependency_handling": "strict",
                "parallelization": "none"
            },
            "parallel": {
                "description": "Identify sub-goals that can be executed concurrently",
                "applicable_to": ["distributed", "independent_tasks", "efficiency_critical"],
                "dependency_handling": "partial",
                "parallelization": "maximum"
            },
            "iterative": {
                "description": "Execute similar sub-goals repeatedly with refinement",
                "applicable_to": ["learning", "optimization", "refinement"],
                "max_iterations": 10,
                "convergence_threshold": 0.01
            },
            "adaptive": {
                "description": "Adjust sub-goals based on feedback during execution",
                "applicable_to": ["uncertain_environment", "complex_feedback", "dynamic"],
                "feedback_frequency": "continuous",
                "adaptation_threshold": 0.3
            },
            "constraint_based": {
                "description": "Define goals in terms of constraints to be satisfied",
                "applicable_to": ["optimization", "resource_allocation", "satisfiability"],
                "constraint_types": ["hard", "soft"],
                "optimization_method": "constraint_satisfaction"
            }
        }
    
    def _initialize_goal_types(self) -> Dict[str, Dict[str, Any]]:
        """Initialize types of goals for planning."""
        return {
            "achievement": {
                "description": "Reach a specific target state",
                "verification_method": "state_comparison",
                "example": "Analyze the data and produce a report",
                "preferred_strategies": ["decomposition", "sequential"]
            },
            "maintenance": {
                "description": "Keep a system within specified parameters",
                "verification_method": "continuous_monitoring",
                "example": "Keep error rate below 0.1% during operation",
                "preferred_strategies": ["adaptive", "constraint_based"]
            },
            "optimization": {
                "description": "Maximize or minimize some value",
                "verification_method": "metric_evaluation",
                "example": "Minimize energy consumption while maintaining performance",
                "preferred_strategies": ["iterative", "constraint_based"]
            },
            "learning": {
                "description": "Acquire knowledge or skills",
                "verification_method": "performance_testing",
                "example": "Learn to classify images with 95% accuracy",
                "preferred_strategies": ["iterative", "adaptive"]
            },
            "exploration": {
                "description": "Gather information about unknown space",
                "verification_method": "coverage_measurement",
                "example": "Explore all potential data distributions in the input",
                "preferred_strategies": ["parallel", "adaptive"]
            },
            "prevention": {
                "description": "Ensure certain states are never reached",
                "verification_method": "boundary_checking",
                "example": "Prevent system from exceeding resource limits",
                "preferred_strategies": ["constraint_based", "adaptive"]
            }
        }
    
    def _initialize_execution_modes(self) -> Dict[str, Dict[str, Any]]:
        """Initialize execution modes for plans."""
        return {
            "depth_first": {
                "description": "Complete each sub-goal branch before starting others",
                "benefits": ["Lower memory overhead", "Faster completion of specific paths"],
                "limitations": ["May get stuck in deep branches", "Inefficient for parallel tasks"],
                "suitable_for": ["Sequential dependencies", "Limited resource environments"]
            },
            "breadth_first": {
                "description": "Work on all sub-goals at the same level before going deeper",
                "benefits": ["Better coverage of solution space", "More balanced progress"],
                "limitations": ["Higher memory requirements", "Slower to reach leaf goals"],
                "suitable_for": ["Parallel execution", "Uniform progress requirements"]
            },
            "priority_based": {
                "description": "Execute sub-goals based on priority metrics",
                "benefits": ["Focus on high-value goals first", "Adaptable to changing conditions"],
                "limitations": ["Requires good priority metrics", "May leave low-priority goals unfinished"],
                "suitable_for": ["Time-critical tasks", "Variable importance goals"]
            },
            "iterative_deepening": {
                "description": "Gradually increase depth of exploration",
                "benefits": ["Combines advantages of depth and breadth", "Finds shallow solutions quickly"],
                "limitations": ["Repeats work at shallow levels", "Complexity in implementation"],
                "suitable_for": ["Unknown solution depth", "Anytime algorithms"]
            },
            "dynamic_adjustment": {
                "description": "Shift execution strategy based on feedback",
                "benefits": ["Adapts to discovered constraints", "Handles unexpected situations"],
                "limitations": ["Complex control logic", "Potential thrashing between modes"],
                "suitable_for": ["Uncertain environments", "Complex dependencies"]
            }
        }
    
    def _initialize_dependency_types(self) -> Dict[str, Dict[str, Any]]:
        """Initialize types of dependencies between goals."""
        return {
            "prerequisite": {
                "description": "Target goal requires source goal to be completed first",
                "enforcement": "strict",
                "example": "Must have data before analyzing it"
            },
            "enablement": {
                "description": "Source goal enables but doesn't require completion of target",
                "enforcement": "flexible",
                "example": "Having a tool makes a task easier but not mandatory"
            },
            "exclusion": {
                "description": "Source and target goals cannot be active simultaneously",
                "enforcement": "strict",
                "example": "Can't run two conflicting operations on same resource"
            },
            "reinforcement": {
                "description": "Source goal improves efficiency or outcome of target",
                "enforcement": "optimization",
                "example": "Preprocessing data improves analysis quality"
            },
            "temporal": {
                "description": "Timing relationship between goals (before, after, during)",
                "enforcement": "scheduled",
                "example": "Monitoring must occur during execution"
            },
            "resource": {
                "description": "Goals compete for or share resources",
                "enforcement": "constrained",
                "example": "Memory allocation between concurrent processes"
            }
        }
    
    def create_recursive_plan(self, goal: Dict[str, Any], 
                           context: Dict[str, Any],
                           config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a recursive plan to achieve a complex goal.
        
        Args:
            goal: Goal specification
            context: Context information for planning
            config: Optional configuration for the planning process
            
        Returns:
            Dictionary with the recursive plan
        """
        # Set default configuration if not provided
        if config is None:
            config = {
                "max_recursion_depth": 4,
                "max_sub_goals": 10,
                "execution_mode": "depth_first",
                "allow_parallel_execution": True,
                "optimization_target": "balanced",  # Options: efficiency, thoroughness, balanced
                "include_contingencies": True,
                "resource_constraints": {},
                "time_horizon": "medium"  # Options: short, medium, long
            }
        
        # Validate inputs
        if not goal or "description" not in goal:
            return {
                "success": False,
                "error": "Invalid goal specification",
                "plan": None
            }
        
        # Create plan ID
        plan_id = str(uuid.uuid4())[:8]
        
        # Classify goal type
        goal_type = goal.get("type")
        if not goal_type or goal_type not in self.goal_types:
            goal_type = self._classify_goal_type(goal, context)
        
        # Select planning strategies
        strategies = self._select_planning_strategies(goal_type, goal, context, config)
        
        # Create initial plan structure
        plan = {
            "id": plan_id,
            "goal": copy.deepcopy(goal),
            "goal_type": goal_type,
            "strategies": strategies,
            "sub_goals": [],
            "dependencies": [],
            "execution_mode": config.get("execution_mode", "depth_first"),
            "max_recursion_depth": config.get("max_recursion_depth", 4),
            "depth": 0,  # Current recursive depth
            "status": "planned",
            "progress": 0.0,
            "resource_requirements": self._estimate_resource_requirements(goal, context),
            "estimated_completion_time": self._estimate_completion_time(goal, context, config),
            "metrics": {},
            "creation_timestamp": time.time()
        }
        
        # Recursively decompose goal
        self._recursive_goal_decomposition(plan, context, config, 0)
        
        # Calculate plan metrics
        self._calculate_plan_metrics(plan)
        
        # Check for successful plan creation
        if not plan.get("sub_goals") and self._requires_decomposition(goal, context):
            return {
                "success": False,
                "error": "Failed to decompose goal into sub-goals",
                "plan": plan
            }
        
        return {
            "success": True,
            "plan": plan
        }
    
    def _classify_goal_type(self, goal: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Classify the type of goal based on its description and context.
        
        Args:
            goal: Goal specification
            context: Context information
            
        Returns:
            Goal type classification
        """
        description = goal.get("description", "").lower()
        
        # Check for keywords associated with each goal type
        achievement_keywords = ["create", "build", "achieve", "implement", "complete", "reach", "generate", "produce"]
        maintenance_keywords = ["maintain", "keep", "ensure", "sustain", "preserve", "continue", "regulate"]
        optimization_keywords = ["optimize", "maximize", "minimize", "improve", "enhance", "reduce", "increase"]
        learning_keywords = ["learn", "understand", "acquire", "master", "study", "train", "develop knowledge"]
        exploration_keywords = ["explore", "investigate", "discover", "search", "survey", "examine", "analyze"]
        prevention_keywords = ["prevent", "avoid", "mitigate", "eliminate", "reduce risk", "protect against"]
        
        # Count keyword matches for each type
        counts = {
            "achievement": sum(1 for kw in achievement_keywords if kw in description),
            "maintenance": sum(1 for kw in maintenance_keywords if kw in description),
            "optimization": sum(1 for kw in optimization_keywords if kw in description),
            "learning": sum(1 for kw in learning_keywords if kw in description),
            "exploration": sum(1 for kw in exploration_keywords if kw in description),
            "prevention": sum(1 for kw in prevention_keywords if kw in description)
        }
        
        # Determine the primary type based on keyword count
        primary_type = max(counts.items(), key=lambda x: x[1])
        
        # If no clear winner (no matches or ties), use additional heuristics
        if primary_type[1] == 0 or list(counts.values()).count(primary_type[1]) > 1:
            # Check for measurable targets (optimization)
            if any(kw in description for kw in ["percent", "percentage", "%", "level", "threshold", "score"]):
                return "optimization"
            
            # Check for time-related words (maintenance)
            if any(kw in description for kw in ["always", "continuously", "ongoing", "throughout"]):
                return "maintenance"
            
            # Check for knowledge-related words (learning)
            if any(kw in description for kw in ["knowledge", "skill", "proficiency", "understanding"]):
                return "learning"
            
            # Default to achievement if still unclear
            return "achievement"
        
        return primary_type[0]
    
    def _select_planning_strategies(self, goal_type: str, goal: Dict[str, Any], 
                                 context: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
        """
        Select planning strategies appropriate for the goal.
        
        Args:
            goal_type: Type of the goal
            goal: Goal specification
            context: Context information
            config: Planning configuration
            
        Returns:
            List of selected strategy names
        """
        selected_strategies = []
        
        # Start with preferred strategies for the goal type
        if goal_type in self.goal_types:
            preferred = self.goal_types[goal_type].get("preferred_strategies", [])
            selected_strategies.extend(preferred)
        
        # Always include decomposition for complex goals
        if "decomposition" not in selected_strategies and self._requires_decomposition(goal, context):
            selected_strategies.append("decomposition")
        
        # Check for sequential dependencies
        if ("sequential" not in selected_strategies and 
            (goal.get("sequential", False) or context.get("requires_sequence", False))):
            selected_strategies.append("sequential")
        
        # Check for parallelization opportunities
        if ("parallel" not in selected_strategies and 
            config.get("allow_parallel_execution", True) and
            not goal.get("sequential", False)):
            selected_strategies.append("parallel")
        
        # Check for iterative requirements
        if ("iterative" not in selected_strategies and 
            (goal.get("iterative", False) or context.get("requires_iteration", False))):
            selected_strategies.append("iterative")
        
        # Check for adaptive requirements
        if ("adaptive" not in selected_strategies and 
            (goal.get("adaptive", False) or context.get("uncertain_environment", False))):
            selected_strategies.append("adaptive")
        
        # Check for constraint-based requirements
        if ("constraint_based" not in selected_strategies and 
            (goal.get("constraints", []) or context.get("resource_limited", False))):
            selected_strategies.append("constraint_based")
        
        # Ensure at least one strategy is selected
        if not selected_strategies:
            selected_strategies.append("decomposition")
        
        return selected_strategies
    
    def _requires_decomposition(self, goal: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Determine if a goal requires decomposition.
        
        Args:
            goal: Goal specification
            context: Context information
            
        Returns:
            True if the goal should be decomposed
        """
        # Check explicit flags
        if goal.get("requires_decomposition", False):
            return True
        
        # Check complexity indicators
        description = goal.get("description", "")
        
        # Check description length (longer descriptions often need decomposition)
        if len(description.split()) > 15:
            return True
        
        # Check for multiple actions/tasks
        action_indicators = ["and", ",", ";", "then", "after", "before", "while"]
        if any(indicator in description for indicator in action_indicators):
            return True
        
        # Check for complexity indicators
        complexity_indicators = ["complex", "multiple", "several", "various", "comprehensive", "detailed", "extensive"]
        if any(indicator in description.lower() for indicator in complexity_indicators):
            return True
        
        # Check for specified steps
        if goal.get("steps") or goal.get("sub_tasks"):
            return True
        
        # Check context for complexity indicators
        if context.get("complex_goal", False) or context.get("requires_planning", False):
            return True
        
        return False
    
    def _estimate_resource_requirements(self, goal: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate resources required for a goal.
        
        Args:
            goal: Goal specification
            context: Context information
            
        Returns:
            Dictionary with resource estimates
        """
        # Default resource estimates
        resources = {
            "time": 1.0,  # Relative time units
            "computational": 1.0,  # Relative computational resources
            "memory": 1.0,  # Relative memory requirements
            "knowledge": 1.0  # Relative knowledge requirements
        }
        
        # Adjust based on goal complexity
        if self._requires_decomposition(goal, context):
            complexity_factor = 2.0
            resources["time"] *= complexity_factor
            resources["computational"] *= complexity_factor
        
        # Apply explicit resource requirements if specified
        if "resource_requirements" in goal:
            for resource, value in goal["resource_requirements"].items():
                if resource in resources:
                    resources[resource] = value
        
        # Adjust for context factors
        if context.get("resource_limited", False):
            limitation_factor = context.get("resource_limitation_factor", 1.5)
            # When limited, estimates tend to be higher (more conservative)
            for resource in resources:
                resources[resource] *= limitation_factor
        
        return resources
    
    def _estimate_completion_time(self, goal: Dict[str, Any], context: Dict[str, Any], 
                               config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate the completion time for a goal.
        
        Args:
            goal: Goal specification
            context: Context information
            config: Planning configuration
            
        Returns:
            Dictionary with time estimates
        """
        # Default time estimates
        time_estimate = {
            "units": "relative",
            "estimated_duration": 1.0,
            "confidence": 0.7,
            "depends_on_sub_goals": self._requires_decomposition(goal, context)
        }
        
        # Adjust for explicit time requirements
        if "time_requirement" in goal:
            time_estimate["estimated_duration"] = goal["time_requirement"]
            time_estimate["confidence"] = 0.9  # Higher confidence if explicitly specified
        
        # Adjust based on goal complexity
        elif self._requires_decomposition(goal, context):
            # Complex goals take longer
            complexity_factor = 2.0
            time_estimate["estimated_duration"] *= complexity_factor
            time_estimate["confidence"] = 0.6  # Lower confidence for complex goals
        
        # Adjust based on time horizon
        time_horizon = config.get("time_horizon", "medium")
        if time_horizon == "short":
            time_estimate["estimated_duration"] *= 0.7
        elif time_horizon == "long":
            time_estimate["estimated_duration"] *= 1.5
            time_estimate["confidence"] *= 0.9  # Less confidence in long-term estimates
        
        return time_estimate
    
    def _recursive_goal_decomposition(self, plan: Dict[str, Any], context: Dict[str, Any], 
                                   config: Dict[str, Any], depth: int) -> None:
        """
        Recursively decompose a goal into sub-goals.
        
        Args:
            plan: Current plan structure to update
            context: Context information
            config: Planning configuration
            depth: Current recursion depth
            
        Returns:
            None (updates plan in place)
        """
        # Check recursion depth limit
        max_depth = min(plan["max_recursion_depth"], config.get("max_recursion_depth", 4))
        if depth >= max_depth:
            return
        
        # Update plan depth
        plan["depth"] = depth
        
        # Check if the goal requires decomposition
        goal = plan["goal"]
        if not self._requires_decomposition(goal, context):
            return
        
        # Apply selected strategies to generate sub-goals
        for strategy in plan["strategies"]:
            self._apply_strategy(strategy, plan, context, config, depth)
        
        # If no sub-goals were generated, try a default decomposition
        if not plan["sub_goals"]:
            self._apply_default_decomposition(plan, context, config, depth)
        
        # Identify and record dependencies between sub-goals
        self._identify_dependencies(plan)
        
        # Recursively decompose each sub-goal
        max_sub_goals = config.get("max_sub_goals", 10)
        for i, sub_goal in enumerate(plan["sub_goals"]):
            if i >= max_sub_goals:
                break
                
            self._recursive_goal_decomposition(sub_goal, context, config, depth + 1)
    
    def _apply_strategy(self, strategy: str, plan: Dict[str, Any], 
                     context: Dict[str, Any], config: Dict[str, Any], depth: int) -> None:
        """
        Apply a planning strategy to generate sub-goals.
        
        Args:
            strategy: Strategy name to apply
            plan: Current plan structure to update
            context: Context information
            config: Planning configuration
            depth: Current recursion depth
            
        Returns:
            None (updates plan in place)
        """
        if strategy == "decomposition":
            self._apply_decomposition_strategy(plan, context, config, depth)
        elif strategy == "sequential":
            self._apply_sequential_strategy(plan, context, config, depth)
        elif strategy == "parallel":
            self._apply_parallel_strategy(plan, context, config, depth)
        elif strategy == "iterative":
            self._apply_iterative_strategy(plan, context, config, depth)
        elif strategy == "adaptive":
            self._apply_adaptive_strategy(plan, context, config, depth)
        elif strategy == "constraint_based":
            self._apply_constraint_based_strategy(plan, context, config, depth)
    
    def _apply_decomposition_strategy(self, plan: Dict[str, Any], 
                                   context: Dict[str, Any], 
                                   config: Dict[str, Any], 
                                   depth: int) -> None:
        """
        Apply the decomposition strategy to break a goal into sub-goals.
        
        Args:
            plan: Current plan structure to update
            context: Context information
            config: Planning configuration
            depth: Current recursion depth
            
        Returns:
            None (updates plan in place)
        """
        goal = plan["goal"]
        description = goal.get("description", "")
        
        # Check if goal already has specified sub-goals or steps
        if "sub_goals" in goal:
            self._convert_specified_sub_goals(plan, goal["sub_goals"], depth)
            return
        
        if "steps" in goal:
            self._convert_steps_to_sub_goals(plan, goal["steps"], depth)
            return
        
        # Use context hints if available
        if "suggested_decomposition" in context:
            if isinstance(context["suggested_decomposition"], dict) and goal.get("id") in context["suggested_decomposition"]:
                self._convert_specified_sub_goals(plan, context["suggested_decomposition"][goal.get("id")], depth)
                return
            elif isinstance(context["suggested_decomposition"], list):
                self._convert_specified_sub_goals(plan, context["suggested_decomposition"], depth)
                return
        
        # Rule-based decomposition if no explicit structure
        # First, try to identify distinct parts using common separators
        parts = self._split_into_parts(description)
        
        if len(parts) > 1:
            # Create a sub-goal for each part
            for i, part in enumerate(parts):
                sub_goal = {
                    "id": f"{plan['id']}_sub_{i}",
                    "type": plan["goal_type"],
                    "description": part,
                    "parent_goal_id": plan["id"],
                    "order": i,
                    "status": "planned",
                    "progress": 0.0
                }
                
                sub_goal_plan = self._create_sub_goal_plan(sub_goal, plan, depth)
                plan["sub_goals"].append(sub_goal_plan)
            
            return
        
        # If we can't split by parts, try to create standard phases
        # This is a fallback generic decomposition
        goal_type = plan["goal_type"]
        
        if goal_type == "achievement":
            self._create_achievement_phases(plan, description, depth)
        elif goal_type == "optimization":
            self._create_optimization_phases(plan, description, depth)
        elif goal_type == "learning":
            self._create_learning_phases(plan, description, depth)
        elif goal_type == "exploration":
            self._create_exploration_phases(plan, description, depth)
        else:
            # Generic phases for other goal types
            self._create_generic_phases(plan, description, depth)
    
    def _split_into_parts(self, description: str) -> List[str]:
        """
        Split a goal description into parts based on separators.
        
        Args:
            description: Goal description text
            
        Returns:
            List of description parts
        """
        # Try splitting by explicit separators
        parts = []
        
        # Try numbered items first (1., 2., etc.)
        if any(str(i) + "." in description for i in range(1, 10)):
            # Likely a numbered list
            for line in description.split("\n"):
                line = line.strip()
                if line and any(line.startswith(str(i) + ".") for i in range(1, 10)):
                    parts.append(line)
            
            if len(parts) > 1:
                return parts
        
        # Try bullet points
        if any(marker in description for marker in ["• ", "* ", "- "]):
            potential_parts = []
            for line in description.split("\n"):
                line = line.strip()
                for marker in ["• ", "* ", "- "]:
                    if line.startswith(marker):
                        potential_parts.append(line)
                        break
            
            if len(potential_parts) > 1:
                return potential_parts
        
        # Try semicolons
        if ";" in description:
            potential_parts = [part.strip() for part in description.split(";")]
            if all(part for part in potential_parts):
                return potential_parts
        
        # Try "and" or "then" combinations
        conjunction_splits = []
        if " and " in description:
            conjunction_splits.extend([part.strip() for part in description.split(" and ")])
        
        if " then " in description:
            conjunction_splits.extend([part.strip() for part in description.split(" then ")])
        
        if len(conjunction_splits) > 1:
            return conjunction_splits
        
        # If no good splits found, return the original as a single item
        return [description] if description else []
    
    def _convert_specified_sub_goals(self, plan: Dict[str, Any], 
                                  sub_goals: List[Dict[str, Any]], 
                                  depth: int) -> None:
        """
        Convert explicitly specified sub-goals into plan structures.
        
        Args:
            plan: Current plan structure to update
            sub_goals: List of specified sub-goals
            depth: Current recursion depth
            
        Returns:
            None (updates plan in place)
        """
        for i, sg in enumerate(sub_goals):
            # Create a standardized sub-goal structure
            sub_goal = sg.copy()
            
            # Ensure required fields
            if "id" not in sub_goal:
                sub_goal["id"] = f"{plan['id']}_sub_{i}"
            
            if "type" not in sub_goal:
                # Inherit from parent or classify
                sub_goal["type"] = plan["goal_type"]
            
            if "parent_goal_id" not in sub_goal:
                sub_goal["parent_goal_id"] = plan["id"]
            
            if "order" not in sub_goal:
                sub_goal["order"] = i
            
            if "status" not in sub_goal:
                sub_goal["status"] = "planned"
            
            if "progress" not in sub_goal:
                sub_goal["progress"] = 0.0
            
            # Create plan structure for this sub-goal
            sub_goal_plan = self._create_sub_goal_plan(sub_goal, plan, depth)
            plan["sub_goals"].append(sub_goal_plan)
    
    def _convert_steps_to_sub_goals(self, plan: Dict[str, Any], 
                                 steps: List[Any], 
                                 depth: int) -> None:
        """
        Convert a list of steps into sub-goals.
        
        Args:
            plan: Current plan structure to update
            steps: List of steps (strings or dictionaries)
            depth: Current recursion depth
            
        Returns:
            None (updates plan in place)
        """
        for i, step in enumerate(steps):
            # Convert step to a standardized sub-goal
            if isinstance(step, str):
                # Simple string step
                sub_goal = {
                    "id": f"{plan['id']}_step_{i}",
                    "type": "achievement",  # Steps are typically achievement goals
                    "description": step,
                    "parent_goal_id": plan["id"],
                    "order": i,
                    "status": "planned",
                    "progress": 0.0
                }
            else:
                # Step is already a dictionary
                sub_goal = step.copy()
                
                # Ensure required fields
                if "id" not in sub_goal:
                    sub_goal["id"] = f"{plan['id']}_step_{i}"
                
                if "type" not in sub_goal:
                    sub_goal["type"] = "achievement"
                
                if "parent_goal_id" not in sub_goal:
                    sub_goal["parent_goal_id"] = plan["id"]
                
                if "order" not in sub_goal:
                    sub_goal["order"] = i
                
                if "status" not in sub_goal:
                    sub_goal["status"] = "planned"
                
                if "progress" not in sub_goal:
                    sub_goal["progress"] = 0.0
            
            # Create plan structure for this sub-goal
            sub_goal_plan = self._create_sub_goal_plan(sub_goal, plan, depth)
            plan["sub_goals"].append(sub_goal_plan)
    
    def _create_sub_goal_plan(self, sub_goal: Dict[str, Any], 
                           parent_plan: Dict[str, Any], 
                           depth: int) -> Dict[str, Any]:
        """
        Create a plan structure for a sub-goal.
        
        Args:
            sub_goal: Sub-goal specification
            parent_plan: Parent plan structure
            depth: Current recursion depth
            
        Returns:
            Plan structure for the sub-goal
        """
        # Classify goal type if not specified
        goal_type = sub_goal.get("type")
        if not goal_type or goal_type not in self.goal_types:
            goal_type = self._classify_goal_type(sub_goal, {})
        
        # Inherit appropriate context from parent
        sub_context = {
            "parent_goal_id": parent_plan["id"],
            "parent_goal_type": parent_plan["goal_type"],
            "parent_strategies": parent_plan["strategies"]
        }
        
        # Create default configuration
        sub_config = {
            "max_recursion_depth": parent_plan["max_recursion_depth"],
            "execution_mode": parent_plan.get("execution_mode", "depth_first")
        }
        
        # Select strategies appropriate for this sub-goal
        strategies = self._select_planning_strategies(goal_type, sub_goal, sub_context, sub_config)
        
        # Create plan structure
        sub_plan = {
            "id": sub_goal["id"],
            "goal": sub_goal,
            "goal_type": goal_type,
            "strategies": strategies,
            "sub_goals": [],
            "dependencies": [],
            "execution_mode": parent_plan.get("execution_mode", "depth_first"),
            "max_recursion_depth": parent_plan["max_recursion_depth"],
            "depth": depth + 1,
            "status": sub_goal.get("status", "planned"),
            "progress": sub_goal.get("progress", 0.0),
            "resource_requirements": self._estimate_resource_requirements(sub_goal, sub_context),
            "estimated_completion_time": self._estimate_completion_time(sub_goal, sub_context, sub_config),
            "metrics": {},
            "parent_plan_id": parent_plan["id"],
            "creation_timestamp": time.time()
        }
        
        return sub_plan
    
    def _create_achievement_phases(self, plan: Dict[str, Any], 
                                description: str, 
                                depth: int) -> None:
        """
        Create standard phases for an achievement goal.
        
        Args:
            plan: Current plan structure to update
            description: Goal description
            depth: Current recursion depth
            
        Returns:
            None (updates plan in place)
        """
        # Phases for achievement goals
        phases = [
            {
                "id": f"{plan['id']}_phase_1",
                "type": "exploration",
                "description": f"Analyze requirements for: {description}",
                "order": 0
            },
            {
                "id": f"{plan['id']}_phase_2",
                "type": "achievement",
                "description": f"Develop initial approach for: {description}",
                "order": 1
            },
            {
                "id": f"{plan['id']}_phase_3",
                "type": "achievement",
                "description": f"Implement solution for: {description}",
                "order": 2
            },
            {
                "id": f"{plan['id']}_phase_4",
                "type": "optimization",
                "description": f"Evaluate and refine results for: {description}",
                "order": 3
            }
        ]
        
        self._convert_specified_sub_goals(plan, phases, depth)
    
    def _create_optimization_phases(self, plan: Dict[str, Any], 
                                 description: str, 
                                 depth: int) -> None:
        """
        Create standard phases for an optimization goal.
        
        Args:
            plan: Current plan structure to update
            description: Goal description
            depth: Current recursion depth
            
        Returns:
            None (updates plan in place)
        """
        # Phases for optimization goals
        phases = [
            {
                "id": f"{plan['id']}_phase_1",
                "type": "exploration",
                "description": f"Define optimization metrics for: {description}",
                "order": 0
            },
            {
                "id": f"{plan['id']}_phase_2",
                "type": "exploration",
                "description": f"Analyze current state and identify improvement opportunities for: {description}",
                "order": 1
            },
            {
                "id": f"{plan['id']}_phase_3",
                "type": "optimization",
                "description": f"Develop optimization strategy for: {description}",
                "order": 2
            },
            {
                "id": f"{plan['id']}_phase_4",
                "type": "achievement",
                "description": f"Implement optimizations for: {description}",
                "order": 3
            },
            {
                "id": f"{plan['id']}_phase_5",
                "type": "optimization",
                "description": f"Measure results and iteratively refine for: {description}",
                "order": 4
            }
        ]
        
        self._convert_specified_sub_goals(plan, phases, depth)
    
    def _create_learning_phases(self, plan: Dict[str, Any], 
                             description: str, 
                             depth: int) -> None:
        """
        Create standard phases for a learning goal.
        
        Args:
            plan: Current plan structure to update
            description: Goal description
            depth: Current recursion depth
            
        Returns:
            None (updates plan in place)
        """
        # Phases for learning goals
        phases = [
            {
                "id": f"{plan['id']}_phase_1",
                "type": "exploration",
                "description": f"Assess current knowledge and define learning objectives for: {description}",
                "order": 0
            },
            {
                "id": f"{plan['id']}_phase_2",
                "type": "exploration",
                "description": f"Gather learning resources and plan approach for: {description}",
                "order": 1
            },
            {
                "id": f"{plan['id']}_phase_3",
                "type": "learning",
                "description": f"Acquire foundational knowledge for: {description}",
                "order": 2
            },
            {
                "id": f"{plan['id']}_phase_4",
                "type": "learning",
                "description": f"Apply and practice skills related to: {description}",
                "order": 3
            },
            {
                "id": f"{plan['id']}_phase_5",
                "type": "optimization",
                "description": f"Evaluate understanding and refine knowledge of: {description}",
                "order": 4
            }
        ]
        
        self._convert_specified_sub_goals(plan, phases, depth)
    
    def _create_exploration_phases(self, plan: Dict[str, Any], 
                                description: str, 
                                depth: int) -> None:
        """
        Create standard phases for an exploration goal.
        
        Args:
            plan: Current plan structure to update
            description: Goal description
            depth: Current recursion depth
            
        Returns:
            None (updates plan in place)
        """
        # Phases for exploration goals
        phases = [
            {
                "id": f"{plan['id']}_phase_1",
                "type": "exploration",
                "description": f"Define scope and approach for exploring: {description}",
                "order": 0
            },
            {
                "id": f"{plan['id']}_phase_2",
                "type": "exploration",
                "description": f"Conduct initial survey of: {description}",
                "order": 1
            },
            {
                "id": f"{plan['id']}_phase_3",
                "type": "exploration",
                "description": f"Identify and investigate key areas of: {description}",
                "order": 2
            },
            {
                "id": f"{plan['id']}_phase_4",
                "type": "achievement",
                "description": f"Document and structure findings from: {description}",
                "order": 3
            },
            {
                "id": f"{plan['id']}_phase_5",
                "type": "learning",
                "description": f"Synthesize insights and identify opportunities from: {description}",
                "order": 4
            }
        ]
        
        self._convert_specified_sub_goals(plan, phases, depth)
    
    def _create_generic_phases(self, plan: Dict[str, Any], 
                            description: str, 
                            depth: int) -> None:
        """
        Create generic phases for any goal type.
        
        Args:
            plan: Current plan structure to update
            description: Goal description
            depth: Current recursion depth
            
        Returns:
            None (updates plan in place)
        """
        # Generic phases applicable to most goal types
        phases = [
            {
                "id": f"{plan['id']}_phase_1",
                "type": "exploration",
                "description": f"Analyze and plan approach for: {description}",
                "order": 0
            },
            {
                "id": f"{plan['id']}_phase_2",
                "type": "achievement",
                "description": f"Develop initial solution for: {description}",
                "order": 1
            },
            {
                "id": f"{plan['id']}_phase_3",
                "type": "achievement",
                "description": f"Implement and execute for: {description}",
                "order": 2
            },
            {
                "id": f"{plan['id']}_phase_4",
                "type": "optimization",
                "description": f"Review, evaluate and refine: {description}",
                "order": 3
            }
        ]
        
        self._convert_specified_sub_goals(plan, phases, depth)
    
    def _apply_sequential_strategy(self, plan: Dict[str, Any], 
                                context: Dict[str, Any], 
                                config: Dict[str, Any], 
                                depth: int) -> None:
        """
        Apply the sequential strategy to organize sub-goals.
        
        Args:
            plan: Current plan structure to update
            context: Context information
            config: Planning configuration
            depth: Current recursion depth
            
        Returns:
            None (updates plan in place)
        """
        # Check if we already have sub-goals
        if not plan["sub_goals"]:
            # No sub-goals yet, so nothing to sequence
            return
        
        # Sort sub-goals by order if specified
        plan["sub_goals"].sort(key=lambda x: x["goal"].get("order", 999))
        
        # Ensure sequential execution by creating dependencies
        for i in range(1, len(plan["sub_goals"])):
            prev_id = plan["sub_goals"][i-1]["id"]
            curr_id = plan["sub_goals"][i]["id"]
            
            # Create prerequisite dependency
            dependency = {
                "id": f"dep_{prev_id}_to_{curr_id}",
                "source": prev_id,
                "target": curr_id,
                "type": "prerequisite",
                "description": f"Complete {prev_id} before starting {curr_id}"
            }
            
            # Add to dependencies if not already present
            if not any(d["source"] == prev_id and d["target"] == curr_id for d in plan["dependencies"]):
                plan["dependencies"].append(dependency)
    
    def _apply_parallel_strategy(self, plan: Dict[str, Any], 
                              context: Dict[str, Any], 
                              config: Dict[str, Any], 
                              depth: int) -> None:
        """
        Apply the parallel strategy to identify concurrent sub-goals.
        
        Args:
            plan: Current plan structure to update
            context: Context information
            config: Planning configuration
            depth: Current recursion depth
            
        Returns:
            None (updates plan in place)
        """
        # Check if we already have sub-goals
        if not plan["sub_goals"]:
            # No sub-goals yet, so nothing to parallelize
            return
        
        # Check for existing dependencies
        existing_dependencies = set()
        for dep in plan["dependencies"]:
            if dep["type"] == "prerequisite":
                existing_dependencies.add((dep["source"], dep["target"]))
        
        # Group sub-goals that can be executed in parallel
        parallel_groups = []
        current_group = []
        
        # Sort by order first
        ordered_goals = sorted(plan["sub_goals"], key=lambda x: x["goal"].get("order", 999))
        
        for sub_goal in ordered_goals:
            # Check if this goal has prerequisites or exclusions with the current group
            has_dependency = False
            for group_goal in current_group:
                if ((group_goal["id"], sub_goal["id"]) in existing_dependencies or
                    (sub_goal["id"], group_goal["id"]) in existing_dependencies):
                    has_dependency = True
                    break
                
                # Check for resource conflicts
                if self._has_resource_conflict(group_goal, sub_goal, context):
                    has_dependency = True
                    break
            
            if has_dependency:
                # Start a new group
                if current_group:
                    parallel_groups.append(current_group)
                current_group = [sub_goal]
            else:
                # Add to current group
                current_group.append(sub_goal)
        
        # Add the last group
        if current_group:
            parallel_groups.append(current_group)
        
        # Mark parallel groups in the plan
        for i, group in enumerate(parallel_groups):
            for sub_goal in group:
                sub_goal["parallel_group"] = i
                
                # Add parallelization info to goal
                sub_goal["goal"]["parallelizable"] = True
                sub_goal["goal"]["parallel_group"] = i
    
    def _has_resource_conflict(self, goal1: Dict[str, Any], 
                            goal2: Dict[str, Any], 
                            context: Dict[str, Any]) -> bool:
        """
        Check if two goals have conflicting resource requirements.
        
        Args:
            goal1: First goal plan
            goal2: Second goal plan
            context: Context information
            
        Returns:
            True if the goals have a resource conflict
        """
        # Check for explicit exclusions
        if "exclusions" in goal1["goal"]:
            if goal2["id"] in goal1["goal"]["exclusions"]:
                return True
        
        if "exclusions" in goal2["goal"]:
            if goal1["id"] in goal2["goal"]["exclusions"]:
                return True
        
        # Check for resource limitation in context
        if context.get("limited_resources", False):
            # In resource-limited environments, assume conflicts unless specified otherwise
            if context.get("allow_parallelization", False):
                return False
            return True
        
        # Check for specific resource conflicts
        resources1 = goal1.get("resource_requirements", {})
        resources2 = goal2.get("resource_requirements", {})
        
        # Check for high combined resource usage
        total_computational = (resources1.get("computational", 1.0) + 
                               resources2.get("computational", 1.0))
        
        total_memory = (resources1.get("memory", 1.0) + 
                         resources2.get("memory", 1.0))
        
        # If combined resources exceed thresholds, consider it a conflict
        if total_computational > 1.5 or total_memory > 1.5:
            return True
        
        return False
    
    def _apply_iterative_strategy(self, plan: Dict[str, Any], 
                               context: Dict[str, Any], 
                               config: Dict[str, Any], 
                               depth: int) -> None:
        """
        Apply the iterative strategy for refinement-based goals.
        
        Args:
            plan: Current plan structure to update
            context: Context information
            config: Planning configuration
            depth: Current recursion depth
            
        Returns:
            None (updates plan in place)
        """
        goal = plan["goal"]
        
        # Check if iterative structure already exists
        if any(sg["goal"].get("is_iteration", False) for sg in plan["sub_goals"]):
            return
        
        # Get iteration settings
        max_iterations = self.planning_strategies["iterative"]["max_iterations"]
        if "iterations" in goal:
            if isinstance(goal["iterations"], int):
                max_iterations = goal["iterations"]
            elif isinstance(goal["iterations"], dict):
                max_iterations = goal["iterations"].get("max", max_iterations)
        
        # Limit maximum iterations based on configuration
        max_iterations = min(max_iterations, 10)
        
        # Create iteration phases
        description = goal.get("description", "")
        iteration_phases = [
            {
                "id": f"{plan['id']}_init",
                "type": "achievement",
                "description": f"Initial setup for iterative process: {description}",
                "order": 0,
                "is_iteration": False
            }
        ]
        
        # Add iteration placeholder
        iteration_phases.append({
            "id": f"{plan['id']}_iterations",
            "type": plan["goal_type"],
            "description": f"Execute iterations for: {description}",
            "order": 1,
            "is_iteration": True,
            "iteration_count": max_iterations,
            "iteration_template": {
                "type": plan["goal_type"],
                "phases": [
                    {
                        "description": f"Plan iteration for: {description}",
                        "type": "exploration"
                    },
                    {
                        "description": f"Execute iteration for: {description}",
                        "type": "achievement"
                    },
                    {
                        "description": f"Evaluate results of iteration for: {description}",
                        "type": "optimization"
                    }
                ]
            }
        })
        
        # Add final consolidation
        iteration_phases.append({
            "id": f"{plan['id']}_final",
            "type": "achievement",
            "description": f"Finalize and integrate results from iterations: {description}",
            "order": 2,
            "is_iteration": False
        })
        
        # Add these to the plan's sub-goals
        self._convert_specified_sub_goals(plan, iteration_phases, depth)
        
        # Add dependencies between phases
        self._apply_sequential_strategy(plan, context, config, depth)
    
    def _apply_adaptive_strategy(self, plan: Dict[str, Any], 
                              context: Dict[str, Any], 
                              config: Dict[str, Any], 
                              depth: int) -> None:
        """
        Apply the adaptive strategy for uncertainty handling.
        
        Args:
            plan: Current plan structure to update
            context: Context information
            config: Planning configuration
            depth: Current recursion depth
            
        Returns:
            None (updates plan in place)
        """
        # Adaptive strategy adds monitoring, evaluation and adaptation phases
        
        # Check if we already have sub-goals
        if not plan["sub_goals"]:
            # No sub-goals to adapt
            return
        
        # Add adaptive flags to all sub-goals
        for sub_goal in plan["sub_goals"]:
            sub_goal["goal"]["adaptive"] = True
            
            # Add adaptation parameters if not present
            if "adaptation_parameters" not in sub_goal["goal"]:
                sub_goal["goal"]["adaptation_parameters"] = {
                    "feedback_frequency": "after_completion",
                    "adjustment_threshold": 0.3,
                    "max_adjustments": 2
                }
        
        # Add evaluation and adaptation phases
        goal = plan["goal"]
        description = goal.get("description", "")
        
        # Create adaptive phases
        adaptive_phases = [
            {
                "id": f"{plan['id']}_monitoring",
                "type": "maintenance",
                "description": f"Monitor execution and collect feedback for: {description}",
                "order": len(plan["sub_goals"]),  # After other sub-goals
                "is_adaptive": True,
                "adaptive_role": "monitoring"
            },
            {
                "id": f"{plan['id']}_adaptation",
                "type": "optimization",
                "description": f"Adapt approach based on feedback for: {description}",
                "order": len(plan["sub_goals"]) + 1,
                "is_adaptive": True,
                "adaptive_role": "adaptation",
                "activation_condition": "feedback_threshold_exceeded"
            }
        ]
        
        # Add these to the plan's sub-goals
        self._convert_specified_sub_goals(plan, adaptive_phases, depth)
        
        # Mark the plan as adaptive
        plan["is_adaptive"] = True
        plan["adaptation_parameters"] = {
            "monitoring_frequency": "continuous",
            "adaptation_threshold": 0.3,
            "feedback_sources": ["execution_metrics", "environment_changes"]
        }
    
    def _apply_constraint_based_strategy(self, plan: Dict[str, Any], 
                                      context: Dict[str, Any], 
                                      config: Dict[str, Any], 
                                      depth: int) -> None:
        """
        Apply the constraint-based strategy for optimization problems.
        
        Args:
            plan: Current plan structure to update
            context: Context information
            config: Planning configuration
            depth: Current recursion depth
            
        Returns:
            None (updates plan in place)
        """
        goal = plan["goal"]
        description = goal.get("description", "")
        
        # Extract constraints
        constraints = goal.get("constraints", [])
        
        # If no explicit constraints, infer from description or context
        if not constraints:
            constraints = self._infer_constraints(goal, context)
        
        # Add constraint phases
        constraint_phases = [
            {
                "id": f"{plan['id']}_constraint_identification",
                "type": "exploration",
                "description": f"Identify and formalize constraints for: {description}",
                "order": 0,
                "constraints": constraints
            },
            {
                "id": f"{plan['id']}_solution_space_analysis",
                "type": "exploration",
                "description": f"Analyze solution space within constraints for: {description}",
                "order": 1
            },
            {
                "id": f"{plan['id']}_constraint_satisfaction",
                "type": "optimization",
                "description": f"Develop solution satisfying constraints for: {description}",
                "order": 2
            },
            {
                "id": f"{plan['id']}_constraint_validation",
                "type": "verification",
                "description": f"Validate solution against constraints for: {description}",
                "order": 3,
                "constraints": constraints
            }
        ]
        
        # Add these to the plan's sub-goals
        self._convert_specified_sub_goals(plan, constraint_phases, depth)
        
        # Add dependencies between phases
        self._apply_sequential_strategy(plan, context, config, depth)
        
        # Mark the plan as constraint-based
        plan["is_constraint_based"] = True
        plan["constraints"] = constraints
    
    def _infer_constraints(self, goal: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Infer constraints from goal description and context.
        
        Args:
            goal: Goal specification
            context: Context information
            
        Returns:
            List of inferred constraints
        """
        inferred_constraints = []
        description = goal.get("description", "").lower()
        
        # Resource constraints from context
        if context.get("resource_limited", False):
            for resource, limit in context.get("resource_limits", {}).items():
                inferred_constraints.append({
                    "type": "resource",
                    "resource": resource,
                    "limit": limit,
                    "priority": "hard"
                })
        
        # Time constraints from description
        time_indicators = ["within", "by", "before", "until", "deadline"]
        for indicator in time_indicators:
            if indicator in description:
                inferred_constraints.append({
                    "type": "time",
                    "description": f"Time constraint inferred from: {description}",
                    "priority": "hard" if "must" in description else "soft"
                })
                break
        
        # Quality constraints from description
        quality_indicators = ["high quality", "excellent", "best", "optimal", "accurate", "precise"]
        for indicator in quality_indicators:
            if indicator in description:
                inferred_constraints.append({
                    "type": "quality",
                    "description": f"Quality constraint inferred from: {description}",
                    "priority": "soft"
                })
                break
        
        # Compliance constraints from context
        if context.get("requires_compliance", False):
            inferred_constraints.append({
                "type": "compliance",
                "description": "Must meet compliance requirements",
                "priority": "hard"
            })
        
        return inferred_constraints
    
    def _apply_default_decomposition(self, plan: Dict[str, Any], 
                                  context: Dict[str, Any], 
                                  config: Dict[str, Any], 
                                  depth: int) -> None:
        """
        Apply a default decomposition when no strategy generated sub-goals.
        
        Args:
            plan: Current plan structure to update
            context: Context information
            config: Planning configuration
            depth: Current recursion depth
            
        Returns:
            None (updates plan in place)
        """
        # Use generic phases as fallback
        goal = plan["goal"]
        description = goal.get("description", "")
        
        self._create_generic_phases(plan, description, depth)
    
    def _identify_dependencies(self, plan: Dict[str, Any]) -> None:
        """
        Identify and record dependencies between sub-goals.
        
        Args:
            plan: Current plan structure to update
            
        Returns:
            None (updates plan in place)
        """
        # Skip if no sub-goals or only one sub-goal
        if len(plan["sub_goals"]) <= 1:
            return
        
        # Check for existing sequential dependencies
        has_sequential = any(dep["type"] == "prerequisite" for dep in plan["dependencies"])
        
        # If sequential strategy already applied, don't add more dependencies
        if has_sequential and "sequential" in plan["strategies"]:
            return
        
        # Check for explicit dependencies in sub-goals
        for sub_goal in plan["sub_goals"]:
            goal_data = sub_goal["goal"]
            
            # Check for prerequisites
            if "prerequisites" in goal_data:
                for prereq in goal_data["prerequisites"]:
                    # Find the prerequisite sub-goal
                    prereq_id = prereq
                    if isinstance(prereq, dict):
                        prereq_id = prereq.get("id")
                    
                    prereq_goal = None
                    for sg in plan["sub_goals"]:
                        if sg["id"] == prereq_id or sg["goal"].get("id") == prereq_id:
                            prereq_goal = sg
                            break
                    
                    # If found, add dependency
                    if prereq_goal:
                        dependency = {
                            "id": f"dep_{prereq_goal['id']}_to_{sub_goal['id']}",
                            "source": prereq_goal["id"],
                            "target": sub_goal["id"],
                            "type": "prerequisite",
                            "description": f"Complete {prereq_goal['id']} before starting {sub_goal['id']}"
                        }
                        
                        # Add if not already present
                        if not any(d["source"] == dependency["source"] and d["target"] == dependency["target"] 
                                   for d in plan["dependencies"]):
                            plan["dependencies"].append(dependency)
            
            # Check for conflicts
            if "conflicts_with" in goal_data:
                for conflict in goal_data["conflicts_with"]:
                    # Find the conflicting sub-goal
                    conflict_id = conflict
                    if isinstance(conflict, dict):
                        conflict_id = conflict.get("id")
                    
                    conflict_goal = None
                    for sg in plan["sub_goals"]:
                        if sg["id"] == conflict_id or sg["goal"].get("id") == conflict_id:
                            conflict_goal = sg
                            break
                    
                    # If found, add dependency
                    if conflict_goal:
                        dependency = {
                            "id": f"excl_{conflict_goal['id']}_with_{sub_goal['id']}",
                            "source": conflict_goal["id"],
                            "target": sub_goal["id"],
                            "type": "exclusion",
                            "description": f"{conflict_goal['id']} and {sub_goal['id']} cannot be active simultaneously"
                        }
                        
                        # Add if not already present
                        if not any(d["source"] == dependency["source"] and d["target"] == dependency["target"] 
                                   and d["type"] == "exclusion" for d in plan["dependencies"]):
                            plan["dependencies"].append(dependency)
        
        # Infer logical dependencies from order if no explicit dependencies found
        if not plan["dependencies"] and "sequential" not in plan["strategies"]:
            ordered_goals = sorted(plan["sub_goals"], key=lambda x: x["goal"].get("order", 999))
            
            for i in range(1, len(ordered_goals)):
                prev_id = ordered_goals[i-1]["id"]
                curr_id = ordered_goals[i]["id"]
                
                # Create enablement dependency (softer than prerequisite)
                dependency = {
                    "id": f"dep_{prev_id}_to_{curr_id}",
                    "source": prev_id,
                    "target": curr_id,
                    "type": "enablement",
                    "description": f"{prev_id} enables {curr_id}"
                }
                
                plan["dependencies"].append(dependency)
    
    def _calculate_plan_metrics(self, plan: Dict[str, Any]) -> None:
        """
        Calculate metrics for a plan.
        
        Args:
            plan: Plan structure to analyze
            
        Returns:
            None (updates plan in place)
        """
        metrics = {}
        
        # Count sub-goals and calculate complexity
        sub_goal_count = len(plan["sub_goals"])
        recursive_count = 0
        max_depth = 0
        
        # Calculate recursive metrics using BFS
        if sub_goal_count > 0:
            queue = [(sg, plan["depth"] + 1) for sg in plan["sub_goals"]]
            visited = set(sg["id"] for sg in plan["sub_goals"])
            
            while queue:
                sub_goal, depth = queue.pop(0)
                recursive_count += 1
                max_depth = max(max_depth, depth)
                
                if "sub_goals" in sub_goal and sub_goal["sub_goals"]:
                    for sg in sub_goal["sub_goals"]:
                        if sg["id"] not in visited:
                            visited.add(sg["id"])
                            queue.append((sg, depth + 1))
        
        metrics["sub_goal_count"] = sub_goal_count
        metrics["recursive_sub_goal_count"] = recursive_count
        metrics["max_depth"] = max_depth
        
        # Calculate parallel metrics if parallel strategy used
        if "parallel" in plan["strategies"]:
            parallel_groups = set()
            for sg in plan["sub_goals"]:
                if "parallel_group" in sg:
                    parallel_groups.add(sg["parallel_group"])
            
            metrics["parallel_group_count"] = len(parallel_groups)
        
        # Calculate dependency metrics
        metrics["dependency_count"] = len(plan["dependencies"])
        dependency_types = {}
        for dep in plan["dependencies"]:
            dep_type = dep["type"]
            dependency_types[dep_type] = dependency_types.get(dep_type, 0) + 1
        
        metrics["dependency_types"] = dependency_types
        
        # Calculate estimated execution time
        if sub_goal_count > 0:
            # For parallel execution, use critical path
            if "parallel" in plan["strategies"]:
                critical_path_length = self._calculate_critical_path(plan)
                metrics["critical_path_length"] = critical_path_length
                
                # Estimate total time based on critical path
                total_time = 0
                for sg in plan["sub_goals"]:
                    if sg["goal"].get("on_critical_path", False):
                        est_time = sg["estimated_completion_time"].get("estimated_duration", 1.0)
                        total_time += est_time
                
                metrics["estimated_parallel_execution_time"] = total_time
            
            # For sequential execution, sum the times
            sequential_time = 0
            for sg in plan["sub_goals"]:
                est_time = sg["estimated_completion_time"].get("estimated_duration", 1.0)
                sequential_time += est_time
            
            metrics["estimated_sequential_execution_time"] = sequential_time
        
        plan["metrics"] = metrics
    
    def _calculate_critical_path(self, plan: Dict[str, Any]) -> int:
        """
        Calculate the critical path for a plan with dependencies.
        
        Args:
            plan: Plan structure to analyze
            
        Returns:
            Length of the critical path
        """
        # Create a directed graph of dependencies
        graph = {}
        for sub_goal in plan["sub_goals"]:
            graph[sub_goal["id"]] = []
        
        # Add edges for prerequisite and enablement dependencies
        for dep in plan["dependencies"]:
            if dep["type"] in ["prerequisite", "enablement"]:
                if dep["source"] in graph:
                    graph[dep["source"]].append(dep["target"])
        
        # Find sources (nodes with no incoming edges)
        incoming_edges = {node: 0 for node in graph}
        for node, edges in graph.items():
            for target in edges:
                if target in incoming_edges:
                    incoming_edges[target] += 1
        
        sources = [node for node, count in incoming_edges.items() if count == 0]
        
        # Calculate longest path using BFS
        distances = {node: 0 for node in graph}
        queue = deque([(source, 0) for source in sources])
        
        while queue:
            node, dist = queue.popleft()
            
            for neighbor in graph[node]:
                if dist + 1 > distances[neighbor]:
                    distances[neighbor] = dist + 1
                    queue.append((neighbor, dist + 1))
        
        # Find the maximum distance
        if distances:
            critical_path_length = max(distances.values()) + 1  # +1 to count nodes, not edges
        else:
            critical_path_length = 0
        
        # Mark nodes on the critical path
        if critical_path_length > 0:
            # Find nodes with the maximum distance
            critical_nodes = [node for node, dist in distances.items() 
                             if dist == critical_path_length - 1]
            
            # Trace back to find the full critical path
            critical_path = set(critical_nodes)
            for node in critical_nodes:
                path = self._trace_critical_path(node, graph, distances)
                critical_path.update(path)
            
            # Mark sub-goals on the critical path
            for sub_goal in plan["sub_goals"]:
                if sub_goal["id"] in critical_path:
                    sub_goal["goal"]["on_critical_path"] = True
        
        return critical_path_length
    
    def _trace_critical_path(self, node: str, graph: Dict[str, List[str]], 
                          distances: Dict[str, int]) -> Set[str]:
        """
        Trace the critical path from a node back to a source.
        
        Args:
            node: Current node
            graph: Directed graph
            distances: Distances from source
            
        Returns:
            Set of nodes on the critical path
        """
        path = {node}
        current_dist = distances[node]
        
        # Find predecessors
        predecessors = []
        for pred, neighbors in graph.items():
            if node in neighbors:
                predecessors.append(pred)
        
        # Follow predecessors with distance one less
        for pred in predecessors:
            if pred in distances and distances[pred] == current_dist - 1:
                pred_path = self._trace_critical_path(pred, graph, distances)
                path.update(pred_path)
                break
        
        return path
    
    def execute_plan(self, plan: Dict[str, Any], 
                   context: Dict[str, Any],
                   config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a recursive plan.
        
        Args:
            plan: Plan structure to execute
            context: Context information for execution
            config: Optional configuration for execution
            
        Returns:
            Dictionary with execution results
        """
        # Set default configuration if not provided
        if config is None:
            config = {
                "execution_mode": plan.get("execution_mode", "depth_first"),
                "max_parallel_tasks": 5,
                "detailed_progress": True,
                "halt_on_error": False,
                "execution_timeout": 3600,  # 1 hour in seconds
                "progress_callback": None
            }
        
        # Validate inputs
        if not plan or "goal" not in plan:
            return {
                "success": False,
                "error": "Invalid plan structure",
                "execution_result": None
            }
        
        # Create execution state
        execution_state = {
            "plan_id": plan["id"],
            "start_time": time.time(),
            "current_tasks": [],
            "completed_tasks": [],
            "failed_tasks": [],
            "execution_log": [],
            "progress": 0.0,
            "status": "running"
        }
        
        # Execute based on selected mode
        execution_mode = config.get("execution_mode", "depth_first")
        
        if execution_mode == "depth_first":
            result = self._execute_depth_first(plan, context, config, execution_state)
        elif execution_mode == "breadth_first":
            result = self._execute_breadth_first(plan, context, config, execution_state)
        elif execution_mode == "priority_based":
            result = self._execute_priority_based(plan, context, config, execution_state)
        elif execution_mode == "iterative_deepening":
            result = self._execute_iterative_deepening(plan, context, config, execution_state)
        elif execution_mode == "dynamic_adjustment":
            result = self._execute_dynamic_adjustment(plan, context, config, execution_state)
        else:
            # Default to depth first
            result = self._execute_depth_first(plan, context, config, execution_state)
        
        # Update execution state
        execution_state["end_time"] = time.time()
        execution_state["execution_time"] = execution_state["end_time"] - execution_state["start_time"]
        
        # Determine overall success
        if execution_state["failed_tasks"]:
            if config.get("halt_on_error", False):
                execution_state["status"] = "failed"
            else:
                execution_state["status"] = "completed_with_errors"
        else:
            execution_state["status"] = "completed"
        
        # Prepare result
        return {
            "success": execution_state["status"] == "completed",
            "execution_state": execution_state,
            "execution_result": result
        }
    
    def _execute_depth_first(self, plan: Dict[str, Any], 
                          context: Dict[str, Any],
                          config: Dict[str, Any],
                          execution_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute plan using depth-first strategy.
        
        Args:
            plan: Plan structure to execute
            context: Context information
            config: Execution configuration
            execution_state: Current execution state
            
        Returns:
            Dictionary with execution results
        """
        # If this is a leaf goal (no sub-goals), execute it directly
        if not plan.get("sub_goals"):
            result = self._execute_leaf_goal(plan["goal"], context, config)
            
            self._update_execution_state(execution_state, plan["id"], result)
            return result
        
        # Get dependency information
        dependencies = self._build_dependency_graph(plan)
        
        # Find sub-goals with no dependencies (or all dependencies satisfied)
        ready_goals = self._find_ready_goals(plan, dependencies, execution_state)
        
        # Execute sub-goals depth-first
        results = {}
        for sub_goal in ready_goals:
            # Execute this sub-goal and all its descendants
            sub_result = self._execute_depth_first(sub_goal, context, config, execution_state)
            results[sub_goal["id"]] = sub_result
            
            # Check if execution should halt on error
            if config.get("halt_on_error", False) and not sub_result.get("success", False):
                break
            
            # Update dependencies and get next ready goals
            ready_goals = self._find_ready_goals(plan, dependencies, execution_state)
        
        # All sub-goals executed or error occurred
        # Calculate goal result based on sub-goal results
        goal_result = self._calculate_goal_result(plan, results)
        
        # Update plan status and progress
        plan["status"] = goal_result["status"]
        plan["progress"] = goal_result["progress"]
        
        # Update execution state
        self._update_execution_state(execution_state, plan["id"], goal_result)
        
        return goal_result
    
    def _execute_breadth_first(self, plan: Dict[str, Any], 
                            context: Dict[str, Any],
                            config: Dict[str, Any],
                            execution_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute plan using breadth-first strategy.
        
        Args:
            plan: Plan structure to execute
            context: Context information
            config: Execution configuration
            execution_state: Current execution state
            
        Returns:
            Dictionary with execution results
        """
        # Initialize queue with root plan
        queue = deque([(plan, [])])  # (plan, dependency_path)
        results = {}
        
        while queue:
            current_plan, dep_path = queue.popleft()
            
            # Skip if already processed
            if current_plan["id"] in results:
                continue
            
            # Check if dependencies are satisfied
            if dep_path:
                dependencies_satisfied = all(results.get(dep, {}).get("success", False) for dep in dep_path)
                if not dependencies_satisfied:
                    # Put back in queue for later
                    queue.append((current_plan, dep_path))
                    continue
            
            # If this is a leaf goal (no sub-goals), execute it directly
            if not current_plan.get("sub_goals"):
                result = self._execute_leaf_goal(current_plan["goal"], context, config)
                results[current_plan["id"]] = result
                self._update_execution_state(execution_state, current_plan["id"], result)
                continue
            
            # Queue the sub-goals
            dependencies = self._build_dependency_graph(current_plan)
            
            for sub_goal in current_plan.get("sub_goals", []):
                # Calculate dependency path for this sub-goal
                sub_deps = dep_path.copy()
                if sub_goal["id"] in dependencies:
                    sub_deps.extend(dependencies[sub_goal["id"]])
                
                queue.append((sub_goal, sub_deps))
            
            # Calculate result for this level based on completed sub-goals
            sub_results = {sg_id: results[sg_id] for sg_id in 
                           [sg["id"] for sg in current_plan.get("sub_goals", [])]
                           if sg_id in results}
            
            if len(sub_results) == len(current_plan.get("sub_goals", [])):
                # All sub-goals complete
                goal_result = self._calculate_goal_result(current_plan, sub_results)
                results[current_plan["id"]] = goal_result
                self._update_execution_state(execution_state, current_plan["id"], goal_result)
            else:
                # Not all sub-goals complete, re-queue
                queue.append((current_plan, dep_path))
        
        # Return the result for the root plan
        return results.get(plan["id"], {})
    
    def _execute_priority_based(self, plan: Dict[str, Any], 
                             context: Dict[str, Any],
                             config: Dict[str, Any],
                             execution_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute plan using priority-based strategy.
        
        Args:
            plan: Plan structure to execute
            context: Context information
            config: Execution configuration
            execution_state: Current execution state
            
        Returns:
            Dictionary with execution results
        """
        # If this is a leaf goal (no sub-goals), execute it directly
        if not plan.get("sub_goals"):
            result = self._execute_leaf_goal(plan["goal"], context, config)
            self._update_execution_state(execution_state, plan["id"], result)
            return result
        
        # Get dependency information
        dependencies = self._build_dependency_graph(plan)
        
        # Initialize priority queue of sub-goals
        priority_queue = []
        for sub_goal in plan.get("sub_goals", []):
            priority = sub_goal["goal"].get("priority", 5)  # Default priority
            
            # Adjust priority based on dependencies
            if sub_goal["id"] in dependencies:
                # Goals with more dependencies get lower priority
                priority -= len(dependencies[sub_goal["id"]]) * 0.5
            
            # Adjust priority based on criticality
            if sub_goal["goal"].get("on_critical_path", False):
                priority += 3
            
            # Add to priority queue
            priority_queue.append((priority, sub_goal))
        
        # Sort by priority (highest first)
        priority_queue.sort(reverse=True, key=lambda x: x[0])
        
        # Execute sub-goals by priority
        results = {}
        executed_count = 0
        
        while priority_queue:
            # Find highest priority goal with satisfied dependencies
            next_goal = None
            next_idx = None
            
            for i, (priority, sub_goal) in enumerate(priority_queue):
                goal_id = sub_goal["id"]
                
                # Check if dependencies are satisfied
                if goal_id in dependencies:
                    deps_satisfied = True
                    for dep in dependencies[goal_id]:
                        if dep not in results or not results[dep].get("success", False):
                            deps_satisfied = False
                            break
                    
                    if not deps_satisfied:
                        continue
                
                next_goal = sub_goal
                next_idx = i
                break
            
            if next_goal is None:
                # No goals with satisfied dependencies
                if executed_count == 0:
                    # Nothing executed yet - circular dependency or invalid state
                    break
                else:
                    # Wait for dependencies to be satisfied
                    # In a real implementation, this would yield control or sleep
                    break
            
            # Execute the selected goal
            priority_queue.pop(next_idx)
            result = self._execute_depth_first(next_goal, context, config, execution_state)
            results[next_goal["id"]] = result
            executed_count += 1
            
            # Check if execution should halt on error
            if config.get("halt_on_error", False) and not result.get("success", False):
                break
        
        # Calculate overall result
        goal_result = self._calculate_goal_result(plan, results)
        
        # Update plan status and progress
        plan["status"] = goal_result["status"]
        plan["progress"] = goal_result["progress"]
        
        # Update execution state
        self._update_execution_state(execution_state, plan["id"], goal_result)
        
        return goal_result
    
    def _execute_iterative_deepening(self, plan: Dict[str, Any], 
                                  context: Dict[str, Any],
                                  config: Dict[str, Any],
                                  execution_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute plan using iterative deepening strategy.
        
        Args:
            plan: Plan structure to execute
            context: Context information
            config: Execution configuration
            execution_state: Current execution state
            
        Returns:
            Dictionary with execution results
        """
        # For iterative deepening, execute the plan with incrementally increasing depth limits
        max_depth = plan.get("max_recursion_depth", 4)
        
        result = None
        for depth_limit in range(1, max_depth + 1):
            # Create depth-limited configuration
            depth_config = dict(config)
            depth_config["max_depth"] = depth_limit
            
            # Execute with depth limit
            result = self._execute_with_depth_limit(plan, context, depth_config, execution_state, 0, depth_limit)
            
            # Check if goal is complete or execution should halt
            if result.get("status", "") == "completed" or config.get("halt_on_error", False) and not result.get("success", False):
                break
        
        # Update execution state
        self._update_execution_state(execution_state, plan["id"], result)
        
        return result
    
    def _execute_with_depth_limit(self, plan: Dict[str, Any], 
                               context: Dict[str, Any],
                               config: Dict[str, Any],
                               execution_state: Dict[str, Any],
                               current_depth: int,
                               depth_limit: int) -> Dict[str, Any]:
        """
        Execute plan with a specific depth limit.
        
        Args:
            plan: Plan structure to execute
            context: Context information
            config: Execution configuration
            execution_state: Current execution state
            current_depth: Current recursion depth
            depth_limit: Maximum recursion depth
            
        Returns:
            Dictionary with execution results
        """
        # If at depth limit or no sub-goals, execute as leaf
        if current_depth >= depth_limit or not plan.get("sub_goals"):
            if current_depth >= depth_limit and plan.get("sub_goals"):
                # Create a partial result for non-leaf goals at depth limit
                result = {
                    "success": True,
                    "status": "partial",
                    "progress": 0.5,
                    "message": f"Execution limited to depth {depth_limit}"
                }
            else:
                # Execute leaf goal normally
                result = self._execute_leaf_goal(plan["goal"], context, config)
            
            self._update_execution_state(execution_state, plan["id"], result)
            return result
        
        # Execute sub-goals up to depth limit
        dependencies = self._build_dependency_graph(plan)
        results = {}
        
        # Find sub-goals with no dependencies
        ready_goals = self._find_ready_goals(plan, dependencies, execution_state)
        
        for sub_goal in ready_goals:
            # Execute with the depth limit
            sub_result = self._execute_with_depth_limit(
                sub_goal, context, config, execution_state, 
                current_depth + 1, depth_limit
            )
            
            results[sub_goal["id"]] = sub_result
            
            # Check if execution should halt on error
            if config.get("halt_on_error", False) and not sub_result.get("success", False):
                break
            
            # Update dependencies and get next ready goals
            ready_goals = self._find_ready_goals(plan, dependencies, execution_state)
        
        # Calculate goal result
        goal_result = self._calculate_goal_result(plan, results)
        
        # Update execution state
        self._update_execution_state(execution_state, plan["id"], goal_result)
        
        return goal_result
    
    def _execute_dynamic_adjustment(self, plan: Dict[str, Any], 
                                 context: Dict[str, Any],
                                 config: Dict[str, Any],
                                 execution_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute plan using dynamic adjustment strategy.
        
        Args:
            plan: Plan structure to execute
            context: Context information
            config: Execution configuration
            execution_state: Current execution state
            
        Returns:
            Dictionary with execution results
        """
        # Dynamic adjustment uses feedback to adjust execution strategy
        # Start with depth-first as the default strategy
        strategy = "depth_first"
        results = {}
        
        # Execute iteratively, adjusting strategy based on feedback
        while True:
            # Execute one step with current strategy
            if strategy == "depth_first":
                partial_result = self._execute_depth_first_step(plan, context, config, execution_state, results)
            elif strategy == "breadth_first":
                partial_result = self._execute_breadth_first_step(plan, context, config, execution_state, results)
            elif strategy == "priority_based":
                partial_result = self._execute_priority_based_step(plan, context, config, execution_state, results)
            else:
                # Default to depth-first
                partial_result = self._execute_depth_first_step(plan, context, config, execution_state, results)
            
            # Check for completion
            if partial_result.get("completed", False):
                # Execution complete
                break
            
            # Check for error
            if config.get("halt_on_error", False) and not partial_result.get("success", False):
                # Execution failed
                break
            
            # Adjust strategy based on feedback
            new_strategy = self._adjust_execution_strategy(strategy, partial_result, config)
            if new_strategy != strategy:
                # Strategy changed
                self._log_strategy_change(execution_state, strategy, new_strategy, partial_result.get("reason", ""))
                strategy = new_strategy
        
        # Calculate final result
        goal_result = self._calculate_goal_result(plan, results)
        
        # Update execution state
        self._update_execution_state(execution_state, plan["id"], goal_result)
        
        return goal_result
    
    def _execute_depth_first_step(self, plan: Dict[str, Any], 
                               context: Dict[str, Any],
                               config: Dict[str, Any],
                               execution_state: Dict[str, Any],
                               results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute one step of depth-first execution.
        
        Args:
            plan: Plan structure to execute
            context: Context information
            config: Execution configuration
            execution_state: Current execution state
            results: Current execution results
            
        Returns:
            Dictionary with step execution results
        """
        # For a real implementation, this would execute one sub-goal
        # Here we give a simplified version that just checks completion
        
        # Check if all sub-goals are completed
        all_completed = True
        for sub_goal in plan.get("sub_goals", []):
            if sub_goal["id"] not in results:
                all_completed = False
                break
        
        if all_completed:
            return {
                "completed": True,
                "success": all(results[sg["id"]].get("success", False) for sg in plan.get("sub_goals", []))
            }
        
        # If leaf goal, execute it
        if not plan.get("sub_goals"):
            result = self._execute_leaf_goal(plan["goal"], context, config)
            results[plan["id"]] = result
            
            return {
                "completed": True,
                "success": result.get("success", False)
            }
        
        # Find next goal to execute
        dependencies = self._build_dependency_graph(plan)
        ready_goals = self._find_ready_goals(plan, dependencies, execution_state)
        
        if not ready_goals:
            # No ready goals - check if it's due to circular dependencies
            all_sub_goals = set(sg["id"] for sg in plan.get("sub_goals", []))
            executed_goals = set(results.keys())
            pending_goals = all_sub_goals - executed_goals
            
            if pending_goals:
                # Circular dependency or all goals pending dependencies
                return {
                    "completed": False,
                    "success": False,
                    "reason": "circular_dependency"
                }
            else:
                # All goals already executed
                return {
                    "completed": True,
                    "success": all(results[sg_id].get("success", False) for sg_id in all_sub_goals)
                }
        
        # Execute the first ready goal
        next_goal = ready_goals[0]
        result = self._execute_depth_first(next_goal, context, config, execution_state)
        results[next_goal["id"]] = result
        
        return {
            "completed": False,
            "success": result.get("success", False),
            "executed_goal": next_goal["id"]
        }
    
    def _execute_breadth_first_step(self, plan: Dict[str, Any], 
                                 context: Dict[str, Any],
                                 config: Dict[str, Any],
                                 execution_state: Dict[str, Any],
                                 results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute one step of breadth-first execution.
        
        Args:
            plan: Plan structure to execute
            context: Context information
            config: Execution configuration
            execution_state: Current execution state
            results: Current execution results
            
        Returns:
            Dictionary with step execution results
        """
        # For demonstration, this is a simplified version that's similar to depth-first step
        # A full implementation would maintain a breadth-first queue
        
        # Check completion
        all_completed = True
        for sub_goal in plan.get("sub_goals", []):
            if sub_goal["id"] not in results:
                all_completed = False
                break
        
        if all_completed:
            return {
                "completed": True,
                "success": all(results[sg["id"]].get("success", False) for sg in plan.get("sub_goals", []))
            }
        
        # Find all goals at the current level
        dependencies = self._build_dependency_graph(plan)
        ready_goals = self._find_ready_goals(plan, dependencies, execution_state)
        
        if not ready_goals:
            # No ready goals - check if it's due to circular dependencies
            all_sub_goals = set(sg["id"] for sg in plan.get("sub_goals", []))
            executed_goals = set(results.keys())
            pending_goals = all_sub_goals - executed_goals
            
            if pending_goals:
                # Circular dependency or all goals pending dependencies
                return {
                    "completed": False,
                    "success": False,
                    "reason": "circular_dependency"
                }
            else:
                # All goals already executed
                return {
                    "completed": True,
                    "success": all(results[sg_id].get("success", False) for sg_id in all_sub_goals)
                }
        
        # Execute the first ready goal
        next_goal = ready_goals[0]
        
        # For real breadth-first, we would execute just the goal itself, not its children
        # But for simplicity in this demonstration, we'll use the same approach as depth-first
        result = self._execute_leaf_goal(next_goal["goal"], context, config)
        results[next_goal["id"]] = result
        
        return {
            "completed": False,
            "success": result.get("success", False),
            "executed_goal": next_goal["id"]
        }
    
    def _execute_priority_based_step(self, plan: Dict[str, Any], 
                                  context: Dict[str, Any],
                                  config: Dict[str, Any],
                                  execution_state: Dict[str, Any],
                                  results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute one step of priority-based execution.
        
        Args:
            plan: Plan structure to execute
            context: Context information
            config: Execution configuration
            execution_state: Current execution state
            results: Current execution results
            
        Returns:
            Dictionary with step execution results
        """
        # Check completion
        all_completed = True
        for sub_goal in plan.get("sub_goals", []):
            if sub_goal["id"] not in results:
                all_completed = False
                break
        
        if all_completed:
            return {
                "completed": True,
                "success": all(results[sg["id"]].get("success", False) for sg in plan.get("sub_goals", []))
            }
        
        # Get dependency information
        dependencies = self._build_dependency_graph(plan)
        
        # Find ready goals
        ready_sub_goals = []
        for sub_goal in plan.get("sub_goals", []):
            # Skip if already executed
            if sub_goal["id"] in results:
                continue
            
            # Check dependencies
            deps_satisfied = True
            if sub_goal["id"] in dependencies:
                for dep in dependencies[sub_goal["id"]]:
                    if dep not in results or not results[dep].get("success", False):
                        deps_satisfied = False
                        break
            
            if deps_satisfied:
                ready_sub_goals.append(sub_goal)
        
        if not ready_sub_goals:
            # No ready goals - check if it's due to circular dependencies
            all_sub_goals = set(sg["id"] for sg in plan.get("sub_goals", []))
            executed_goals = set(results.keys())
            pending_goals = all_sub_goals - executed_goals
            
            if pending_goals:
                # Circular dependency or all goals pending dependencies
                return {
                    "completed": False,
                    "success": False,
                    "reason": "circular_dependency"
                }
            else:
                # All goals already executed
                return {
                    "completed": True,
                    "success": all(results[sg_id].get("success", False) for sg_id in all_sub_goals)
                }
        
        # Sort ready goals by priority
        priority_goals = []
        for sub_goal in ready_sub_goals:
            priority = sub_goal["goal"].get("priority", 5)  # Default priority
            
            # Adjust priority based on critical path
            if sub_goal["goal"].get("on_critical_path", False):
                priority += 3
            
            priority_goals.append((priority, sub_goal))
        
        # Sort by priority (highest first)
        priority_goals.sort(reverse=True, key=lambda x: x[0])
        
        # Execute highest priority goal
        _, next_goal = priority_goals[0]
        result = self._execute_leaf_goal(next_goal["goal"], context, config)
        results[next_goal["id"]] = result
        
        return {
            "completed": False,
            "success": result.get("success", False),
            "executed_goal": next_goal["id"],
            "priority": priority_goals[0][0]
        }
    
    def _adjust_execution_strategy(self, current_strategy: str, 
                                partial_result: Dict[str, Any],
                                config: Dict[str, Any]) -> str:
        """
        Adjust execution strategy based on feedback.
        
        Args:
            current_strategy: Current execution strategy
            partial_result: Result from the last execution step
            config: Execution configuration
            
        Returns:
            New execution strategy
        """
        # Check for specific conditions that warrant strategy changes
        
        # If we detected circular dependencies, switch to priority-based
        if partial_result.get("reason") == "circular_dependency":
            return "priority_based"
        
        # If we're getting timeouts, switch to breadth-first
        if partial_result.get("reason") == "timeout":
            return "breadth_first"
        
        # If we're under resource pressure, switch to depth-first (less memory)
        if partial_result.get("reason") == "resource_pressure":
            return "depth_first"
        
        # If critical path is important, use priority-based
        if partial_result.get("reason") == "critical_path_delay":
            return "priority_based"
        
        # Default: keep the current strategy
        return current_strategy
    
    def _log_strategy_change(self, execution_state: Dict[str, Any], 
                          old_strategy: str, new_strategy: str, reason: str) -> None:
        """
        Log a change in execution strategy.
        
        Args:
            execution_state: Current execution state
            old_strategy: Previous execution strategy
            new_strategy: New execution strategy
            reason: Reason for the change
            
        Returns:
            None
        """
        log_entry = {
            "timestamp": time.time(),
            "type": "strategy_change",
            "old_strategy": old_strategy,
            "new_strategy": new_strategy,
            "reason": reason
        }
        
        execution_state["execution_log"].append(log_entry)
    
    def _execute_leaf_goal(self, goal: Dict[str, Any], 
                        context: Dict[str, Any],
                        config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a leaf goal (no sub-goals).
        
        Args:
            goal: Goal to execute
            context: Context information
            config: Execution configuration
            
        Returns:
            Dictionary with execution results
        """
        # In a real implementation, this would execute the goal by calling appropriate functions
        # For this demonstration, we'll simulate execution
        
        # Extract goal information
        goal_id = goal.get("id", "unknown")
        description = goal.get("description", "")
        goal_type = goal.get("type", "achievement")
        
        # Simulated execution result
        # In a real system, this would call domain-specific execution functions
        result = {
            "goal_id": goal_id,
            "executed": True,
            "start_time": time.time()
        }
        
        # Simulate execution time based on goal complexity
        complexity = len(description) / 50  # Simple proxy for complexity
        execution_time = 0.01 * complexity  # Simulated time in seconds
        
        # Add a small random variation to simulate execution differences
        execution_time *= random.uniform(0.8, 1.2)
        
        # Simulate processing
        # time.sleep(execution_time)  # Uncomment for actual delay
        
        # Determine success based on goal type and simulated execution
        success_probability = 0.9  # 90% success rate for simulation
        
        # Adjust based on goal type
        if goal_type == "optimization":
            success_probability = 0.85  # Slightly lower for optimization
        elif goal_type == "exploration":
            success_probability = 0.95  # Higher for exploration
        
        # Simulate success/failure
        success = random.random() < success_probability
        
        # Complete result
        result["end_time"] = time.time()
        result["execution_time"] = result["end_time"] - result["start_time"]
        result["success"] = success
        
        if success:
            result["status"] = "completed"
            result["progress"] = 1.0
            result["message"] = f"Successfully executed: {description}"
            
            # Add goal-type specific results
            if goal_type == "optimization":
                result["optimization_improvement"] = random.uniform(0.1, 0.5)
            elif goal_type == "exploration":
                result["exploration_coverage"] = random.uniform(0.7, 0.95)
        else:
            result["status"] = "failed"
            result["progress"] = random.uniform(0.2, 0.8)
            result["message"] = f"Failed to execute: {description}"
            result["error"] = "Simulated execution failure"
        
        return result
    
    def _build_dependency_graph(self, plan: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Build a dependency graph from plan dependencies.
        
        Args:
            plan: Plan structure
            
        Returns:
            Dictionary mapping goal IDs to lists of prerequisite goal IDs
        """
        dependencies = {}
        
        for dep in plan.get("dependencies", []):
            # Only include prerequisite and enablement dependencies
            if dep["type"] in ["prerequisite", "enablement"]:
                target = dep["target"]
                source = dep["source"]
                
                if target not in dependencies:
                    dependencies[target] = []
                
                dependencies[target].append(source)
        
        return dependencies
    
    def _find_ready_goals(self, plan: Dict[str, Any], 
                       dependencies: Dict[str, List[str]],
                       execution_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find goals ready for execution (dependencies satisfied).
        
        Args:
            plan: Plan structure
            dependencies: Dependency graph
            execution_state: Current execution state
            
        Returns:
            List of sub-goals ready for execution
        """
        # Get IDs of completed tasks
        completed_ids = set(task["goal_id"] for task in execution_state["completed_tasks"])
        
        # Find ready goals
        ready_goals = []
        
        for sub_goal in plan.get("sub_goals", []):
            goal_id = sub_goal["id"]
            
            # Skip if already completed
            if goal_id in completed_ids:
                continue
            
            # Check if all dependencies are satisfied
            deps_satisfied = True
            if goal_id in dependencies:
                for dep_id in dependencies[goal_id]:
                    if dep_id not in completed_ids:
                        deps_satisfied = False
                        break
            
            if deps_satisfied:
                ready_goals.append(sub_goal)
        
        return ready_goals
    
    def _calculate_goal_result(self, plan: Dict[str, Any], 
                            sub_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate the result for a goal based on sub-goal results.
        
        Args:
            plan: Plan structure
            sub_results: Results of sub-goals
            
        Returns:
            Dictionary with calculated goal result
        """
        # If no sub-goals, return default success
        if not plan.get("sub_goals"):
            return {
                "goal_id": plan["id"],
                "success": True,
                "status": "completed",
                "progress": 1.0,
                "message": f"Goal achieved: {plan['goal'].get('description', '')}"
            }
        
        # Get results for all sub-goals
        all_sub_goals = [sg["id"] for sg in plan["sub_goals"]]
        executed_sub_goals = set(sub_results.keys())
        
        # Calculate overall success
        all_executed = set(all_sub_goals).issubset(executed_sub_goals)
        all_successful = all(sub_results.get(sg_id, {}).get("success", False) for sg_id in all_sub_goals)
        
        # Calculate progress as average of sub-goal progress
        total_progress = 0
        for sg_id in all_sub_goals:
            if sg_id in sub_results:
                total_progress += sub_results[sg_id].get("progress", 0)
            
        avg_progress = total_progress / len(all_sub_goals) if all_sub_goals else 0
        
        # Determine status
        if not all_executed:
            status = "in_progress"
        elif all_successful:
            status = "completed"
        else:
            status = "failed"
        
        # Create result
        result = {
            "goal_id": plan["id"],
            "success": all_executed and all_successful,
            "status": status,
            "progress": avg_progress,
            "sub_goal_count": len(all_sub_goals),
            "executed_count": len(executed_sub_goals),
            "successful_count": sum(1 for sg_id in executed_sub_goals if sub_results.get(sg_id, {}).get("success", False)),
            "sub_results": sub_results
        }
        
        if status == "completed":
            result["message"] = f"Goal achieved: {plan['goal'].get('description', '')}"
        elif status == "failed":
            result["message"] = f"Goal failed: {plan['goal'].get('description', '')}"
        else:
            result["message"] = f"Goal in progress: {plan['goal'].get('description', '')}"
        
        return result
    
    def _update_execution_state(self, execution_state: Dict[str, Any], 
                             goal_id: str, result: Dict[str, Any]) -> None:
        """
        Update execution state with goal execution result.
        
        Args:
            execution_state: Current execution state
            goal_id: ID of the executed goal
            result: Execution result
            
        Returns:
            None (updates execution_state in place)
        """
        # Create a task result entry
        task_result = {
            "goal_id": goal_id,
            "timestamp": time.time(),
            "success": result.get("success", False),
            "status": result.get("status", "unknown"),
            "message": result.get("message", "")
        }
        
        # Add to appropriate list
        if result.get("success", False):
            execution_state["completed_tasks"].append(task_result)
        else:
            execution_state["failed_tasks"].append(task_result)
        
        # Add to execution log
        log_entry = {
            "timestamp": time.time(),
            "type": "goal_execution",
            "goal_id": goal_id,
            "success": result.get("success", False),
            "status": result.get("status", "unknown"),
            "message": result.get("message", "")
        }
        
        execution_state["execution_log"].append(log_entry)
        
        # Update overall progress
        executed_count = len(execution_state["completed_tasks"]) + len(execution_state["failed_tasks"])
        total_count = max(1, executed_count + len(execution_state["current_tasks"]))
        execution_state["progress"] = executed_count / total_count


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Recursive Planning AGI Core (KA-56) on the provided data.
    
    Args:
        data: A dictionary containing goal description and optional configuration
        
    Returns:
        Dictionary with planning or execution results
    """
    mode = data.get("mode", "plan")  # "plan" or "execute"
    goal = data.get("goal", {})
    context = data.get("context", {})
    config = data.get("config", None)
    plan = data.get("plan")  # Only needed for execute mode
    
    # Generate sample data if requested
    if not goal and data.get("generate_sample", False):
        goal, context = generate_sample_data(
            data.get("goal_type", "achievement"),
            data.get("complexity", "medium")
        )
    
    # Validate inputs
    if not goal and mode == "plan":
        return {
            "algorithm": "KA-56",
            "success": False,
            "error": "No goal specification provided for planning",
            "timestamp": time.time()
        }
    
    if not plan and mode == "execute":
        return {
            "algorithm": "KA-56",
            "success": False,
            "error": "No plan provided for execution",
            "timestamp": time.time()
        }
    
    planner = RecursivePlanningAGICore()
    
    try:
        if mode == "plan":
            # Create a recursive plan
            result = planner.create_recursive_plan(goal, context, config)
            
            if not result.get("success", False):
                return {
                    "algorithm": "KA-56",
                    "success": False,
                    "error": result.get("error", "Unknown planning error"),
                    "timestamp": time.time()
                }
            
            return {
                "algorithm": "KA-56",
                "success": True,
                "plan": result["plan"],
                "timestamp": time.time()
            }
        
        elif mode == "execute":
            # Execute a plan
            result = planner.execute_plan(plan, context, config)
            
            if not result.get("success", False):
                return {
                    "algorithm": "KA-56",
                    "success": False,
                    "error": "Plan execution failed",
                    "execution_state": result.get("execution_state"),
                    "timestamp": time.time()
                }
            
            return {
                "algorithm": "KA-56",
                "success": True,
                "execution_result": result["execution_result"],
                "execution_state": result["execution_state"],
                "timestamp": time.time()
            }
        
        else:
            return {
                "algorithm": "KA-56",
                "success": False,
                "error": f"Invalid mode: {mode}",
                "timestamp": time.time()
            }
    
    except Exception as e:
        logger.error(f"Error in KA-56 Recursive Planning AGI Core: {str(e)}")
        return {
            "algorithm": "KA-56",
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        }


def generate_sample_data(goal_type: str, complexity: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generate sample data for testing.
    
    Args:
        goal_type: Type of goal to generate
        complexity: Complexity level (simple, medium, complex)
        
    Returns:
        Tuple of (goal, context)
    """
    # Sample goals by type
    sample_goals = {
        "achievement": {
            "simple": "Create a data visualization of user activity",
            "medium": "Build a recommendation system that suggests products based on user behavior",
            "complex": "Develop an end-to-end machine learning pipeline for predictive maintenance"
        },
        "optimization": {
            "simple": "Improve database query performance",
            "medium": "Optimize resource allocation across microservices to reduce costs",
            "complex": "Minimize energy consumption while maintaining system performance across distributed nodes"
        },
        "learning": {
            "simple": "Learn basic Python programming concepts",
            "medium": "Master natural language processing techniques for text analysis",
            "complex": "Develop expertise in quantum computing algorithms and their applications"
        },
        "exploration": {
            "simple": "Investigate available data visualization libraries",
            "medium": "Explore patterns in user behavior across different demographics",
            "complex": "Research emerging technologies in artificial intelligence and their potential applications"
        },
        "maintenance": {
            "simple": "Keep system uptime above 99%",
            "medium": "Maintain data quality metrics within acceptable thresholds",
            "complex": "Ensure consistent performance across all services while handling increasing load"
        },
        "prevention": {
            "simple": "Prevent unauthorized access to user data",
            "medium": "Avoid performance degradation during peak usage periods",
            "complex": "Prevent cascading failures in the distributed system architecture"
        }
    }
    
    # Get the specified goal description
    if goal_type in sample_goals and complexity in sample_goals[goal_type]:
        description = sample_goals[goal_type][complexity]
    else:
        # Default to a generic achievement goal
        description = "Complete the assigned task successfully"
        goal_type = "achievement"
    
    # Create the goal structure
    goal = {
        "id": f"goal_{str(uuid.uuid4())[:8]}",
        "type": goal_type,
        "description": description
    }
    
    # Add complexity-specific attributes
    if complexity == "complex":
        # Complex goals might have constraints or specific requirements
        if goal_type == "optimization":
            goal["constraints"] = [
                {
                    "type": "resource",
                    "resource": "budget",
                    "limit": 1000,
                    "priority": "hard"
                },
                {
                    "type": "performance",
                    "metric": "response_time",
                    "threshold": 200,  # ms
                    "priority": "soft"
                }
            ]
        elif goal_type == "achievement":
            # Add specific steps for achievement goals
            goal["steps"] = [
                "Analyze requirements and create specification",
                "Design system architecture",
                "Implement core components",
                "Test and validate functionality",
                "Deploy and monitor performance"
            ]
    
    # Create context based on complexity
    context = {
        "domain": "software_development",
        "resource_limited": complexity != "simple"
    }
    
    if complexity == "medium" or complexity == "complex":
        context["requires_planning"] = True
    
    if complexity == "complex":
        context["uncertain_environment"] = True
        context["requires_adaptation"] = True
        context["resource_limits"] = {
            "time": 40,  # hours
            "budget": 5000  # arbitrary units
        }
    
    return goal, context
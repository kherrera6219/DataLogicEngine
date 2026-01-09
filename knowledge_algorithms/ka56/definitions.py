"""
KA-56 Definitions
Contains static configuration for planning strategies, goal types, and execution modes.
"""

def get_planning_strategies():
    return {
        "decomposition": {
            "description": "Break complex goals into simpler sub-goals",
            "applicable_to": ["high_level", "complex_task", "long_term"],
            "max_recursion_depth": 5,
            "branching_factor": [3, 7]
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

def get_goal_types():
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

def get_execution_modes():
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

def get_dependency_types():
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

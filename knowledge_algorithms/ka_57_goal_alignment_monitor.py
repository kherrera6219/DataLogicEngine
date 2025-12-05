"""
KA-57: Goal Alignment Monitor

This algorithm monitors goal alignment between sub-goals and overall objectives,
ensuring all generated steps and actions remain aligned with intended purposes
and constraints.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
import time
import math
import random
import uuid
import copy

logger = logging.getLogger(__name__)

class GoalAlignmentMonitor:
    """
    KA-57: Goal Alignment Monitor.
    
    This algorithm monitors and verifies goal alignment between sub-goals, plans,
    and overall objectives, ensuring that generated steps and actions remain 
    aligned with intended purposes and constraints. It can detect goal drift,
    measure alignment strength, and suggest corrective actions.
    """
    
    def __init__(self):
        """Initialize the Goal Alignment Monitor."""
        self.alignment_metrics = self._initialize_alignment_metrics()
        self.alignment_thresholds = self._initialize_alignment_thresholds()
        self.drift_patterns = self._initialize_drift_patterns()
        self.verification_methods = self._initialize_verification_methods()
        logger.info("KA-57: Goal Alignment Monitor initialized")
    
    def _initialize_alignment_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Initialize metrics for measuring goal alignment."""
        return {
            "semantic_similarity": {
                "description": "Measure of meaning similarity between goals",
                "weight": 0.35,
                "evaluation_method": "semantic_embedding",
                "scale": [0.0, 1.0],
                "threshold": 0.75
            },
            "objective_consistency": {
                "description": "Consistency of objectives across goal hierarchy",
                "weight": 0.25,
                "evaluation_method": "constraint_checking",
                "scale": [0.0, 1.0],
                "threshold": 0.8
            },
            "value_alignment": {
                "description": "Alignment with core values and principles",
                "weight": 0.15,
                "evaluation_method": "value_comparison",
                "scale": [0.0, 1.0],
                "threshold": 0.9
            },
            "path_coherence": {
                "description": "Logical coherence of goals, sub-goals, and actions",
                "weight": 0.15,
                "evaluation_method": "graph_analysis",
                "scale": [0.0, 1.0],
                "threshold": 0.7
            },
            "outcome_convergence": {
                "description": "Likelihood that sub-goals lead to desired outcome",
                "weight": 0.1,
                "evaluation_method": "simulation",
                "scale": [0.0, 1.0],
                "threshold": 0.8
            }
        }
    
    def _initialize_alignment_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Initialize thresholds for different alignment levels."""
        return {
            "perfect": {
                "description": "Complete alignment with original goals",
                "threshold": 0.95,
                "action_required": "none"
            },
            "strong": {
                "description": "Strong alignment with minor deviations",
                "threshold": 0.85,
                "action_required": "monitoring"
            },
            "acceptable": {
                "description": "Acceptable alignment with some deviations",
                "threshold": 0.7,
                "action_required": "review"
            },
            "concerning": {
                "description": "Notable deviations that may affect outcome",
                "threshold": 0.5,
                "action_required": "adjustment"
            },
            "misaligned": {
                "description": "Significant deviations from original goals",
                "threshold": 0.3,
                "action_required": "revision"
            },
            "conflicting": {
                "description": "Actions working against original goals",
                "threshold": 0.0,
                "action_required": "halt_and_reset"
            }
        }
    
    def _initialize_drift_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns of goal drift to detect."""
        return {
            "scope_creep": {
                "description": "Gradual expansion beyond original goals",
                "indicators": ["increasing_complexity", "breadth_expansion", "vague_boundaries"],
                "detection_metrics": ["semantic_similarity", "path_coherence"],
                "risk_level": "medium"
            },
            "means_end_inversion": {
                "description": "Sub-goals become ends in themselves",
                "indicators": ["metric_fixation", "process_over_outcome", "lost_purpose"],
                "detection_metrics": ["objective_consistency", "outcome_convergence"],
                "risk_level": "high"
            },
            "value_substitution": {
                "description": "Original values replaced by proxies",
                "indicators": ["metric_gaming", "value_narrowing", "externality_creation"],
                "detection_metrics": ["value_alignment"],
                "risk_level": "critical"
            },
            "mission_creep": {
                "description": "Gradual shift to different mission",
                "indicators": ["priority_shift", "resource_reallocation", "changing_focus"],
                "detection_metrics": ["semantic_similarity", "objective_consistency"],
                "risk_level": "high"
            },
            "optimization_drift": {
                "description": "Over-optimization of one aspect at expense of others",
                "indicators": ["imbalanced_metrics", "diminishing_returns", "negative_externalities"],
                "detection_metrics": ["value_alignment", "objective_consistency"],
                "risk_level": "medium"
            },
            "goal_fragmentation": {
                "description": "Sub-goals disconnect from each other",
                "indicators": ["siloed_execution", "coordination_failure", "conflicting_actions"],
                "detection_metrics": ["path_coherence", "outcome_convergence"],
                "risk_level": "high"
            }
        }
    
    def _initialize_verification_methods(self) -> Dict[str, Dict[str, Any]]:
        """Initialize methods for verifying goal alignment."""
        return {
            "semantic_analysis": {
                "description": "Analyze semantic meaning of goals and sub-goals",
                "applicability": "all_goal_types",
                "required_data": ["goal_descriptions"],
                "reliability": 0.8
            },
            "constraint_validation": {
                "description": "Check if sub-goals maintain all constraints of parent goals",
                "applicability": "constrained_goals",
                "required_data": ["goal_constraints", "sub_goal_specifications"],
                "reliability": 0.9
            },
            "outcome_projection": {
                "description": "Project likely outcomes of sub-goals and compare to desired outcome",
                "applicability": "achievement_goals",
                "required_data": ["goal_specification", "sub_goal_specifications", "outcome_metrics"],
                "reliability": 0.7
            },
            "value_consistency": {
                "description": "Check if values and principles are maintained",
                "applicability": "value_sensitive_goals",
                "required_data": ["value_specifications", "sub_goal_specifications"],
                "reliability": 0.85
            },
            "graph_theoretic": {
                "description": "Analyze goal dependency graphs for consistency",
                "applicability": "complex_goal_structures",
                "required_data": ["goal_hierarchy", "dependency_graph"],
                "reliability": 0.8
            },
            "temporal_consistency": {
                "description": "Verify alignment across time steps during execution",
                "applicability": "sequential_goals",
                "required_data": ["goal_history", "current_state", "planned_actions"],
                "reliability": 0.75
            }
        }
    
    def monitor_goal_alignment(self, goal_hierarchy: Dict[str, Any], 
                             execution_history: Optional[List[Dict[str, Any]]] = None,
                             config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Monitor and evaluate alignment across a goal hierarchy.
        
        Args:
            goal_hierarchy: Hierarchical structure of goals and sub-goals
            execution_history: Optional history of goal execution
            config: Optional configuration for monitoring
            
        Returns:
            Dictionary with alignment analysis
        """
        # Set default configuration if not provided
        if config is None:
            config = {
                "monitoring_depth": 3,  # How many levels to check
                "metrics_to_use": ["semantic_similarity", "objective_consistency", "path_coherence"],
                "min_threshold": "acceptable",  # Minimum acceptable alignment level
                "verification_methods": ["semantic_analysis", "constraint_validation"],
                "detailed_analysis": True,
                "suggest_corrections": True
            }
        
        # Validate inputs
        if not goal_hierarchy or "root_goal" not in goal_hierarchy:
            return {
                "success": False,
                "error": "Invalid goal hierarchy structure",
                "alignment_score": 0.0
            }
        
        # Extract maximum depth for monitoring
        max_depth = config.get("monitoring_depth", 3)
        
        # Get metrics to use
        metrics_to_use = config.get("metrics_to_use", list(self.alignment_metrics.keys()))
        
        # Get verification methods to use
        methods_to_use = config.get("verification_methods", list(self.verification_methods.keys()))
        
        # Build hierarchical alignment map
        alignment_map = self._build_alignment_map(
            goal_hierarchy,
            metrics_to_use,
            methods_to_use,
            max_depth,
            execution_history
        )
        
        # Calculate overall alignment score
        overall_score = self._calculate_overall_alignment(alignment_map)
        
        # Determine alignment category
        alignment_category = self._categorize_alignment(overall_score)
        
        # Detect drift patterns
        drift_patterns = self._detect_drift_patterns(alignment_map, execution_history)
        
        # Generate suggestions if requested
        suggestions = []
        if config.get("suggest_corrections", True) and drift_patterns:
            suggestions = self._generate_alignment_suggestions(
                goal_hierarchy, 
                alignment_map, 
                drift_patterns
            )
        
        # Prepare result
        result = {
            "success": True,
            "alignment_score": overall_score,
            "alignment_category": alignment_category,
            "detail_map": alignment_map,
            "detected_drift": drift_patterns,
            "suggestions": suggestions,
            "timestamp": time.time()
        }
        
        return result
    
    def _build_alignment_map(self, goal_hierarchy: Dict[str, Any], 
                          metrics: List[str],
                          methods: List[str],
                          max_depth: int,
                          execution_history: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Build a map of alignment scores across the goal hierarchy.
        
        Args:
            goal_hierarchy: Hierarchical structure of goals and sub-goals
            metrics: List of metrics to compute
            methods: List of verification methods to apply
            max_depth: Maximum depth to analyze
            execution_history: Optional history of goal execution
            
        Returns:
            Dictionary with alignment map
        """
        alignment_map = {
            "root": {
                "goal_id": goal_hierarchy.get("root_goal", {}).get("id", "root"),
                "description": goal_hierarchy.get("root_goal", {}).get("description", ""),
                "alignment_score": 1.0,  # Root is perfectly aligned with itself
                "metrics": {metric: 1.0 for metric in metrics},
                "children": []
            }
        }
        
        # Process sub-goals
        root_goal = goal_hierarchy.get("root_goal", {})
        sub_goals = goal_hierarchy.get("sub_goals", [])
        
        if sub_goals:
            # Process first level sub-goals
            self._process_sub_goals(
                alignment_map["root"], 
                root_goal, 
                sub_goals, 
                metrics, 
                methods, 
                1, 
                max_depth, 
                execution_history
            )
        
        return alignment_map
    
    def _process_sub_goals(self, parent_map: Dict[str, Any], 
                         parent_goal: Dict[str, Any],
                         sub_goals: List[Dict[str, Any]],
                         metrics: List[str],
                         methods: List[str],
                         current_depth: int,
                         max_depth: int,
                         execution_history: Optional[List[Dict[str, Any]]]) -> None:
        """
        Process sub-goals and calculate alignment with parent.
        
        Args:
            parent_map: Parent node in the alignment map
            parent_goal: Parent goal information
            sub_goals: List of sub-goals
            metrics: List of metrics to compute
            methods: List of verification methods to apply
            current_depth: Current depth in the hierarchy
            max_depth: Maximum depth to analyze
            execution_history: Optional history of goal execution
            
        Returns:
            None (updates parent_map in place)
        """
        # Stop if max depth reached
        if current_depth > max_depth:
            return
        
        # Process each sub-goal
        for sub_goal in sub_goals:
            # Calculate alignment metrics for this sub-goal
            alignment_scores = self._calculate_alignment_metrics(
                parent_goal, 
                sub_goal, 
                metrics, 
                methods, 
                execution_history
            )
            
            # Calculate overall alignment for this sub-goal
            overall_alignment = self._calculate_weighted_alignment(alignment_scores)
            
            # Create map entry for this sub-goal
            sub_goal_map = {
                "goal_id": sub_goal.get("id", "unknown"),
                "description": sub_goal.get("description", ""),
                "alignment_score": overall_alignment,
                "metrics": alignment_scores,
                "children": []
            }
            
            # Add to parent's children
            parent_map["children"].append(sub_goal_map)
            
            # Process this sub-goal's sub-goals if any
            sub_sub_goals = sub_goal.get("sub_goals", [])
            if sub_sub_goals:
                self._process_sub_goals(
                    sub_goal_map, 
                    sub_goal, 
                    sub_sub_goals, 
                    metrics, 
                    methods, 
                    current_depth + 1, 
                    max_depth, 
                    execution_history
                )
    
    def _calculate_alignment_metrics(self, parent_goal: Dict[str, Any], 
                                  sub_goal: Dict[str, Any],
                                  metrics_to_use: List[str],
                                  methods_to_use: List[str],
                                  execution_history: Optional[List[Dict[str, Any]]]) -> Dict[str, float]:
        """
        Calculate alignment metrics between a goal and sub-goal.
        
        Args:
            parent_goal: Parent goal information
            sub_goal: Sub-goal information
            metrics_to_use: List of metrics to compute
            methods_to_use: List of verification methods to apply
            execution_history: Optional history of goal execution
            
        Returns:
            Dictionary mapping metric names to scores
        """
        metric_scores = {}
        
        for metric_name in metrics_to_use:
            if metric_name not in self.alignment_metrics:
                continue
                
            metric_info = self.alignment_metrics[metric_name]
            eval_method = metric_info["evaluation_method"]
            
            # Calculate this metric using the appropriate evaluation method
            if eval_method == "semantic_embedding":
                score = self._evaluate_semantic_similarity(parent_goal, sub_goal)
            elif eval_method == "constraint_checking":
                score = self._evaluate_constraint_consistency(parent_goal, sub_goal)
            elif eval_method == "value_comparison":
                score = self._evaluate_value_alignment(parent_goal, sub_goal)
            elif eval_method == "graph_analysis":
                score = self._evaluate_path_coherence(parent_goal, sub_goal)
            elif eval_method == "simulation":
                score = self._evaluate_outcome_convergence(parent_goal, sub_goal, execution_history)
            else:
                # Default method - semantic similarity
                score = self._evaluate_semantic_similarity(parent_goal, sub_goal)
            
            metric_scores[metric_name] = score
        
        return metric_scores
    
    def _evaluate_semantic_similarity(self, parent_goal: Dict[str, Any], 
                                   sub_goal: Dict[str, Any]) -> float:
        """
        Evaluate semantic similarity between goal descriptions.
        
        Args:
            parent_goal: Parent goal information
            sub_goal: Sub-goal information
            
        Returns:
            Semantic similarity score (0-1)
        """
        # In a real implementation, this would use embeddings or NLP models
        # For this demonstration, we'll use a simplified approach
        
        parent_desc = parent_goal.get("description", "").lower()
        sub_desc = sub_goal.get("description", "").lower()
        
        if not parent_desc or not sub_desc:
            return 0.5  # Neutral score for missing descriptions
        
        # Simple word overlap measure
        parent_words = set(parent_desc.split())
        sub_words = set(sub_desc.split())
        
        if not parent_words or not sub_words:
            return 0.5
        
        # Calculate Jaccard similarity
        intersection = len(parent_words.intersection(sub_words))
        union = len(parent_words.union(sub_words))
        
        jaccard_similarity = intersection / union if union > 0 else 0
        
        # Check for key phrases
        parent_key_phrases = parent_goal.get("key_phrases", [])
        if parent_key_phrases:
            phrase_match_score = 0
            for phrase in parent_key_phrases:
                if phrase.lower() in sub_desc:
                    phrase_match_score += 1
            
            phrase_score = phrase_match_score / len(parent_key_phrases) if parent_key_phrases else 0
            
            # Combine scores (give more weight to key phrases if available)
            return 0.4 * jaccard_similarity + 0.6 * phrase_score
        
        return jaccard_similarity
    
    def _evaluate_constraint_consistency(self, parent_goal: Dict[str, Any], 
                                      sub_goal: Dict[str, Any]) -> float:
        """
        Evaluate if sub-goal maintains parent goal constraints.
        
        Args:
            parent_goal: Parent goal information
            sub_goal: Sub-goal information
            
        Returns:
            Constraint consistency score (0-1)
        """
        # Check for explicit constraints
        parent_constraints = parent_goal.get("constraints", [])
        sub_constraints = sub_goal.get("constraints", [])
        
        if not parent_constraints:
            # No explicit constraints to check
            return 0.9  # Assume high consistency if no constraints specified
        
        # Check if sub-goal inherits or respects parent constraints
        inherited_constraints = 0
        for p_constraint in parent_constraints:
            constraint_type = p_constraint.get("type", "")
            constraint_respected = False
            
            # Check if constraint is explicitly inherited
            for s_constraint in sub_constraints:
                if (s_constraint.get("type") == constraint_type and
                    s_constraint.get("inherited", False)):
                    constraint_respected = True
                    break
            
            # Check if constraint is implicitly respected
            if not constraint_respected and "description" in sub_goal:
                constraint_desc = p_constraint.get("description", "")
                if constraint_desc and constraint_desc.lower() in sub_goal["description"].lower():
                    constraint_respected = True
            
            if constraint_respected:
                inherited_constraints += 1
        
        # Calculate the proportion of constraints respected
        if not parent_constraints:
            return 0.9  # High default if no constraints
        
        return inherited_constraints / len(parent_constraints)
    
    def _evaluate_value_alignment(self, parent_goal: Dict[str, Any], 
                               sub_goal: Dict[str, Any]) -> float:
        """
        Evaluate alignment with core values and principles.
        
        Args:
            parent_goal: Parent goal information
            sub_goal: Sub-goal information
            
        Returns:
            Value alignment score (0-1)
        """
        # Check for explicit values
        parent_values = parent_goal.get("values", [])
        sub_values = sub_goal.get("values", [])
        
        if not parent_values:
            # No explicit values to check
            return 0.8  # Assume good alignment if no values specified
        
        # Check if sub-goal maintains parent values
        maintained_values = 0
        for p_value in parent_values:
            value_maintained = False
            
            # Check if value is explicitly maintained
            for s_value in sub_values:
                if isinstance(p_value, str) and isinstance(s_value, str):
                    if p_value.lower() == s_value.lower():
                        value_maintained = True
                        break
                elif isinstance(p_value, dict) and isinstance(s_value, dict):
                    if (p_value.get("name") == s_value.get("name") or
                        p_value.get("type") == s_value.get("type")):
                        value_maintained = True
                        break
            
            # Check if value is implicitly mentioned
            if not value_maintained and "description" in sub_goal:
                value_name = p_value if isinstance(p_value, str) else p_value.get("name", "")
                if value_name and value_name.lower() in sub_goal["description"].lower():
                    value_maintained = True
            
            if value_maintained:
                maintained_values += 1
        
        # Calculate the proportion of values maintained
        if not parent_values:
            return 0.8  # High default if no values
        
        return maintained_values / len(parent_values)
    
    def _evaluate_path_coherence(self, parent_goal: Dict[str, Any], 
                              sub_goal: Dict[str, Any]) -> float:
        """
        Evaluate logical coherence between goals and sub-goals.
        
        Args:
            parent_goal: Parent goal information
            sub_goal: Sub-goal information
            
        Returns:
            Path coherence score (0-1)
        """
        # Check for goal type consistency
        parent_type = parent_goal.get("type", "achievement")
        sub_type = sub_goal.get("type", "achievement")
        
        # Some goal types are inherently coherent with others
        coherent_types = {
            "achievement": ["achievement", "optimization", "learning"],
            "optimization": ["optimization", "achievement"],
            "learning": ["learning", "exploration", "achievement"],
            "exploration": ["exploration", "learning"],
            "maintenance": ["maintenance", "prevention", "optimization"],
            "prevention": ["prevention", "maintenance"]
        }
        
        type_coherence = 1.0 if sub_type in coherent_types.get(parent_type, []) else 0.5
        
        # Check for step ordering
        parent_steps = parent_goal.get("steps", [])
        step_order = sub_goal.get("order", -1)
        
        if parent_steps and step_order >= 0 and step_order < len(parent_steps):
            # Sub-goal is an explicit step in parent sequence
            step_coherence = 1.0
        elif parent_steps:
            # Check if sub-goal matches a step description
            sub_desc = sub_goal.get("description", "").lower()
            step_match = False
            
            for step in parent_steps:
                if isinstance(step, str) and step.lower() in sub_desc:
                    step_match = True
                    break
                elif isinstance(step, dict) and step.get("description", "").lower() in sub_desc:
                    step_match = True
                    break
            
            step_coherence = 0.8 if step_match else 0.5
        else:
            # No steps to check
            step_coherence = 0.7
        
        # Check for prerequisites and dependencies
        parent_id = parent_goal.get("id", "")
        prerequisites = sub_goal.get("prerequisites", [])
        
        prereq_coherence = 0.0
        if prerequisites:
            # Check if parent is a prerequisite
            for prereq in prerequisites:
                if prereq == parent_id:
                    prereq_coherence = 1.0
                    break
            
            if prereq_coherence == 0.0:
                # Parent not explicitly listed, but other prerequisites exist
                prereq_coherence = 0.6
        else:
            # No prerequisites specified
            prereq_coherence = 0.7
        
        # Combine scores
        return 0.3 * type_coherence + 0.4 * step_coherence + 0.3 * prereq_coherence
    
    def _evaluate_outcome_convergence(self, parent_goal: Dict[str, Any], 
                                   sub_goal: Dict[str, Any],
                                   execution_history: Optional[List[Dict[str, Any]]]) -> float:
        """
        Evaluate likelihood that sub-goal leads to parent goal outcome.
        
        Args:
            parent_goal: Parent goal information
            sub_goal: Sub-goal information
            execution_history: Optional history of goal execution
            
        Returns:
            Outcome convergence score (0-1)
        """
        # Check for explicit outcome metrics
        parent_outcomes = parent_goal.get("desired_outcomes", [])
        sub_contribution = sub_goal.get("contributes_to", [])
        
        if parent_outcomes and sub_contribution:
            # Check direct contribution to outcomes
            contribution_score = 0
            for outcome in parent_outcomes:
                outcome_id = outcome.get("id", outcome) if isinstance(outcome, dict) else outcome
                
                if outcome_id in sub_contribution:
                    contribution_score += 1
            
            outcome_score = contribution_score / len(parent_outcomes) if parent_outcomes else 0
            
            if outcome_score > 0:
                return outcome_score
        
        # If no explicit outcomes or no direct contribution, use execution history if available
        if execution_history:
            # Find parent and sub-goal in execution history
            parent_executions = [h for h in execution_history if h.get("goal_id") == parent_goal.get("id")]
            sub_executions = [h for h in execution_history if h.get("goal_id") == sub_goal.get("id")]
            
            if parent_executions and sub_executions:
                # Check if successful sub-goal executions correlate with parent success
                sub_successes = [e for e in sub_executions if e.get("success", False)]
                parent_successes = [e for e in parent_executions if e.get("success", False)]
                
                if sub_successes and parent_successes:
                    # Calculate correlation using timestamps
                    # (simplified - in reality would be more sophisticated)
                    convergence_probability = min(0.9, len(sub_successes) / len(sub_executions))
                    return convergence_probability
        
        # If no execution history or outcomes, estimate based on goal type and relationship
        parent_type = parent_goal.get("type", "achievement")
        sub_type = sub_goal.get("type", "achievement")
        
        # Matrix of outcome convergence by goal type
        convergence_matrix = {
            "achievement": {
                "achievement": 0.8,
                "optimization": 0.7,
                "learning": 0.6,
                "exploration": 0.5,
                "maintenance": 0.6,
                "prevention": 0.5
            },
            "optimization": {
                "optimization": 0.9,
                "achievement": 0.6,
                "learning": 0.5,
                "exploration": 0.4,
                "maintenance": 0.7,
                "prevention": 0.5
            },
            "learning": {
                "learning": 0.9,
                "exploration": 0.8,
                "achievement": 0.6,
                "optimization": 0.5,
                "maintenance": 0.4,
                "prevention": 0.3
            },
            "exploration": {
                "exploration": 0.9,
                "learning": 0.8,
                "achievement": 0.5,
                "optimization": 0.4,
                "maintenance": 0.3,
                "prevention": 0.3
            },
            "maintenance": {
                "maintenance": 0.9,
                "prevention": 0.8,
                "optimization": 0.7,
                "achievement": 0.6,
                "learning": 0.4,
                "exploration": 0.3
            },
            "prevention": {
                "prevention": 0.9,
                "maintenance": 0.8,
                "optimization": 0.6,
                "achievement": 0.5,
                "learning": 0.3,
                "exploration": 0.3
            }
        }
        
        # Get convergence score from matrix
        if parent_type in convergence_matrix and sub_type in convergence_matrix.get(parent_type, {}):
            return convergence_matrix[parent_type][sub_type]
        
        # Default
        return 0.6
    
    def _calculate_weighted_alignment(self, metric_scores: Dict[str, float]) -> float:
        """
        Calculate weighted alignment score from individual metrics.
        
        Args:
            metric_scores: Dictionary mapping metric names to scores
            
        Returns:
            Weighted alignment score (0-1)
        """
        if not metric_scores:
            return 0.0
            
        total_weight = 0.0
        weighted_sum = 0.0
        
        for metric_name, score in metric_scores.items():
            if metric_name in self.alignment_metrics:
                weight = self.alignment_metrics[metric_name]["weight"]
                total_weight += weight
                weighted_sum += weight * score
        
        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            # If no weights, use simple average
            return sum(metric_scores.values()) / len(metric_scores)
    
    def _calculate_overall_alignment(self, alignment_map: Dict[str, Any]) -> float:
        """
        Calculate overall alignment score for the entire hierarchy.
        
        Args:
            alignment_map: Hierarchical map of alignment scores
            
        Returns:
            Overall alignment score (0-1)
        """
        # Recursive function to calculate alignment
        def calculate_tree_alignment(node, depth=0, decay_factor=0.9):
            # Get node's alignment score
            node_score = node.get("alignment_score", 0.0)
            
            # Get children's scores
            children = node.get("children", [])
            if not children:
                return node_score
            
            # Calculate average child score with depth decay
            child_scores = [calculate_tree_alignment(child, depth + 1, decay_factor) for child in children]
            avg_child_score = sum(child_scores) / len(child_scores) if child_scores else 0
            
            # Apply depth decay to child contribution
            decayed_child_score = avg_child_score * (decay_factor ** depth)
            
            # Combine node score with children scores (weighted by depth)
            if depth == 0:
                # Root node - more weight to children
                return 0.3 * node_score + 0.7 * decayed_child_score
            else:
                # Non-root nodes - more weight to own alignment
                return 0.7 * node_score + 0.3 * decayed_child_score
        
        # Calculate starting from root
        return calculate_tree_alignment(alignment_map["root"])
    
    def _categorize_alignment(self, alignment_score: float) -> str:
        """
        Categorize alignment score according to thresholds.
        
        Args:
            alignment_score: Overall alignment score
            
        Returns:
            Alignment category string
        """
        for category, info in sorted(
            self.alignment_thresholds.items(), 
            key=lambda x: x[1]["threshold"], 
            reverse=True
        ):
            if alignment_score >= info["threshold"]:
                return category
        
        # Default to lowest category
        return "conflicting"
    
    def _detect_drift_patterns(self, alignment_map: Dict[str, Any], 
                            execution_history: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Detect goal drift patterns in the alignment map.
        
        Args:
            alignment_map: Hierarchical map of alignment scores
            execution_history: Optional history of goal execution
            
        Returns:
            List of detected drift patterns
        """
        detected_patterns = []
        
        # Extract low-scoring nodes
        low_scoring_nodes = self._find_low_scoring_nodes(alignment_map["root"])
        
        # Check each drift pattern
        for pattern_name, pattern_info in self.drift_patterns.items():
            # Check if relevant metrics show issues
            relevant_metrics = pattern_info["detection_metrics"]
            
            # Count nodes with low scores in relevant metrics
            affected_nodes = []
            
            for node in low_scoring_nodes:
                node_metrics = node.get("metrics", {})
                
                # Check if this node has low scores in relevant metrics
                metric_issues = 0
                for metric in relevant_metrics:
                    if metric in node_metrics and node_metrics[metric] < self.alignment_metrics[metric]["threshold"]:
                        metric_issues += 1
                
                # If multiple metrics have issues, add to affected nodes
                if metric_issues > 0:
                    affected_nodes.append(node)
            
            # If enough nodes are affected, detect this pattern
            if len(affected_nodes) > 0:
                # Calculate confidence based on number of affected nodes and severity
                confidence = min(0.9, (len(affected_nodes) / max(1, len(low_scoring_nodes))) * 0.8 + 0.1)
                
                detected_patterns.append({
                    "pattern": pattern_name,
                    "description": pattern_info["description"],
                    "confidence": confidence,
                    "risk_level": pattern_info["risk_level"],
                    "affected_nodes": [node["goal_id"] for node in affected_nodes[:5]],  # Limit to 5 nodes
                    "indicators": pattern_info["indicators"]
                })
        
        # Check for temporal drift if execution history available
        if execution_history:
            temporal_drift = self._detect_temporal_drift(execution_history)
            if temporal_drift:
                detected_patterns.append(temporal_drift)
        
        return detected_patterns
    
    def _find_low_scoring_nodes(self, node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find nodes with low alignment scores in the hierarchy.
        
        Args:
            node: Current node in alignment map
            
        Returns:
            List of nodes with low alignment scores
        """
        low_scoring = []
        
        # Check current node
        if node.get("alignment_score", 1.0) < 0.7:  # Threshold for concerning alignment
            low_scoring.append(node)
        
        # Check children recursively
        for child in node.get("children", []):
            low_scoring.extend(self._find_low_scoring_nodes(child))
        
        return low_scoring
    
    def _detect_temporal_drift(self, execution_history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Detect goal drift over time in execution history.
        
        Args:
            execution_history: History of goal execution
            
        Returns:
            Drift pattern if detected, None otherwise
        """
        if len(execution_history) < 3:
            return None  # Not enough history to detect trends
        
        # Sort history by timestamp
        sorted_history = sorted(execution_history, key=lambda x: x.get("timestamp", 0))
        
        # Check for drift in focus (priority changes)
        focus_drift = False
        # This would normally check patterns in which goals get attention over time
        # For demonstration, we'll detect if successful goals change dramatically
        
        early_successes = set()
        late_successes = set()
        
        mid_point = len(sorted_history) // 2
        
        for i, entry in enumerate(sorted_history):
            if entry.get("success", False):
                if i < mid_point:
                    early_successes.add(entry.get("goal_id", ""))
                else:
                    late_successes.add(entry.get("goal_id", ""))
        
        # Calculate Jaccard similarity between early and late successes
        if early_successes or late_successes:
            intersection = len(early_successes.intersection(late_successes))
            union = len(early_successes.union(late_successes))
            
            similarity = intersection / union if union > 0 else 0
            
            # If similarity is low, detect focus drift
            if similarity < 0.3:
                focus_drift = True
        
        if focus_drift:
            return {
                "pattern": "temporal_focus_drift",
                "description": "Significant shift in focus over time",
                "confidence": 0.7,
                "risk_level": "high",
                "affected_nodes": list(early_successes.symmetric_difference(late_successes))[:5],
                "indicators": ["shifting_priorities", "changing_focus", "inconsistent_execution"]
            }
        
        return None
    
    def _generate_alignment_suggestions(self, goal_hierarchy: Dict[str, Any], 
                                      alignment_map: Dict[str, Any],
                                      drift_patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate suggestions to improve goal alignment.
        
        Args:
            goal_hierarchy: Hierarchical structure of goals and sub-goals
            alignment_map: Hierarchical map of alignment scores
            drift_patterns: List of detected drift patterns
            
        Returns:
            List of suggestions to improve alignment
        """
        suggestions = []
        
        # Generate pattern-specific suggestions
        for pattern in drift_patterns:
            pattern_name = pattern["pattern"]
            affected_nodes = pattern.get("affected_nodes", [])
            
            if pattern_name == "scope_creep":
                suggestions.append({
                    "type": "scope_refinement",
                    "description": "Refine and narrow scope of affected sub-goals",
                    "affected_goals": affected_nodes,
                    "priority": "high" if pattern["risk_level"] in ["high", "critical"] else "medium",
                    "actions": [
                        "Define explicit boundaries for each affected goal",
                        "Remove non-essential objectives that have been added",
                        "Realign metrics with original core objectives"
                    ]
                })
            
            elif pattern_name == "means_end_inversion":
                suggestions.append({
                    "type": "goal_realignment",
                    "description": "Reconnect sub-goals to parent goal outcomes",
                    "affected_goals": affected_nodes,
                    "priority": "critical" if pattern["risk_level"] == "critical" else "high",
                    "actions": [
                        "Explicitly link each sub-goal to parent outcomes",
                        "Replace process metrics with outcome metrics",
                        "Add periodic outcome validation checkpoints"
                    ]
                })
            
            elif pattern_name == "value_substitution":
                suggestions.append({
                    "type": "value_restoration",
                    "description": "Restore original values and principles",
                    "affected_goals": affected_nodes,
                    "priority": "critical",
                    "actions": [
                        "Reintroduce original value metrics",
                        "Add value impact analysis to execution steps",
                        "Implement value alignment verification"
                    ]
                })
            
            elif pattern_name == "mission_creep":
                suggestions.append({
                    "type": "mission_refocus",
                    "description": "Refocus on original mission and purpose",
                    "affected_goals": affected_nodes,
                    "priority": "high",
                    "actions": [
                        "Revisit and restate original mission",
                        "Reset priority hierarchy to match original intent",
                        "Archive or deprioritize divergent sub-goals"
                    ]
                })
            
            elif pattern_name == "optimization_drift":
                suggestions.append({
                    "type": "balanced_optimization",
                    "description": "Rebalance optimization across all important dimensions",
                    "affected_goals": affected_nodes,
                    "priority": "medium",
                    "actions": [
                        "Implement balanced scorecard approach",
                        "Add constraints to prevent over-optimization",
                        "Monitor secondary effects of optimization"
                    ]
                })
            
            elif pattern_name == "goal_fragmentation":
                suggestions.append({
                    "type": "coordination_enhancement",
                    "description": "Enhance coordination between disconnected sub-goals",
                    "affected_goals": affected_nodes,
                    "priority": "high",
                    "actions": [
                        "Create explicit dependencies between related sub-goals",
                        "Implement cross-goal coordination mechanisms",
                        "Add integration validation steps"
                    ]
                })
            
            elif pattern_name == "temporal_focus_drift":
                suggestions.append({
                    "type": "consistency_restoration",
                    "description": "Restore consistent focus over time",
                    "affected_goals": affected_nodes,
                    "priority": "high",
                    "actions": [
                        "Review and reset goal priorities",
                        "Implement persistence mechanisms for important goals",
                        "Create time-based alignment checks"
                    ]
                })
        
        # Generate suggestions for specific low-scoring nodes
        low_scoring_nodes = self._find_low_scoring_nodes(alignment_map["root"])
        
        for node in low_scoring_nodes:
            # Skip if already covered by pattern suggestions
            if node["goal_id"] in [g for s in suggestions for g in s.get("affected_goals", [])]:
                continue
                
            # Generate node-specific suggestion
            metrics = node.get("metrics", {})
            
            # Identify the lowest scoring metric
            lowest_metric = min(metrics.items(), key=lambda x: x[1]) if metrics else (None, 1.0)
            
            if lowest_metric[0] and lowest_metric[1] < 0.5:
                metric_name = lowest_metric[0]
                
                if metric_name == "semantic_similarity":
                    suggestions.append({
                        "type": "description_alignment",
                        "description": f"Align description of goal {node['goal_id']} with parent goal",
                        "affected_goals": [node["goal_id"]],
                        "priority": "medium",
                        "actions": [
                            "Revise goal description to use key terms from parent goal",
                            "Explicitly reference parent goal in description",
                            "Add 'contributes_to' relationship to parent goal"
                        ]
                    })
                
                elif metric_name == "objective_consistency":
                    suggestions.append({
                        "type": "constraint_alignment",
                        "description": f"Align constraints of goal {node['goal_id']} with parent goal",
                        "affected_goals": [node["goal_id"]],
                        "priority": "high",
                        "actions": [
                            "Inherit and explicitly reference parent constraints",
                            "Remove any contradicting constraints",
                            "Add validation step for constraint consistency"
                        ]
                    })
                
                elif metric_name == "value_alignment":
                    suggestions.append({
                        "type": "value_alignment",
                        "description": f"Align values of goal {node['goal_id']} with parent goal",
                        "affected_goals": [node["goal_id"]],
                        "priority": "high",
                        "actions": [
                            "Add explicit value references to goal",
                            "Implement value impact assessment",
                            "Review for unintended value consequences"
                        ]
                    })
                
                elif metric_name == "path_coherence":
                    suggestions.append({
                        "type": "structural_alignment",
                        "description": f"Improve structural coherence of goal {node['goal_id']}",
                        "affected_goals": [node["goal_id"]],
                        "priority": "medium",
                        "actions": [
                            "Add explicit prerequisite relationship to parent goal",
                            "Clarify the goal's position in overall sequence",
                            "Add logical connection to related goals"
                        ]
                    })
                
                elif metric_name == "outcome_convergence":
                    suggestions.append({
                        "type": "outcome_alignment",
                        "description": f"Strengthen outcome contribution of goal {node['goal_id']}",
                        "affected_goals": [node["goal_id"]],
                        "priority": "high",
                        "actions": [
                            "Add explicit 'contributes_to' references to parent outcomes",
                            "Define success metrics in terms of parent outcomes",
                            "Add validation step to verify outcome contribution"
                        ]
                    })
        
        return suggestions
    
    def verify_goal_alignment(self, goal: Dict[str, Any], 
                           execution_plan: Dict[str, Any],
                           config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Verify alignment between a goal and its execution plan.
        
        Args:
            goal: Goal specification
            execution_plan: Plan for achieving the goal
            config: Optional configuration for verification
            
        Returns:
            Dictionary with verification results
        """
        # Set default configuration if not provided
        if config is None:
            config = {
                "verification_methods": ["semantic_analysis", "constraint_validation"],
                "min_alignment_threshold": 0.7,
                "detailed_analysis": True
            }
        
        # Validate inputs
        if not goal or not execution_plan:
            return {
                "success": False,
                "error": "Invalid goal or execution plan",
                "verification_result": "failed",
                "alignment_score": 0.0
            }
        
        # Get verification methods to use
        methods_to_use = config.get("verification_methods", list(self.verification_methods.keys()))
        
        # Apply each verification method
        verification_results = {}
        
        for method_name in methods_to_use:
            if method_name not in self.verification_methods:
                continue

            _method_info = self.verification_methods[method_name]  # noqa: F841 - For future use

            # Apply this method if applicable
            if self._is_method_applicable(method_name, goal, execution_plan):
                result = self._apply_verification_method(
                    method_name, goal, execution_plan
                )
                
                verification_results[method_name] = result
        
        # Calculate overall alignment score
        if verification_results:
            overall_score = sum(r["score"] for r in verification_results.values()) / len(verification_results)
        else:
            overall_score = 0.0
        
        # Determine verification result
        min_threshold = config.get("min_alignment_threshold", 0.7)
        
        if overall_score >= min_threshold:
            verification_result = "aligned"
        elif overall_score >= min_threshold * 0.7:
            verification_result = "partially_aligned"
        else:
            verification_result = "misaligned"
        
        # Generate detailed analysis if requested
        detailed_analysis = None
        if config.get("detailed_analysis", True):
            detailed_analysis = self._generate_detailed_analysis(
                goal, execution_plan, verification_results, overall_score
            )
        
        return {
            "success": True,
            "verification_result": verification_result,
            "alignment_score": overall_score,
            "method_results": verification_results,
            "detailed_analysis": detailed_analysis,
            "timestamp": time.time()
        }
    
    def _is_method_applicable(self, method_name: str, 
                           goal: Dict[str, Any], 
                           execution_plan: Dict[str, Any]) -> bool:
        """
        Check if a verification method is applicable.
        
        Args:
            method_name: Name of verification method
            goal: Goal specification
            execution_plan: Plan for achieving the goal
            
        Returns:
            True if method is applicable
        """
        method_info = self.verification_methods[method_name]
        applicability = method_info["applicability"]
        required_data = method_info["required_data"]
        
        # Check applicability
        if applicability == "all_goal_types":
            # Method applies to all goals
            pass
        elif applicability == "constrained_goals" and not goal.get("constraints"):
            # Method requires constraints
            return False
        elif applicability == "achievement_goals" and goal.get("type") != "achievement":
            # Method requires achievement goal
            return False
        elif applicability == "value_sensitive_goals" and not goal.get("values"):
            # Method requires value specifications
            return False
        elif applicability == "complex_goal_structures" and not execution_plan.get("sub_goals"):
            # Method requires complex structure
            return False
        elif applicability == "sequential_goals" and not execution_plan.get("dependencies"):
            # Method requires sequential structure
            return False
        
        # Check required data
        for data_item in required_data:
            if data_item == "goal_descriptions" and not goal.get("description"):
                return False
            elif data_item == "goal_constraints" and not goal.get("constraints"):
                return False
            elif data_item == "sub_goal_specifications" and not execution_plan.get("sub_goals"):
                return False
            elif data_item == "outcome_metrics" and not goal.get("desired_outcomes"):
                return False
            elif data_item == "value_specifications" and not goal.get("values"):
                return False
            elif data_item == "goal_hierarchy" and not execution_plan.get("sub_goals"):
                return False
            elif data_item == "dependency_graph" and not execution_plan.get("dependencies"):
                return False
            elif data_item == "goal_history" and not execution_plan.get("execution_history"):
                return False
        
        return True
    
    def _apply_verification_method(self, method_name: str, 
                                goal: Dict[str, Any], 
                                execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a verification method to check alignment.
        
        Args:
            method_name: Name of verification method
            goal: Goal specification
            execution_plan: Plan for achieving the goal
            
        Returns:
            Dictionary with verification result
        """
        method_info = self.verification_methods[method_name]
        
        # Apply method based on name
        if method_name == "semantic_analysis":
            result = self._apply_semantic_analysis(goal, execution_plan)
        elif method_name == "constraint_validation":
            result = self._apply_constraint_validation(goal, execution_plan)
        elif method_name == "outcome_projection":
            result = self._apply_outcome_projection(goal, execution_plan)
        elif method_name == "value_consistency":
            result = self._apply_value_consistency(goal, execution_plan)
        elif method_name == "graph_theoretic":
            result = self._apply_graph_theoretic(goal, execution_plan)
        elif method_name == "temporal_consistency":
            result = self._apply_temporal_consistency(goal, execution_plan)
        else:
            # Default method - semantic analysis
            result = self._apply_semantic_analysis(goal, execution_plan)
        
        # Add method metadata
        result["method"] = method_name
        result["description"] = method_info["description"]
        result["reliability"] = method_info["reliability"]
        
        return result
    
    def _apply_semantic_analysis(self, goal: Dict[str, Any], 
                              execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply semantic analysis verification method.
        
        Args:
            goal: Goal specification
            execution_plan: Plan for achieving the goal
            
        Returns:
            Dictionary with verification result
        """
        goal_desc = goal.get("description", "")
        
        # Collect all relevant descriptions from the plan
        plan_descriptions = []
        
        # Add plan goal description
        if "goal" in execution_plan and "description" in execution_plan["goal"]:
            plan_descriptions.append(execution_plan["goal"]["description"])
        
        # Add sub-goal descriptions
        for sub_goal in execution_plan.get("sub_goals", []):
            if "goal" in sub_goal and "description" in sub_goal["goal"]:
                plan_descriptions.append(sub_goal["goal"]["description"])
            elif "description" in sub_goal:
                plan_descriptions.append(sub_goal["description"])
        
        # Calculate semantic similarity scores
        similarity_scores = []
        
        for desc in plan_descriptions:
            # Create temporary goal and sub-goal dictionaries
            temp_goal = {"description": goal_desc}
            temp_sub = {"description": desc}
            
            # Use semantic similarity function
            similarity = self._evaluate_semantic_similarity(temp_goal, temp_sub)
            similarity_scores.append(similarity)
        
        # Calculate average similarity
        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0
        
        # Check for key phrases from goal in plan
        key_phrases = goal.get("key_phrases", [])
        if not key_phrases and goal_desc:
            # Extract potential key phrases (in a real implementation, this would use NLP)
            words = goal_desc.split()
            if len(words) > 3:
                key_phrases = [" ".join(words[i:i+2]) for i in range(0, len(words)-1, 2)]
        
        phrase_coverage = 0.0
        if key_phrases:
            phrase_matches = 0
            for phrase in key_phrases:
                for desc in plan_descriptions:
                    if phrase.lower() in desc.lower():
                        phrase_matches += 1
                        break
            
            phrase_coverage = phrase_matches / len(key_phrases) if key_phrases else 0
        
        # Combine scores
        if key_phrases:
            semantic_score = 0.6 * avg_similarity + 0.4 * phrase_coverage
        else:
            semantic_score = avg_similarity
        
        return {
            "score": semantic_score,
            "details": {
                "average_similarity": avg_similarity,
                "phrase_coverage": phrase_coverage,
                "description_count": len(plan_descriptions)
            },
            "timestamp": time.time()
        }
    
    def _apply_constraint_validation(self, goal: Dict[str, Any], 
                                  execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply constraint validation verification method.
        
        Args:
            goal: Goal specification
            execution_plan: Plan for achieving the goal
            
        Returns:
            Dictionary with verification result
        """
        goal_constraints = goal.get("constraints", [])
        
        if not goal_constraints:
            # No constraints to validate
            return {
                "score": 0.9,  # High default for no constraints
                "details": {
                    "constraint_count": 0,
                    "message": "No constraints to validate"
                },
                "timestamp": time.time()
            }
        
        # Extract plan constraints
        plan_constraints = []
        
        # Check main plan
        if "constraints" in execution_plan:
            plan_constraints.extend(execution_plan["constraints"])
        
        # Check in goal
        if "goal" in execution_plan and "constraints" in execution_plan["goal"]:
            plan_constraints.extend(execution_plan["goal"]["constraints"])
        
        # Check sub-goals
        for sub_goal in execution_plan.get("sub_goals", []):
            if "constraints" in sub_goal:
                plan_constraints.extend(sub_goal["constraints"])
            elif "goal" in sub_goal and "constraints" in sub_goal["goal"]:
                plan_constraints.extend(sub_goal["goal"]["constraints"])
        
        # Validate each goal constraint
        constraint_scores = []
        
        for goal_constraint in goal_constraints:
            # Extract constraint details
            if isinstance(goal_constraint, dict):
                constraint_type = goal_constraint.get("type", "")
                constraint_desc = goal_constraint.get("description", "")
                constraint_value = goal_constraint.get("value", goal_constraint.get("limit", None))
            else:
                constraint_type = ""
                constraint_desc = str(goal_constraint)
                constraint_value = None
            
            # Look for matching constraints in plan
            constraint_score = 0.0
            
            for plan_constraint in plan_constraints:
                if isinstance(plan_constraint, dict):
                    plan_type = plan_constraint.get("type", "")
                    plan_desc = plan_constraint.get("description", "")
                    plan_value = plan_constraint.get("value", plan_constraint.get("limit", None))
                    
                    # Check for match
                    type_match = constraint_type and plan_type and constraint_type == plan_type
                    desc_match = constraint_desc and plan_desc and constraint_desc.lower() in plan_desc.lower()
                    value_match = constraint_value and plan_value and constraint_value == plan_value
                    
                    if type_match and (desc_match or value_match):
                        constraint_score = 1.0
                        break
                    elif type_match or desc_match:
                        constraint_score = 0.7
                        break
                else:
                    # Simple string constraint
                    plan_desc = str(plan_constraint)
                    if constraint_desc and constraint_desc.lower() in plan_desc.lower():
                        constraint_score = 0.8
                        break
            
            constraint_scores.append(constraint_score)
        
        # Calculate overall score
        constraint_alignment = sum(constraint_scores) / len(constraint_scores) if constraint_scores else 0
        
        return {
            "score": constraint_alignment,
            "details": {
                "constraint_count": len(goal_constraints),
                "plan_constraint_count": len(plan_constraints),
                "constraint_scores": constraint_scores
            },
            "timestamp": time.time()
        }
    
    def _apply_outcome_projection(self, goal: Dict[str, Any], 
                               execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply outcome projection verification method.
        
        Args:
            goal: Goal specification
            execution_plan: Plan for achieving the goal
            
        Returns:
            Dictionary with verification result
        """
        goal_outcomes = goal.get("desired_outcomes", [])
        
        if not goal_outcomes:
            # Try to infer from description
            if "description" in goal:
                # In a real implementation, this would use NLP to extract outcomes
                # For this demonstration, we'll create a simple outcome
                goal_outcomes = [{"description": f"Achieve: {goal['description']}"}]
        
        if not goal_outcomes:
            # No outcomes to project
            return {
                "score": 0.7,  # Moderate default for no explicit outcomes
                "details": {
                    "outcome_count": 0,
                    "message": "No explicit outcomes to project"
                },
                "timestamp": time.time()
            }
        
        # Extract plan outcomes and results
        plan_outcomes = []
        
        # Check plan metrics
        if "metrics" in execution_plan:
            plan_outcomes.extend([
                {"description": f"Metric: {metric}", "value": value}
                for metric, value in execution_plan["metrics"].items()
            ])
        
        # Check explicit outcomes
        if "expected_outcomes" in execution_plan:
            plan_outcomes.extend(execution_plan["expected_outcomes"])
        
        # Analyze sub-goals for outcome contributions
        for sub_goal in execution_plan.get("sub_goals", []):
            sub_goal_data = sub_goal.get("goal", sub_goal)
            
            if "contributes_to" in sub_goal_data:
                contributions = sub_goal_data["contributes_to"]
                if isinstance(contributions, list):
                    for contrib in contributions:
                        plan_outcomes.append({
                            "description": f"Contribution to: {contrib}",
                            "source": sub_goal_data.get("id", "unknown")
                        })
        
        # Project outcomes
        outcome_scores = []
        
        for goal_outcome in goal_outcomes:
            outcome_desc = ""
            
            if isinstance(goal_outcome, dict):
                outcome_desc = goal_outcome.get("description", "")
                outcome_id = goal_outcome.get("id", "")
            else:
                outcome_desc = str(goal_outcome)
                outcome_id = ""
            
            # Look for matches in plan outcomes
            outcome_score = 0.0
            
            for plan_outcome in plan_outcomes:
                if isinstance(plan_outcome, dict):
                    plan_desc = plan_outcome.get("description", "")
                    plan_id = plan_outcome.get("id", "")
                    
                    # Check for match
                    if outcome_id and plan_id and outcome_id == plan_id:
                        outcome_score = 1.0
                        break
                    elif outcome_desc and plan_desc and outcome_desc.lower() in plan_desc.lower():
                        outcome_score = 0.8
                        break
                    elif outcome_id and plan_desc and outcome_id in plan_desc:
                        outcome_score = 0.7
                        break
                else:
                    # Simple string outcome
                    plan_desc = str(plan_outcome)
                    if outcome_desc.lower() in plan_desc.lower():
                        outcome_score = 0.8
                        break
            
            # If no explicit match, check sub-goal descriptions
            if outcome_score == 0.0:
                for sub_goal in execution_plan.get("sub_goals", []):
                    sub_goal_data = sub_goal.get("goal", sub_goal)
                    
                    if "description" in sub_goal_data:
                        sub_desc = sub_goal_data["description"]
                        
                        if outcome_desc.lower() in sub_desc.lower():
                            outcome_score = 0.6
                            break
            
            outcome_scores.append(outcome_score)
        
        # Calculate overall score
        outcome_alignment = sum(outcome_scores) / len(outcome_scores) if outcome_scores else 0
        
        return {
            "score": outcome_alignment,
            "details": {
                "outcome_count": len(goal_outcomes),
                "plan_outcome_count": len(plan_outcomes),
                "outcome_scores": outcome_scores
            },
            "timestamp": time.time()
        }
    
    def _apply_value_consistency(self, goal: Dict[str, Any], 
                              execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply value consistency verification method.
        
        Args:
            goal: Goal specification
            execution_plan: Plan for achieving the goal
            
        Returns:
            Dictionary with verification result
        """
        goal_values = goal.get("values", [])
        
        if not goal_values:
            # No values to check
            return {
                "score": 0.8,  # Good default for no values
                "details": {
                    "value_count": 0,
                    "message": "No values to validate"
                },
                "timestamp": time.time()
            }
        
        # Extract plan values
        plan_values = []
        
        # Check main plan
        if "values" in execution_plan:
            plan_values.extend(execution_plan["values"])
        
        # Check in goal
        if "goal" in execution_plan and "values" in execution_plan["goal"]:
            plan_values.extend(execution_plan["goal"]["values"])
        
        # Check sub-goals
        for sub_goal in execution_plan.get("sub_goals", []):
            if "values" in sub_goal:
                plan_values.extend(sub_goal["values"])
            elif "goal" in sub_goal and "values" in sub_goal["goal"]:
                plan_values.extend(sub_goal["goal"]["values"])
        
        # Also check for value mentions in descriptions
        value_mentions = []
        
        # Check main plan
        if "goal" in execution_plan and "description" in execution_plan["goal"]:
            value_mentions.append(execution_plan["goal"]["description"])
        
        # Check sub-goals
        for sub_goal in execution_plan.get("sub_goals", []):
            if "goal" in sub_goal and "description" in sub_goal["goal"]:
                value_mentions.append(sub_goal["goal"]["description"])
        
        # Check value consistency
        value_scores = []
        
        for goal_value in goal_values:
            value_name = ""
            value_type = ""
            
            if isinstance(goal_value, dict):
                value_name = goal_value.get("name", "")
                value_type = goal_value.get("type", "")
            else:
                value_name = str(goal_value)
            
            # Look for matches in plan values
            value_score = 0.0
            
            for plan_value in plan_values:
                if isinstance(plan_value, dict):
                    plan_name = plan_value.get("name", "")
                    plan_type = plan_value.get("type", "")
                    
                    # Check for match
                    if value_name and plan_name and value_name.lower() == plan_name.lower():
                        value_score = 1.0
                        break
                    elif value_type and plan_type and value_type.lower() == plan_type.lower():
                        value_score = 0.7
                        break
                else:
                    # Simple string value
                    plan_name = str(plan_value)
                    if value_name.lower() == plan_name.lower():
                        value_score = 1.0
                        break
            
            # If no explicit match, check descriptions
            if value_score == 0.0:
                for mention in value_mentions:
                    if value_name.lower() in mention.lower():
                        value_score = 0.6
                        break
            
            value_scores.append(value_score)
        
        # Calculate overall score
        value_alignment = sum(value_scores) / len(value_scores) if value_scores else 0
        
        return {
            "score": value_alignment,
            "details": {
                "value_count": len(goal_values),
                "plan_value_count": len(plan_values),
                "value_scores": value_scores
            },
            "timestamp": time.time()
        }
    
    def _apply_graph_theoretic(self, goal: Dict[str, Any], 
                            execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply graph theoretic verification method.
        
        Args:
            goal: Goal specification
            execution_plan: Plan for achieving the goal
            
        Returns:
            Dictionary with verification result
        """
        # Extract dependencies from plan
        dependencies = execution_plan.get("dependencies", [])
        
        if not dependencies:
            # No dependencies to analyze
            return {
                "score": 0.7,  # Moderate default for no dependencies
                "details": {
                    "dependency_count": 0,
                    "message": "No dependencies to analyze"
                },
                "timestamp": time.time()
            }
        
        # Extract sub-goals
        sub_goals = execution_plan.get("sub_goals", [])
        
        if not sub_goals:
            # No sub-goals to analyze
            return {
                "score": 0.7,  # Moderate default for no sub-goals
                "details": {
                    "sub_goal_count": 0,
                    "message": "No sub-goals to analyze"
                },
                "timestamp": time.time()
            }
        
        # Build dependency graph
        graph = {}
        
        for sub_goal in sub_goals:
            sub_goal_id = sub_goal.get("id", "")
            graph[sub_goal_id] = {"in": [], "out": []}
        
        for dep in dependencies:
            source = dep.get("source", "")
            target = dep.get("target", "")
            dep_type = dep.get("type", "")
            
            if source in graph and target in graph:
                graph[source]["out"].append({"target": target, "type": dep_type})
                graph[target]["in"].append({"source": source, "type": dep_type})
        
        # Check graph properties
        connectedness = self._check_graph_connectedness(graph)
        acyclicity = self._check_graph_acyclicity(graph)
        completeness = self._check_graph_completeness(graph, sub_goals)
        
        # Combine scores
        graph_alignment = 0.4 * connectedness + 0.3 * acyclicity + 0.3 * completeness
        
        return {
            "score": graph_alignment,
            "details": {
                "connectedness": connectedness,
                "acyclicity": acyclicity,
                "completeness": completeness,
                "node_count": len(graph),
                "edge_count": len(dependencies)
            },
            "timestamp": time.time()
        }
    
    def _check_graph_connectedness(self, graph: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> float:
        """
        Check if the dependency graph is connected.
        
        Args:
            graph: Dependency graph
            
        Returns:
            Connectedness score (0-1)
        """
        if not graph:
            return 0.0
            
        # Find sources (nodes with no incoming edges)
        sources = [node for node, data in graph.items() if not data["in"]]
        
        if not sources:
            # No sources - cyclic graph
            return 0.5
        
        # Perform BFS from each source
        reachable = set()
        
        for source in sources:
            queue = [source]
            visited = set(queue)
            
            while queue:
                node = queue.pop(0)
                reachable.add(node)
                
                for edge in graph[node]["out"]:
                    target = edge["target"]
                    if target not in visited:
                        visited.add(target)
                        queue.append(target)
        
        # Calculate connectedness
        connectedness = len(reachable) / len(graph)
        
        return connectedness
    
    def _check_graph_acyclicity(self, graph: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> float:
        """
        Check if the dependency graph is acyclic.
        
        Args:
            graph: Dependency graph
            
        Returns:
            Acyclicity score (0-1)
        """
        if not graph:
            return 1.0  # Empty graph is acyclic
            
        # Check for cycles using DFS
        visited = set()
        temp = set()
        
        def has_cycle(node):
            if node in temp:
                return True
                
            if node in visited:
                return False
                
            temp.add(node)
            
            for edge in graph[node]["out"]:
                if has_cycle(edge["target"]):
                    return True
                    
            temp.remove(node)
            visited.add(node)
            return False
        
        # Check each node
        cycle_count = 0
        
        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    cycle_count += 1
        
        # Calculate acyclicity
        if cycle_count == 0:
            return 1.0
        else:
            return max(0.0, 1.0 - (cycle_count / len(graph)))
    
    def _check_graph_completeness(self, graph: Dict[str, Dict[str, List[Dict[str, Any]]]],
                               sub_goals: List[Dict[str, Any]]) -> float:
        """
        Check if the dependency graph completely represents all sub-goals.
        
        Args:
            graph: Dependency graph
            sub_goals: List of sub-goals
            
        Returns:
            Completeness score (0-1)
        """
        if not graph or not sub_goals:
            return 0.0
            
        # Count nodes with no connections
        isolated_count = 0
        
        for node, data in graph.items():
            if not data["in"] and not data["out"]:
                isolated_count += 1
        
        # Calculate completeness
        completeness = 1.0 - (isolated_count / len(graph))
        
        return completeness
    
    def _apply_temporal_consistency(self, goal: Dict[str, Any], 
                                 execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply temporal consistency verification method.
        
        Args:
            goal: Goal specification
            execution_plan: Plan for achieving the goal
            
        Returns:
            Dictionary with verification result
        """
        # Check for execution history
        execution_history = execution_plan.get("execution_history", [])
        
        if not execution_history:
            # No history to analyze
            return {
                "score": 0.8,  # Good default for no history
                "details": {
                    "history_count": 0,
                    "message": "No execution history to analyze"
                },
                "timestamp": time.time()
            }
        
        # Sort history by timestamp
        sorted_history = sorted(execution_history, key=lambda x: x.get("timestamp", 0))
        
        # Check for consistency over time
        goal_id = goal.get("id", "")
        
        # Check success rate
        success_count = sum(1 for entry in sorted_history if entry.get("success", False))
        success_rate = success_count / len(sorted_history) if sorted_history else 0
        
        # Check for focus on relevant goals
        relevant_count = sum(1 for entry in sorted_history if entry.get("goal_id") == goal_id or
                            entry.get("parent_goal_id") == goal_id)
        focus_ratio = relevant_count / len(sorted_history) if sorted_history else 0
        
        # Check for progress over time
        progress_trend = 0.0
        
        if len(sorted_history) > 1:
            # Calculate progress difference from start to end
            start_progress = sorted_history[0].get("progress", 0.0)
            end_progress = sorted_history[-1].get("progress", 0.0)
            
            progress_trend = end_progress - start_progress
        
        # Combine scores
        temporal_score = 0.4 * success_rate + 0.3 * focus_ratio + 0.3 * min(1.0, progress_trend)
        
        return {
            "score": temporal_score,
            "details": {
                "success_rate": success_rate,
                "focus_ratio": focus_ratio,
                "progress_trend": progress_trend,
                "history_count": len(sorted_history)
            },
            "timestamp": time.time()
        }
    
    def _generate_detailed_analysis(self, goal: Dict[str, Any], 
                                 execution_plan: Dict[str, Any],
                                 verification_results: Dict[str, Dict[str, Any]],
                                 overall_score: float) -> Dict[str, Any]:
        """
        Generate detailed analysis of verification results.
        
        Args:
            goal: Goal specification
            execution_plan: Plan for achieving the goal
            verification_results: Results from verification methods
            overall_score: Overall alignment score
            
        Returns:
            Dictionary with detailed analysis
        """
        # Extract goal information (for future detailed analysis)
        _goal_type = goal.get("type", "achievement")  # noqa: F841
        _goal_desc = goal.get("description", "")  # noqa: F841
        
        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        
        for method, result in verification_results.items():
            score = result.get("score", 0.0)
            
            if score >= 0.8:
                # High score - strength
                strengths.append({
                    "aspect": method,
                    "score": score,
                    "description": f"Strong {method.replace('_', ' ')} alignment"
                })
            elif score <= 0.5:
                # Low score - weakness
                weaknesses.append({
                    "aspect": method,
                    "score": score,
                    "description": f"Weak {method.replace('_', ' ')} alignment"
                })
        
        # Generate improvement suggestions
        suggestions = []
        
        for weakness in weaknesses:
            aspect = weakness["aspect"]
            
            if aspect == "semantic_analysis":
                suggestions.append({
                    "focus": "description_alignment",
                    "action": "Revise plan descriptions to better match goal terminology and intent"
                })
            elif aspect == "constraint_validation":
                suggestions.append({
                    "focus": "constraint_preservation",
                    "action": "Explicitly include goal constraints in plan and sub-goals"
                })
            elif aspect == "outcome_projection":
                suggestions.append({
                    "focus": "outcome_linkage",
                    "action": "Clearly link sub-goals to goal outcomes and metrics"
                })
            elif aspect == "value_consistency":
                suggestions.append({
                    "focus": "value_integration",
                    "action": "Incorporate goal values into plan execution steps"
                })
            elif aspect == "graph_theoretic":
                suggestions.append({
                    "focus": "dependency_structure",
                    "action": "Improve sub-goal dependency structure for better coherence"
                })
            elif aspect == "temporal_consistency":
                suggestions.append({
                    "focus": "execution_consistency",
                    "action": "Maintain consistent focus on goal throughout execution"
                })
        
        # Categorize alignment
        if overall_score >= 0.9:
            alignment_category = "excellent"
            alignment_description = "The plan shows excellent alignment with the goal"
        elif overall_score >= 0.8:
            alignment_category = "good"
            alignment_description = "The plan shows good alignment with the goal, with minor improvements possible"
        elif overall_score >= 0.7:
            alignment_category = "acceptable"
            alignment_description = "The plan is acceptably aligned with the goal, but has areas for improvement"
        elif overall_score >= 0.5:
            alignment_category = "concerning"
            alignment_description = "The plan shows concerning alignment issues that should be addressed"
        else:
            alignment_category = "poor"
            alignment_description = "The plan is poorly aligned with the goal and needs significant revision"
        
        return {
            "alignment_category": alignment_category,
            "alignment_description": alignment_description,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improvement_suggestions": suggestions
        }


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Goal Alignment Monitor (KA-57) on the provided data.
    
    Args:
        data: A dictionary containing goal hierarchy or verification data
        
    Returns:
        Dictionary with monitoring or verification results
    """
    mode = data.get("mode", "monitor")  # "monitor" or "verify"
    
    if mode == "monitor":
        goal_hierarchy = data.get("goal_hierarchy", {})
        execution_history = data.get("execution_history")
        config = data.get("config")
        
        # Generate sample data if requested
        if not goal_hierarchy and data.get("generate_sample", False):
            goal_hierarchy, execution_history = generate_sample_goal_hierarchy(
                data.get("complexity", "medium")
            )
        
        # Validate inputs
        if not goal_hierarchy:
            return {
                "algorithm": "KA-57",
                "success": False,
                "error": "No goal hierarchy provided for monitoring",
                "timestamp": time.time()
            }
        
        monitor = GoalAlignmentMonitor()
        
        try:
            result = monitor.monitor_goal_alignment(goal_hierarchy, execution_history, config)
            
            if not result.get("success", False):
                return {
                    "algorithm": "KA-57",
                    "success": False,
                    "error": result.get("error", "Unknown monitoring error"),
                    "timestamp": time.time()
                }
            
            return {
                "algorithm": "KA-57",
                "success": True,
                "alignment_score": result["alignment_score"],
                "alignment_category": result["alignment_category"],
                "detected_drift": result["detected_drift"],
                "suggestions": result["suggestions"],
                "timestamp": time.time()
            }
        
        except Exception as e:
            logger.error(f"Error in KA-57 Goal Alignment Monitor: {str(e)}")
            return {
                "algorithm": "KA-57",
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }
    
    elif mode == "verify":
        goal = data.get("goal", {})
        execution_plan = data.get("execution_plan", {})
        config = data.get("config")
        
        # Generate sample data if requested
        if (not goal or not execution_plan) and data.get("generate_sample", False):
            goal, execution_plan = generate_sample_verification_data(
                data.get("alignment_quality", "good")
            )
        
        # Validate inputs
        if not goal or not execution_plan:
            return {
                "algorithm": "KA-57",
                "success": False,
                "error": "Invalid goal or execution plan for verification",
                "timestamp": time.time()
            }
        
        monitor = GoalAlignmentMonitor()
        
        try:
            result = monitor.verify_goal_alignment(goal, execution_plan, config)
            
            if not result.get("success", False):
                return {
                    "algorithm": "KA-57",
                    "success": False,
                    "error": result.get("error", "Unknown verification error"),
                    "timestamp": time.time()
                }
            
            return {
                "algorithm": "KA-57",
                "success": True,
                "verification_result": result["verification_result"],
                "alignment_score": result["alignment_score"],
                "detailed_analysis": result.get("detailed_analysis"),
                "timestamp": time.time()
            }
        
        except Exception as e:
            logger.error(f"Error in KA-57 Goal Alignment Monitor: {str(e)}")
            return {
                "algorithm": "KA-57",
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }
    
    else:
        return {
            "algorithm": "KA-57",
            "success": False,
            "error": f"Invalid mode: {mode}",
            "timestamp": time.time()
        }


def generate_sample_goal_hierarchy(complexity: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Generate a sample goal hierarchy for testing.
    
    Args:
        complexity: Complexity level (simple, medium, complex)
        
    Returns:
        Tuple of (goal_hierarchy, execution_history)
    """
    # Create root goal
    if complexity == "simple":
        root_goal = {
            "id": "goal_1",
            "type": "achievement",
            "description": "Create a data visualization dashboard",
            "constraints": [
                {"type": "time", "description": "Complete within 2 weeks"}
            ],
            "values": ["accuracy", "usability"]
        }
        
        # Create sub-goals
        sub_goals = [
            {
                "id": "sub_1",
                "type": "achievement",
                "description": "Set up the dashboard framework",
                "parent_goal_id": "goal_1",
                "order": 0
            },
            {
                "id": "sub_2",
                "type": "achievement",
                "description": "Implement data visualization components",
                "parent_goal_id": "goal_1",
                "order": 1
            },
            {
                "id": "sub_3",
                "type": "achievement",
                "description": "Connect to data sources",
                "parent_goal_id": "goal_1",
                "order": 2
            }
        ]
        
        # No sub-sub-goals for simple case
        
    elif complexity == "complex":
        root_goal = {
            "id": "goal_1",
            "type": "achievement",
            "description": "Develop an enterprise-grade data analytics platform",
            "constraints": [
                {"type": "time", "description": "Complete within 6 months"},
                {"type": "resource", "description": "Stay within budget of $500,000"},
                {"type": "quality", "description": "99.9% uptime guarantee"}
            ],
            "values": [
                {"name": "security", "priority": "critical"},
                {"name": "scalability", "priority": "high"},
                {"name": "user_experience", "priority": "high"}
            ],
            "key_phrases": ["analytics platform", "enterprise-grade", "data"],
            "desired_outcomes": [
                {"id": "outcome_1", "description": "Increased decision-making speed by 50%"},
                {"id": "outcome_2", "description": "Reduced data processing costs by 30%"}
            ]
        }
        
        # Create main sub-goals
        sub_goals = [
            {
                "id": "sub_1",
                "type": "achievement",
                "description": "Design system architecture",
                "parent_goal_id": "goal_1",
                "order": 0,
                "constraints": [
                    {"type": "quality", "description": "Follow best practices for scalability"}
                ],
                "values": ["security", "scalability"],
                "sub_goals": [
                    {
                        "id": "sub_1_1",
                        "type": "achievement",
                        "description": "Define technical requirements",
                        "parent_goal_id": "sub_1",
                        "order": 0
                    },
                    {
                        "id": "sub_1_2",
                        "type": "achievement",
                        "description": "Create architecture diagrams",
                        "parent_goal_id": "sub_1",
                        "order": 1
                    },
                    {
                        "id": "sub_1_3",
                        "type": "achievement",
                        "description": "Perform security analysis",
                        "parent_goal_id": "sub_1",
                        "order": 2,
                        "values": ["security"]
                    }
                ]
            },
            {
                "id": "sub_2",
                "type": "achievement",
                "description": "Implement backend services",
                "parent_goal_id": "goal_1",
                "order": 1,
                "constraints": [
                    {"type": "quality", "description": "99.9% uptime guarantee", "inherited": True},
                    {"type": "performance", "description": "Process 1000 requests per second"}
                ],
                "values": ["security", "scalability"],
                "sub_goals": [
                    {
                        "id": "sub_2_1",
                        "type": "achievement",
                        "description": "Build authentication system",
                        "parent_goal_id": "sub_2",
                        "order": 0,
                        "values": ["security"]
                    },
                    {
                        "id": "sub_2_2",
                        "type": "achievement",
                        "description": "Develop data processing pipeline",
                        "parent_goal_id": "sub_2",
                        "order": 1,
                        "values": ["scalability"]
                    },
                    {
                        "id": "sub_2_3",
                        "type": "achievement",
                        "description": "Create database optimization engine",
                        "parent_goal_id": "sub_2",
                        "order": 2,
                        "contributes_to": ["outcome_2"]
                    }
                ]
            },
            {
                "id": "sub_3",
                "type": "achievement",
                "description": "Create user interface",
                "parent_goal_id": "goal_1",
                "order": 2,
                "values": ["user_experience"],
                "sub_goals": [
                    {
                        "id": "sub_3_1",
                        "type": "achievement",
                        "description": "Design UI components",
                        "parent_goal_id": "sub_3",
                        "order": 0
                    },
                    {
                        "id": "sub_3_2",
                        "type": "achievement",
                        "description": "Implement dashboard",
                        "parent_goal_id": "sub_3",
                        "order": 1
                    },
                    {
                        "id": "sub_3_3",
                        "type": "optimization",
                        "description": "Optimize UI performance",
                        "parent_goal_id": "sub_3",
                        "order": 2
                    }
                ]
            },
            {
                "id": "sub_4",
                "type": "optimization",
                "description": "Optimize system performance",
                "parent_goal_id": "goal_1",
                "order": 3,
                "contributes_to": ["outcome_1", "outcome_2"],
                "sub_goals": [
                    {
                        "id": "sub_4_1",
                        "type": "optimization",
                        "description": "Benchmark current performance",
                        "parent_goal_id": "sub_4",
                        "order": 0
                    },
                    {
                        "id": "sub_4_2",
                        "type": "optimization",
                        "description": "Identify and resolve bottlenecks",
                        "parent_goal_id": "sub_4",
                        "order": 1
                    }
                ]
            },
            {
                "id": "sub_5",
                "type": "exploration",
                "description": "Research enterprise AI applications",
                "parent_goal_id": "goal_1",
                "order": 4,
                "sub_goals": [
                    {
                        "id": "sub_5_1",
                        "type": "exploration",
                        "description": "Evaluate machine learning frameworks",
                        "parent_goal_id": "sub_5",
                        "order": 0
                    },
                    {
                        "id": "sub_5_2",
                        "type": "maintenance",
                        "description": "Ensure AI model quality",
                        "parent_goal_id": "sub_5",
                        "order": 1
                    }
                ]
            }
        ]
    
    else:  # medium complexity
        root_goal = {
            "id": "goal_1",
            "type": "achievement",
            "description": "Build a data analytics application",
            "constraints": [
                {"type": "time", "description": "Complete within 1 month"},
                {"type": "resource", "description": "Stay within budget"}
            ],
            "values": ["accuracy", "usability", "performance"],
            "desired_outcomes": [
                {"description": "Improved decision making"}
            ]
        }
        
        # Create sub-goals
        sub_goals = [
            {
                "id": "sub_1",
                "type": "achievement",
                "description": "Design application architecture",
                "parent_goal_id": "goal_1",
                "order": 0,
                "sub_goals": [
                    {
                        "id": "sub_1_1",
                        "type": "achievement",
                        "description": "Define technical requirements",
                        "parent_goal_id": "sub_1",
                        "order": 0
                    },
                    {
                        "id": "sub_1_2",
                        "type": "achievement",
                        "description": "Create system diagrams",
                        "parent_goal_id": "sub_1",
                        "order": 1
                    }
                ]
            },
            {
                "id": "sub_2",
                "type": "achievement",
                "description": "Implement backend functionality",
                "parent_goal_id": "goal_1",
                "order": 1,
                "constraints": [
                    {"type": "performance", "description": "Fast response times"}
                ],
                "values": ["performance"],
                "sub_goals": [
                    {
                        "id": "sub_2_1",
                        "type": "achievement",
                        "description": "Create data models",
                        "parent_goal_id": "sub_2",
                        "order": 0
                    },
                    {
                        "id": "sub_2_2",
                        "type": "achievement",
                        "description": "Build data processing system",
                        "parent_goal_id": "sub_2",
                        "order": 1
                    }
                ]
            },
            {
                "id": "sub_3",
                "type": "achievement",
                "description": "Develop user interface",
                "parent_goal_id": "goal_1",
                "order": 2,
                "values": ["usability"],
                "sub_goals": [
                    {
                        "id": "sub_3_1",
                        "type": "achievement",
                        "description": "Design UI mockups",
                        "parent_goal_id": "sub_3",
                        "order": 0
                    },
                    {
                        "id": "sub_3_2",
                        "type": "achievement",
                        "description": "Implement UI components",
                        "parent_goal_id": "sub_3",
                        "order": 1
                    }
                ]
            },
            {
                "id": "sub_4",
                "type": "optimization",
                "description": "Test and optimize",
                "parent_goal_id": "goal_1",
                "order": 3,
                "sub_goals": [
                    {
                        "id": "sub_4_1",
                        "type": "achievement",
                        "description": "Perform system testing",
                        "parent_goal_id": "sub_4",
                        "order": 0
                    },
                    {
                        "id": "sub_4_2",
                        "type": "optimization",
                        "description": "Optimize performance",
                        "parent_goal_id": "sub_4",
                        "order": 1,
                        "values": ["performance"]
                    }
                ]
            }
        ]
    
    # Create goal hierarchy
    goal_hierarchy = {
        "root_goal": root_goal,
        "sub_goals": sub_goals
    }
    
    # Generate simulated execution history
    execution_history = []
    
    if complexity != "simple":
        # Add some execution entries
        execution_history = [
            {
                "goal_id": "sub_1",
                "timestamp": time.time() - 3600 * 24 * 10,  # 10 days ago
                "success": True,
                "progress": 1.0
            },
            {
                "goal_id": "sub_1_1",
                "timestamp": time.time() - 3600 * 24 * 12,  # 12 days ago
                "success": True,
                "progress": 1.0
            },
            {
                "goal_id": "sub_1_2",
                "timestamp": time.time() - 3600 * 24 * 11,  # 11 days ago
                "success": True,
                "progress": 1.0
            },
            {
                "goal_id": "sub_2",
                "timestamp": time.time() - 3600 * 24 * 5,  # 5 days ago
                "success": True,
                "progress": 1.0
            },
            {
                "goal_id": "sub_2_1",
                "timestamp": time.time() - 3600 * 24 * 7,  # 7 days ago
                "success": True,
                "progress": 1.0
            },
            {
                "goal_id": "sub_2_2",
                "timestamp": time.time() - 3600 * 24 * 6,  # 6 days ago
                "success": True,
                "progress": 1.0
            },
            {
                "goal_id": "sub_3",
                "timestamp": time.time() - 3600 * 24 * 2,  # 2 days ago
                "success": False,
                "progress": 0.6
            },
            {
                "goal_id": "sub_3_1",
                "timestamp": time.time() - 3600 * 24 * 3,  # 3 days ago
                "success": True,
                "progress": 1.0
            },
            {
                "goal_id": "sub_3_2",
                "timestamp": time.time() - 3600 * 24 * 2,  # 2 days ago
                "success": False,
                "progress": 0.4
            }
        ]
        
        # Add some drift if complex
        if complexity == "complex":
            # Add some goal drift entries
            execution_history.extend([
                {
                    "goal_id": "sub_5_3",  # Not in original plan - scope expansion
                    "timestamp": time.time() - 3600 * 24 * 1,  # 1 day ago
                    "success": True,
                    "progress": 1.0,
                    "description": "Investigate machine learning marketplace opportunities"  # Mission creep
                },
                {
                    "goal_id": "sub_2_4",  # Not in original plan
                    "timestamp": time.time() - 3600 * 24 * 4,  # 4 days ago
                    "success": True,
                    "progress": 1.0,
                    "description": "Optimize code aesthetics"  # Value substitution
                }
            ])
    
    return goal_hierarchy, execution_history


def generate_sample_verification_data(alignment_quality: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generate sample data for verification testing.
    
    Args:
        alignment_quality: Quality of alignment (good, medium, poor)
        
    Returns:
        Tuple of (goal, execution_plan)
    """
    # Create goal
    goal = {
        "id": "goal_1",
        "type": "achievement",
        "description": "Build a data analytics dashboard",
        "constraints": [
            {"type": "time", "description": "Complete within 3 weeks"},
            {"type": "resource", "description": "Use only approved libraries"}
        ],
        "values": ["accuracy", "usability", "performance"],
        "desired_outcomes": [
            {"id": "outcome_1", "description": "Faster data-driven decisions"},
            {"id": "outcome_2", "description": "Improved visibility into key metrics"}
        ]
    }
    
    # Create execution plan with different alignment levels
    if alignment_quality == "good":
        # Well-aligned plan
        execution_plan = {
            "id": "plan_1",
            "goal": {
                "id": "goal_1",
                "description": "Build a data analytics dashboard for faster decision-making",
                "constraints": [
                    {"type": "time", "description": "Complete within 3 weeks", "inherited": True},
                    {"type": "resource", "description": "Use only approved libraries", "inherited": True}
                ],
                "values": ["accuracy", "usability", "performance"]
            },
            "sub_goals": [
                {
                    "id": "sub_1",
                    "goal": {
                        "description": "Design dashboard layout and components",
                        "values": ["usability"],
                        "contributes_to": ["outcome_2"]
                    }
                },
                {
                    "id": "sub_2",
                    "goal": {
                        "description": "Implement data processing backend",
                        "values": ["accuracy", "performance"],
                        "contributes_to": ["outcome_1"]
                    }
                },
                {
                    "id": "sub_3",
                    "goal": {
                        "description": "Create interactive visualizations",
                        "values": ["usability"],
                        "contributes_to": ["outcome_2"]
                    }
                },
                {
                    "id": "sub_4",
                    "goal": {
                        "description": "Optimize dashboard performance",
                        "values": ["performance"],
                        "contributes_to": ["outcome_1"]
                    }
                }
            ],
            "dependencies": [
                {
                    "source": "sub_1",
                    "target": "sub_3",
                    "type": "prerequisite"
                },
                {
                    "source": "sub_2",
                    "target": "sub_3",
                    "type": "prerequisite"
                },
                {
                    "source": "sub_3",
                    "target": "sub_4",
                    "type": "prerequisite"
                }
            ]
        }
    
    elif alignment_quality == "poor":
        # Poorly aligned plan
        execution_plan = {
            "id": "plan_1",
            "goal": {
                "id": "goal_1",
                "description": "Create a visualization system",
                "constraints": [
                    {"type": "time", "description": "Complete by end of quarter"}
                ]
            },
            "sub_goals": [
                {
                    "id": "sub_1",
                    "goal": {
                        "description": "Research visualization libraries"
                    }
                },
                {
                    "id": "sub_2",
                    "goal": {
                        "description": "Set up development environment",
                        "values": ["developer_productivity"]
                    }
                },
                {
                    "id": "sub_3",
                    "goal": {
                        "description": "Implement basic charts"
                    }
                },
                {
                    "id": "sub_4",
                    "goal": {
                        "description": "Document code",
                        "values": ["maintainability"]
                    }
                },
                {
                    "id": "sub_5",
                    "goal": {
                        "description": "Explore machine learning integration possibilities",
                        "values": ["innovation"]
                    }
                }
            ],
            "dependencies": [
                {
                    "source": "sub_1",
                    "target": "sub_3",
                    "type": "prerequisite"
                },
                {
                    "source": "sub_2",
                    "target": "sub_3",
                    "type": "prerequisite"
                }
            ]
        }
    
    else:  # medium alignment
        # Moderately aligned plan
        execution_plan = {
            "id": "plan_1",
            "goal": {
                "id": "goal_1",
                "description": "Build a data visualization dashboard",
                "constraints": [
                    {"type": "time", "description": "Complete within 1 month"}
                ],
                "values": ["usability", "performance"]
            },
            "sub_goals": [
                {
                    "id": "sub_1",
                    "goal": {
                        "description": "Design dashboard UI",
                        "values": ["usability"]
                    }
                },
                {
                    "id": "sub_2",
                    "goal": {
                        "description": "Implement data connectors",
                        "values": ["accuracy"]
                    }
                },
                {
                    "id": "sub_3",
                    "goal": {
                        "description": "Create visualization components"
                    }
                },
                {
                    "id": "sub_4",
                    "goal": {
                        "description": "Test dashboard with users",
                        "values": ["usability"],
                        "contributes_to": ["outcome_2"]
                    }
                },
                {
                    "id": "sub_5",
                    "goal": {
                        "description": "Implement user feedback system",
                        "values": ["user_satisfaction"]
                    }
                }
            ],
            "dependencies": [
                {
                    "source": "sub_1",
                    "target": "sub_3",
                    "type": "prerequisite"
                },
                {
                    "source": "sub_2",
                    "target": "sub_3",
                    "type": "prerequisite"
                },
                {
                    "source": "sub_3",
                    "target": "sub_4",
                    "type": "prerequisite"
                }
            ]
        }
    
    return goal, execution_plan
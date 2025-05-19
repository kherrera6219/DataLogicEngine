"""
KA-50: Agent Identity Consistency Checker

This algorithm verifies the consistency of agent identities across sessions and interactions,
ensuring stable and coherent simulation experiences.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
import time
import hashlib

logger = logging.getLogger(__name__)

class AgentIdentityConsistencyChecker:
    """
    KA-50: Checks consistency of agent identities across sessions.
    
    This algorithm verifies that agent identities remain consistent and coherent
    across multiple simulation sessions, maintaining stable interaction experiences.
    """
    
    def __init__(self):
        """Initialize the Agent Identity Consistency Checker."""
        self.identity_aspects = self._initialize_identity_aspects()
        self.inconsistency_types = self._initialize_inconsistency_types()
        logger.info("KA-50: Agent Identity Consistency Checker initialized")
    
    def _initialize_identity_aspects(self) -> Dict[str, Dict[str, Any]]:
        """Initialize aspects of agent identity to check."""
        return {
            "core_attributes": {
                "description": "Fundamental attributes defining agent identity",
                "importance": "critical",
                "consistency_threshold": 0.95,
                "examples": ["id", "name", "role", "type", "creation_timestamp"]
            },
            "capabilities": {
                "description": "Agent functional capabilities and skills",
                "importance": "high",
                "consistency_threshold": 0.8,
                "examples": ["supported_tasks", "skill_levels", "permissions"]
            },
            "knowledge_base": {
                "description": "Knowledge and information accessible to agent",
                "importance": "high",
                "consistency_threshold": 0.85,
                "examples": ["domain_knowledge", "training_data", "reference_material"]
            },
            "behavior_patterns": {
                "description": "Consistent behavioral characteristics",
                "importance": "medium",
                "consistency_threshold": 0.7,
                "examples": ["response_style", "decision_preferences", "interaction_patterns"]
            },
            "memory": {
                "description": "Persistent memory of past interactions and experiences",
                "importance": "high",
                "consistency_threshold": 0.9,
                "examples": ["conversation_history", "past_decisions", "user_preferences"]
            },
            "metadata": {
                "description": "Technical metadata about agent",
                "importance": "low",
                "consistency_threshold": 0.6,
                "examples": ["version", "last_updated", "deployment_context"]
            }
        }
    
    def _initialize_inconsistency_types(self) -> Dict[str, Dict[str, Any]]:
        """Initialize types of inconsistencies to detect."""
        return {
            "attribute_mismatch": {
                "description": "Core attributes don't match across sessions",
                "severity": "critical",
                "detection_method": "direct_comparison",
                "remediation": "restore_from_baseline"
            },
            "capability_drift": {
                "description": "Agent capabilities changing between sessions",
                "severity": "high",
                "detection_method": "capability_comparison",
                "remediation": "capability_reconciliation"
            },
            "memory_gap": {
                "description": "Missing memories from previous sessions",
                "severity": "high",
                "detection_method": "memory_continuity_check",
                "remediation": "memory_restoration"
            },
            "behavior_shift": {
                "description": "Significant changes in behavioral patterns",
                "severity": "medium",
                "detection_method": "behavior_analysis",
                "remediation": "behavior_alignment"
            },
            "knowledge_inconsistency": {
                "description": "Contradictions in knowledge across sessions",
                "severity": "high",
                "detection_method": "knowledge_verification",
                "remediation": "knowledge_reconciliation"
            },
            "temporal_paradox": {
                "description": "Logical inconsistencies in temporal sequence",
                "severity": "medium",
                "detection_method": "temporal_analysis",
                "remediation": "timeline_reconciliation"
            }
        }
    
    def check_identity_consistency(self, session_ids: List[str],
                                agent_states: Optional[List[Dict[str, Any]]] = None,
                                baseline_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check consistency of agent identity across sessions.
        
        Args:
            session_ids: List of session identifiers to check
            agent_states: Optional list of agent state dictionaries
            baseline_id: Optional baseline session ID to compare against
            
        Returns:
            Dictionary with consistency check results
        """
        # Validate inputs
        if not session_ids:
            return {
                "consistent_identity": True,
                "sessions_checked": 0,
                "consistency_score": 1.0,
                "message": "No sessions to check"
            }
        
        # Simple case with just session IDs
        if len(set(session_ids)) == 1:
            # All session IDs are identical - perfect consistency
            return {
                "consistent_identity": True,
                "sessions_checked": len(session_ids),
                "consistency_score": 1.0,
                "session_ids": session_ids,
                "message": "All session IDs are identical"
            }
        
        # More complex case with agent states
        if agent_states is None or len(agent_states) != len(session_ids):
            return self._check_session_id_consistency(session_ids)
        
        # Full check with agent states
        return self._check_full_consistency(session_ids, agent_states, baseline_id)
    
    def _check_session_id_consistency(self, session_ids: List[str]) -> Dict[str, Any]:
        """
        Check consistency based only on session IDs.
        
        Args:
            session_ids: List of session identifiers to check
            
        Returns:
            Dictionary with consistency check results
        """
        unique_ids = set(session_ids)
        
        # Calculate basic consistency score
        consistency_score = 1.0 if len(unique_ids) == 1 else 1.0 / len(unique_ids)
        
        # Determine if consistent (single ID or hash pattern)
        consistent = len(unique_ids) == 1
        
        # Check for sequential pattern
        if not consistent and all(s.isdigit() for s in session_ids):
            # Convert to integers and check if sequential
            int_ids = [int(s) for s in session_ids]
            sorted_ids = sorted(int_ids)
            sequential = all(sorted_ids[i] + 1 == sorted_ids[i+1] for i in range(len(sorted_ids)-1))
            
            if sequential:
                consistent = True
                consistency_score = 0.9  # High but not perfect
        
        # Check for hash-based pattern
        if not consistent:
            # Check if IDs might be hash-based (all same length, similar format)
            lengths = [len(s) for s in session_ids]
            if len(set(lengths)) == 1 and all(all(c in "0123456789abcdef-" for c in s.lower()) for s in session_ids):
                # Might be hash-based IDs
                consistent = True
                consistency_score = 0.85  # Reasonable confidence
        
        # Prepare result
        result = {
            "consistent_identity": consistent,
            "sessions_checked": len(session_ids),
            "unique_sessions": len(unique_ids),
            "consistency_score": round(consistency_score, 3),
            "session_ids": session_ids,
            "message": "Session IDs consistent" if consistent else "Inconsistent session IDs detected"
        }
        
        return result
    
    def _check_full_consistency(self, session_ids: List[str],
                             agent_states: List[Dict[str, Any]],
                             baseline_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform full consistency check on agent states.
        
        Args:
            session_ids: List of session identifiers to check
            agent_states: List of agent state dictionaries
            baseline_id: Optional baseline session ID to compare against
            
        Returns:
            Dictionary with consistency check results
        """
        # Determine baseline state
        baseline_index = 0
        if baseline_id is not None:
            for i, session_id in enumerate(session_ids):
                if session_id == baseline_id:
                    baseline_index = i
                    break
        
        baseline_state = agent_states[baseline_index]
        
        # Check each aspect of identity
        aspect_scores = {}
        inconsistencies = []
        
        for aspect_name, aspect_info in self.identity_aspects.items():
            aspect_score, aspect_issues = self._check_aspect_consistency(
                aspect_name, aspect_info, baseline_state, session_ids, agent_states, baseline_index
            )
            
            aspect_scores[aspect_name] = aspect_score
            
            # Record inconsistencies
            if aspect_issues:
                inconsistencies.extend(aspect_issues)
        
        # Calculate overall consistency score
        importance_weights = {
            "critical": 5.0,
            "high": 3.0,
            "medium": 2.0,
            "low": 1.0
        }
        
        weighted_scores = 0.0
        total_weight = 0.0
        
        for aspect_name, score in aspect_scores.items():
            aspect_info = self.identity_aspects[aspect_name]
            weight = importance_weights.get(aspect_info["importance"], 1.0)
            
            weighted_scores += score * weight
            total_weight += weight
        
        overall_score = weighted_scores / total_weight if total_weight > 0 else 0.0
        
        # Determine if consistent based on thresholds
        consistent = True
        for aspect_name, score in aspect_scores.items():
            aspect_info = self.identity_aspects[aspect_name]
            threshold = aspect_info["consistency_threshold"]
            
            if score < threshold and aspect_info["importance"] in ["critical", "high"]:
                consistent = False
                break
        
        # Prepare result
        result = {
            "consistent_identity": consistent,
            "sessions_checked": len(session_ids),
            "consistency_score": round(overall_score, 3),
            "aspect_scores": {k: round(v, 3) for k, v in aspect_scores.items()},
            "inconsistencies": inconsistencies,
            "baseline_session": session_ids[baseline_index],
            "message": "Agent identity is consistent" if consistent else "Agent identity inconsistencies detected"
        }
        
        return result
    
    def _check_aspect_consistency(self, aspect_name: str,
                               aspect_info: Dict[str, Any],
                               baseline_state: Dict[str, Any],
                               session_ids: List[str],
                               agent_states: List[Dict[str, Any]],
                               baseline_index: int) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Check consistency of a specific identity aspect.
        
        Args:
            aspect_name: Name of aspect to check
            aspect_info: Information about the aspect
            baseline_state: Baseline agent state
            session_ids: List of session identifiers
            agent_states: List of agent states
            baseline_index: Index of baseline in lists
            
        Returns:
            Tuple of (consistency_score, list_of_inconsistencies)
        """
        # Extract relevant keys for this aspect
        relevant_keys = self._get_relevant_keys(aspect_name, baseline_state)
        
        # Check consistency against baseline
        consistency_scores = []
        inconsistencies = []
        
        for i, (session_id, state) in enumerate(zip(session_ids, agent_states)):
            if i == baseline_index:
                continue  # Skip comparing baseline to itself
            
            # Calculate consistency for this session
            score, issues = self._compare_states(
                aspect_name, 
                relevant_keys,
                baseline_state, 
                state, 
                session_ids[baseline_index], 
                session_id
            )
            
            consistency_scores.append(score)
            inconsistencies.extend(issues)
        
        # Calculate overall aspect score
        aspect_score = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 1.0
        
        return aspect_score, inconsistencies
    
    def _get_relevant_keys(self, aspect_name: str, state: Dict[str, Any]) -> List[str]:
        """
        Get keys relevant to a specific aspect from state.
        
        Args:
            aspect_name: Name of aspect to check
            state: Agent state dictionary
            
        Returns:
            List of relevant keys
        """
        # Real implementation would map aspect names to key patterns
        # For this demonstration, we'll use a simplified approach
        
        aspect_key_patterns = {
            "core_attributes": ["id", "name", "role", "type", "agent_id", "persona"],
            "capabilities": ["capabilities", "skills", "functions", "actions", "permissions"],
            "knowledge_base": ["knowledge", "data", "training", "corpus", "facts"],
            "behavior_patterns": ["behavior", "style", "preferences", "personality", "traits"],
            "memory": ["memory", "history", "conversations", "interactions", "experiences"],
            "metadata": ["version", "updated", "metadata", "timestamp", "config"]
        }
        
        patterns = aspect_key_patterns.get(aspect_name, [])
        
        # Find keys matching patterns
        relevant_keys = []
        for key in state.keys():
            if any(pattern in key.lower() for pattern in patterns):
                relevant_keys.append(key)
        
        return relevant_keys
    
    def _compare_states(self, aspect_name: str,
                      relevant_keys: List[str],
                      baseline_state: Dict[str, Any],
                      current_state: Dict[str, Any],
                      baseline_id: str,
                      current_id: str) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Compare aspects between two states.
        
        Args:
            aspect_name: Name of aspect being compared
            relevant_keys: Keys relevant to this aspect
            baseline_state: Baseline state dictionary
            current_state: Current state dictionary
            baseline_id: Baseline session ID
            current_id: Current session ID
            
        Returns:
            Tuple of (consistency_score, list_of_inconsistencies)
        """
        # Track matches and mismatches
        total_checks = 0
        matches = 0
        inconsistencies = []
        
        # Compare relevant keys
        for key in relevant_keys:
            # Skip if key not in both states
            if key not in baseline_state or key not in current_state:
                continue
            
            total_checks += 1
            
            # Compare values
            baseline_value = baseline_state[key]
            current_value = current_state[key]
            
            # Different comparison strategies based on value type
            if isinstance(baseline_value, (str, int, float, bool)) and isinstance(current_value, (str, int, float, bool)):
                # Direct comparison for simple types
                if baseline_value == current_value:
                    matches += 1
                else:
                    inconsistencies.append({
                        "type": "attribute_mismatch",
                        "aspect": aspect_name,
                        "key": key,
                        "baseline_value": baseline_value,
                        "current_value": current_value,
                        "baseline_id": baseline_id,
                        "current_id": current_id,
                        "severity": self.identity_aspects[aspect_name]["importance"]
                    })
            
            elif isinstance(baseline_value, list) and isinstance(current_value, list):
                # Compare lists
                similarity = self._compare_lists(baseline_value, current_value)
                if similarity >= 0.8:  # 80% similar is a match
                    matches += similarity
                else:
                    inconsistencies.append({
                        "type": "list_divergence",
                        "aspect": aspect_name,
                        "key": key,
                        "similarity": similarity,
                        "baseline_id": baseline_id,
                        "current_id": current_id,
                        "severity": self.identity_aspects[aspect_name]["importance"]
                    })
            
            elif isinstance(baseline_value, dict) and isinstance(current_value, dict):
                # Compare dictionaries
                similarity = self._compare_dicts(baseline_value, current_value)
                if similarity >= 0.8:  # 80% similar is a match
                    matches += similarity
                else:
                    inconsistencies.append({
                        "type": "structure_divergence",
                        "aspect": aspect_name,
                        "key": key,
                        "similarity": similarity,
                        "baseline_id": baseline_id,
                        "current_id": current_id,
                        "severity": self.identity_aspects[aspect_name]["importance"]
                    })
            
            else:
                # Different types entirely
                inconsistencies.append({
                    "type": "type_mismatch",
                    "aspect": aspect_name,
                    "key": key,
                    "baseline_type": type(baseline_value).__name__,
                    "current_type": type(current_value).__name__,
                    "baseline_id": baseline_id,
                    "current_id": current_id,
                    "severity": self.identity_aspects[aspect_name]["importance"]
                })
        
        # Calculate consistency score
        consistency_score = matches / total_checks if total_checks > 0 else 1.0
        
        return consistency_score, inconsistencies
    
    def _compare_lists(self, list1: List[Any], list2: List[Any]) -> float:
        """
        Compare similarity between two lists.
        
        Args:
            list1: First list
            list2: Second list
            
        Returns:
            Similarity score (0-1)
        """
        # Handle empty lists
        if not list1 and not list2:
            return 1.0
        if not list1 or not list2:
            return 0.0
        
        # Convert to sets for simple comparison if possible
        if all(isinstance(x, (str, int, float, bool)) for x in list1 + list2):
            set1 = set(list1)
            set2 = set(list2)
            
            # Calculate Jaccard similarity
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            
            return intersection / union
        
        # For more complex lists, compare based on length and sampling
        len_similarity = min(len(list1), len(list2)) / max(len(list1), len(list2))
        
        # Sample comparison of a few elements
        samples = min(5, min(len(list1), len(list2)))
        sample_similarity = 0.0
        
        for i in range(samples):
            idx1 = (i * len(list1)) // samples
            idx2 = (i * len(list2)) // samples
            
            item1 = list1[idx1]
            item2 = list2[idx2]
            
            if isinstance(item1, (str, int, float, bool)) and isinstance(item2, (str, int, float, bool)):
                sample_similarity += 1.0 if item1 == item2 else 0.0
            elif isinstance(item1, dict) and isinstance(item2, dict):
                sample_similarity += self._compare_dicts(item1, item2)
            else:
                sample_similarity += 0.5  # Partial credit for non-comparable items
        
        sample_similarity /= samples
        
        # Combine length and sample similarity
        return (len_similarity * 0.4) + (sample_similarity * 0.6)
    
    def _compare_dicts(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> float:
        """
        Compare similarity between two dictionaries.
        
        Args:
            dict1: First dictionary
            dict2: Second dictionary
            
        Returns:
            Similarity score (0-1)
        """
        # Handle empty dictionaries
        if not dict1 and not dict2:
            return 1.0
        if not dict1 or not dict2:
            return 0.0
        
        # Compare keys
        keys1 = set(dict1.keys())
        keys2 = set(dict2.keys())
        
        key_intersection = keys1.intersection(keys2)
        key_union = keys1.union(keys2)
        
        key_similarity = len(key_intersection) / len(key_union)
        
        # Compare values for common keys
        value_similarity = 0.0
        for key in key_intersection:
            val1 = dict1[key]
            val2 = dict2[key]
            
            if isinstance(val1, (str, int, float, bool)) and isinstance(val2, (str, int, float, bool)):
                value_similarity += 1.0 if val1 == val2 else 0.0
            elif isinstance(val1, list) and isinstance(val2, list):
                value_similarity += self._compare_lists(val1, val2)
            elif isinstance(val1, dict) and isinstance(val2, dict):
                value_similarity += self._compare_dicts(val1, val2)
            else:
                value_similarity += 0.5  # Partial credit
        
        value_similarity /= len(key_intersection) if key_intersection else 1.0
        
        # Combine key and value similarity
        return (key_similarity * 0.4) + (value_similarity * 0.6)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Agent Identity Consistency Checker (KA-50) on the provided data.
    
    Args:
        data: A dictionary containing session IDs and optional agent states
        
    Returns:
        Dictionary with consistency check results
    """
    session_ids = data.get("session_ids", [])
    agent_states = data.get("agent_states")
    baseline_id = data.get("baseline_id")
    
    # Simple case with just session IDs
    if isinstance(session_ids, list) and all(isinstance(s, str) for s in session_ids):
        if len(set(session_ids)) == 1:
            return {
                "algorithm": "KA-50",
                "consistent_identity": True,
                "session_ids": session_ids,
                "timestamp": time.time(),
                "success": True
            }
    
    # Run full check
    checker = AgentIdentityConsistencyChecker()
    result = checker.check_identity_consistency(session_ids, agent_states, baseline_id)
    
    return {
        "algorithm": "KA-50",
        "consistent_identity": result["consistent_identity"],
        "consistency_score": result.get("consistency_score", 1.0),
        "session_ids": session_ids,
        "timestamp": time.time(),
        "success": True
    }
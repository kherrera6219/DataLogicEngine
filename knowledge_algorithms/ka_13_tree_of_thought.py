"""
KA-13: Tree of Thought

This algorithm implements a tree-based thinking structure that enables
complex decision making through branching paths of analysis.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import time

logger = logging.getLogger(__name__)

class TreeOfThought:
    """
    KA-13: Implements structured decision trees for complex problem solving.
    
    The Tree of Thought algorithm enables multi-path reasoning by exploring
    different decision branches with associated conditions and evaluations.
    """
    
    def __init__(self):
        """Initialize the Tree of Thought algorithm."""
        logger.info("KA-13: Tree of Thought initialized")
    
    def generate_decision_tree(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a decision tree for a given query.
        
        Args:
            query: The query or problem statement
            context: Optional context including domain, constraints, etc.
            
        Returns:
            Dictionary containing the decision tree structure
        """
        context = context or {}
        domain = context.get("domain", "general")
        
        # Determine root decision/problem based on query and domain
        root_decision = self._determine_root_decision(query, domain)
        
        # Generate primary branches (main decision options)
        branches = self._generate_primary_branches(root_decision, domain)
        
        # Generate secondary branches (implications/consequences)
        decision_tree = self._generate_secondary_branches(branches, domain)
        
        # Calculate confidence score for the tree
        confidence = self._calculate_tree_confidence(decision_tree, query, domain)
        
        # Add metadata
        result = {
            "algorithm": "KA-13",
            "query": query,
            "domain": domain,
            "root_decision": root_decision,
            "decision_tree": decision_tree,
            "confidence": confidence
        }
        
        return result
    
    def _determine_root_decision(self, query: str, domain: str) -> str:
        """
        Determine the root decision or problem statement.
        
        Args:
            query: The query text
            domain: The domain context
            
        Returns:
            Root decision as a string
        """
        # In a full implementation, this would use NLP to extract the decision point
        # For now, we'll use a simplified approach based on keywords and domain
        
        query_lower = query.lower()
        
        # Check for explicit decision indicators
        decision_indicators = [
            "should", "shall", "decide", "determine", "select", "choose", 
            "evaluate", "assess", "consider"
        ]
        
        # Extract decision fragments that follow indicators
        for indicator in decision_indicators:
            if indicator in query_lower:
                # Find the position of the indicator
                pos = query_lower.find(indicator)
                # Extract the fragment after the indicator
                fragment = query[pos:pos + 50]  # Take up to 50 chars after
                # Clean up the fragment
                fragment = fragment.strip()
                if len(fragment) > 10:  # If we have a substantial fragment
                    return fragment
        
        # Domain-specific default decisions if no explicit indicators found
        domain_defaults = {
            "healthcare": "Should the proposed medical treatment be approved?",
            "finance": "Should the financial risk be accepted?",
            "legal": "Does the action comply with applicable regulations?",
            "technology": "Should the technical solution be implemented?",
            "education": "Is the educational approach effective?",
            "general": "What is the optimal decision for this situation?"
        }
        
        return domain_defaults.get(domain, "What is the best course of action?")
    
    def _generate_primary_branches(self, root_decision: str, domain: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate primary decision branches.
        
        Args:
            root_decision: The root decision text
            domain: The domain context
            
        Returns:
            Dictionary mapping root to branch options
        """
        # Common branch structure across domains
        common_branches = [
            {
                "option": "Yes/Approve/Accept",
                "conditions": [],
                "implications": []
            },
            {
                "option": "No/Reject/Decline",
                "conditions": [],
                "implications": []
            },
            {
                "option": "Defer/Gather More Information",
                "conditions": [],
                "implications": []
            }
        ]
        
        # Domain-specific branch customization
        if domain == "healthcare":
            common_branches[0]["option"] = "Approve Treatment"
            common_branches[0]["conditions"] = ["Medical Necessity Confirmed", "Cost-Benefit Favorable", "Patient Consent Obtained"]
            common_branches[1]["option"] = "Reject Treatment"
            common_branches[1]["conditions"] = ["Medical Necessity Not Established", "Adverse Risk Profile", "Alternative Options Available"]
            common_branches[2]["option"] = "Seek Additional Consultation"
            common_branches[2]["conditions"] = ["Incomplete Medical History", "Ambiguous Test Results", "Complex Comorbidities"]
        
        elif domain == "finance":
            common_branches[0]["option"] = "Approve Investment"
            common_branches[0]["conditions"] = ["ROI Exceeds Threshold", "Risk Within Tolerance", "Due Diligence Complete"]
            common_branches[1]["option"] = "Reject Investment"
            common_branches[1]["conditions"] = ["Insufficient Returns", "Excessive Risk", "Regulatory Concerns"]
            common_branches[2]["option"] = "Request Additional Analysis"
            common_branches[2]["conditions"] = ["Market Uncertainty", "Incomplete Financial Data", "Timing Considerations"]
        
        elif domain == "legal":
            common_branches[0]["option"] = "Confirm Compliance"
            common_branches[0]["conditions"] = ["All Requirements Met", "Documentation Complete", "Legal Review Favorable"]
            common_branches[1]["option"] = "Flag Non-Compliance"
            common_branches[1]["conditions"] = ["Requirements Not Met", "Documentation Incomplete", "Legal Issues Identified"]
            common_branches[2]["option"] = "Initiate Legal Review"
            common_branches[2]["conditions"] = ["Regulatory Ambiguity", "Precedent Unclear", "Complex Jurisdictional Issues"]
        
        return {root_decision: common_branches}
    
    def _generate_secondary_branches(self, branches: Dict[str, List[Dict[str, Any]]], domain: str) -> Dict[str, Any]:
        """
        Generate secondary branches with implications.
        
        Args:
            branches: Primary branches dictionary
            domain: The domain context
            
        Returns:
            Enhanced tree with secondary branches
        """
        # Start with the primary branches
        decision_tree = branches.copy()
        
        # For each primary branch, add implications
        for root, options in decision_tree.items():
            for i, option in enumerate(options):
                # Generate implications based on the option and domain
                implications = self._generate_implications(option["option"], domain)
                decision_tree[root][i]["implications"] = implications
                
                # Add confidence score for each branch
                decision_tree[root][i]["branch_confidence"] = self._calculate_branch_confidence(option, implications)
        
        return decision_tree
    
    def _generate_implications(self, option: str, domain: str) -> List[Dict[str, Any]]:
        """
        Generate implications for a decision option.
        
        Args:
            option: The decision option
            domain: The domain context
            
        Returns:
            List of implication dictionaries
        """
        # Extract decision type (approve/reject/defer)
        decision_type = ""
        if any(keyword in option.lower() for keyword in ["yes", "approve", "accept", "confirm"]):
            decision_type = "approve"
        elif any(keyword in option.lower() for keyword in ["no", "reject", "decline", "flag"]):
            decision_type = "reject"
        else:
            decision_type = "defer"
        
        # Domain-specific implications
        implications = []
        
        if domain == "healthcare":
            if decision_type == "approve":
                implications = [
                    {"effect": "Treatment Initiated", "impact": "positive", "timeframe": "immediate"},
                    {"effect": "Resource Allocation", "impact": "neutral", "timeframe": "immediate"},
                    {"effect": "Patient Outcome Improvement", "impact": "positive", "timeframe": "long-term"},
                    {"effect": "Healthcare Costs Incurred", "impact": "negative", "timeframe": "immediate"}
                ]
            elif decision_type == "reject":
                implications = [
                    {"effect": "Alternative Treatment Consideration", "impact": "neutral", "timeframe": "immediate"},
                    {"effect": "Patient Dissatisfaction Risk", "impact": "negative", "timeframe": "immediate"},
                    {"effect": "Resource Conservation", "impact": "positive", "timeframe": "immediate"},
                    {"effect": "Potential Malpractice Concern", "impact": "negative", "timeframe": "long-term"}
                ]
            else:  # defer
                implications = [
                    {"effect": "Diagnostic Process Extended", "impact": "neutral", "timeframe": "immediate"},
                    {"effect": "Treatment Delay", "impact": "negative", "timeframe": "immediate"},
                    {"effect": "Improved Decision Accuracy", "impact": "positive", "timeframe": "medium-term"}
                ]
        
        elif domain == "finance":
            if decision_type == "approve":
                implications = [
                    {"effect": "Capital Deployment", "impact": "neutral", "timeframe": "immediate"},
                    {"effect": "Potential Returns Generated", "impact": "positive", "timeframe": "medium-term"},
                    {"effect": "Portfolio Risk Adjustment", "impact": "neutral", "timeframe": "immediate"},
                    {"effect": "Resource Commitment", "impact": "negative", "timeframe": "immediate"}
                ]
            elif decision_type == "reject":
                implications = [
                    {"effect": "Capital Preservation", "impact": "positive", "timeframe": "immediate"},
                    {"effect": "Opportunity Cost Incurred", "impact": "negative", "timeframe": "long-term"},
                    {"effect": "Alternative Investment Opportunity", "impact": "neutral", "timeframe": "immediate"}
                ]
            else:  # defer
                implications = [
                    {"effect": "Timing Risk", "impact": "negative", "timeframe": "immediate"},
                    {"effect": "Improved Analysis Quality", "impact": "positive", "timeframe": "medium-term"},
                    {"effect": "Decision Process Extended", "impact": "neutral", "timeframe": "immediate"}
                ]
        
        else:  # generic implications for other domains
            if decision_type == "approve":
                implications = [
                    {"effect": "Resource Commitment", "impact": "neutral", "timeframe": "immediate"},
                    {"effect": "Expected Benefits Realized", "impact": "positive", "timeframe": "medium-term"},
                    {"effect": "Associated Costs Incurred", "impact": "negative", "timeframe": "immediate"}
                ]
            elif decision_type == "reject":
                implications = [
                    {"effect": "Resource Conservation", "impact": "positive", "timeframe": "immediate"},
                    {"effect": "Opportunity Cost", "impact": "negative", "timeframe": "medium-term"},
                    {"effect": "Alternative Options Available", "impact": "neutral", "timeframe": "immediate"}
                ]
            else:  # defer
                implications = [
                    {"effect": "Decision Quality Improvement", "impact": "positive", "timeframe": "medium-term"},
                    {"effect": "Timing Impact", "impact": "negative", "timeframe": "immediate"},
                    {"effect": "Process Extension", "impact": "neutral", "timeframe": "immediate"}
                ]
        
        return implications
    
    def _calculate_branch_confidence(self, option: Dict[str, Any], implications: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence score for a specific branch.
        
        Args:
            option: The option dictionary
            implications: List of implications
            
        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence
        confidence = 0.5
        
        # Adjust based on conditions specificity
        conditions = option.get("conditions", [])
        condition_specificity = min(0.3, len(conditions) * 0.1)
        confidence += condition_specificity
        
        # Adjust based on implications depth
        implication_depth = min(0.2, len(implications) * 0.05)
        confidence += implication_depth
        
        # Adjust based on positive/negative balance of implications
        if implications:
            positive_count = sum(1 for imp in implications if imp.get("impact") == "positive")
            negative_count = sum(1 for imp in implications if imp.get("impact") == "negative")
            
            # If balanced, higher confidence
            balance = 1.0 - abs(positive_count - negative_count) / len(implications)
            balance_boost = balance * 0.1
            confidence += balance_boost
        
        # Cap at 0.95
        return min(0.95, confidence)
    
    def _calculate_tree_confidence(self, decision_tree: Dict[str, Any], query: str, domain: str) -> float:
        """
        Calculate overall confidence for the decision tree.
        
        Args:
            decision_tree: The complete decision tree
            query: The original query
            domain: The domain context
            
        Returns:
            Overall confidence score
        """
        # Start with base confidence
        confidence = 0.6
        
        # Extract branch confidences
        branch_confidences = []
        for root, options in decision_tree.items():
            for option in options:
                if "branch_confidence" in option:
                    branch_confidences.append(option["branch_confidence"])
        
        # Average branch confidence (if any)
        if branch_confidences:
            avg_branch_confidence = sum(branch_confidences) / len(branch_confidences)
            confidence = avg_branch_confidence
        
        # Adjust for quality of root decision extraction
        if "should" in query.lower() or "decide" in query.lower():
            confidence += 0.1
        
        # Domain-specific adjustments
        domain_confidence_boosts = {
            "healthcare": 0.05,
            "finance": 0.05,
            "legal": 0.05
        }
        confidence += domain_confidence_boosts.get(domain, 0)
        
        # Cap at 0.95
        return min(0.95, confidence)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Tree of Thought algorithm (KA-13) on the provided data.
    
    Args:
        data: A dictionary containing the query and optional context
        
    Returns:
        The decision tree result
    """
    query = data.get("query", "")
    context = data.get("context", {})
    
    if not query and not data.get("root_decision"):
        return {
            "algorithm": "KA-13",
            "error": "No query or root decision provided",
            "success": False
        }
    
    # Use provided root decision or extract from query
    root_decision = data.get("root_decision")
    
    engine = TreeOfThought()
    
    if root_decision:
        # If root decision provided, add it to context
        context["root_decision"] = root_decision
    
    result = engine.generate_decision_tree(query, context)
    
    return {
        **result,
        "success": True
    }
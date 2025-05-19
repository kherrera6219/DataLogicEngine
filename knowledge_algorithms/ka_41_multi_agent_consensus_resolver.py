"""
KA-41: Multi-Agent Consensus Resolver

This algorithm determines consensus among multiple agent outputs, weighing different
opinions and finding the most supported conclusion across diverse perspectives.
"""

import logging
from typing import Dict, List, Any, Optional, Counter
import time
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

class MultiAgentConsensusResolver:
    """
    KA-41: Resolves consensus among multiple agent outputs.
    
    This algorithm analyzes outputs from multiple agents or models,
    determining the most supported conclusions and identifying areas of agreement.
    """
    
    def __init__(self):
        """Initialize the Multi-Agent Consensus Resolver."""
        self.consensus_strategies = self._initialize_consensus_strategies()
        logger.info("KA-41: Multi-Agent Consensus Resolver initialized")
    
    def _initialize_consensus_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize strategies for resolving consensus."""
        return {
            "majority_vote": {
                "description": "Select the most common output as consensus",
                "weighting": "equal",
                "threshold": 0.5
            },
            "weighted_vote": {
                "description": "Weight votes by agent confidence or expertise",
                "weighting": "confidence",
                "threshold": 0.5
            },
            "unanimous_only": {
                "description": "Only accept consensus when all agents agree",
                "weighting": "equal",
                "threshold": 1.0
            },
            "supermajority": {
                "description": "Require two-thirds majority for consensus",
                "weighting": "equal",
                "threshold": 0.667
            },
            "ranked_choice": {
                "description": "Use ranked preferences to determine consensus",
                "weighting": "preference_rank",
                "threshold": 0.5
            }
        }
    
    def resolve_consensus(self, agent_outputs: List[Any],
                        agent_weights: Optional[List[float]] = None,
                        strategy: str = "majority_vote",
                        threshold: Optional[float] = None) -> Dict[str, Any]:
        """
        Resolve consensus among multiple agent outputs.
        
        Args:
            agent_outputs: List of outputs from different agents
            agent_weights: Optional list of weights for each agent
            strategy: Strategy for resolving consensus
            threshold: Optional custom threshold for consensus
            
        Returns:
            Dictionary with consensus resolution
        """
        # Validate inputs
        if not agent_outputs:
            return {
                "consensus": None,
                "confidence": 0.0,
                "agreement_ratio": 0.0,
                "original_outputs": []
            }
        
        # Get strategy information
        if strategy not in self.consensus_strategies:
            strategy = "majority_vote"  # Default to majority vote
        
        strategy_info = self.consensus_strategies[strategy]
        
        # Set threshold
        if threshold is None:
            threshold = strategy_info["threshold"]
        
        # Normalize weights if provided
        weights = agent_weights
        if weights is None:
            weights = [1.0] * len(agent_outputs)  # Equal weights
        else:
            # Ensure weights match outputs
            if len(weights) != len(agent_outputs):
                weights = weights[:len(agent_outputs)] if len(weights) > len(agent_outputs) else weights + [1.0] * (len(agent_outputs) - len(weights))
            
            # Normalize to sum to 1.0
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights] if total_weight > 0 else [1.0 / len(weights)] * len(weights)
        
        # Apply appropriate resolution strategy
        if strategy == "majority_vote":
            consensus, confidence, votes = self._apply_majority_vote(agent_outputs, weights)
        elif strategy == "weighted_vote":
            consensus, confidence, votes = self._apply_weighted_vote(agent_outputs, weights)
        elif strategy == "unanimous_only":
            consensus, confidence, votes = self._apply_unanimous_only(agent_outputs, weights)
        elif strategy == "supermajority":
            consensus, confidence, votes = self._apply_supermajority(agent_outputs, weights)
        elif strategy == "ranked_choice":
            consensus, confidence, votes = self._apply_ranked_choice(agent_outputs, weights)
        else:
            # Fallback to majority vote
            consensus, confidence, votes = self._apply_majority_vote(agent_outputs, weights)
        
        # Calculate agreement ratio
        agreement_ratio = 0.0
        if len(agent_outputs) > 1:
            agreement_pairs = 0
            total_pairs = 0
            
            for i in range(len(agent_outputs)):
                for j in range(i + 1, len(agent_outputs)):
                    total_pairs += 1
                    if str(agent_outputs[i]) == str(agent_outputs[j]):
                        agreement_pairs += 1
            
            agreement_ratio = agreement_pairs / total_pairs if total_pairs > 0 else 0.0
        else:
            agreement_ratio = 1.0  # Single agent always agrees with itself
        
        # Check if consensus meets threshold
        if confidence < threshold:
            consensus = None
            
        # Prepare result
        result = {
            "consensus": consensus,
            "confidence": round(confidence, 4),
            "agreement_ratio": round(agreement_ratio, 4),
            "original_outputs": agent_outputs,
            "votes": votes,
            "strategy": strategy,
            "threshold": threshold,
            "agent_weights": weights,
            "agents_count": len(agent_outputs),
            "meets_threshold": confidence >= threshold
        }
        
        return result
    
    def _apply_majority_vote(self, outputs: List[Any], weights: List[float]) -> tuple:
        """
        Apply majority vote strategy.
        
        Args:
            outputs: List of agent outputs
            weights: List of agent weights
            
        Returns:
            Tuple of (consensus, confidence, votes)
        """
        # Count occurrences
        output_counts = Counter(str(output) for output in outputs)
        
        # Find most common
        most_common = output_counts.most_common(1)
        if not most_common:
            return None, 0.0, {}
        
        consensus_str, count = most_common[0]
        
        # Try to convert back to original type if possible
        try:
            # Find original output with this string representation
            for output in outputs:
                if str(output) == consensus_str:
                    consensus = output
                    break
            else:
                consensus = consensus_str
        except:
            consensus = consensus_str
        
        # Calculate confidence
        confidence = count / len(outputs)
        
        # Prepare votes
        votes = {output: count for output, count in output_counts.items()}
        
        return consensus, confidence, votes
    
    def _apply_weighted_vote(self, outputs: List[Any], weights: List[float]) -> tuple:
        """
        Apply weighted vote strategy.
        
        Args:
            outputs: List of agent outputs
            weights: List of agent weights
            
        Returns:
            Tuple of (consensus, confidence, votes)
        """
        # Count weighted occurrences
        weighted_counts = defaultdict(float)
        for output, weight in zip(outputs, weights):
            weighted_counts[str(output)] += weight
        
        # Find highest weighted output
        if not weighted_counts:
            return None, 0.0, {}
        
        consensus_str = max(weighted_counts.items(), key=lambda x: x[1])[0]
        total_weight = sum(weighted_counts.values())
        
        # Try to convert back to original type if possible
        try:
            # Find original output with this string representation
            for output in outputs:
                if str(output) == consensus_str:
                    consensus = output
                    break
            else:
                consensus = consensus_str
        except:
            consensus = consensus_str
        
        # Calculate confidence
        confidence = weighted_counts[consensus_str] / total_weight if total_weight > 0 else 0.0
        
        # Prepare votes
        votes = {output: weight for output, weight in weighted_counts.items()}
        
        return consensus, confidence, votes
    
    def _apply_unanimous_only(self, outputs: List[Any], weights: List[float]) -> tuple:
        """
        Apply unanimous only strategy.
        
        Args:
            outputs: List of agent outputs
            weights: List of agent weights
            
        Returns:
            Tuple of (consensus, confidence, votes)
        """
        # Check if all outputs are the same
        first_output = str(outputs[0]) if outputs else None
        all_same = all(str(output) == first_output for output in outputs)
        
        if all_same and first_output is not None:
            consensus = outputs[0]  # Use original output
            confidence = 1.0
        else:
            consensus = None
            confidence = 0.0
        
        # Prepare votes
        output_counts = Counter(str(output) for output in outputs)
        votes = {output: count for output, count in output_counts.items()}
        
        return consensus, confidence, votes
    
    def _apply_supermajority(self, outputs: List[Any], weights: List[float]) -> tuple:
        """
        Apply supermajority strategy.
        
        Args:
            outputs: List of agent outputs
            weights: List of agent weights
            
        Returns:
            Tuple of (consensus, confidence, votes)
        """
        # Count occurrences
        output_counts = Counter(str(output) for output in outputs)
        
        # Find most common
        most_common = output_counts.most_common(1)
        if not most_common:
            return None, 0.0, {}
        
        consensus_str, count = most_common[0]
        
        # Try to convert back to original type if possible
        try:
            # Find original output with this string representation
            for output in outputs:
                if str(output) == consensus_str:
                    consensus = output
                    break
            else:
                consensus = consensus_str
        except:
            consensus = consensus_str
        
        # Calculate confidence
        confidence = count / len(outputs)
        
        # Prepare votes
        votes = {output: count for output, count in output_counts.items()}
        
        return consensus, confidence, votes
    
    def _apply_ranked_choice(self, outputs: List[Any], weights: List[float]) -> tuple:
        """
        Apply ranked choice strategy.
        For simplification, we'll treat the current outputs as first choices only.
        
        Args:
            outputs: List of agent outputs
            weights: List of agent weights
            
        Returns:
            Tuple of (consensus, confidence, votes)
        """
        # Since we don't have full ranking information, we'll apply weighted vote
        return self._apply_weighted_vote(outputs, weights)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Multi-Agent Consensus Resolver (KA-41) on the provided data.
    
    Args:
        data: A dictionary containing agent outputs and resolution parameters
        
    Returns:
        Dictionary with consensus resolution
    """
    agent_outputs = data.get("agent_outputs", [])
    agent_weights = data.get("agent_weights")
    strategy = data.get("strategy", "majority_vote")
    threshold = data.get("threshold")
    
    resolver = MultiAgentConsensusResolver()
    result = resolver.resolve_consensus(agent_outputs, agent_weights, strategy, threshold)
    
    return {
        "algorithm": "KA-41",
        "consensus": result["consensus"],
        "confidence": result["confidence"],
        "agreement_ratio": result["agreement_ratio"],
        "original_outputs": result["original_outputs"],
        "timestamp": time.time(),
        "success": True
    }
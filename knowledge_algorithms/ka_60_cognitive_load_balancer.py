"""
KA-060: Cognitive Load Balancer
Purpose: Allocate computational effort to the most complex query subparts and prune low-yield reasoning branches to optimize resource usage.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA060CognitiveLoadBalancer(KnowledgeAlgorithm):
    """
    KA-060: Effort allocation and branch pruning engine.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_60_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        branches = input_data.get("branches", [])
        total_budget = input_data.get("total_budget", 100)
        
        self.log_execution_step("Balancing Cognitive Load", {"branch_count": len(branches)})
        
        pruned_branches = []
        allocations = {}
        
        # 1. Evaluate yield/complexity and allocate (Stub)
        threshold = self.config.get("min_yield_threshold", 0.2)
        
        for b in branches:
             bid = b.get("id")
             expected_yield = b.get("expected_yield", 0.5)
             
             if expected_yield < threshold and self.config.get("pruning_enabled", True):
                  pruned_branches.append(bid)
             else:
                  # Simple priority-based allocation
                  allocations[bid] = total_budget // max(1, (len(branches) - len(pruned_branches)))
                  
        return {
            "ka_id": "KA-060",
            "ka_name": "Cognitive Load Balancer",
            "success": True,
            "resource_allocations": allocations,
            "pruned_branches": pruned_branches,
            "branches_kept": len(allocations)
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA060CognitiveLoadBalancer(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-060 Failed: {e}")
        return {"success": False, "error": str(e)}

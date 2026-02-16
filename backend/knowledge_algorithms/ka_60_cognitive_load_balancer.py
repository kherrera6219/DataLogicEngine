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

from pydantic import BaseModel, Field

class KA060LoadBalancerInput(BaseModel):
    branches: List[Dict[str, Any]] = Field(default_factory=list, description="Reasoning branches to evaluate for load balancing")
    total_budget: int = Field(100, description="The total computational budget to distribute")

class KA060CognitiveLoadBalancer(KnowledgeAlgorithm):
    """
    KA-060: Effort allocation and reasoning branch pruning engine for resource efficiency.
    """
    input_schema = KA060LoadBalancerInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-060"
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

    def _run_logic(self, input_data: KA060LoadBalancerInput) -> Dict[str, Any]:
        branches = input_data.branches
        total_budget = input_data.total_budget
        self.log_execution_step("Balancing Cognitive Load", {"branch_count": len(branches)})
        
        pruned_branches = []
        allocations = {}
        threshold = self.config.get("min_yield_threshold", 0.2)
        pruning_enabled = self.config.get("pruning_enabled", True)
        
        active_count = 0
        for b in branches:
             if b.get("expected_yield", 0.5) < threshold and pruning_enabled:
                  pruned_branches.append(b.get("id"))
             else:
                  active_count += 1
                  
        for b in branches:
             bid = b.get("id")
             if bid not in pruned_branches:
                  allocations[bid] = total_budget // max(1, active_count)
                  
        return {
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

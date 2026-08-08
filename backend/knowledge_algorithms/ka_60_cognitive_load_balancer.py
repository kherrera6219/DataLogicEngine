"""
KA-060: Cognitive Load Balancer
Purpose: Allocate computational effort to the most complex query subparts and prune low-yield reasoning branches to optimize resource usage.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, ConfigDict, Field, model_validator

logger = logging.getLogger(__name__)


class KA060LoadBalancerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    branches: List[Dict[str, Any]] = Field(default_factory=list, description="Reasoning branches to evaluate for load balancing")
    total_budget: int = Field(100, ge=0, le=1_000_000, description="The total computational budget to distribute")
    dependency_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_branch_ids(self):
        identifiers = [str(branch.get("id") or "").strip() for branch in self.branches]
        if not all(identifiers):
            raise ValueError("every branch requires a non-empty id")
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("branch ids must be unique")
        return self

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
        dependencies = input_data.dependency_results
        estimate = dependencies.get("KA-1080", {})
        budget_admission = dependencies.get("KA-1081", {})
        self.log_execution_step("Balancing Cognitive Load", {"branch_count": len(branches)})
        
        pruned_branches = []
        allocations = {}
        threshold = self.config.get("min_yield_threshold", 0.2)
        pruning_enabled = self.config.get("pruning_enabled", True)
        
        if budget_admission and budget_admission.get("allowed") is not True:
            pruned_branches = sorted(str(branch["id"]) for branch in branches)
            return {
                "success": True,
                "status": "budget_blocked",
                "resource_allocations": {},
                "pruned_branches": pruned_branches,
                "branches_kept": 0,
                "unallocated_budget": total_budget,
                "dependencies_consumed": sorted(dependencies),
                "execution_started": False,
            }

        active = []
        for branch in branches:
            expected_yield = max(0.0, min(1.0, float(branch.get("expected_yield", 0.5))))
            complexity = max(0.0, float(branch.get("complexity", 1.0)))
            if expected_yield < threshold and pruning_enabled:
                pruned_branches.append(str(branch["id"]))
            else:
                active.append((str(branch["id"]), expected_yield * max(1.0, complexity)))

        total_weight = sum(weight for _, weight in active)
        remaining = total_budget
        for index, (branch_id, weight) in enumerate(sorted(active)):
            allocation = (
                remaining
                if index == len(active) - 1
                else int(total_budget * weight / total_weight)
                if total_weight
                else 0
            )
            allocations[branch_id] = allocation
            remaining -= allocation
                  
        return {
            "success": True,
            "resource_allocations": allocations,
            "pruned_branches": sorted(pruned_branches),
            "branches_kept": len(allocations),
            "unallocated_budget": remaining,
            "estimate_reviewed": bool(estimate),
            "dependencies_consumed": sorted(dependencies),
            "execution_started": False,
            "limitations": (
                "Allocations are advisory ceilings derived from caller-supplied "
                "yield and complexity estimates; no branch is scheduled or executed."
            ),
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA060CognitiveLoadBalancer(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-060 Failed: {e}")
        return {"success": False, "error": str(e)}

from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA80SimCostEstimator(KnowledgeAlgorithm):
    ka_id = "KA-080"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-080",
            name="Simulation Cost Estimator",
            description="Estimate compute/time cost of deeper simulation.",
            tier="Control",
            layer=1
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        complexity = state.get("complexity", "medium")
        branches = len(state.get("branch_nodes", [])) or 1
        
        base_cost = 10
        if complexity == "high":
            base_cost = 50
            
        estimated_cost = base_cost * branches
        
        return KAResult(
            output={"estimated_cost": estimated_cost},
            log=f"KA-080 estimated cost at {estimated_cost} units."
        )

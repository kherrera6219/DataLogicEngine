from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA104TruthUtilityArbiter(KnowledgeAlgorithm):
    ka_id = "KA-104"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-104",
            name="Truth vs Utility Arbiter",
            description="Balance correctness vs operational safety/utility.",
            tier="Safety",
            layer=8
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        truth_score = state.get("truth", 1.0)
        utility_score = state.get("utility", 1.0)
        
        decision = "publish"
        if truth_score < 0.9 and utility_score < 0.5:
            decision = "withhold"
            
        return KAResult(
            output=decision,
            log=f"KA-104 decision: {decision} (Truth={truth_score}, Utility={utility_score})"
        )

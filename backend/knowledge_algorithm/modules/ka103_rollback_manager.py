from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA103RollbackManager(KnowledgeAlgorithm):
    ka_id = "KA-103"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-103",
            name="Simulation State Rollback Manager",
            description="Checkpoint and rollback simulation state.",
            tier="Safety",
            layer=7
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        action = state.get("action", "checkpoint")
        
        # Mock rollback logic
        result = "Checkpoint saved"
        if action == "rollback":
            result = "State restored to previous checkpoint"
            
        return KAResult(
            output=result,
            log=f"KA-103 executed {action}."
        )

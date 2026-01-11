from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA05RecursiveControl(KnowledgeAlgorithm):
    ka_id = "KA-005"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-005",
            name="Recursive Control",
            description="Manage recursion depth.",
            tier="Control",
            layer=2
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        depth = state.get("depth", 0)
        max_depth = state.get("max_depth", 5)
        
        should_terminate = depth >= max_depth
        action = "terminate" if should_terminate else "continue"
        
        return KAResult(
            output=action,
            flags={"terminate": should_terminate},
            log=f"Recursion check: depth {depth}/{max_depth} -> {action}"
        )

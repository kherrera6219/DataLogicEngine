from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA23BeliefDecay(KnowledgeAlgorithm):
    ka_id = "KA-023"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-023",
            name="Belief Decay",
            description="Decay stale beliefs; reduce reliance on outdated knowledge.",
            tier="Lifecycle",
            layer=10
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        beliefs = state.get("beliefs", {})
        
        # Mock decay
        decayed = {k: v * 0.9 for k, v in beliefs.items()}
        
        return KAResult(
            output=decayed,
            log="KA-023 applied decay to beliefs."
        )

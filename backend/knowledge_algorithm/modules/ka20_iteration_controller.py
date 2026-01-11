from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA20IterationController(KnowledgeAlgorithm):
    ka_id = "KA-020"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-020",
            name="Iteration Controller",
            description="Decide if loop-back is required for refinement.",
            tier="Control",
            layer=5
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        confidence = state.get("confidence", 1.0)
        threshold = state.get("confidence_threshold", 0.8)
        
        needs_loop = confidence < threshold
        return KAResult(
            output="Loop" if needs_loop else "Proceed",
            flags={"loop_required": needs_loop},
            log=f"KA-20 Check: {confidence} vs {threshold} -> {'Loop' if needs_loop else 'Proceed'}"
        )

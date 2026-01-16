from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA10BiasDetection(KnowledgeAlgorithm):
    ka_id = "KA-010"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-010",
            name="Bias Detection",
            description="Detect bias signals in reasoning/output.",
            tier="Ethics",
            layer=8
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        reasoning_trace = state.get("trace", "")
        
        # Simple keyword based bias check (Mock)
        bias_flags = []
        if "always" in reasoning_trace.lower() or "never" in reasoning_trace.lower():
            bias_flags.append("extremism_heuristic")
            
        return KAResult(
            output=bias_flags,
            flags={"bias_detected": len(bias_flags) > 0},
            log="KA-010 completed bias scan."
        )

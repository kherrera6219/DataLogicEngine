from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA27EthicalImpactAnalysis(KnowledgeAlgorithm):
    ka_id = "KA-027"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-027",
            name="Ethical Impact Analysis",
            description="Evaluate ethical implications; harm assessment.",
            tier="Ethics",
            layer=8
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        action = state.get("action", "")
        
        harm_flags = []
        if "delete" in action.lower() or "destroy" in action.lower():
            harm_flags.append("potential_data_loss")
            
        return KAResult(
            output=harm_flags,
            flags={"ethical_concern": len(harm_flags) > 0},
            log="KA-027 completed ethics scan."
        )

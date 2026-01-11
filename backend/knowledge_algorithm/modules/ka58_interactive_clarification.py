from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA58InteractiveClarification(KnowledgeAlgorithm):
    ka_id = "KA-058"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-058",
            name="Interactive Clarification & Learning",
            description="Ask for user input when ambiguity thresholds are met.",
            tier="Context",
            layer=5
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        ambiguity = state.get("ambiguity", 0.0)
        
        ask_user = False
        if ambiguity > 0.7:
            ask_user = True
            
        return KAResult(
            output={"prompt_user": ask_user},
            flags={"human_input_needed": ask_user},
            log=f"KA-058 ambiguity check: {ambiguity}"
        )

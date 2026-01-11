from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA73IntentClarifier(KnowledgeAlgorithm):
    ka_id = "KA-073"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-073",
            name="Intent Clarifier",
            description="Resolve ambiguous user intents before execution.",
            tier="Context",
            layer=1
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        intent = state.get("intent", "unclear")
        
        clarified = intent
        if intent == "book":
            clarified = "book_flight"
            
        return KAResult(
            output={"clarified_intent": clarified},
            log=f"KA-073 clarified intent to {clarified}."
        )

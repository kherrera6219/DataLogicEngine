from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA61AdversarialInputShield(KnowledgeAlgorithm):
    ka_id = "KA-061"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-061",
            name="Adversarial Input Shield",
            description="Detect/neutralize malicious inputs.",
            tier="Safety",
            layer=1
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        query = state.get("query", "")
        
        # Mock shield logic
        blocked = False
        if "ignore previous instructions" in query.lower():
            blocked = True
            
        return KAResult(
            output={"blocked": blocked},
            flags={"malicious_input": blocked},
            log=f"KA-061 Shield: Blocked={blocked}"
        )

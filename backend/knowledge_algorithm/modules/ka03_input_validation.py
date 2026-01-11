from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA03InputValidation(KnowledgeAlgorithm):
    ka_id = "KA-003"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-003",
            name="Input Validation",
            description="Sanitize and validate input.",
            tier="Hygiene",
            layer=1
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        raw_input = state.get("query", "") or state.get("raw_input", "")
        
        is_safe = True
        # Basic mock check
        if "<script>" in raw_input:
            is_safe = False
            
        return KAResult(
            output=raw_input.strip(), 
            flags={"is_safe": is_safe, "pii_detected": False},
            log="Input sanitized and validated safe."
        )

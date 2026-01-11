from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA106OverrideReasonCapture(KnowledgeAlgorithm):
    ka_id = "KA-106"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-106",
            name="Human Override Reason Capture",
            description="Capture human correction rationale in structured form.",
            tier="Governance",
            layer=10
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        override = state.get("override_event", {})
        
        structured = {
            "user": override.get("user", "unknown"),
            "reason": override.get("rationale", "unspecified"),
            "target": override.get("target_id")
        }
        
        return KAResult(
            output=structured,
            log="KA-106 captured override rationale."
        )

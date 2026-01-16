from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA108CapabilityEscalationDetector(KnowledgeAlgorithm):
    ka_id = "KA-108"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-108",
            name="Capability Escalation Detector",
            description="Detect unsafe capability drift/escalation patterns.",
            tier="Safety",
            layer=10 # Also L6
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        usage_history = state.get("usage", [])
        
        escalation = False
        # Mock detection: if usage increases rapidly
        if len(usage_history) > 100:
             escalation = True
             
        return KAResult(
            output={"escalation_detected": escalation},
            log=f"KA-108 Escalation Detection: {escalation}"
        )

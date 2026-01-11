from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA95HITLEscalation(KnowledgeAlgorithm):
    ka_id = "KA-095"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-095",
            name="Human-in-the-Loop Escalation",
            description="Escalate uncertain/high-risk cases to humans.",
            tier="Governance",
            layer=9 # L9, L10
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        risk_level = state.get("risk", "low")
        confidence = state.get("confidence", 1.0)
        
        escalate = False
        if risk_level == "high" or confidence < 0.4:
            escalate = True
            
        return KAResult(
            output={"escalate": escalate},
            flags={"human_review_required": escalate},
            log=f"KA-095 HITL Decision: {escalate}"
        )

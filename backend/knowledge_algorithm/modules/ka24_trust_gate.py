from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA24TrustGate(KnowledgeAlgorithm):
    ka_id = "KA-024"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-024",
            name="Trust Gate",
            description="Approve/veto outputs based on trust/risk/policy.",
            tier="Safety",
            layer=8
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        trust_score = state.get("trust_score", 1.0)
        risk_score = state.get("risk_score", 0.0)
        
        approved = True
        reason = ""
        
        if trust_score < 0.7 or risk_score > 0.8:
            approved = False
            reason = "Trust too low or Risk too high"
            
        return KAResult(
            output={"approved": approved, "reason": reason},
            flags={"gate_passed": approved},
            log=f"KA-024 Trust Gate: Approved={approved}"
        )

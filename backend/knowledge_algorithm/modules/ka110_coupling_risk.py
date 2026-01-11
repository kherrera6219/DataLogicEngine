from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA110CrossDomainCouplingRisk(KnowledgeAlgorithm):
    ka_id = "KA-110"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-110",
            name="Cross-Domain Coupling Risk Analyzer",
            description="Detect risky cross-domain coupling pathways.",
            tier="Safety",
            layer=6 # Also L7
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        domains = state.get("active_domains", [])
        
        risk = "low"
        if "finance" in domains and "critical_infrastructure" in domains:
            risk = "critical"
            
        return KAResult(
            output={"coupling_risk": risk},
            flags={"risky_coupling": risk == "critical"},
            log=f"KA-110 Coupling Risk: {risk}"
        )

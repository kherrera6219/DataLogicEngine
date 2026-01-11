from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA26ContradictionDetection(KnowledgeAlgorithm):
    ka_id = "KA-026"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-026",
            name="Contradiction Detection",
            description="Detect conflicts across branches/personas/evidence.",
            tier="Truth",
            layer=6
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        claims = state.get("claims", [])
        
        # Mock: check for direct opposites strings
        conflicts = []
        for i, c1 in enumerate(claims):
            for c2 in claims[i+1:]:
                if "not " + c1 in c2 or "not " + c2 in c1:
                    conflicts.append((c1, c2))
                    
        return KAResult(
            output=conflicts,
            flags={"has_conflicts": len(conflicts) > 0},
            log=f"KA-026 found {len(conflicts)} contradictions."
        )

from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA41ConfidenceNormalization(KnowledgeAlgorithm):
    ka_id = "KA-041"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-041",
            name="Concept Confidence Normalization",
            description="Normalize confidence scales across domains.",
            tier="Truth",
            layer=6
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        raw_confidence = state.get("confidence_scores", [])
        
        # Mock normalization to 0-1
        normalized = [min(max(c, 0.0), 1.0) for c in raw_confidence]
        
        return KAResult(
            output=normalized,
            log="KA-041 normalized confidence scores."
        )

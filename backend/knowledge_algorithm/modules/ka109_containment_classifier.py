from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA109ContainmentClassifier(KnowledgeAlgorithm):
    ka_id = "KA-109"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-109",
            name="Knowledge Containment Classifier",
            description="Classify knowledge persistence safety (public/restricted/never).",
            tier="Governance",
            layer=10
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        data = state.get("data", {})
        
        classification = "public"
        if data.get("sensitive"):
            classification = "restricted"
            
        return KAResult(
            output=classification,
            log=f"KA-109 classified as {classification}."
        )

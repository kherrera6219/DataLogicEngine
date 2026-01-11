from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA105ObsolescenceMonitor(KnowledgeAlgorithm):
    ka_id = "KA-105"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-105",
            name="Conceptual Obsolescence Monitor",
            description="Detect paradigm-level obsolescence.",
            tier="Lifecycle",
            layer=10
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        concepts = state.get("concepts", [])
        
        obsolete = []
        # Mock check
        for c in concepts:
            if c.get("last_citation_year", 2025) < 1990:
                obsolete.append(c["id"])
                
        return KAResult(
            output=obsolete,
            log=f"KA-105 found {len(obsolete)} obsolete concepts."
        )

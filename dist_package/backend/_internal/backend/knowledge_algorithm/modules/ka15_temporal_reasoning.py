from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA15TemporalReasoning(KnowledgeAlgorithm):
    ka_id = "KA-015"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-015",
            name="Temporal Reasoning",
            description="Reason across time; timelines; validity windows.",
            tier="Reasoning",
            layer=3
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        events = state.get("events", [])
        
        # Mock timeline construction
        timeline = sorted(events, key=lambda x: x.get("timestamp", 0))
        
        return KAResult(
            output=timeline,
            artifacts={"timeline_graph": timeline},
            log=f"KA-015 ordered {len(events)} events."
        )

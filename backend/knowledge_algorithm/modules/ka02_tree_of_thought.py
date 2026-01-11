from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA02TreeOfThought(KnowledgeAlgorithm):
    ka_id = "KA-002"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-002",
            name="Tree of Thought",
            description="Explore multiple reasoning paths.",
            tier="Reasoning",
            layer=1
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        tasks = state.get("tasks", [])
        
        branches = [
            {"id": "A", "probability": 0.8, "tasks": tasks},
            {"id": "B", "probability": 0.4, "tasks": tasks}
        ]
        
        return KAResult(
            output=branches,
            artifacts={"selected_branch": "A"},
            log="Generated 2 branches, selected A."
        )

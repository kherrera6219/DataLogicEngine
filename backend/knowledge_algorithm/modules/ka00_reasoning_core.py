from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA01AlgorithmOfThought(KnowledgeAlgorithm):
    ka_id = "KA-001"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-001",
            name="Algorithm of Thought",
            description="Execute reasoning via structured algorithmic steps.",
            tier="Reasoning",
            layer=3
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        return KAResult(output="AoT Executed", log="KA-001 active.")

@KARegistry.register_ka
class KA02TreeOfThought(KnowledgeAlgorithm):
    ka_id = "KA-002"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-002",
            name="Tree of Thought",
            description="Explore multiple reasoning paths simultaneously.",
            tier="Reasoning",
            layer=3
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        return KAResult(output="ToT Executed", log="KA-002 active.")

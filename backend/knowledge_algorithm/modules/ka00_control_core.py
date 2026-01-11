from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA05QueryClassification(KnowledgeAlgorithm):
    ka_id = "KA-005"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-005",
            name="Query Classification",
            description="Categorize incoming query for optimal routing.",
            tier="Control",
            layer=1
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        return KAResult(output="Classified", log="KA-005 active.")

@KARegistry.register_ka
class KA06DeepPlanning(KnowledgeAlgorithm):
    ka_id = "KA-006"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-006",
            name="Deep Planning",
            description="Generate multi-step execution plans.",
            tier="Reasoning",
            layer=3
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        return KAResult(output="Planned", log="KA-006 active.")

@KARegistry.register_ka
class KA07RecursiveControl(KnowledgeAlgorithm):
    ka_id = "KA-007"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-007",
            name="Recursive Reasoning Control",
            description="Manage recursion depth and termination.",
            tier="Control",
            layer=2
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        return KAResult(output="Recursive Control", log="KA-007 active.")

@KARegistry.register_ka
class KA08SelfCritique(KnowledgeAlgorithm):
    ka_id = "KA-008"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-008",
            name="Self-Critique & Reflection",
            description="Evaluate previous reasoning steps for errors.",
            tier="Reasoning",
            layer=3
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        return KAResult(output="Reflected", log="KA-008 active.")

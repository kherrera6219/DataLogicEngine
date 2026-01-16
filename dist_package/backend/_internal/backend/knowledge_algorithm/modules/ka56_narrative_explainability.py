from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA56NarrativeExplainability(KnowledgeAlgorithm):
    ka_id = "KA-056"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-056",
            name="Narrative Explainability Engine",
            description="Synthesize narrative explanations for decisions.",
            tier="Synthesis",
            layer=9
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        decision = state.get("decision", {})
        
        explanation = f"The system decided {decision.get('action', 'X')} because {decision.get('reason', 'Y')}."
        
        return KAResult(
            output=explanation,
            log="KA-056 generated narrative."
        )

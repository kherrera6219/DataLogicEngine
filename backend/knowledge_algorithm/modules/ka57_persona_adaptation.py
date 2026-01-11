from typing import Dict, Any
from backend.knowledge_algorithm.base import KnowledgeAlgorithm, KAResult
from backend.knowledge_algorithm.registry import KARegistry

@KARegistry.register_ka
class KA57PersonaAdaptation(KnowledgeAlgorithm):
    ka_id = "KA-057"
    
    def __init__(self):
        super().__init__(
            ka_id="KA-057",
            name="Persona/Emotion Adaptation",
            description="Tune simulation response based on persona emotional state.",
            tier="Context",
            layer=3
        )

    def execute(self, state: Dict[str, Any], context: Any) -> KAResult:
        persona = state.get("persona", {})
        emotion = persona.get("emotion", "neutral")
        
        # Mock adaptation
        tone = "calm"
        if emotion == "angry":
            tone = "defensive"
            
        return KAResult(
            output={"tone": tone},
            log=f"KA-057 adapted tone to {tone}."
        )

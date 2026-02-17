"""
KA-057: Persona/Emotion Adaptation
Purpose: Adapt the tone, structure, and complexity of outputs to match specific stakeholder personas and emotional contexts.
"""
import logging
import json
import os
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA057Input(BaseModel):
    output_object: Dict[str, Any] = Field(default_factory=dict, description="The output object to adapt")
    persona: str = Field("general", description="The target stakeholder persona")

class KA057PersonaEmotionAdaptation(KnowledgeAlgorithm):
    """
    KA-057: Output styling and persona adaptation engine for empathetic context.
    """
    input_schema = KA057Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-057"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_57_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA057Input) -> Dict[str, Any]:
        output_object = input_data.output_object
        target_persona = input_data.persona
        self.log_execution_step("Adapting Output to Persona", {"persona": target_persona})
        
        vibe_overrides = self.config.get("vibe_overrides", {})
        vibe = vibe_overrides.get(target_persona, {"complexity": "medium", "empathy": "medium"})
        adapted_plan = {
            "persona_applied": target_persona,
            "vibe_settings": vibe,
            "style_hints": [f"Complexity level: {vibe.get('complexity')}", f"Empathy level: {vibe.get('empathy')}"],
            "original_id": output_object.get("id")
        }
        return {
            "success": True,
            "adapted_style_plan": adapted_plan,
            "intensity": self.config.get("adaptation_intensity", 0.8)
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA057PersonaEmotionAdaptation(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-057 Failed: {e}")
        return {"success": False, "error": str(e)}

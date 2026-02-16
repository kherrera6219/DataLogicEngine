"""
KA-069: Cultural Context Adapter
Purpose: Adjust the framing, terminology, and sensitivity of outputs to align with specific cultural or regional norms.
"""
import logging
import json
import os
from typing import Dict, Any
from pydantic import BaseModel
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA069Input(BaseModel):
    class Config:
        extra = 'allow'
class KA069CulturalContextAdapter(KnowledgeAlgorithm):
    input_schema = KA069Input
    """
    KA-069: Localized framing and cultural adaptation engine.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.join(os.path.dirname(__file__), "config"), "ka_69_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA069Input) -> Dict[str, Any]:
        input_dict = input_data.model_dump()
        target_culture = input_dict.get("culture", self.config.get("default_culture", "global"))
        
        self.log_execution_step("Adapting to Cultural Context", {"culture": target_culture})
        
        adaptation_rules = self.config.get("adaptation_rules", [])
        active_framing = "neutral"
        
        for rule in adaptation_rules:
             if rule.get("culture") == target_culture:
                  active_framing = rule.get("framing")
                  break
                  
        return {
            "ka_id": "KA-069",
            "ka_name": "Cultural Context Adapter",
            "success": True,
            "applied_framing": active_framing,
            "culture_applied": target_culture,
            "style_directives": [f"Prioritize {active_framing} framing"]
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA069CulturalContextAdapter(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-069 Failed: {e}")
        return {"success": False, "error": str(e)}

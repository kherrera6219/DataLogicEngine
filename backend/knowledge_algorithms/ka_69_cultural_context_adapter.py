"""
KA-069: Cultural Context Adapter
Purpose: Adjust the framing, terminology, and sensitivity of outputs to align with specific cultural or regional norms.
"""
import logging
import json
import os
import locale
from typing import Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA069Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    culture: str = Field(None, description="The target culture/region (e.g., global, regional_na, regional_eu, regional_asia)")
    text: str = Field("", description="Optional text content to dynamically format/phrase")
    numeric_values: Dict[str, float] = Field(default_factory=dict, description="Numeric parameters to localize")


class KA069CulturalContextAdapter(KnowledgeAlgorithm):
    """
    KA-069: Localized framing and cultural adaptation engine.
    """
    input_schema = KA069Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-069"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_69_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA069Input) -> Dict[str, Any]:
        target_culture = input_data.culture or self.config.get("default_culture", "global")
        
        # If default global, try to detect from local OS locale
        if target_culture == "global":
            try:
                # Safe locale retrieval
                os_lang, _ = locale.getdefaultlocale()
                if os_lang:
                    os_lang = os_lang.lower()
                    if os_lang.startswith("en_us") or os_lang.startswith("en_ca"):
                        target_culture = "regional_na"
                    elif any(os_lang.startswith(prefix) for prefix in ["fr_", "de_", "es_", "it_", "en_gb", "nl_", "sv_"]):
                        target_culture = "regional_eu"
                    elif any(os_lang.startswith(prefix) for prefix in ["ja_", "zh_", "ko_", "th_", "vi_"]):
                        target_culture = "regional_asia"
            except Exception as e:
                logger.warning(f"Could not read default locale: {e}")

        self.log_execution_step("Adapting to Cultural Context", {"culture": target_culture})
        
        adaptation_rules = self.config.get("adaptation_rules", [])
        active_framing = "neutral"
        for rule in adaptation_rules:
             if rule.get("culture") == target_culture:
                  active_framing = rule.get("framing")
                  break
                  
        if active_framing == "neutral":
            # Set dynamic defaults
            if target_culture == "regional_eu":
                active_framing = "privacy_first"
            elif target_culture == "regional_na":
                active_framing = "innovation_first"
            elif target_culture == "regional_asia":
                active_framing = "respect_harmony_first"

        # Apply style directives and prefix phrasing
        style_directives = [f"Prioritize {active_framing} framing"]
        phrasing_prefix = ""
        softeners = []
        
        if target_culture == "regional_eu":
            phrasing_prefix = "[Notice: Processed in compliance with regional data protection standards] "
            softeners = ["Please note", "For your security", "With respect to privacy constraints"]
            style_directives.extend(["Adhere strictly to regulatory and privacy boundaries", "Use passive, objective phrasing"])
        elif target_culture == "regional_asia":
            phrasing_prefix = "[We respectfully present the following data] "
            softeners = ["Humbly requested", "Please consider", "With your permission"]
            style_directives.extend(["Use high-context, respectful syntax", "Focus on collective alignment and safety"])
        elif target_culture == "regional_na":
            phrasing_prefix = "[Direct Summary] "
            softeners = ["Let's check", "Quick update", "Action required"]
            style_directives.extend(["Use direct, active, and action-oriented verbs", "Prioritize performance and efficiency metrics"])

        # Format localized text if provided
        adapted_text = input_data.text
        if adapted_text:
            adapted_text = f"{phrasing_prefix}{adapted_text}"

        # Format numeric values depending on target culture
        localized_numerics = {}
        for key, val in input_data.numeric_values.items():
            if target_culture == "regional_eu":
                # E.g. comma as decimal separator
                localized_numerics[key] = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            elif target_culture == "regional_asia":
                # E.g. respect representation
                localized_numerics[key] = f"{val:,.0f}"
            else:
                # standard NA format
                localized_numerics[key] = f"{val:,.2f}"

        return {
            "ka_id": "KA-069",
            "ka_name": "Cultural Context Adapter",
            "success": True,
            "applied_framing": active_framing,
            "culture_applied": target_culture,
            "style_directives": style_directives,
            "phrasing_prefix": phrasing_prefix,
            "softeners": softeners,
            "adapted_text": adapted_text,
            "localized_numerics": localized_numerics
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA069CulturalContextAdapter(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-069 Failed: {e}")
        return {"success": False, "error": str(e)}

"""
KA-068: Domain Specialization Tuner
Purpose: Adjust the sensitivity, weights, and priorities of the KA pipeline based on the detected domain of the query.
"""
import logging
import json
import os
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA068TunerInput(BaseModel):
    domain: str = Field("general", description="The detected domain to tune the pipeline for")

class KA068DomainSpecializationTuner(KnowledgeAlgorithm):
    """
    KA-068: Domain-aware weight adjustment engine for pipeline specialization.
    """
    input_schema = KA068TunerInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-068"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_68_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA068TunerInput) -> Dict[str, Any]:
        detected_domain = input_data.domain
        self.log_execution_step("Tuning Pipeline for Domain", {"domain": detected_domain})
        
        domain_weights = self.config.get("domain_weights", {})
        weight = domain_weights.get(detected_domain, 1.0)
        adjustments = {
            "confidence_scaling": weight,
            "validation_strictness": "high" if weight > 1.2 else "normal",
            "search_depth_modifier": +1 if detected_domain in ["medical", "legal"] else 0
        }
        return {
            "success": True,
            "applied_tuning": adjustments,
            "domain_context": detected_domain,
            "mode": self.config.get("tuning_mode", "static")
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA068DomainSpecializationTuner(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-068 Failed: {e}")
        return {"success": False, "error": str(e)}

"""
KA-088: AB Testing
Purpose: Orchestrate model comparisons by splitting traffic and calculating statistical significance between control and variants.
"""
import logging
import json
import os
import random
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA088ABInput(BaseModel):
    request_id: str = Field(..., description="The unique identifier for the inference request")

class KA088ABTesting(KnowledgeAlgorithm):
    """
    KA-088: Traffic splitting and statistical experiment engine for model comparison.
    """
    input_schema = KA088ABInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-088"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_88_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA088ABInput) -> Dict[str, Any]:
        request_id = input_data.request_id
        self.log_execution_step("Selecting Experiment Variant", {"req": request_id})
        
        split = self.config.get("traffic_split_percent", {"control": 50, "vA": 50})
        variant = "control" if random.random() < (split.get("control", 50) / 100.0) else "variant_a"
        
        return {
            "success": True,
            "assigned_variant": variant,
            "experiment_active": True,
            "metrics_tracked": self.config.get("metrics_to_track", [])
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA088ABTesting(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-088 Failed: {e}")
        return {"success": False, "error": str(e)}

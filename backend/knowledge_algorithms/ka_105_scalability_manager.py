"""
KA-105: Scalability Manager
Purpose: Manage horizontal and vertical scaling of system resources based on real-time load triggers.
"""
import logging
import json
import os
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA105ScalabilityInput(BaseModel):
    metrics: Dict[str, float] = Field(default_factory=dict, description="Real-time system metrics for scaling evaluation")
    current_replicas: int = Field(2, ge=1, description="The number of currently active service replicas")

class KA105ScalabilityManager(KnowledgeAlgorithm):
    """
    KA-105: Resource scalability and elasticity engine for adaptive infrastructure.
    """
    input_schema = KA105ScalabilityInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-105"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_105_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA105ScalabilityInput) -> Dict[str, Any]:
        metrics = input_data.metrics
        current_replicas = input_data.current_replicas
        self.log_execution_step("Evaluating Scaling Needs", {"metrics": metrics})
        
        triggers = self.config.get("scaling_triggers", {"cpu_threshold": 0.85, "memory_threshold": 0.9})
        needs_scale_up = metrics.get("cpu_usage", 0) > triggers.get("cpu_threshold", 0.85)
        
        target_replicas = current_replicas + 1 if needs_scale_up else current_replicas
        
        return {
            "success": True,
            "scaling_action": "SCALE_UP" if needs_scale_up else "NONE",
            "current_replicas": current_replicas,
            "target_replicas": target_replicas,
            "enabled": self.config.get("auto_scaling_enabled", True),
            "cooldown_active": False
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA105ScalabilityManager(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-105 Failed: {e}")
        return {"success": False, "error": str(e)}

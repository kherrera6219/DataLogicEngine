"""
KA-101: Environment Management
Purpose: Manage system environments, configuration injection, and orchestration provider settings (AWS, K8s).
"""
import logging
import json
import os
import hashlib
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

class KA101EnvInput(BaseModel):
    env: str = Field("dev", description="The target environment (e.g., dev, staging, prod)")

class KA101EnvironmentManagement(KnowledgeAlgorithm):
    """
    KA-101: System environment and provider configuration engine for orchestration.
    """
    input_schema = KA101EnvInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-101"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_101_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA101EnvInput) -> Dict[str, Any]:
        target_env = input_data.env
        self.log_execution_step("Resolving Env Config", {"target": target_env})
        
        env_vars = self.config.get("env_variables", {"LOG_LEVEL": "INFO"})
        
        return {
            "success": True,
            "resolved_env": target_env,
            "provider_active": "Kubernetes",
            "config_checksum": hashlib.sha256(json.dumps(env_vars, sort_keys=True).encode()).hexdigest()[:8],
            "injected_vars_count": len(env_vars)
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA101EnvironmentManagement(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-101 Failed: {e}")
        return {"success": False, "error": str(e)}

import logging
import json
import os
from typing import Dict, Any, List, Optional
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

from core.knowledge_algorithm.exceptions import KAError, KAConfigError

class KA111Input(BaseModel):
    headers: Dict[str, str] = Field(default_factory=dict)
    query: Optional[str] = None

class KA111APIGateway(KnowledgeAlgorithm):
    """
    KA-111: Unified API gateway and request routing engine.
    """
    input_schema = KA111Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-111"
        self.config = self._load_config()

    def _default_config(self) -> Dict[str, Any]:
        return {"auth_provider": "apiKey"}

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_111_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    loaded = json.load(f) or {}
                    return {**self._default_config(), **loaded}
            return self._default_config()
        except Exception:
            return self._default_config()

    def _run_logic(self, input_data: KA111Input) -> Dict[str, Any]:
        headers = input_data.headers
        self.log_execution_step("Authorizing Request", {"origin": headers.get("X-Forwarded-For")})
        
        # Simulate authentication
        if "Authorization" not in headers:
            return {
                "success": False,
                "status_code": 401,
                "gateway_node": "gw-01",
                "error_msg": "Missing Authorization Header",
                "required": "Bearer Token",
            }
        
        return {
            "success": True,
            "status_code": 200,
            "gateway_node": "gw-01",
            "rate_limit_remaining": 99,
            "auth_mode": self.config.get("auth_provider", "apiKey")
        }

    def _fallback_logic(self, input_data: KA111Input, error: Exception) -> Dict[str, Any]:
        """Graceful degradation for the API Gateway."""
        self.logger.warning(f"Fallback engaged for KA-111: {str(error)}")
        return {
            "success": False,
            "status_code": 503,
            "gateway_node": "fallback-static-01",
            "error_msg": "Service temporarily degraded. Using static routing."
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA111APIGateway(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-111 Failed: {e}")
        return {"success": False, "error": str(e)}

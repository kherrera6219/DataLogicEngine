import json
import logging
import os
import re
from typing import Any, Dict, Optional

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA111Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    headers: Dict[str, str] = Field(default_factory=dict)
    query: Optional[str] = None
    path: str = "/"
    method: str = "GET"
    client_id: Optional[str] = None
    request_count: int = 1


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
        return {
            "auth_provider": "apiKey",
            "gateway_node": "gw-local-01",
            "valid_api_keys": ["local-dev-key"],
            "valid_bearer_tokens": ["local-dev-token"],
            "rate_limiting": {"requests_per_second": 100, "burst_limit": 20},
            "routes": {
                "/ka": "ka_orchestrator",
                "/health": "health_service",
                "/search": "retrieval_service",
            },
        }

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
        self.log_execution_step("Authorizing Request", {"origin": headers.get("X-Forwarded-For"), "path": input_data.path})

        auth_result = self._authorize(headers)
        if not auth_result["authorized"]:
            return {
                "success": False,
                "status_code": 401,
                "gateway_node": self.config.get("gateway_node", "gw-local-01"),
                "error_msg": auth_result["reason"],
                "required": auth_result["required"],
            }

        rate_limit = self._rate_limit(input_data)
        if not rate_limit["allowed"]:
            return {
                "success": False,
                "status_code": 429,
                "gateway_node": self.config.get("gateway_node", "gw-local-01"),
                "error_msg": "Rate limit exceeded",
                **rate_limit,
            }

        return {
            "success": True,
            "status_code": 200,
            "gateway_node": self.config.get("gateway_node", "gw-local-01"),
            "rate_limit_remaining": rate_limit["remaining"],
            "rate_limit_policy": rate_limit["policy"],
            "auth_mode": self.config.get("auth_provider", "apiKey"),
            "principal": auth_result["principal"],
            "route_target": self._route(input_data.path),
            "method": input_data.method.upper(),
        }

    def _authorize(self, headers: Dict[str, str]) -> Dict[str, Any]:
        normalized = {key.lower(): value for key, value in headers.items()}
        api_key = normalized.get("x-api-key")
        if api_key and api_key in set(self.config.get("valid_api_keys", [])):
            return {"authorized": True, "principal": f"api_key:{api_key[-4:]}", "required": "API key", "reason": ""}

        authorization = normalized.get("authorization", "")
        bearer_match = re.match(r"Bearer\s+(.+)", authorization, flags=re.IGNORECASE)
        if bearer_match and bearer_match.group(1) in set(self.config.get("valid_bearer_tokens", [])):
            return {"authorized": True, "principal": "bearer:local", "required": "Bearer token", "reason": ""}
        if authorization and self.config.get("auth_provider") == "jwt_plus_oauth2":
            parts = authorization.split()
            if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1].count(".") == 2:
                return {"authorized": True, "principal": "jwt:unsigned-local", "required": "Bearer token", "reason": ""}

        return {
            "authorized": False,
            "principal": None,
            "required": "X-API-Key or Bearer token",
            "reason": "Missing or invalid credentials",
        }

    def _rate_limit(self, input_data: KA111Input) -> Dict[str, Any]:
        policy = self.config.get("rate_limiting", {})
        burst = int(policy.get("burst_limit", policy.get("requests_per_second", 100)))
        used = max(0, int(input_data.request_count or 0))
        remaining = max(0, burst - used)
        return {
            "allowed": used <= burst,
            "remaining": remaining,
            "policy": {"burst_limit": burst, "requests_per_second": int(policy.get("requests_per_second", burst))},
            "client_id": input_data.client_id or input_data.headers.get("X-Forwarded-For", "anonymous"),
        }

    def _route(self, path: str) -> str:
        routes = self.config.get("routes", {})
        for prefix, target in sorted(routes.items(), key=lambda item: len(item[0]), reverse=True):
            if path.startswith(prefix):
                return target
        return "default_service"

    def _fallback_logic(self, input_data: KA111Input, error: Exception) -> Dict[str, Any]:
        """Graceful degradation for the API Gateway."""
        self.logger.warning(f"Fallback engaged for KA-111: {str(error)}")
        return {
            "success": False,
            "status_code": 503,
            "gateway_node": "fallback-static-01",
            "error_msg": "Service temporarily degraded. Using static routing.",
        }


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA111APIGateway(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-111 Failed: {e}")
        return {"success": False, "error": str(e)}

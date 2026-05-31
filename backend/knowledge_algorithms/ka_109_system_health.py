"""
KA-109: System Health
Purpose: Continuously monitor system liveness and readiness, aggregating health states from multiple sub-services.
"""
import logging
import json
import os
import shutil
import time
from pathlib import Path
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA109HealthInput(BaseModel):
    check_mode: str = Field("standard", description="The health check mode (e.g., standard, deep, liveness)")

class KA109SystemHealth(KnowledgeAlgorithm):
    """
    KA-109: System health monitoring and status aggregation engine for enterprise observability.
    """
    input_schema = KA109HealthInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-109"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_109_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA109HealthInput) -> Dict[str, Any]:
        self.log_execution_step("Aggregating System Health", {"mode": input_data.check_mode})
        
        endpoints = self.config.get("health_endpoints", ["db_svc", "mcp_gateway", "ka_master"])
        component_health = {
            "python_runtime": self._check_python_runtime(),
            "filesystem": self._check_filesystem(),
            "ka_registry": self._check_ka_registry(),
        }
        if input_data.check_mode in {"deep", "readiness"}:
            component_health["disk_space"] = self._check_disk_space()
        for endpoint in endpoints:
            component_health[f"configured_endpoint:{endpoint}"] = {
                "status": "configured",
                "detail": "Endpoint is configured for external health polling; KA-109 local check does not perform network calls.",
            }
        unhealthy = {
            name: status
            for name, status in component_health.items()
            if status.get("status") not in {"ok", "configured"}
        }
        overall_status = "HEALTHY" if not unhealthy else "DEGRADED"
        
        return {
            "success": True,
            "overall_status": overall_status,
            "sub_component_health": component_health,
            "liveness_verified": component_health["python_runtime"]["status"] == "ok",
            "readiness_verified": not unhealthy,
            "uptime_seconds": round(time.monotonic(), 3),
        }

    @staticmethod
    def _check_python_runtime() -> Dict[str, Any]:
        return {"status": "ok", "detail": "Python runtime responsive"}

    @staticmethod
    def _check_filesystem() -> Dict[str, Any]:
        cwd = Path.cwd()
        return {
            "status": "ok" if cwd.exists() and os.access(cwd, os.R_OK) else "degraded",
            "path": str(cwd),
            "readable": os.access(cwd, os.R_OK),
            "writable": os.access(cwd, os.W_OK),
        }

    @staticmethod
    def _check_ka_registry() -> Dict[str, Any]:
        registry = Path(__file__).with_name("ka_registry.yaml")
        return {
            "status": "ok" if registry.exists() else "degraded",
            "path": str(registry),
            "exists": registry.exists(),
        }

    @staticmethod
    def _check_disk_space() -> Dict[str, Any]:
        usage = shutil.disk_usage(Path.cwd())
        free_ratio = usage.free / usage.total if usage.total else 0
        return {
            "status": "ok" if free_ratio >= 0.05 else "degraded",
            "free_bytes": usage.free,
            "total_bytes": usage.total,
            "free_ratio": round(free_ratio, 4),
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA109SystemHealth(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-109 Failed: {e}")
        return {"success": False, "error": str(e)}

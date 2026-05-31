"""
KA-083: Model Deployment
Purpose: Orchestrate model deployments using canary or blue-green strategies with rollback logic.
"""
import hashlib
import json
import logging
import os
from typing import Any, Dict

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA083DeploymentInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    version: str = Field("v1.0.0", description="The version of the model to deploy")
    env: str = Field("staging", description="The target environment")
    health_signals: Dict[str, Any] = Field(default_factory=dict)
    current_version: str | None = None


class KA083ModelDeployment(KnowledgeAlgorithm):
    """
    KA-083: Model deployment and canary orchestration engine.
    """
    input_schema = KA083DeploymentInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-083"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_83_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA083DeploymentInput) -> Dict[str, Any]:
        self.log_execution_step("Planning Model Deployment", {"version": input_data.version, "env": input_data.env})
        allowed_envs = set(self.config.get("target_environments", ["staging", "production"]))
        health = self._health(input_data.health_signals)
        strategy = self.config.get("deployment_strategy", "recreate")
        valid_env = input_data.env in allowed_envs
        rollback = bool(self.config.get("rollback_on_failure", True) and not health["healthy"])
        return {
            "success": valid_env and health["healthy"],
            "deployment_id": self._deployment_id(input_data.version, input_data.env),
            "applied_strategy": strategy,
            "steps_completed": self._steps(strategy, input_data.env),
            "status": "INVALID_ENVIRONMENT" if not valid_env else "ROLLBACK_RECOMMENDED" if rollback else "LIVE" if input_data.env == "production" else "STAGED",
            "health_assessment": health,
            "rollback_plan": self._rollback_plan(input_data.current_version) if rollback else None,
        }

    def _health(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        failures = self._safe_int(signals.get("failures_per_hour"), 0)
        latency = self._safe_int(signals.get("p95_latency_ms"), 0)
        threshold = self._safe_int(self.config.get("failure_threshold_per_hour", 5), 5)
        healthy = failures <= threshold and latency < self._safe_int(signals.get("latency_threshold_ms"), 5000)
        return {"healthy": healthy, "failures_per_hour": failures, "p95_latency_ms": latency, "failure_threshold": threshold}

    def _steps(self, strategy: str, env: str) -> list[str]:
        steps = ["Pre-flight validation", "Artifact verification", f"Deploy to {env}"]
        if strategy == "canary":
            steps.append(f"Route {self.config.get('canary_percent', 10)}% canary traffic")
        elif strategy == "blue_green":
            steps.append("Switch blue-green target after health gate")
        steps.append("Health gate evaluation")
        return steps

    @staticmethod
    def _rollback_plan(current_version: str | None) -> Dict[str, Any]:
        return {"target_version": current_version or "previous_stable", "action": "restore_previous_artifact_and_routes"}

    @staticmethod
    def _deployment_id(version: str, env: str) -> str:
        return f"dep_{hashlib.sha256(f'{version}:{env}'.encode()).hexdigest()[:10]}"

    @staticmethod
    def _safe_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return int(default)


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA083ModelDeployment(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-083 Failed: {e}")
        return {"success": False, "error": str(e)}

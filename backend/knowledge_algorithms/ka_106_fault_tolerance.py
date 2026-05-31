"""
KA-106: Fault Tolerance
Purpose: Implement circuit breakers, retry strategies, and graceful degradation to ensure system reliability under stress.
"""
import json
import logging
import os
from typing import Any, Dict

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA106FaultInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    operation: str = Field("generic", description="The operation to apply fault tolerance policies to")
    failures: int = 0
    successes: int = 0
    latency_ms: Any = None
    last_failure_age_s: Any = None
    dependency_status: Dict[str, str] = Field(default_factory=dict)


class KA106FaultTolerance(KnowledgeAlgorithm):
    """
    KA-106: System reliability and fault tolerance engine with resilience patterns.
    """
    input_schema = KA106FaultInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-106"
        self.config = self._load_config()

    def _default_config(self) -> Dict[str, Any]:
        return {
            "circuit_breakers": {
                "default": {"failure_percent": 50, "reset_timeout": 30, "minimum_samples": 3},
                "payment_gateway": {"failure_percent": 50, "reset_timeout": 30, "minimum_samples": 3},
            },
            "retry_strategies": {
                "network": {"attempts": 3, "backoff": "exponential"},
                "database": {"attempts": 2, "backoff": "fixed"},
            },
            "graceful_degradation_enabled": True,
        }

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_106_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    loaded = json.load(f) or {}
                    return {**self._default_config(), **loaded}
            return self._default_config()
        except Exception:
            return self._default_config()

    def _run_logic(self, input_data: KA106FaultInput) -> Dict[str, Any]:
        target_op = input_data.operation
        self.log_execution_step("Enforcing Reliability Policies", {"op": target_op})

        circuit_breakers = self.config.get("circuit_breakers", {})
        breaker_config = circuit_breakers.get(target_op, circuit_breakers.get("default", {}))
        status, reason = self._determine_circuit_state(input_data, breaker_config)
        retry_policy = self._select_retry_policy(target_op)
        degraded_dependencies = {
            name: state
            for name, state in input_data.dependency_status.items()
            if str(state).upper() not in {"OK", "HEALTHY"}
        }
        fallback_engaged = status == "OPEN" or bool(degraded_dependencies)

        return {
            "success": True,
            "circuit_state": status,
            "circuit_reason": reason,
            "retry_policy_applied": retry_policy,
            "graceful_degradation_active": self.config.get("graceful_degradation_enabled", True),
            "fallback_engaged": fallback_engaged,
            "degraded_dependencies": degraded_dependencies,
            "failure_rate": self._failure_rate(input_data.failures, input_data.successes),
        }

    def _determine_circuit_state(self, input_data: KA106FaultInput, breaker_config: Any) -> tuple[str, str]:
        if isinstance(breaker_config, str):
            state = breaker_config.upper()
            return state if state in {"OPEN", "CLOSED", "HALF_OPEN"} else "CLOSED", "configured_state"

        config = breaker_config if isinstance(breaker_config, dict) else {}
        threshold = float(config.get("failure_percent", 50)) / 100.0
        minimum_samples = int(config.get("minimum_samples", 3))
        reset_timeout = int(config.get("reset_timeout", 30))
        total = input_data.failures + input_data.successes
        failure_rate = self._failure_rate(input_data.failures, input_data.successes)

        latency_ms = self._safe_int(input_data.latency_ms)
        last_failure_age_s = self._safe_int(input_data.last_failure_age_s)
        if latency_ms and latency_ms >= int(config.get("latency_threshold_ms", 10000)):
            return "OPEN", "latency_threshold_exceeded"
        if total >= minimum_samples and failure_rate >= threshold:
            if last_failure_age_s is not None and last_failure_age_s >= reset_timeout:
                return "HALF_OPEN", "reset_timeout_elapsed"
            return "OPEN", "failure_rate_threshold_exceeded"
        return "CLOSED", "within_policy"

    def _select_retry_policy(self, operation: str) -> Dict[str, Any]:
        strategies = self.config.get("retry_strategies", {})
        policy = strategies.get(operation) or strategies.get("network") or {"attempts": 3, "backoff": "exponential"}
        if isinstance(policy, str):
            return {"name": policy, "attempts": 3, "backoff": policy}
        return dict(policy)

    @staticmethod
    def _failure_rate(failures: int, successes: int) -> float:
        total = max(0, failures) + max(0, successes)
        return round(max(0, failures) / total, 4) if total else 0.0

    @staticmethod
    def _safe_int(value: Any, default: int | None = None) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _fallback_logic(self, input_data: KA106FaultInput, error: Exception) -> Dict[str, Any]:
        """Failsafe: Force open circuits if the fault tolerance engine itself is failing."""
        self.logger.critical(f"Fault Tolerance ENGINE FAILURE: {str(error)}")
        return {
            "success": False,
            "circuit_state": "OPEN",
            "retry_policy_applied": {"name": "IMMEDIATE_STOP", "attempts": 0, "backoff": "none"},
            "fallback_engaged": True,
            "error_msg": "Emergency circuit break triggered by engine failure.",
        }


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    algo = KA106FaultTolerance(context)
    return algo.run(context)

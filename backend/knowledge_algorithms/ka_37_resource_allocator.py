"""
KA-037: Resource Allocator
Purpose: Allocate compute/token resources.
"""
import json
import logging
import os
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA037Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    priority: str = "normal"
    task_type: str = "general"
    complexity: str | float | int = "medium"
    input_size: int = 0
    expected_steps: int = 1
    latency_target_ms: Any = None


class KA037ResourceAllocator(KnowledgeAlgorithm):
    input_schema = KA037Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-037"
        self.config = self._load_config()

    def _default_config(self) -> Dict[str, Any]:
        return {
            "base_token_budget": 1200,
            "min_token_budget": 500,
            "max_token_budget": 12000,
            "base_timeout_ms": 4000,
            "max_timeout_ms": 30000,
            "priority_multipliers": {"low": 0.7, "normal": 1.0, "high": 2.2, "critical": 3.0},
            "task_multipliers": {
                "general": 1.0,
                "retrieval": 1.2,
                "reasoning": 1.6,
                "summarization": 1.3,
                "analysis": 1.8,
                "orchestration": 2.0,
            },
        }

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_37_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    loaded = json.load(f) or {}
                return {**self._default_config(), **loaded}
        except Exception:
            logger.debug("KA-037 config load failed; using defaults", exc_info=True)
        return self._default_config()

    def _run_logic(self, input_data: KA037Input) -> Dict[str, Any]:
        input_dict = input_data.model_dump()
        priority = str(input_data.priority or "normal").lower()
        task_type = str(input_data.task_type or "general").lower()
        complexity_score = self._complexity_score(input_data.complexity)
        input_size = max(0, int(input_data.input_size or len(str(input_dict.get("text", "") or input_dict.get("query", "")))))
        expected_steps = max(1, int(input_data.expected_steps or 1))
        
        self.log_execution_step(
            "Allocating",
            {
                "priority": priority,
                "task_type": task_type,
                "complexity": complexity_score,
                "input_size": input_size,
                "expected_steps": expected_steps,
            },
        )

        priority_multiplier = self.config["priority_multipliers"].get(priority, 1.0)
        task_multiplier = self.config["task_multipliers"].get(task_type, 1.0)
        size_tokens = min(4000, input_size // 4)
        step_tokens = (expected_steps - 1) * 350
        raw_budget = (
            self.config["base_token_budget"] * priority_multiplier * task_multiplier * complexity_score
            + size_tokens
            + step_tokens
        )
        token_budget = self._clamp_int(raw_budget, self.config["min_token_budget"], self.config["max_token_budget"])

        timeout_ms = self._clamp_int(
            self.config["base_timeout_ms"] * priority_multiplier * complexity_score + expected_steps * 750,
            1000,
            self.config["max_timeout_ms"],
        )
        latency_target_ms = self._safe_int(input_data.latency_target_ms)
        if latency_target_ms:
            timeout_ms = min(timeout_ms, max(500, latency_target_ms))

        queue = "interactive"
        if priority in {"high", "critical"} or input_data.latency_target_ms:
            queue = "priority"
        elif complexity_score >= 1.5 or expected_steps >= 5:
            queue = "batch"

        return {
            "ka_id": "KA-037",
            "success": True,
            "token_budget": token_budget,
            "timeout_ms": timeout_ms,
            "execution_queue": queue,
            "allocation_factors": {
                "priority_multiplier": priority_multiplier,
                "task_multiplier": task_multiplier,
                "complexity_score": complexity_score,
                "input_size": input_size,
                "expected_steps": expected_steps,
            },
        }

    @staticmethod
    def _complexity_score(value: str | float | int) -> float:
        if isinstance(value, (int, float)):
            return max(0.5, min(3.0, float(value)))
        lookup = {"low": 0.75, "medium": 1.0, "normal": 1.0, "high": 1.6, "complex": 2.0, "critical": 2.4}
        return lookup.get(str(value).lower(), 1.0)

    @staticmethod
    def _clamp_int(value: float, minimum: int, maximum: int) -> int:
        return max(minimum, min(maximum, int(round(value))))

    @staticmethod
    def _safe_int(value: Any, default: int | None = None) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA037ResourceAllocator(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-037 Failed: {e}")
        return {"success": False, "error": str(e)}



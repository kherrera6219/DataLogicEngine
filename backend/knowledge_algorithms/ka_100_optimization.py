"""KA-100: deterministic runtime optimization recommendation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.knowledge_algorithms.production_utils import (
    load_config,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA100OptimizationInput(BaseModel):
    load_profile: float = Field(default=0.5, ge=0.0, le=1.0)
    current_worker_limit: int = Field(default=8, ge=1, le=1_024)


class KA100Optimization(KnowledgeAlgorithm):
    """Recommend bounded tuning without mutating the runtime."""

    input_schema = KA100OptimizationInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-100"
        self.config = load_config(__file__, "ka_100_config.json")

    def _run_logic(self, input_data: KA100OptimizationInput) -> dict[str, Any]:
        if input_data.load_profile >= 0.8:
            action = "review_capacity_increase"
            recommended_worker_limit = min(input_data.current_worker_limit + 2, 1_024)
        elif input_data.load_profile <= 0.2 and input_data.current_worker_limit > 2:
            action = "review_capacity_decrease"
            recommended_worker_limit = max(input_data.current_worker_limit - 1, 2)
        else:
            action = "retain_current_capacity"
            recommended_worker_limit = input_data.current_worker_limit
        recommendation = {
            "target": self.config.get("optimization_target", "latency"),
            "action": action,
            "observed_load_profile": input_data.load_profile,
            "current_worker_limit": input_data.current_worker_limit,
            "recommended_worker_limit": recommended_worker_limit,
        }
        return {
            "success": True,
            "recommendation_id": stable_identifier("optimization", recommendation),
            "recommendation": recommendation,
            "optimization_applied": False,
            "operations_applied": [],
            "measured_resources_reclaimed": None,
            "limitations": (
                "KA-100 recommends capacity settings; it does not change thread "
                "pools, enable JIT compilation, run garbage collection, or claim "
                "reclaimed resources."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA100Optimization(context).run(context)

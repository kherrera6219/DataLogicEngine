"""
KA-059: Predictive Layer Preemption
Purpose: Skip unneeded layers or KAs for simple or low-complexity queries to optimize performance and reduce latency.
"""

import json
import logging
import os
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA059Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    complexity_tier: str = Field(
        "medium", description="The detected complexity tier of the query"
    )
    budget: float = Field(1.0, ge=0, le=1)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA059PredictiveLayerPreemption(KnowledgeAlgorithm):
    """
    KA-059: Fast-path routing and layer skipping engine for performance optimization.
    """

    input_schema = KA059Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-059"
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        try:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "ka_59_config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return {}

    def _run_logic(self, input_data: KA059Input) -> dict[str, Any]:
        dependencies = input_data.dependency_results
        complexity_tier = str(
            dependencies.get("KA-113", {}).get("complexity_tier")
            or input_data.complexity_tier
        ).lower()
        self.log_execution_step(
            "Executing Layer Preemption Check", {"tier": complexity_tier}
        )

        proposed_skips = []
        fast_path = False
        for rule in self.config.get("preemption_rules", []):
            if rule.get("complexity") == complexity_tier:
                proposed_skips = [str(value) for value in rule.get("skip_layers", [])]
                fast_path = True
                break
        protected_layers = {"L6", "L7", "L8", "L9", "L10"}
        blocked_skips = sorted(set(proposed_skips) & protected_layers)

        return {
            "success": True,
            "fast_path_recommended": fast_path,
            "proposed_skipped_layers": proposed_skips,
            "blocked_safety_layers": blocked_skips,
            "skipped_layers": [],
            "routing_hint": "REVIEW_FAST_PATH" if fast_path else "FULL_PIPELINE",
            "dependencies_consumed": sorted(dependencies),
            "preemption_applied": False,
            "deterministic": True,
            "limitations": (
                "This is an advisory latency proposal. It cannot skip validation, "
                "policy, convergence, or release layers and applies no routing "
                "mutation."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA059PredictiveLayerPreemption(context).run(context)

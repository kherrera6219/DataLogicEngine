"""KA-1097: deterministic system performance tuning proposals."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.knowledge_algorithms.production_utils import stable_identifier
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class PerformanceMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component_id: str = Field(min_length=1, max_length=200)
    metric: Literal["latency_ms", "error_rate", "queue_depth", "memory_mb"]
    observed: float = Field(ge=0)
    target_maximum: float = Field(gt=0)
    current_setting: float = Field(gt=0)
    minimum_setting: float = Field(gt=0)
    maximum_setting: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_setting_bounds(self) -> PerformanceMetric:
        if not self.minimum_setting <= self.current_setting <= self.maximum_setting:
            raise ValueError("current setting must be within declared bounds")
        return self


class KA1097Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "metrics": [
                        {
                            "component_id": "retrieval",
                            "metric": "latency_ms",
                            "observed": 200,
                            "target_maximum": 100,
                            "current_setting": 4,
                            "minimum_setting": 1,
                            "maximum_setting": 8,
                        }
                    ],
                    "maximum_adjustment_ratio": 0.25,
                }
            ]
        },
    )

    metrics: list[PerformanceMetric] = Field(min_length=1, max_length=10_000)
    maximum_adjustment_ratio: float = Field(default=0.25, gt=0, le=1)

    @model_validator(mode="after")
    def validate_metric_identity(self) -> KA1097Input:
        identities = [(item.component_id, item.metric) for item in self.metrics]
        if len(identities) != len(set(identities)):
            raise ValueError("component/metric pairs must be unique")
        return self


class KA1097SystemPerformanceOptimizer(KnowledgeAlgorithm):
    """Propose bounded setting changes from declared budget overruns."""

    input_schema = KA1097Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1097"

    def _run_logic(self, input_data: KA1097Input) -> dict[str, Any]:
        proposals = []
        for item in sorted(
            input_data.metrics,
            key=lambda row: (row.component_id, row.metric),
        ):
            overrun_ratio = max(item.observed / item.target_maximum - 1, 0)
            adjustment_ratio = min(
                overrun_ratio,
                input_data.maximum_adjustment_ratio,
            )
            proposed = min(
                item.current_setting * (1 + adjustment_ratio),
                item.maximum_setting,
            )
            proposals.append(
                {
                    "component_id": item.component_id,
                    "metric": item.metric,
                    "budget_met": item.observed <= item.target_maximum,
                    "overrun_ratio": round(overrun_ratio, 8),
                    "current_setting": item.current_setting,
                    "proposed_setting": round(proposed, 8),
                }
            )
        effect_proposals = [
            {
                "effect_id": stable_identifier(
                    "performance-setting",
                    {
                        "component_id": item["component_id"],
                        "metric": item["metric"],
                        "proposed_setting": item["proposed_setting"],
                    },
                ),
                "kind": "apply_performance_setting_canary",
                "status": "proposed",
                "service": "operations_control_service",
                "payload": item,
            }
            for item in proposals
            if not item["budget_met"]
            and item["proposed_setting"] != item["current_setting"]
        ]
        return {
            "success": True,
            "status": "system_performance_tuning_proposed",
            "proposals": proposals,
            "settings_applied": 0,
            "effect_proposals": effect_proposals,
            "authoritative_receipts": [],
            "measurement_status": "caller_supplied",
            "deterministic": True,
            "limitations": (
                "Proposals use caller-supplied measurements and monotonic setting "
                "assumptions. OperationsControlService must apply and receipt a "
                "separately authorized canary before any setting change."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1097SystemPerformanceOptimizer(context).run(context)

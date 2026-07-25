"""KA-1080: transparent bounded simulation resource-cost estimation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class SimulationStepEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    step_id: str = Field(min_length=1, max_length=200)
    iterations: int = Field(ge=1, le=1_000_000)
    estimated_ms_per_iteration: float = Field(ge=0, le=3_600_000)
    estimated_tokens_per_iteration: int = Field(ge=0, le=10_000_000)
    estimated_peak_memory_mb: float = Field(ge=0, le=10_000_000)
    estimated_cost_per_iteration: float = Field(
        default=0,
        ge=0,
        le=1_000_000,
    )


class KA1080Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "planned_steps": [
                        {
                            "step_id": "scenario",
                            "iterations": 10,
                            "estimated_ms_per_iteration": 50,
                            "estimated_tokens_per_iteration": 100,
                            "estimated_peak_memory_mb": 256,
                        }
                    ],
                    "contingency_ratio": 0.2,
                }
            ]
        },
    )

    planned_steps: list[SimulationStepEstimate] = Field(
        min_length=1,
        max_length=1_000,
    )
    contingency_ratio: float = Field(default=0.2, ge=0, le=5)


class KA1080SimulationCostEstimator(KnowledgeAlgorithm):
    """Aggregate caller-supplied unit estimates without claiming measurement."""

    input_schema = KA1080Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1080"

    def _run_logic(self, input_data: KA1080Input) -> dict[str, Any]:
        base_duration = sum(
            item.iterations * item.estimated_ms_per_iteration
            for item in input_data.planned_steps
        )
        base_tokens = sum(
            item.iterations * item.estimated_tokens_per_iteration
            for item in input_data.planned_steps
        )
        base_cost = sum(
            item.iterations * item.estimated_cost_per_iteration
            for item in input_data.planned_steps
        )
        multiplier = 1 + input_data.contingency_ratio
        return {
            "success": True,
            "status": "simulation_cost_estimated",
            "estimate": {
                "duration_ms": round(base_duration * multiplier, 4),
                "tokens": int(base_tokens * multiplier),
                "cost_units": round(base_cost * multiplier, 8),
                "peak_memory_mb": max(
                    item.estimated_peak_memory_mb for item in input_data.planned_steps
                ),
                "step_count": len(input_data.planned_steps),
                "contingency_ratio": input_data.contingency_ratio,
            },
            "measurement_status": "caller_supplied_estimate",
            "limitations": (
                "Results are arithmetic projections over supplied unit "
                "estimates, not measured runtime, provider billing, or a "
                "capacity guarantee."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1080SimulationCostEstimator(context).run(context)

"""KA-105: bounded scaling recommendation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA105ScalabilityInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "cpu_utilization": 0.8,
                    "memory_utilization": 0.5,
                    "cpu_scale_up_threshold": 0.75,
                    "memory_scale_up_threshold": 0.8,
                    "scale_down_threshold": 0.25,
                    "current_replicas": 2,
                    "minimum_replicas": 1,
                    "maximum_replicas": 5,
                    "cooldown_elapsed": True,
                }
            ]
        },
    )

    cpu_utilization: float = Field(ge=0, le=1)
    memory_utilization: float = Field(ge=0, le=1)
    cpu_scale_up_threshold: float = Field(gt=0, le=1)
    memory_scale_up_threshold: float = Field(gt=0, le=1)
    scale_down_threshold: float = Field(ge=0, lt=1)
    current_replicas: int = Field(ge=1, le=10_000)
    minimum_replicas: int = Field(ge=1, le=10_000)
    maximum_replicas: int = Field(ge=1, le=10_000)
    cooldown_elapsed: bool

    @model_validator(mode="after")
    def validate_bounds(self) -> KA105ScalabilityInput:
        if not self.minimum_replicas <= self.current_replicas <= self.maximum_replicas:
            raise ValueError("current replicas must be within declared bounds")
        if self.minimum_replicas > self.maximum_replicas:
            raise ValueError("minimum replicas must not exceed maximum replicas")
        if self.scale_down_threshold >= min(
            self.cpu_scale_up_threshold, self.memory_scale_up_threshold
        ):
            raise ValueError("scale-down threshold must be below scale-up thresholds")
        return self


class KA105ScalabilityManager(KnowledgeAlgorithm):
    """Recommend a single bounded replica change without applying it."""

    input_schema = KA105ScalabilityInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-105"

    def _run_logic(self, input_data: KA105ScalabilityInput) -> dict[str, Any]:
        target = input_data.current_replicas
        reason = "within_thresholds"
        if not input_data.cooldown_elapsed:
            reason = "cooldown_active"
        elif (
            input_data.cpu_utilization >= input_data.cpu_scale_up_threshold
            or input_data.memory_utilization >= input_data.memory_scale_up_threshold
        ):
            target = min(input_data.current_replicas + 1, input_data.maximum_replicas)
            reason = "scale_up_threshold_reached"
        elif (
            input_data.cpu_utilization <= input_data.scale_down_threshold
            and input_data.memory_utilization <= input_data.scale_down_threshold
        ):
            target = max(input_data.current_replicas - 1, input_data.minimum_replicas)
            reason = "scale_down_threshold_reached"
        return {
            "success": True,
            "status": "scaling_recommendation_created",
            "current_replicas": input_data.current_replicas,
            "recommended_replicas": target,
            "recommendation": (
                "scale_up"
                if target > input_data.current_replicas
                else "scale_down"
                if target < input_data.current_replicas
                else "hold"
            ),
            "reason": reason,
            "scaling_applied": False,
            "measurement_status": "caller_supplied",
            "deterministic": True,
            "limitations": (
                "The recommendation assumes supplied utilization is authoritative; "
                "OperationsControlService owns any scaling action."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA105ScalabilityManager(context).run(context)

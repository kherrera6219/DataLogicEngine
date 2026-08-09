"""KA-138: deterministic bounded health-trend projection."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class HealthSeries(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component_id: str = Field(min_length=1, max_length=200)
    metric: str = Field(min_length=1, max_length=200)
    values: list[float] = Field(min_length=2, max_length=100_000)
    warning_threshold: float
    critical_threshold: float

    @model_validator(mode="after")
    def validate_thresholds(self) -> HealthSeries:
        if self.critical_threshold <= self.warning_threshold:
            raise ValueError("critical threshold must exceed warning threshold")
        return self


class KA138Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "series": [
                        {
                            "component_id": "worker",
                            "metric": "queue_depth",
                            "values": [10, 20, 30],
                            "warning_threshold": 35,
                            "critical_threshold": 50,
                        }
                    ],
                    "forecast_steps": 2,
                }
            ]
        },
    )

    series: list[HealthSeries] = Field(min_length=1, max_length=10_000)
    forecast_steps: int = Field(default=1, ge=1, le=1_000)

    @model_validator(mode="after")
    def validate_series_keys(self) -> KA138Input:
        keys = [(item.component_id, item.metric) for item in self.series]
        if len(keys) != len(set(keys)):
            raise ValueError("component and metric pairs must be unique")
        return self


class KA138PredictiveHealth(KnowledgeAlgorithm):
    """Project a least-squares trend without claiming live health telemetry."""

    input_schema = KA138Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-138"

    def _run_logic(self, input_data: KA138Input) -> dict[str, Any]:
        forecasts = []
        for item in sorted(
            input_data.series, key=lambda row: (row.component_id, row.metric)
        ):
            count = len(item.values)
            x_mean = (count - 1) / 2
            y_mean = sum(item.values) / count
            denominator = sum((index - x_mean) ** 2 for index in range(count))
            slope = (
                sum(
                    (index - x_mean) * (value - y_mean)
                    for index, value in enumerate(item.values)
                )
                / denominator
            )
            projected = y_mean + slope * (
                count - 1 + input_data.forecast_steps - x_mean
            )
            classification = (
                "critical"
                if projected >= item.critical_threshold
                else "warning"
                if projected >= item.warning_threshold
                else "nominal"
            )
            forecasts.append(
                {
                    "component_id": item.component_id,
                    "metric": item.metric,
                    "trend_per_step": round(slope, 8),
                    "projected_value": round(projected, 8),
                    "classification": classification,
                }
            )
        return {
            "success": True,
            "status": "predictive_health_projected",
            "forecasts": forecasts,
            "measurement_status": "caller_supplied",
            "actions_applied": 0,
            "deterministic": True,
            "limitations": (
                "Linear projection is not a calibrated failure probability and "
                "does not replace live monitoring or component diagnostics."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA138PredictiveHealth(context).run(context)

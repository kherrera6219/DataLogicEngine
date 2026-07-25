"""KA-1082: deterministic confidence-series drift measurement."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ConfidenceObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observed_at: datetime
    confidence: float = Field(ge=0, le=1)


class ConfidenceSeries(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_id: str = Field(min_length=1, max_length=200)
    observations: list[ConfidenceObservation] = Field(min_length=2, max_length=10_000)

    @model_validator(mode="after")
    def validate_timestamps(self) -> ConfidenceSeries:
        timestamps = [item.observed_at for item in self.observations]
        if len(timestamps) != len(set(timestamps)):
            raise ValueError("observation timestamps must be unique")
        return self


class KA1082Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "series": [
                        {
                            "knowledge_id": "knowledge-1",
                            "observations": [
                                {
                                    "observed_at": "2026-01-01T00:00:00Z",
                                    "confidence": 0.9,
                                },
                                {
                                    "observed_at": "2026-02-01T00:00:00Z",
                                    "confidence": 0.7,
                                },
                            ],
                        }
                    ],
                    "degradation_threshold": 0.1,
                }
            ]
        },
    )

    series: list[ConfidenceSeries] = Field(min_length=1, max_length=5_000)
    degradation_threshold: float = Field(default=0.1, ge=0, le=1)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1082Input:
        identifiers = [item.knowledge_id for item in self.series]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("knowledge IDs must be unique")
        return self


class KA1082ConfidenceDriftMonitor(KnowledgeAlgorithm):
    """Measure net degradation and maximum drawdown in supplied observations."""

    input_schema = KA1082Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1082"

    def _run_logic(self, input_data: KA1082Input) -> dict[str, Any]:
        measurements = []
        for series in sorted(input_data.series, key=lambda item: item.knowledge_id):
            ordered = sorted(series.observations, key=lambda item: item.observed_at)
            first = ordered[0].confidence
            last = ordered[-1].confidence
            peak = ordered[0].confidence
            maximum_drawdown = 0.0
            for observation in ordered:
                peak = max(peak, observation.confidence)
                maximum_drawdown = max(
                    maximum_drawdown,
                    peak - observation.confidence,
                )
            net_change = last - first
            measurements.append(
                {
                    "knowledge_id": series.knowledge_id,
                    "first_confidence": first,
                    "latest_confidence": last,
                    "net_change": round(net_change, 8),
                    "maximum_drawdown": round(maximum_drawdown, 8),
                    "degradation_detected": (
                        -net_change >= input_data.degradation_threshold
                        or maximum_drawdown >= input_data.degradation_threshold
                    ),
                    "observation_count": len(ordered),
                }
            )
        return {
            "success": True,
            "status": "confidence_drift_measured",
            "measurements": measurements,
            "measurement_status": "observational",
            "deterministic": True,
            "limitations": (
                "Confidence changes are observational and do not establish the "
                "cause or correctness of any confidence value."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1082ConfidenceDriftMonitor(context).run(context)

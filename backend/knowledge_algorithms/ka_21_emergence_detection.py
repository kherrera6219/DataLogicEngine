"""KA-021: deterministic detection of measured emergence candidates."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class EmergenceObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation_id: str = Field(min_length=1, max_length=200)
    metric_name: str = Field(min_length=1, max_length=200)
    baseline_value: float
    observed_value: float
    tolerance: float = Field(ge=0)
    corroborating_trace_ids: list[str] = Field(default_factory=list, max_length=1_000)


class KA021Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "observations": [
                        {
                            "observation_id": "obs-1",
                            "metric_name": "plan_conflict_rate",
                            "baseline_value": 0.1,
                            "observed_value": 0.5,
                            "tolerance": 0.2,
                            "corroborating_trace_ids": ["trace-1", "trace-2"],
                        }
                    ]
                }
            ]
        },
    )

    observations: list[EmergenceObservation] = Field(min_length=1, max_length=20_000)

    @model_validator(mode="after")
    def validate_ids(self) -> KA021Input:
        identifiers = [item.observation_id for item in self.observations]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("observation IDs must be unique")
        return self


class KA021EmergenceDetection(KnowledgeAlgorithm):
    """Flag corroborated deviations without claiming causal novelty."""

    input_schema = KA021Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-021"

    def _run_logic(self, input_data: KA021Input) -> dict[str, Any]:
        candidates = []
        for item in sorted(input_data.observations, key=lambda row: row.observation_id):
            deviation = abs(item.observed_value - item.baseline_value)
            traces = sorted(set(item.corroborating_trace_ids))
            if deviation > item.tolerance and traces:
                candidates.append(
                    {
                        "observation_id": item.observation_id,
                        "metric_name": item.metric_name,
                        "absolute_deviation": round(deviation, 8),
                        "tolerance": item.tolerance,
                        "corroborating_trace_ids": traces,
                        "proposed_action": "owner_review",
                    }
                )
        return {
            "success": True,
            "status": "emergence_candidates_assessed",
            "is_emergent": bool(candidates),
            "emergence_candidates": candidates,
            "emergence_established": False,
            "actions_applied": 0,
            "deterministic": True,
            "limitations": (
                "A threshold deviation is only a review candidate. This does not "
                "establish novelty, causation, or an emergent system property."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA021EmergenceDetection(context).run(context)

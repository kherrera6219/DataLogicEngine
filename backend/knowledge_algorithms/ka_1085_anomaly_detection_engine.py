"""KA-1085: deterministic z-score analysis of reasoning/output features."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class FeatureBaseline(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    feature: str = Field(min_length=1, max_length=200)
    mean: float
    standard_deviation: float = Field(gt=0)
    warning_z: float = Field(default=3, gt=0, le=100)


class ReasoningObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    observation_id: str = Field(min_length=1, max_length=200)
    features: dict[str, float] = Field(min_length=1, max_length=200)


class KA1085Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "baselines": [
                        {
                            "feature": "reasoning_steps",
                            "mean": 10,
                            "standard_deviation": 2,
                        }
                    ],
                    "observations": [
                        {
                            "observation_id": "run-1",
                            "features": {"reasoning_steps": 20},
                        }
                    ],
                }
            ]
        },
    )

    baselines: list[FeatureBaseline] = Field(
        min_length=1,
        max_length=200,
    )
    observations: list[ReasoningObservation] = Field(
        min_length=1,
        max_length=10_000,
    )

    @model_validator(mode="after")
    def validate_features(self) -> KA1085Input:
        names = [item.feature for item in self.baselines]
        if len(names) != len(set(names)):
            raise ValueError("baseline feature names must be unique")
        expected = set(names)
        observation_ids = [item.observation_id for item in self.observations]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("observation IDs must be unique")
        if any(set(item.features) != expected for item in self.observations):
            raise ValueError("observation features must match baselines")
        return self


class KA1085AnomalyDetectionEngine(KnowledgeAlgorithm):
    """Flag supplied feature deviations without causal interpretation."""

    input_schema = KA1085Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1085"

    def _run_logic(self, input_data: KA1085Input) -> dict[str, Any]:
        baselines = {item.feature: item for item in input_data.baselines}
        evaluated = []
        for observation in sorted(
            input_data.observations,
            key=lambda item: item.observation_id,
        ):
            deviations = [
                {
                    "feature": feature,
                    "value": value,
                    "z_score": round(
                        (value - baselines[feature].mean)
                        / baselines[feature].standard_deviation,
                        8,
                    ),
                    "warning_z": baselines[feature].warning_z,
                }
                for feature, value in sorted(observation.features.items())
            ]
            flags = [
                item for item in deviations if abs(item["z_score"]) >= item["warning_z"]
            ]
            evaluated.append(
                {
                    "observation_id": observation.observation_id,
                    "anomalous": bool(flags),
                    "deviations": deviations,
                    "flags": flags,
                }
            )
        return {
            "success": True,
            "status": "reasoning_features_evaluated",
            "observations": evaluated,
            "anomaly_count": sum(item["anomalous"] for item in evaluated),
            "measurement_status": "statistical_deviation_only",
            "limitations": (
                "Z-score deviation depends on supplied baselines and does not "
                "establish error, attack, unsafe reasoning, or root cause."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1085AnomalyDetectionEngine(context).run(context)

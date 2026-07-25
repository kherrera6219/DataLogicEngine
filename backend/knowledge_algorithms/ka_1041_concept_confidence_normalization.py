"""KA-1041: explicit cross-domain confidence-scale normalization."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ConfidenceObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    concept_id: str = Field(min_length=1, max_length=200)
    domain: str = Field(min_length=1, max_length=200)
    value: float
    scale_minimum: float
    scale_maximum: float
    weight: float = Field(default=1.0, gt=0, le=1_000)
    evidence_count: int | None = Field(default=None, ge=0, le=1_000_000)

    @model_validator(mode="after")
    def validate_scale(self) -> ConfidenceObservation:
        if self.scale_maximum <= self.scale_minimum:
            raise ValueError("scale maximum must exceed scale minimum")
        if not self.scale_minimum <= self.value <= self.scale_maximum:
            raise ValueError("confidence value is outside its declared scale")
        return self


class KA1041Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "confidence_vectors": [
                        {
                            "concept_id": "control-a",
                            "domain": "percent",
                            "value": 80,
                            "scale_minimum": 0,
                            "scale_maximum": 100,
                        }
                    ]
                }
            ]
        },
    )

    confidence_vectors: list[ConfidenceObservation] = Field(
        min_length=1,
        max_length=10_000,
    )
    aggregation: Literal["weighted_mean"] = "weighted_mean"


class KA1041ConceptConfidenceNormalization(KnowledgeAlgorithm):
    """Normalize declared scales without treating scores as probabilities."""

    input_schema = KA1041Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1041"

    def _run_logic(self, input_data: KA1041Input) -> dict[str, Any]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for observation in input_data.confidence_vectors:
            normalized = (observation.value - observation.scale_minimum) / (
                observation.scale_maximum - observation.scale_minimum
            )
            grouped[observation.concept_id].append(
                {
                    "domain": observation.domain,
                    "normalized_value": normalized,
                    "weight": observation.weight,
                    "evidence_count": observation.evidence_count,
                    "source_value": observation.value,
                    "source_scale": [
                        observation.scale_minimum,
                        observation.scale_maximum,
                    ],
                }
            )

        normalized_concepts: list[dict[str, Any]] = []
        for concept_id, observations in sorted(grouped.items()):
            total_weight = sum(item["weight"] for item in observations)
            aggregate = (
                sum(item["normalized_value"] * item["weight"] for item in observations)
                / total_weight
            )
            values = [item["normalized_value"] for item in observations]
            normalized_concepts.append(
                {
                    "concept_id": concept_id,
                    "normalized_confidence": round(aggregate, 8),
                    "normalized_range": [
                        round(min(values), 8),
                        round(max(values), 8),
                    ],
                    "domain_count": len({item["domain"] for item in observations}),
                    "observations": [
                        {
                            **item,
                            "normalized_value": round(
                                item["normalized_value"],
                                8,
                            ),
                        }
                        for item in sorted(
                            observations,
                            key=lambda item: (
                                item["domain"],
                                item["source_value"],
                            ),
                        )
                    ],
                }
            )
        return {
            "success": True,
            "status": "confidence_scales_normalized",
            "normalized_confidence": normalized_concepts,
            "aggregation": input_data.aggregation,
            "calibrated_probability": False,
            "limitations": (
                "Linear scale normalization makes declared scales comparable; "
                "it does not calibrate scores as empirical probabilities or "
                "validate the underlying evidence."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1041ConceptConfidenceNormalization(context).run(context)

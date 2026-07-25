"""KA-1075: deterministic group reweighting proposal."""

from __future__ import annotations

from collections import Counter
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class MitigationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: str = Field(min_length=1, max_length=200)
    group: str = Field(min_length=1, max_length=200)
    observed_label: str = Field(min_length=1, max_length=500)
    base_weight: float = Field(default=1, gt=0, le=100)


class KA1075Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "records": [
                        {"record_id": "a1", "group": "a", "observed_label": "yes"},
                        {"record_id": "a2", "group": "a", "observed_label": "no"},
                        {"record_id": "b1", "group": "b", "observed_label": "yes"},
                    ]
                }
            ]
        },
    )

    records: list[MitigationRecord] = Field(min_length=2, max_length=100_000)
    maximum_multiplier: float = Field(default=10, ge=1, le=100)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1075Input:
        identifiers = [record.record_id for record in self.records]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("mitigation record IDs must be unique")
        return self


class KA1075BiasMitigationEngine(KnowledgeAlgorithm):
    """Propose inverse-frequency weights without changing observed labels."""

    input_schema = KA1075Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1075"

    def _run_logic(self, input_data: KA1075Input) -> dict[str, Any]:
        group_counts = Counter(record.group for record in input_data.records)
        group_total = len(group_counts)
        population = len(input_data.records)
        group_multipliers = {
            group: min(
                population / (group_total * count),
                input_data.maximum_multiplier,
            )
            for group, count in group_counts.items()
        }
        weighted_records = [
            {
                "record_id": record.record_id,
                "group": record.group,
                "observed_label": record.observed_label,
                "original_weight": record.base_weight,
                "proposed_weight": round(
                    record.base_weight * group_multipliers[record.group],
                    8,
                ),
            }
            for record in sorted(input_data.records, key=lambda item: item.record_id)
        ]
        return {
            "success": True,
            "status": "bias_mitigation_proposed",
            "method": "capped_inverse_group_frequency",
            "group_counts": dict(sorted(group_counts.items())),
            "group_multipliers": {
                group: round(value, 8)
                for group, value in sorted(group_multipliers.items())
            },
            "weighted_records": weighted_records,
            "labels_changed": False,
            "mutation_applied": False,
            "deterministic": True,
            "limitations": (
                "Reweighting addresses representation imbalance only. It does "
                "not establish fairness, causality, or label correctness."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1075BiasMitigationEngine(context).run(context)

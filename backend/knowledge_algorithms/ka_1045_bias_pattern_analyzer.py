"""KA-1045: observational population-level outcome disparity analysis."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class PopulationOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    record_id: str = Field(min_length=1, max_length=200)
    group: str = Field(min_length=1, max_length=200)
    outcome: float = Field(ge=0, le=1)
    weight: float = Field(default=1.0, gt=0, le=1_000_000)


class KA1045Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "outputs_corpus": [
                        {
                            "record_id": "a-1",
                            "group": "a",
                            "outcome": 0.8,
                        },
                        {
                            "record_id": "a-2",
                            "group": "a",
                            "outcome": 0.7,
                        },
                        {
                            "record_id": "b-1",
                            "group": "b",
                            "outcome": 0.6,
                        },
                        {
                            "record_id": "b-2",
                            "group": "b",
                            "outcome": 0.5,
                        },
                    ]
                }
            ]
        },
    )

    outputs_corpus: list[PopulationOutcome] = Field(
        min_length=2,
        max_length=20_000,
    )
    disparity_threshold: float = Field(default=0.1, ge=0, le=1)
    minimum_group_size: int = Field(default=2, ge=2, le=10_000)
    reference_group: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_records(self) -> KA1045Input:
        record_ids = [item.record_id for item in self.outputs_corpus]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("population record IDs must be unique")
        return self


class KA1045BiasPatternAnalyzer(KnowledgeAlgorithm):
    """Measure supplied group outcome disparities without causal overclaim."""

    input_schema = KA1045Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1045"

    def _run_logic(self, input_data: KA1045Input) -> dict[str, Any]:
        grouped: dict[str, list[PopulationOutcome]] = defaultdict(list)
        for record in input_data.outputs_corpus:
            grouped[record.group].append(record)

        metrics: list[dict[str, Any]] = []
        for group, records in sorted(grouped.items()):
            total_weight = sum(item.weight for item in records)
            weighted_mean = (
                sum(item.outcome * item.weight for item in records) / total_weight
            )
            metrics.append(
                {
                    "group": group,
                    "record_count": len(records),
                    "total_weight": round(total_weight, 8),
                    "mean_outcome": round(weighted_mean, 8),
                    "eligible": len(records) >= input_data.minimum_group_size,
                }
            )

        eligible = [item for item in metrics if item["eligible"]]
        if len(eligible) < 2:
            return {
                "success": False,
                "status": "insufficient_eligible_groups",
                "group_metrics": metrics,
                "minimum_group_size": input_data.minimum_group_size,
                "limitations": (
                    "At least two groups meeting the minimum sample size are "
                    "required for disparity analysis."
                ),
            }

        if input_data.reference_group is not None:
            reference = next(
                (
                    item
                    for item in eligible
                    if item["group"] == input_data.reference_group
                ),
                None,
            )
            if reference is None:
                return {
                    "success": False,
                    "status": "reference_group_not_eligible",
                    "eligible_groups": [item["group"] for item in eligible],
                }
        else:
            reference = min(
                eligible,
                key=lambda item: (
                    -item["record_count"],
                    item["group"],
                ),
            )

        comparisons = [
            {
                "group": item["group"],
                "reference_group": reference["group"],
                "signed_difference": round(
                    item["mean_outcome"] - reference["mean_outcome"],
                    8,
                ),
                "absolute_disparity": round(
                    abs(item["mean_outcome"] - reference["mean_outcome"]),
                    8,
                ),
            }
            for item in eligible
            if item["group"] != reference["group"]
        ]
        flags = [
            {
                **comparison,
                "code": "observed_group_outcome_disparity",
                "threshold": input_data.disparity_threshold,
            }
            for comparison in comparisons
            if comparison["absolute_disparity"] >= input_data.disparity_threshold
        ]
        return {
            "success": True,
            "status": "population_disparity_measured",
            "reference_group": reference["group"],
            "group_metrics": metrics,
            "comparisons": comparisons,
            "bias_patterns": flags,
            "risk_alerts": flags,
            "measurement_status": "observational",
            "limitations": (
                "Observed outcome differences do not establish discrimination, "
                "causality, legal unfairness, or appropriate remediation. "
                "Confounders and data quality require domain review."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1045BiasPatternAnalyzer(context).run(context)

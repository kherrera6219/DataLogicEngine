"""KA-169: deterministic group fairness audit."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class FairnessGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(min_length=1, max_length=200)
    sample_count: int = Field(gt=0, le=1_000_000_000)
    positive_outcome_count: int = Field(ge=0, le=1_000_000_000)
    qualified_count: int = Field(ge=0, le=1_000_000_000)
    qualified_positive_count: int = Field(ge=0, le=1_000_000_000)

    @model_validator(mode="after")
    def validate_counts(self) -> FairnessGroup:
        if self.positive_outcome_count > self.sample_count:
            raise ValueError("positive outcomes cannot exceed sample count")
        if self.qualified_count > self.sample_count:
            raise ValueError("qualified count cannot exceed sample count")
        if self.qualified_positive_count > self.qualified_count:
            raise ValueError("qualified positive count cannot exceed qualified count")
        return self


class KA169Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "groups": [
                        {
                            "group_id": "a",
                            "sample_count": 100,
                            "positive_outcome_count": 50,
                            "qualified_count": 50,
                            "qualified_positive_count": 40,
                        },
                        {
                            "group_id": "b",
                            "sample_count": 100,
                            "positive_outcome_count": 30,
                            "qualified_count": 50,
                            "qualified_positive_count": 25,
                        },
                    ],
                    "maximum_allowed_disparity": 0.1,
                }
            ]
        },
    )

    groups: list[FairnessGroup] = Field(min_length=2, max_length=10_000)
    maximum_allowed_disparity: float = Field(default=0.1, ge=0, le=1)


class KA169FairnessAudit(KnowledgeAlgorithm):
    """Compute demographic-parity and equal-opportunity disparities."""

    input_schema = KA169Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-169"

    def _run_logic(self, input_data: KA169Input) -> dict[str, Any]:
        rates = []
        for item in sorted(input_data.groups, key=lambda row: row.group_id):
            rates.append(
                {
                    "group_id": item.group_id,
                    "positive_rate": item.positive_outcome_count / item.sample_count,
                    "qualified_positive_rate": (
                        item.qualified_positive_count / item.qualified_count
                        if item.qualified_count
                        else None
                    ),
                }
            )
        positive_values = [row["positive_rate"] for row in rates]
        qualified_values = [
            row["qualified_positive_rate"]
            for row in rates
            if row["qualified_positive_rate"] is not None
        ]
        demographic_disparity = max(positive_values) - min(positive_values)
        opportunity_disparity = (
            max(qualified_values) - min(qualified_values)
            if len(qualified_values) >= 2
            else None
        )
        passed = demographic_disparity <= input_data.maximum_allowed_disparity and (
            opportunity_disparity is None
            or opportunity_disparity <= input_data.maximum_allowed_disparity
        )
        return {
            "success": True,
            "status": "fairness_audited",
            "group_rates": rates,
            "demographic_parity_disparity": round(demographic_disparity, 8),
            "equal_opportunity_disparity": (
                round(opportunity_disparity, 8)
                if opportunity_disparity is not None
                else None
            ),
            "audit_passed": passed,
            "causal_discrimination_established": False,
            "policy_actions_applied": 0,
            "deterministic": True,
            "limitations": (
                "Metrics depend on caller-defined groups and qualification labels "
                "and do not establish legal fairness or causal discrimination."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA169FairnessAudit(context).run(context)

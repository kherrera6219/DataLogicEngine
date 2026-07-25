"""KA-1104: bounded truth-versus-utility option arbitration."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ArbitrationOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    option_id: str = Field(min_length=1, max_length=200)
    truth_confidence: float = Field(ge=0, le=1)
    utility_score: float = Field(ge=0, le=1)
    harm_risk: float = Field(ge=0, le=1)
    evidence_refs: list[str] = Field(default_factory=list, max_length=1_000)


class KA1104Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "options": [
                        {
                            "option_id": "safe-truthful",
                            "truth_confidence": 0.9,
                            "utility_score": 0.7,
                            "harm_risk": 0.1,
                            "evidence_refs": ["evidence-1"],
                        }
                    ],
                    "minimum_truth_confidence": 0.8,
                    "maximum_harm_risk": 0.25,
                }
            ]
        },
    )

    options: list[ArbitrationOption] = Field(min_length=1, max_length=10_000)
    minimum_truth_confidence: float = Field(default=0.8, ge=0, le=1)
    maximum_harm_risk: float = Field(default=0.25, ge=0, le=1)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1104Input:
        identifiers = [item.option_id for item in self.options]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("option IDs must be unique")
        return self


class KA1104TruthVsUtilityArbiter(KnowledgeAlgorithm):
    """Choose utility only among options meeting truth and harm constraints."""

    input_schema = KA1104Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1104"

    def _run_logic(self, input_data: KA1104Input) -> dict[str, Any]:
        eligible = [
            item
            for item in input_data.options
            if item.truth_confidence >= input_data.minimum_truth_confidence
            and item.harm_risk <= input_data.maximum_harm_risk
            and item.evidence_refs
        ]
        eligible.sort(
            key=lambda item: (
                -item.utility_score,
                -item.truth_confidence,
                item.harm_risk,
                item.option_id,
            )
        )
        rejected = [
            {
                "option_id": item.option_id,
                "reasons": [
                    *(
                        ["truth_confidence_below_minimum"]
                        if item.truth_confidence < input_data.minimum_truth_confidence
                        else []
                    ),
                    *(
                        ["harm_risk_above_maximum"]
                        if item.harm_risk > input_data.maximum_harm_risk
                        else []
                    ),
                    *(["evidence_missing"] if not item.evidence_refs else []),
                ],
            }
            for item in sorted(input_data.options, key=lambda row: row.option_id)
            if item not in eligible
        ]
        return {
            "success": True,
            "status": "truth_utility_arbitrated",
            "selected_option_id": eligible[0].option_id if eligible else None,
            "eligible_option_ids": [item.option_id for item in eligible],
            "rejected_options": rejected,
            "truth_floor_relaxed": False,
            "decision_applied": False,
            "deterministic": True,
            "limitations": (
                "The arbiter trusts caller-supplied truth, utility, harm, and "
                "evidence signals; it never lowers the declared truth floor."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1104TruthVsUtilityArbiter(context).run(context)

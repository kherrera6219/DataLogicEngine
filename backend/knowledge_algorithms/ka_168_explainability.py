"""KA-168: evidence-linked decision explanation derivation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class DecisionFactor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    factor_id: str = Field(min_length=1, max_length=200)
    label: str = Field(min_length=1, max_length=500)
    contribution: float = Field(ge=-1, le=1)
    evidence_refs: list[str] = Field(min_length=1, max_length=1_000)


class KA168Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "decision_id": "decision-1",
                    "outcome": "review",
                    "factors": [
                        {
                            "factor_id": "risk",
                            "label": "Risk threshold exceeded",
                            "contribution": 0.8,
                            "evidence_refs": ["trace-1"],
                        }
                    ],
                }
            ]
        },
    )

    decision_id: str = Field(min_length=1, max_length=200)
    outcome: str = Field(min_length=1, max_length=2_000)
    factors: list[DecisionFactor] = Field(min_length=1, max_length=10_000)
    maximum_factors: int = Field(default=5, ge=1, le=100)


class KA168Explainability(KnowledgeAlgorithm):
    """Produce a traceable explanation from supplied decision factors."""

    input_schema = KA168Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-168"

    def _run_logic(self, input_data: KA168Input) -> dict[str, Any]:
        ranked = sorted(
            input_data.factors,
            key=lambda item: (-abs(item.contribution), item.factor_id),
        )[: input_data.maximum_factors]
        return {
            "success": True,
            "status": "explanation_derived",
            "decision_id": input_data.decision_id,
            "outcome": input_data.outcome,
            "explanation": {
                "summary": (
                    f"Outcome '{input_data.outcome}' is linked to "
                    f"{len(ranked)} supplied decision factor(s)."
                ),
                "factors": [
                    {
                        "factor_id": item.factor_id,
                        "label": item.label,
                        "direction": (
                            "supports" if item.contribution >= 0 else "opposes"
                        ),
                        "contribution": item.contribution,
                        "evidence_refs": sorted(set(item.evidence_refs)),
                    }
                    for item in ranked
                ],
            },
            "factors_inferred": 0,
            "deterministic": True,
            "limitations": (
                "The explanation is derived from supplied factors and does not "
                "prove causal influence or inspect a hidden model state."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA168Explainability(context).run(context)

"""KA-1102: normalized Shannon entropy quantification."""

from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class EntropyCategory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1, max_length=200)
    count: float = Field(ge=0, le=1_000_000_000_000)


class KA1102Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "categories": [
                        {"category": "a", "count": 5},
                        {"category": "b", "count": 5},
                    ]
                }
            ]
        },
    )

    categories: list[EntropyCategory] = Field(min_length=1, max_length=100_000)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_distribution(self) -> KA1102Input:
        names = [item.category for item in self.categories]
        if len(names) != len(set(names)):
            raise ValueError("entropy categories must be unique")
        if sum(item.count for item in self.categories) <= 0:
            raise ValueError("entropy distribution total must be positive")
        return self


class KA1102GlobalEntropyQuantifier(KnowledgeAlgorithm):
    """Compute raw and normalized entropy from a declared distribution."""

    input_schema = KA1102Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1102"

    def _run_logic(self, input_data: KA1102Input) -> dict[str, Any]:
        total = sum(item.count for item in input_data.categories)
        probabilities = [
            item.count / total for item in input_data.categories if item.count > 0
        ]
        entropy_bits = -sum(value * math.log2(value) for value in probabilities)
        possible = len(input_data.categories)
        maximum = math.log2(possible) if possible > 1 else 0.0
        normalized = entropy_bits / maximum if maximum else 0.0
        return {
            "success": True,
            "status": "global_entropy_quantified",
            "entropy_bits": round(entropy_bits, 8),
            "maximum_entropy_bits": round(maximum, 8),
            "normalized_entropy": round(normalized, 8),
            "category_count": possible,
            "distribution_total": total,
            "deterministic": True,
            "dependencies_consumed": sorted(input_data.dependency_results),
            "limitations": (
                "Entropy measures distribution uncertainty only and does not "
                "measure truth, risk, quality, or causal complexity."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1102GlobalEntropyQuantifier(context).run(context)

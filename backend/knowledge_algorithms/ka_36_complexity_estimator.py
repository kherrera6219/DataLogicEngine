"""KA-036: bounded complexity estimation from supplied request signals."""

from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA036Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem: str = Field(min_length=1, max_length=100_000)
    target_ka_id: str | None = Field(default=None, max_length=200)
    declared_step_count: int = Field(default=1, ge=1, le=10_000)
    dependency_count: int = Field(default=0, ge=0, le=100_000)
    observed_latencies_ms: list[int] = Field(default_factory=list, max_length=1_000)


class KA036ComplexityEstimator(KnowledgeAlgorithm):
    """Estimate routing complexity without database access or hidden telemetry."""

    input_schema = KA036Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-036"

    def _run_logic(self, input_data: KA036Input) -> dict[str, Any]:
        if any(
            value < 0 or value > 3_600_000 for value in input_data.observed_latencies_ms
        ):
            raise ValueError("observed latencies must be between 0 and 3,600,000 ms")
        length_score = min(len(input_data.problem) // 500, 3)
        step_score = min(math.ceil(input_data.declared_step_count / 5), 3)
        dependency_score = min(math.ceil(input_data.dependency_count / 10), 3)
        raw_score = max(1, min(5, 1 + length_score + step_score + dependency_score))
        latencies = sorted(input_data.observed_latencies_ms)
        p95 = self._percentile(latencies, 95)
        if p95 is not None:
            if p95 >= 5_000:
                raw_score = max(raw_score, 5)
            elif p95 >= 1_500:
                raw_score = max(raw_score, 3)
        category = "low" if raw_score <= 2 else "moderate" if raw_score <= 4 else "high"
        return {
            "success": True,
            "status": "complexity_estimated",
            "complexity_score": raw_score,
            "category": category,
            "signals": {
                "problem_characters": len(input_data.problem),
                "declared_step_count": input_data.declared_step_count,
                "dependency_count": input_data.dependency_count,
                "latency_sample_size": len(latencies),
                "p95_latency_ms": p95,
            },
            "database_read_performed": False,
            "deterministic": True,
            "limitations": (
                "This is a routing estimate from declared structure and supplied "
                "latency observations, not an asymptotic complexity proof."
            ),
        }

    @staticmethod
    def _percentile(values: list[int], percentile: int) -> int | None:
        if not values:
            return None
        rank = max(
            0, min(math.ceil((percentile / 100) * len(values)) - 1, len(values) - 1)
        )
        return values[rank]


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA036ComplexityEstimator(context).run(context)

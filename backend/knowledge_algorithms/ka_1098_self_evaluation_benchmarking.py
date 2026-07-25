"""KA-1098: deterministic benchmark result evaluation."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class BenchmarkResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1, max_length=200)
    suite: str = Field(min_length=1, max_length=200)
    passed: bool
    score: float = Field(ge=0, le=1)
    latency_ms: float = Field(ge=0, le=86_400_000)


class KA1098Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "results": [
                        {
                            "case_id": "case-1",
                            "suite": "retrieval",
                            "passed": True,
                            "score": 0.9,
                            "latency_ms": 100,
                        }
                    ],
                    "minimum_pass_ratio": 0.8,
                    "minimum_mean_score": 0.8,
                }
            ]
        },
    )

    results: list[BenchmarkResult] = Field(min_length=1, max_length=100_000)
    minimum_pass_ratio: float = Field(default=0.8, ge=0, le=1)
    minimum_mean_score: float = Field(default=0.8, ge=0, le=1)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1098Input:
        identifiers = [item.case_id for item in self.results]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("benchmark case IDs must be unique")
        return self


class KA1098SelfEvaluationBenchmarking(KnowledgeAlgorithm):
    """Aggregate already-executed benchmark evidence without running a suite."""

    input_schema = KA1098Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1098"

    def _run_logic(self, input_data: KA1098Input) -> dict[str, Any]:
        grouped: dict[str, list[BenchmarkResult]] = defaultdict(list)
        for result in input_data.results:
            grouped[result.suite].append(result)
        suites = []
        for suite in sorted(grouped):
            rows = grouped[suite]
            pass_ratio = sum(row.passed for row in rows) / len(rows)
            mean_score = sum(row.score for row in rows) / len(rows)
            sorted_latency = sorted(row.latency_ms for row in rows)
            p95_index = max(0, (95 * len(sorted_latency) + 99) // 100 - 1)
            suites.append(
                {
                    "suite": suite,
                    "case_count": len(rows),
                    "pass_ratio": round(pass_ratio, 8),
                    "mean_score": round(mean_score, 8),
                    "p95_latency_ms": sorted_latency[p95_index],
                    "accepted": (
                        pass_ratio >= input_data.minimum_pass_ratio
                        and mean_score >= input_data.minimum_mean_score
                    ),
                }
            )
        return {
            "success": True,
            "status": "benchmark_results_evaluated",
            "suite_results": suites,
            "overall_accepted": all(item["accepted"] for item in suites),
            "benchmarks_executed": False,
            "deterministic": True,
            "limitations": (
                "This evaluates supplied results only and does not establish "
                "benchmark provenance, representativeness, or execution integrity."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1098SelfEvaluationBenchmarking(context).run(context)

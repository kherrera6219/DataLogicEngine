"""KA-1047: bounded selection among approved algorithm candidates."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.knowledge_algorithms.production_utils import stable_identifier
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

RiskClass = Literal["low", "medium", "high", "critical"]


class AlgorithmCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canonical_id: str = Field(
        pattern=(
            r"^(?:KA-(?:\d{3}|\d{4})|L9-KA-\d{3}|"
            r"L10-KA-\d{3}|KA-Master)$"
        )
    )
    version: str = Field(min_length=1, max_length=100)
    capabilities: list[str] = Field(min_length=1, max_length=50)
    quality_score: float = Field(ge=0, le=1)
    success_rate: float = Field(ge=0, le=1)
    p95_latency_ms: float = Field(ge=0, le=3_600_000)
    risk_class: RiskClass
    enabled: bool = True


class KA1047Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "problem_signature": "retrieve governed evidence",
                    "required_capabilities": ["retrieval"],
                    "performance_history": [
                        {
                            "canonical_id": "KA-079",
                            "version": "1.0.0",
                            "capabilities": ["retrieval"],
                            "quality_score": 0.9,
                            "success_rate": 0.95,
                            "p95_latency_ms": 100,
                            "risk_class": "low",
                        }
                    ],
                }
            ]
        },
    )

    problem_signature: str = Field(min_length=1, max_length=5_000)
    required_capabilities: list[str] = Field(min_length=1, max_length=50)
    performance_history: list[AlgorithmCandidate] = Field(
        min_length=1,
        max_length=500,
    )
    maximum_pipeline_steps: int = Field(default=5, ge=1, le=20)
    maximum_p95_latency_ms: float = Field(
        default=5_000,
        gt=0,
        le=3_600_000,
    )
    minimum_quality_score: float = Field(default=0.5, ge=0, le=1)
    allowed_risk_classes: list[RiskClass] = Field(
        default_factory=lambda: ["low", "medium"],
        min_length=1,
        max_length=4,
    )

    @model_validator(mode="after")
    def validate_candidates(self) -> KA1047Input:
        candidate_ids = [item.canonical_id for item in self.performance_history]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("candidate canonical IDs must be unique")
        required = [item.strip().lower() for item in self.required_capabilities]
        if not all(required) or len(required) != len(set(required)):
            raise ValueError("required capabilities must be non-empty and unique")
        if len(self.allowed_risk_classes) != len(set(self.allowed_risk_classes)):
            raise ValueError("allowed risk classes must be unique")
        return self


class KA1047MetaAlgorithmSelection(KnowledgeAlgorithm):
    """Select a bounded approved pipeline; emit only review-only gap drafts."""

    input_schema = KA1047Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1047"

    @staticmethod
    def _rank(candidate: AlgorithmCandidate) -> tuple[float, float, float, str]:
        return (
            -candidate.quality_score,
            -candidate.success_rate,
            candidate.p95_latency_ms,
            candidate.canonical_id,
        )

    def _run_logic(self, input_data: KA1047Input) -> dict[str, Any]:
        required = {item.strip().lower() for item in input_data.required_capabilities}
        eligible = [
            candidate
            for candidate in input_data.performance_history
            if candidate.enabled
            and candidate.risk_class in input_data.allowed_risk_classes
            and candidate.quality_score >= input_data.minimum_quality_score
            and candidate.p95_latency_ms <= input_data.maximum_p95_latency_ms
        ]
        remaining = set(required)
        selected: list[AlgorithmCandidate] = []
        while remaining and len(selected) < input_data.maximum_pipeline_steps:
            ranked = sorted(
                (
                    (
                        candidate,
                        remaining
                        & {
                            capability.strip().lower()
                            for capability in candidate.capabilities
                        },
                    )
                    for candidate in eligible
                    if candidate not in selected
                ),
                key=lambda item: (
                    -len(item[1]),
                    *self._rank(item[0]),
                ),
            )
            if not ranked or not ranked[0][1]:
                break
            candidate, covered = ranked[0]
            selected.append(candidate)
            remaining -= covered

        pipeline = [
            {
                "canonical_id": candidate.canonical_id,
                "version": candidate.version,
                "quality_score": candidate.quality_score,
                "success_rate": candidate.success_rate,
                "p95_latency_ms": candidate.p95_latency_ms,
                "risk_class": candidate.risk_class,
                "covered_capabilities": sorted(
                    required
                    & {
                        capability.strip().lower()
                        for capability in candidate.capabilities
                    }
                ),
            }
            for candidate in selected
        ]
        uncovered = sorted(remaining)
        draft = (
            {
                "draft_id": stable_identifier(
                    "ka-draft",
                    {
                        "problem_signature": input_data.problem_signature,
                        "uncovered_capabilities": uncovered,
                    },
                ),
                "status": "review_required",
                "production_enabled": False,
                "canonical_id": None,
                "implementation": None,
                "required_capabilities": uncovered,
                "reason": "no_approved_candidate_covers_required_capability",
            }
            if uncovered
            else None
        )
        return {
            "success": True,
            "status": (
                "approved_pipeline_selected"
                if not uncovered
                else "partial_pipeline_review_required"
            ),
            "problem_signature": input_data.problem_signature,
            "tuned_pipeline": pipeline,
            "selection_complete": not uncovered,
            "uncovered_capabilities": uncovered,
            "candidate_new_ka_config": draft,
            "execution_started": False,
            "deterministic": True,
            "limitations": (
                "Selection uses caller-supplied performance history and approved "
                "candidate metadata. A gap draft is non-executable and cannot "
                "create, register, enable, or run a new KA."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1047MetaAlgorithmSelection(context).run(context)

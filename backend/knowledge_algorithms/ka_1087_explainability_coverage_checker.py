"""KA-1087: explicit critical-step explanation coverage verification."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class CriticalReasoningStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5_000)
    required_evidence_refs: list[str] = Field(
        default_factory=list,
        max_length=1_000,
    )


class ExplanationSegment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segment_id: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=50_000)
    covers_step_ids: list[str] = Field(min_length=1, max_length=1_000)
    evidence_refs: list[str] = Field(default_factory=list, max_length=1_000)


class KA1087Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "critical_steps": [
                        {
                            "step_id": "s1",
                            "description": "Validate the source",
                            "required_evidence_refs": ["e1"],
                        }
                    ],
                    "explanation_segments": [
                        {
                            "segment_id": "x1",
                            "text": "The source was validated against evidence e1.",
                            "covers_step_ids": ["s1"],
                            "evidence_refs": ["e1"],
                        }
                    ],
                }
            ]
        },
    )

    critical_steps: list[CriticalReasoningStep] = Field(
        min_length=1,
        max_length=1_000,
    )
    explanation_segments: list[ExplanationSegment] = Field(
        default_factory=list,
        max_length=5_000,
    )

    @model_validator(mode="after")
    def validate_references(self) -> KA1087Input:
        step_ids = [item.step_id for item in self.critical_steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("critical step IDs must be unique")
        segment_ids = [item.segment_id for item in self.explanation_segments]
        if len(segment_ids) != len(set(segment_ids)):
            raise ValueError("explanation segment IDs must be unique")
        known = set(step_ids)
        if any(
            step_id not in known
            for segment in self.explanation_segments
            for step_id in segment.covers_step_ids
        ):
            raise ValueError("explanation references an unknown critical step")
        return self


class KA1087ExplainabilityCoverageChecker(KnowledgeAlgorithm):
    """Verify explicit step/evidence coverage without generating explanation."""

    input_schema = KA1087Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1087"

    def _run_logic(self, input_data: KA1087Input) -> dict[str, Any]:
        results = []
        for step in input_data.critical_steps:
            segments = [
                item
                for item in input_data.explanation_segments
                if step.step_id in item.covers_step_ids
            ]
            evidence = {ref for segment in segments for ref in segment.evidence_refs}
            missing_evidence = sorted(set(step.required_evidence_refs) - evidence)
            covered = bool(segments) and not missing_evidence
            results.append(
                {
                    "step_id": step.step_id,
                    "covered": covered,
                    "segment_ids": sorted(item.segment_id for item in segments),
                    "missing_evidence_refs": missing_evidence,
                }
            )
        covered_count = sum(item["covered"] for item in results)
        return {
            "success": True,
            "status": "explanation_coverage_checked",
            "coverage_complete": covered_count == len(results),
            "coverage_ratio": round(covered_count / len(results), 8),
            "step_coverage": results,
            "explanation_generated": False,
            "limitations": (
                "Coverage uses explicit caller-supplied links. It does not "
                "judge whether explanation text is correct, understandable, "
                "faithful, or sufficient for a particular audience."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1087ExplainabilityCoverageChecker(context).run(context)

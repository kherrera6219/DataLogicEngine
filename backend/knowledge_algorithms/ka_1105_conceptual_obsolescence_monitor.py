"""KA-1105: deterministic conceptual-obsolescence monitoring."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ConceptEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str = Field(min_length=1, max_length=200)
    baseline_contradiction_rate: float = Field(ge=0, le=1)
    current_contradiction_rate: float = Field(ge=0, le=1)
    active_citation_count: int = Field(ge=0, le=1_000_000)
    superseding_policy_refs: list[str] = Field(default_factory=list, max_length=1_000)
    paradigm_replacement_refs: list[str] = Field(default_factory=list, max_length=1_000)


class KA1105Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "concepts": [
                        {
                            "concept_id": "legacy-control",
                            "baseline_contradiction_rate": 0.1,
                            "current_contradiction_rate": 0.7,
                            "active_citation_count": 0,
                            "superseding_policy_refs": ["policy-v2"],
                            "paradigm_replacement_refs": ["model-v2"],
                        }
                    ]
                }
            ]
        },
    )

    concepts: list[ConceptEvidence] = Field(min_length=1, max_length=10_000)
    contradiction_increase_threshold: float = Field(default=0.25, ge=0, le=1)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1105Input:
        identifiers = [item.concept_id for item in self.concepts]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("concept IDs must be unique")
        if self.dependency_results:
            if set(self.dependency_results) != {"KA-1082", "KA-1083"}:
                raise ValueError(
                    "KA-1105 requires the exact KA-1082 and KA-1083 results"
                )
            drift = self.dependency_results["KA-1082"]
            schedule = self.dependency_results["KA-1083"]
            if drift.get("status") != "confidence_drift_measured":
                raise ValueError("KA-1082 dependency status is invalid")
            if schedule.get("status") != "revalidation_schedule_planned":
                raise ValueError("KA-1083 dependency status is invalid")
            drift_ids = {
                str(item.get("knowledge_id"))
                for item in drift.get("measurements", [])
                if isinstance(item, dict) and item.get("knowledge_id")
            }
            schedule_ids = {
                str(item.get("knowledge_id"))
                for item in schedule.get("schedule", [])
                if isinstance(item, dict) and item.get("knowledge_id")
            }
            if drift_ids != set(identifiers) or schedule_ids != set(identifiers):
                raise ValueError("dependency results must cover the exact concept IDs")
        return self


class KA1105ConceptualObsolescenceMonitor(KnowledgeAlgorithm):
    """Flag paradigm replacement evidence without changing knowledge state."""

    input_schema = KA1105Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1105"

    def _run_logic(self, input_data: KA1105Input) -> dict[str, Any]:
        drift_by_id = {
            str(item["knowledge_id"]): bool(item.get("degradation_detected"))
            for item in input_data.dependency_results.get("KA-1082", {}).get(
                "measurements", []
            )
        }
        overdue_by_id = {
            str(item["knowledge_id"]): bool(item.get("overdue"))
            for item in input_data.dependency_results.get("KA-1083", {}).get(
                "schedule", []
            )
        }
        assessments = []
        for item in sorted(input_data.concepts, key=lambda row: row.concept_id):
            reasons = []
            increase = (
                item.current_contradiction_rate - item.baseline_contradiction_rate
            )
            if increase >= input_data.contradiction_increase_threshold:
                reasons.append("contradiction_rate_increased")
            if item.superseding_policy_refs:
                reasons.append("superseding_policy_present")
            if item.paradigm_replacement_refs:
                reasons.append("paradigm_replacement_present")
            if drift_by_id.get(item.concept_id, False):
                reasons.append("confidence_drift_detected")
            if overdue_by_id.get(item.concept_id, False):
                reasons.append("revalidation_overdue")
            obsolete = "paradigm_replacement_present" in reasons and (
                "contradiction_rate_increased" in reasons
                or "superseding_policy_present" in reasons
            )
            assessments.append(
                {
                    "concept_id": item.concept_id,
                    "classification": (
                        "obsolescence_candidate" if obsolete else "retain"
                    ),
                    "reasons": reasons,
                    "revalidation_requested": obsolete,
                }
            )
        return {
            "success": True,
            "status": "conceptual_obsolescence_assessed",
            "assessments": assessments,
            "dependencies_consumed": (
                ["KA-1082", "KA-1083"] if input_data.dependency_results else []
            ),
            "requests_dispatched": 0,
            "knowledge_updated": False,
            "deterministic": True,
            "limitations": (
                "The monitor uses declared evidence signals and cannot establish "
                "that a concept is false or safely removable."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1105ConceptualObsolescenceMonitor(context).run(context)

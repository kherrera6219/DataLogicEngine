"""KA-1039: deterministic ontology drift analysis across two snapshots."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.knowledge_algorithms.production_utils import normalized_tokens
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class OntologyConcept(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str = Field(min_length=1, max_length=200)
    label: str = Field(min_length=1, max_length=500)
    definition: str = Field(min_length=1, max_length=20_000)
    parent_ids: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_parents(self) -> OntologyConcept:
        if self.concept_id in self.parent_ids:
            raise ValueError("a concept cannot be its own parent")
        if len(self.parent_ids) != len(set(self.parent_ids)):
            raise ValueError("parent IDs must be unique")
        return self


class KA1039Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "baseline_version": "ontology-v1",
                    "current_version": "ontology-v2",
                    "baseline_concepts": [
                        {
                            "concept_id": "control",
                            "label": "Control",
                            "definition": "A documented risk-reduction measure.",
                        }
                    ],
                    "current_concepts": [
                        {
                            "concept_id": "control",
                            "label": "Control",
                            "definition": "A verified risk-reduction measure.",
                        }
                    ],
                }
            ]
        },
    )

    baseline_version: str = Field(min_length=1, max_length=200)
    current_version: str = Field(min_length=1, max_length=200)
    baseline_concepts: list[OntologyConcept] = Field(
        min_length=1,
        max_length=5_000,
    )
    current_concepts: list[OntologyConcept] = Field(
        min_length=1,
        max_length=5_000,
    )
    definition_drift_threshold: float = Field(default=0.35, ge=0, le=1)

    @model_validator(mode="after")
    def validate_snapshots(self) -> KA1039Input:
        for snapshot in (self.baseline_concepts, self.current_concepts):
            identifiers = [item.concept_id for item in snapshot]
            if len(identifiers) != len(set(identifiers)):
                raise ValueError("concept IDs must be unique within each snapshot")
        return self


class KA1039OntologyDriftDetection(KnowledgeAlgorithm):
    """Measure definition and hierarchy changes without modifying an ontology."""

    input_schema = KA1039Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1039"

    @staticmethod
    def _similarity(left: str, right: str) -> float:
        left_tokens = normalized_tokens(left)
        right_tokens = normalized_tokens(right)
        union = left_tokens | right_tokens
        return 1.0 if not union else len(left_tokens & right_tokens) / len(union)

    def _run_logic(self, input_data: KA1039Input) -> dict[str, Any]:
        baseline = {item.concept_id: item for item in input_data.baseline_concepts}
        current = {item.concept_id: item for item in input_data.current_concepts}
        added = sorted(current.keys() - baseline.keys())
        removed = sorted(baseline.keys() - current.keys())
        concept_drift: list[dict[str, Any]] = []

        for concept_id in sorted(baseline.keys() & current.keys()):
            before = baseline[concept_id]
            after = current[concept_id]
            definition_similarity = self._similarity(
                before.definition,
                after.definition,
            )
            definition_drift = round(1 - definition_similarity, 8)
            label_changed = before.label.casefold().strip() != after.label.casefold().strip()
            parents_added = sorted(set(after.parent_ids) - set(before.parent_ids))
            parents_removed = sorted(set(before.parent_ids) - set(after.parent_ids))
            material = (
                label_changed
                or bool(parents_added)
                or bool(parents_removed)
                or definition_drift >= input_data.definition_drift_threshold
            )
            if material:
                concept_drift.append(
                    {
                        "concept_id": concept_id,
                        "label_changed": label_changed,
                        "definition_drift": definition_drift,
                        "definition_threshold_exceeded": (
                            definition_drift
                            >= input_data.definition_drift_threshold
                        ),
                        "parents_added": parents_added,
                        "parents_removed": parents_removed,
                    }
                )

        changed_count = len(added) + len(removed) + len(concept_drift)
        population = max(len(baseline), len(current), 1)
        return {
            "success": True,
            "status": "ontology_drift_evaluated",
            "baseline_version": input_data.baseline_version,
            "current_version": input_data.current_version,
            "drift_detected": changed_count > 0,
            "added_concept_ids": added,
            "removed_concept_ids": removed,
            "concept_drift": concept_drift,
            "material_change_count": changed_count,
            "drift_ratio": round(min(changed_count / population, 1.0), 8),
            "mutation_applied": False,
            "deterministic": True,
            "limitations": (
                "Definition drift uses bounded token overlap and structural "
                "comparison. It does not prove a semantic change or update the "
                "ontology."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1039OntologyDriftDetection(context).run(context)

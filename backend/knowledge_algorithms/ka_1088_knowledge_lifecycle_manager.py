"""KA-1088: deterministic knowledge lifecycle transition planning."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class LifecycleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_id: str = Field(min_length=1, max_length=200)
    current_state: Literal[
        "candidate",
        "validated",
        "active",
        "disputed",
        "quarantined",
        "obsolete",
        "archived",
    ]
    validation_passed: bool = False
    confidence: float = Field(ge=0, le=1)
    drift_detected: bool = False
    retirement_approved: bool = False


class KA1088Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "records": [
                        {
                            "knowledge_id": "knowledge-1",
                            "current_state": "candidate",
                            "validation_passed": True,
                            "confidence": 0.9,
                        }
                    ]
                }
            ]
        },
    )

    records: list[LifecycleRecord] = Field(min_length=1, max_length=20_000)
    activation_confidence: float = Field(default=0.8, ge=0, le=1)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1088Input:
        identifiers = [item.knowledge_id for item in self.records]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("knowledge IDs must be unique")
        return self


class KA1088KnowledgeLifecycleManager(KnowledgeAlgorithm):
    """Coordinate valid next-state proposals without applying transitions."""

    input_schema = KA1088Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1088"

    def _run_logic(self, input_data: KA1088Input) -> dict[str, Any]:
        plans = []
        for item in sorted(input_data.records, key=lambda row: row.knowledge_id):
            target = item.current_state
            reason = "no_transition_required"
            if item.current_state in {"candidate", "validated"} and item.drift_detected:
                target, reason = "disputed", "drift_detected"
            elif item.current_state == "candidate" and item.validation_passed:
                target, reason = "validated", "validation_passed"
            elif (
                item.current_state == "validated"
                and item.confidence >= input_data.activation_confidence
            ):
                target, reason = "active", "activation_criteria_met"
            elif item.current_state == "disputed":
                target, reason = "quarantined", "dispute_requires_isolation"
            elif item.current_state == "active" and item.retirement_approved:
                target, reason = "obsolete", "retirement_approved"
            elif item.current_state == "obsolete" and item.retirement_approved:
                target, reason = "archived", "archive_approved"
            plans.append(
                {
                    "knowledge_id": item.knowledge_id,
                    "current_state": item.current_state,
                    "proposed_state": target,
                    "transition_required": target != item.current_state,
                    "reason": reason,
                }
            )
        return {
            "success": True,
            "status": "knowledge_lifecycle_planned",
            "transition_plans": plans,
            "transitions_applied": 0,
            "effect_service_required": True,
            "deterministic": True,
            "limitations": (
                "This coordinates state-transition proposals only. The owning "
                "knowledge service must enforce authorization and persistence."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1088KnowledgeLifecycleManager(context).run(context)

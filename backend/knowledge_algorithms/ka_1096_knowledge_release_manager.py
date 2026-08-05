"""KA-1096: deterministic knowledge-release staging decisions."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KnowledgeReleaseCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    release_id: str = Field(min_length=1, max_length=200)
    knowledge_version_ids: list[str] = Field(min_length=1, max_length=10_000)
    validation_status: Literal["pending", "passed", "failed"]
    required_approvals: int = Field(ge=0, le=100)
    recorded_approvals: int = Field(ge=0, le=100)
    dependencies_ready: bool
    rollback_plan_ref: str | None = Field(default=None, max_length=2_000)
    rollout_percent: int = Field(default=100, ge=1, le=100)


class KA1096Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "candidates": [
                        {
                            "release_id": "release-1",
                            "knowledge_version_ids": ["knowledge-1:v2"],
                            "validation_status": "passed",
                            "required_approvals": 1,
                            "recorded_approvals": 1,
                            "dependencies_ready": True,
                            "rollback_plan_ref": "rollback-1",
                            "rollout_percent": 10,
                        }
                    ]
                }
            ]
        },
    )

    candidates: list[KnowledgeReleaseCandidate] = Field(
        min_length=1,
        max_length=5_000,
    )
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1096Input:
        identifiers = [item.release_id for item in self.candidates]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("release IDs must be unique")
        if self.dependency_results and set(self.dependency_results) != {"KA-1079"}:
            raise ValueError("dependency_results must contain KA-1079")
        return self


class KA1096KnowledgeReleaseManager(KnowledgeAlgorithm):
    """Stage release proposals without activating knowledge versions."""

    input_schema = KA1096Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1096"

    def _run_logic(self, input_data: KA1096Input) -> dict[str, Any]:
        promotion_approved = input_data.dependency_results.get("KA-1079", {}).get(
            "decision", "approve"
        ) == "approve"
        plans = []
        for item in sorted(input_data.candidates, key=lambda row: row.release_id):
            blockers = []
            if not promotion_approved:
                blockers.append("promotion_not_approved")
            if item.validation_status != "passed":
                blockers.append(f"validation_{item.validation_status}")
            if item.recorded_approvals < item.required_approvals:
                blockers.append("required_approvals_missing")
            if not item.dependencies_ready:
                blockers.append("dependencies_not_ready")
            if not item.rollback_plan_ref:
                blockers.append("rollback_plan_missing")
            plans.append(
                {
                    "release_id": item.release_id,
                    "knowledge_version_ids": sorted(item.knowledge_version_ids),
                    "decision": "stage" if not blockers else "block",
                    "blockers": blockers,
                    "rollout_percent": item.rollout_percent,
                    "rollback_plan_ref": item.rollback_plan_ref,
                }
            )
        return {
            "success": True,
            "status": "knowledge_release_evaluated",
            "release_plans": plans,
            "releases_activated": 0,
            "effect_service_required": True,
            "promotion_approved": promotion_approved,
            "dependencies_consumed": sorted(input_data.dependency_results),
            "deterministic": True,
            "limitations": (
                "This stages policy decisions only. The release service must "
                "authorize activation, record receipts, monitor, and roll back."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1096KnowledgeReleaseManager(context).run(context)

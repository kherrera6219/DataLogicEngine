"""KA-1046: governed planning for hierarchical memory updates."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

MemoryTier = Literal["working", "long_term", "archive", "quarantine"]


class MemoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    update_id: str = Field(min_length=1, max_length=200)
    knowledge_id: str = Field(min_length=1, max_length=200)
    current_version: str | None = Field(default=None, max_length=200)
    proposed_version: str = Field(min_length=1, max_length=200)
    lifecycle_state: Literal[
        "candidate",
        "validated",
        "disputed",
        "obsolete",
    ]
    confidence: float = Field(ge=0, le=1)
    evidence_count: int = Field(ge=0, le=1_000_000)
    sensitivity: Literal["public", "internal", "restricted"]
    requested_tier: MemoryTier | None = None

    @model_validator(mode="after")
    def validate_version_change(self) -> MemoryUpdate:
        if self.current_version == self.proposed_version:
            raise ValueError("proposed version must differ from current version")
        return self


class KA1046Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "updates": [
                        {
                            "update_id": "update-1",
                            "knowledge_id": "knowledge-1",
                            "current_version": "v1",
                            "proposed_version": "v2",
                            "lifecycle_state": "validated",
                            "confidence": 0.95,
                            "evidence_count": 3,
                            "sensitivity": "internal",
                        }
                    ]
                }
            ]
        },
    )

    updates: list[MemoryUpdate] = Field(min_length=1, max_length=1_000)
    minimum_long_term_confidence: float = Field(default=0.8, ge=0, le=1)
    minimum_long_term_evidence: int = Field(default=2, ge=0, le=10_000)

    @model_validator(mode="after")
    def validate_update_ids(self) -> KA1046Input:
        update_ids = [item.update_id for item in self.updates]
        if len(update_ids) != len(set(update_ids)):
            raise ValueError("memory update IDs must be unique")
        return self


class KA1046HierarchicalMemoryPatcher(KnowledgeAlgorithm):
    """Create authorized-effect patch plans without changing memory stores."""

    input_schema = KA1046Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1046"

    @staticmethod
    def _recommended_tier(
        item: MemoryUpdate,
        minimum_confidence: float,
        minimum_evidence: int,
    ) -> MemoryTier:
        if item.lifecycle_state == "disputed":
            return "quarantine"
        if item.lifecycle_state == "obsolete":
            return "archive"
        if (
            item.lifecycle_state == "validated"
            and item.confidence >= minimum_confidence
            and item.evidence_count >= minimum_evidence
        ):
            return "long_term"
        return "working"

    def _run_logic(self, input_data: KA1046Input) -> dict[str, Any]:
        operations: list[dict[str, Any]] = []
        for item in sorted(input_data.updates, key=lambda value: value.update_id):
            recommended = self._recommended_tier(
                item,
                input_data.minimum_long_term_confidence,
                input_data.minimum_long_term_evidence,
            )
            requested = item.requested_tier
            tier_accepted = requested is None or requested == recommended
            target_tier = recommended if requested is None else requested
            approval_required = (
                item.sensitivity == "restricted"
                or target_tier in {"archive", "quarantine"}
                or not tier_accepted
            )
            operations.append(
                {
                    "update_id": item.update_id,
                    "knowledge_id": item.knowledge_id,
                    "operation": "upsert_version",
                    "current_version_precondition": item.current_version,
                    "proposed_version": item.proposed_version,
                    "recommended_tier": recommended,
                    "requested_tier": requested,
                    "target_tier": target_tier,
                    "tier_policy_match": tier_accepted,
                    "approval_required": approval_required,
                    "preconditions": [
                        "current_version_matches"
                        if item.current_version is not None
                        else "knowledge_record_absent",
                        "owning_service_authorizes_effect",
                    ],
                }
            )
        return {
            "success": True,
            "status": "memory_patch_plan_created",
            "patch_operations": operations,
            "operation_count": len(operations),
            "approval_required_count": sum(
                bool(item["approval_required"]) for item in operations
            ),
            "patch_applied": False,
            "effect_service_required": True,
            "deterministic": True,
            "limitations": (
                "This capability creates version-preconditioned patch plans. "
                "Only the owning memory service may authorize, transact, and "
                "persist a patch."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1046HierarchicalMemoryPatcher(context).run(context)

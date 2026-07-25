"""KA-1089: deterministic policy-version change tracking."""

from __future__ import annotations

from datetime import date
from itertools import pairwise
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class PolicyRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=20_000)


class PolicyVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version_id: str = Field(min_length=1, max_length=200)
    effective_on: date
    source_ref: str = Field(min_length=1, max_length=2_000)
    requirements: list[PolicyRequirement] = Field(max_length=10_000)

    @model_validator(mode="after")
    def validate_requirement_ids(self) -> PolicyVersion:
        identifiers = [item.requirement_id for item in self.requirements]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("requirement IDs must be unique within a version")
        return self


class KA1089Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "policy_id": "policy-1",
                    "versions": [
                        {
                            "version_id": "v1",
                            "effective_on": "2026-01-01",
                            "source_ref": "policy-v1.pdf",
                            "requirements": [
                                {"requirement_id": "r1", "text": "Retain logs."}
                            ],
                        },
                        {
                            "version_id": "v2",
                            "effective_on": "2026-06-01",
                            "source_ref": "policy-v2.pdf",
                            "requirements": [
                                {
                                    "requirement_id": "r1",
                                    "text": "Retain protected logs.",
                                }
                            ],
                        },
                    ],
                }
            ]
        },
    )

    policy_id: str = Field(min_length=1, max_length=200)
    versions: list[PolicyVersion] = Field(min_length=2, max_length=1_000)

    @model_validator(mode="after")
    def validate_versions(self) -> KA1089Input:
        identifiers = [item.version_id for item in self.versions]
        dates = [item.effective_on for item in self.versions]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("policy version IDs must be unique")
        if len(dates) != len(set(dates)):
            raise ValueError("policy effective dates must be unique")
        return self


class KA1089PolicyEvolutionTracker(KnowledgeAlgorithm):
    """Compare consecutive supplied policy versions without persisting changes."""

    input_schema = KA1089Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1089"

    def _run_logic(self, input_data: KA1089Input) -> dict[str, Any]:
        versions = sorted(input_data.versions, key=lambda item: item.effective_on)
        changes = []
        for previous, current in pairwise(versions):
            before = {item.requirement_id: item.text for item in previous.requirements}
            after = {item.requirement_id: item.text for item in current.requirements}
            changes.append(
                {
                    "from_version": previous.version_id,
                    "to_version": current.version_id,
                    "added_requirement_ids": sorted(after.keys() - before.keys()),
                    "removed_requirement_ids": sorted(before.keys() - after.keys()),
                    "changed_requirement_ids": sorted(
                        requirement_id
                        for requirement_id in before.keys() & after.keys()
                        if before[requirement_id].strip() != after[requirement_id].strip()
                    ),
                    "source_refs": [previous.source_ref, current.source_ref],
                }
            )
        return {
            "success": True,
            "status": "policy_evolution_tracked",
            "policy_id": input_data.policy_id,
            "version_order": [item.version_id for item in versions],
            "changes": changes,
            "policy_store_updated": False,
            "deterministic": True,
            "limitations": (
                "This compares declared requirement IDs and text. It does not "
                "interpret legal meaning or authenticate policy sources."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1089PolicyEvolutionTracker(context).run(context)

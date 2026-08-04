"""KA-052: deterministic temporal knowledge-maintenance proposals."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class TemporalKnowledgeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_id: str = Field(min_length=1, max_length=200)
    last_validated_on: date
    current_version: int = Field(ge=1, le=1_000_000)
    protected: bool = False


class KA052Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "reference_date": "2026-07-25",
                    "records": [
                        {
                            "knowledge_id": "knowledge-1",
                            "last_validated_on": "2026-01-01",
                            "current_version": 10,
                            "protected": False,
                        }
                    ],
                    "dependency_results": {
                        "KA-1083": {
                            "status": "revalidation_schedule_planned",
                            "schedule": [
                                {
                                    "knowledge_id": "knowledge-1",
                                    "due_on": "2026-01-31",
                                    "overdue": True,
                                    "interval_days": 30,
                                    "reasons": ["risk:high"],
                                }
                            ],
                        }
                    },
                }
            ]
        },
    )

    reference_date: date
    records: list[TemporalKnowledgeRecord] = Field(min_length=1, max_length=20_000)
    dependency_results: dict[str, dict[str, Any]]
    retirement_review_age_days: int = Field(default=30, ge=1, le=100_000)
    version_review_limit: int = Field(default=10, ge=1, le=1_000_000)

    @model_validator(mode="after")
    def validate_records(self) -> KA052Input:
        identifiers = [item.knowledge_id for item in self.records]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("knowledge IDs must be unique")
        if any(item.last_validated_on > self.reference_date for item in self.records):
            raise ValueError("validation dates cannot be after the reference date")
        if set(self.dependency_results) != {"KA-1083"}:
            raise ValueError("KA-052 requires the exact KA-1083 dependency result")
        scheduler = self.dependency_results["KA-1083"]
        if scheduler.get("status") != "revalidation_schedule_planned":
            raise ValueError("KA-1083 dependency status is invalid")
        schedule = scheduler.get("schedule")
        if not isinstance(schedule, list):
            raise TypeError("KA-1083 schedule is required")
        scheduled_ids = {
            str(item.get("knowledge_id"))
            for item in schedule
            if isinstance(item, dict) and item.get("knowledge_id")
        }
        if scheduled_ids != set(identifiers):
            raise ValueError("KA-1083 schedule must cover the exact knowledge IDs")
        return self


class KA052TemporalKnowledgeEvolution(KnowledgeAlgorithm):
    """Propose version or retirement review without mutating the knowledge base."""

    input_schema = KA052Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-052"

    def _run_logic(self, input_data: KA052Input) -> dict[str, Any]:
        schedule = {
            str(item["knowledge_id"]): item
            for item in input_data.dependency_results["KA-1083"]["schedule"]
        }
        proposals = []
        for item in sorted(input_data.records, key=lambda row: row.knowledge_id):
            scheduled = schedule[item.knowledge_id]
            age_days = (input_data.reference_date - item.last_validated_on).days
            overdue = bool(scheduled.get("overdue"))
            if not overdue:
                action = "retain"
                reasons = ["revalidation_not_due"]
            elif (
                not item.protected
                and age_days >= input_data.retirement_review_age_days
                and item.current_version >= input_data.version_review_limit
            ):
                action = "retirement_review"
                reasons = [
                    "revalidation_overdue",
                    "age_threshold_met",
                    "version_limit_met",
                ]
            else:
                action = "version_review"
                reasons = ["revalidation_overdue"]
                if item.protected:
                    reasons.append("protected_from_retirement")
            proposals.append(
                {
                    "knowledge_id": item.knowledge_id,
                    "current_version": item.current_version,
                    "age_days": age_days,
                    "action": action,
                    "reasons": reasons,
                    "change_applied": False,
                }
            )
        plan_sha256 = hashlib.sha256(
            json.dumps(
                proposals,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return {
            "success": True,
            "status": "temporal_maintenance_proposed",
            "proposals": proposals,
            "plan_sha256": plan_sha256,
            "dependency_consumed": "KA-1083",
            "versions_created": 0,
            "retirements_applied": 0,
            "knowledge_updated": False,
            "deterministic": True,
            "limitations": (
                "The result converts an owner-supplied revalidation schedule into "
                "review proposals only; it neither creates versions nor retires facts."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA052TemporalKnowledgeEvolution(context).run(context)

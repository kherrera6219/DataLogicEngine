"""KA-1083: deterministic knowledge revalidation schedule planning."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class RevalidationCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_id: str = Field(min_length=1, max_length=200)
    last_validated_on: date
    risk_class: Literal["low", "medium", "high", "critical"]
    confidence: float = Field(ge=0, le=1)
    drift_detected: bool = False
    incident_open: bool = False


class KA1083Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "reference_date": "2026-07-25",
                    "candidates": [
                        {
                            "knowledge_id": "knowledge-1",
                            "last_validated_on": "2026-01-01",
                            "risk_class": "high",
                            "confidence": 0.8,
                            "drift_detected": True,
                        }
                    ],
                }
            ]
        },
    )

    reference_date: date
    candidates: list[RevalidationCandidate] = Field(
        min_length=1,
        max_length=20_000,
    )
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1083Input:
        identifiers = [item.knowledge_id for item in self.candidates]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("knowledge IDs must be unique")
        if self.dependency_results:
            if set(self.dependency_results) != {"KA-1082"}:
                raise ValueError("KA-1083 accepts only the KA-1082 dependency result")
            drift = self.dependency_results["KA-1082"]
            if drift.get("status") != "confidence_drift_measured":
                raise ValueError("KA-1082 dependency status is invalid")
            measurements = drift.get("measurements")
            if not isinstance(measurements, list):
                raise ValueError("KA-1082 measurements are required")
            measured_ids = {
                str(item.get("knowledge_id"))
                for item in measurements
                if isinstance(item, dict) and item.get("knowledge_id")
            }
            if measured_ids != set(identifiers):
                raise ValueError(
                    "KA-1082 measurements must cover the exact knowledge IDs"
                )
        return self


class KA1083KnowledgeRevalidationScheduler(KnowledgeAlgorithm):
    """Plan due dates without creating jobs in an external scheduler."""

    input_schema = KA1083Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1083"

    def _run_logic(self, input_data: KA1083Input) -> dict[str, Any]:
        base_intervals = {"low": 180, "medium": 90, "high": 30, "critical": 7}
        drift_by_id = {
            str(item["knowledge_id"]): bool(item.get("degradation_detected"))
            for item in input_data.dependency_results.get("KA-1082", {}).get(
                "measurements", []
            )
        }
        schedule = []
        for item in sorted(input_data.candidates, key=lambda row: row.knowledge_id):
            interval = base_intervals[item.risk_class]
            reasons = [f"risk:{item.risk_class}"]
            if item.confidence < 0.7:
                interval = min(interval, 14)
                reasons.append("low_confidence")
            drift_detected = item.drift_detected or drift_by_id.get(
                item.knowledge_id,
                False,
            )
            if drift_detected:
                interval = 0
                reasons.append("drift_detected")
            if item.incident_open:
                interval = 0
                reasons.append("incident_open")
            due_on = item.last_validated_on + timedelta(days=interval)
            schedule.append(
                {
                    "knowledge_id": item.knowledge_id,
                    "due_on": due_on.isoformat(),
                    "overdue": due_on <= input_data.reference_date,
                    "interval_days": interval,
                    "reasons": reasons,
                }
            )
        schedule.sort(key=lambda item: (item["due_on"], item["knowledge_id"]))
        return {
            "success": True,
            "status": "revalidation_schedule_planned",
            "reference_date": input_data.reference_date.isoformat(),
            "schedule": schedule,
            "dependency_consumed": (
                "KA-1082" if input_data.dependency_results else None
            ),
            "jobs_scheduled": 0,
            "effect_service_required": True,
            "deterministic": True,
            "limitations": (
                "Due dates are policy recommendations. An authorized scheduler "
                "must create, deduplicate, and execute revalidation jobs."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1083KnowledgeRevalidationScheduler(context).run(context)

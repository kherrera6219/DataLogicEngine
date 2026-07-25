"""KA-1086: deterministic aggregation of supplied knowledge-usage events."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class UsageEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=200)
    knowledge_id: str = Field(min_length=1, max_length=200)
    session_id: str = Field(min_length=1, max_length=200)
    occurred_at: datetime
    action: Literal["retrieved", "cited", "updated", "rejected"]
    successful: bool


class KA1086Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "events": [
                        {
                            "event_id": "event-1",
                            "knowledge_id": "knowledge-1",
                            "session_id": "session-1",
                            "occurred_at": "2026-07-25T00:00:00Z",
                            "action": "retrieved",
                            "successful": True,
                        }
                    ]
                }
            ]
        },
    )

    events: list[UsageEvent] = Field(min_length=1, max_length=100_000)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1086Input:
        identifiers = [event.event_id for event in self.events]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("usage event IDs must be unique")
        return self


class KA1086KnowledgeUsageAnalytics(KnowledgeAlgorithm):
    """Aggregate already-recorded events without collecting new telemetry."""

    input_schema = KA1086Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1086"

    def _run_logic(self, input_data: KA1086Input) -> dict[str, Any]:
        grouped: dict[str, list[UsageEvent]] = defaultdict(list)
        for event in input_data.events:
            grouped[event.knowledge_id].append(event)
        analytics = []
        for knowledge_id in sorted(grouped):
            events = grouped[knowledge_id]
            action_counts = {
                action: sum(event.action == action for event in events)
                for action in ("retrieved", "cited", "updated", "rejected")
            }
            successful = sum(event.successful for event in events)
            analytics.append(
                {
                    "knowledge_id": knowledge_id,
                    "event_count": len(events),
                    "successful_event_count": successful,
                    "success_ratio": round(successful / len(events), 8),
                    "unique_session_count": len(
                        {event.session_id for event in events}
                    ),
                    "action_counts": action_counts,
                    "first_used_at": min(event.occurred_at for event in events).isoformat(),
                    "last_used_at": max(event.occurred_at for event in events).isoformat(),
                }
            )
        analytics.sort(key=lambda item: (-item["event_count"], item["knowledge_id"]))
        return {
            "success": True,
            "status": "knowledge_usage_aggregated",
            "analytics": analytics,
            "input_event_count": len(input_data.events),
            "telemetry_collected": False,
            "deterministic": True,
            "limitations": (
                "Results summarize caller-supplied events and cannot measure "
                "unrecorded use, user intent, or knowledge correctness."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1086KnowledgeUsageAnalytics(context).run(context)

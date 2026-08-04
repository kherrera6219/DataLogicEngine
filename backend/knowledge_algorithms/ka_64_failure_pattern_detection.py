"""KA-064: deterministic failure-code frequency measurement."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class FailureEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    occurrence_id: str = Field(min_length=1, max_length=200)
    failure_code: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$",
    )
    component: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$",
    )


class KA064Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "failure_events": [
                        {
                            "occurrence_id": "event-1",
                            "failure_code": "deletion_failed",
                            "component": "neo4j",
                        }
                    ],
                    "minimum_occurrences": 1,
                }
            ]
        },
    )

    failure_events: list[FailureEvent] = Field(default_factory=list, max_length=50_000)
    minimum_occurrences: int = Field(default=3, ge=1, le=50_000)

    @model_validator(mode="after")
    def validate_occurrences(self) -> KA064Input:
        identifiers = [item.occurrence_id for item in self.failure_events]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("failure occurrence IDs must be unique")
        return self


class KA064FailurePatternDetection(KnowledgeAlgorithm):
    """Count exact content-free failure codes without scanning raw log text."""

    input_schema = KA064Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-064"

    def _run_logic(self, input_data: KA064Input) -> dict[str, Any]:
        counts = Counter(
            (item.component.lower(), item.failure_code.lower())
            for item in input_data.failure_events
        )
        patterns = []
        for (component, failure_code), count in sorted(counts.items()):
            if count < input_data.minimum_occurrences:
                continue
            signature_sha256 = hashlib.sha256(
                f"{component}:{failure_code}".encode()
            ).hexdigest()
            patterns.append(
                {
                    "component": component,
                    "failure_code": failure_code,
                    "occurrence_count": count,
                    "signature_sha256": signature_sha256,
                    "review_recommended": True,
                }
            )
        return {
            "success": True,
            "status": "failure_patterns_measured",
            "patterns": patterns,
            "event_count": len(input_data.failure_events),
            "alerts_dispatched": 0,
            "blacklisting_applied": False,
            "log_content_scanned": False,
            "deterministic": True,
            "limitations": (
                "Only exact caller-supplied content-free failure codes are counted. "
                "The result does not inspect logs, diagnose root cause, dispatch an "
                "alert, blacklist a source, or apply mitigation."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA064FailurePatternDetection(context).run(context)

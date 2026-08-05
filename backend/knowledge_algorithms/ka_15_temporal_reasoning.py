"""KA-015: deterministic temporal validity measurement."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


def _utc_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a UTC offset")
    return parsed.astimezone(UTC)


class TemporalFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fact_id: str = Field(min_length=1, max_length=200)
    observed_at: str
    expires_at: str | None = None

    @field_validator("observed_at", "expires_at")
    @classmethod
    def validate_timestamp(cls, value: str | None) -> str | None:
        if value is not None:
            _utc_datetime(value)
        return value

    @model_validator(mode="after")
    def validate_window(self) -> TemporalFact:
        if self.expires_at and _utc_datetime(self.expires_at) < _utc_datetime(
            self.observed_at
        ):
            raise ValueError("expires_at cannot precede observed_at")
        return self


class KA015Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "facts": [
                        {
                            "fact_id": "fact-1",
                            "observed_at": "2026-01-01T00:00:00Z",
                        }
                    ],
                    "reference_time": "2026-08-04T00:00:00Z",
                }
            ]
        },
    )

    facts: list[TemporalFact] = Field(min_length=1, max_length=10_000)
    reference_time: str
    default_validity_days: int = Field(default=365, ge=1, le=36_500)

    @field_validator("reference_time")
    @classmethod
    def validate_reference_time(cls, value: str) -> str:
        _utc_datetime(value)
        return value


class KA015TemporalReasoning(KnowledgeAlgorithm):
    """Measure supplied validity windows without consulting a system clock."""

    input_schema = KA015Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-015"

    def _run_logic(self, input_data: KA015Input) -> dict[str, Any]:
        reference = _utc_datetime(input_data.reference_time)
        results = []
        for fact in sorted(input_data.facts, key=lambda item: item.fact_id):
            observed = _utc_datetime(fact.observed_at)
            expires = (
                _utc_datetime(fact.expires_at)
                if fact.expires_at
                else observed + timedelta(days=input_data.default_validity_days)
            )
            if reference < observed:
                status = "future_dated"
                relative_days = (observed - reference).days
            elif reference > expires:
                status = "expired"
                relative_days = (reference - expires).days
            else:
                status = "valid"
                relative_days = (expires - reference).days
            results.append(
                {
                    "fact_id": fact.fact_id,
                    "status": status,
                    "observed_at": observed.isoformat().replace("+00:00", "Z"),
                    "expires_at": expires.isoformat().replace("+00:00", "Z"),
                    "relative_days": relative_days,
                    "validity_changed": False,
                }
            )
        return {
            "success": True,
            "status": "temporal_validity_measured",
            "reference_time": reference.isoformat().replace("+00:00", "Z"),
            "results": results,
            "expired_count": sum(row["status"] == "expired" for row in results),
            "system_clock_used": False,
            "knowledge_updated": False,
            "deterministic": True,
            "limitations": (
                "Validity reflects only supplied timestamps and the declared default "
                "window; it does not establish factual currency or retire knowledge."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA015TemporalReasoning(context).run(context)

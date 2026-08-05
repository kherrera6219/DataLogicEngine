"""KA-116: deterministic token-distribution entropy measurement."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA116Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"content": "alpha beta gamma delta"}]},
    )

    content: str = Field(default="", max_length=1_000_000)
    claims: list[Any] = Field(default_factory=list, max_length=20_000)
    threshold: float = Field(default=0.82, ge=0, le=1)

    @field_validator("claims", mode="before")
    @classmethod
    def coerce_claims(cls, value: Any) -> list[Any]:
        if value is None:
            return []
        return value if isinstance(value, list) else [value]


class KA116EntropyDetection(KnowledgeAlgorithm):
    """Measure lexical distribution entropy without inferring system decay."""

    input_schema = KA116Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-116"

    def _run_logic(self, input_data: KA116Input) -> dict[str, Any]:
        from backend.knowledge_algorithms.l10.l10_ka_001_entropy_scorer import (
            run as entropy_run,
        )

        content = input_data.content
        if not content and input_data.claims:
            content = " ".join(str(claim) for claim in input_data.claims)
        measurement = entropy_run({"content": content, "threshold": input_data.threshold})
        entropy_score = float(measurement["entropy_score"])
        critical = entropy_score >= input_data.threshold
        return {
            "success": True,
            "status": "token_entropy_measured",
            "entropy_score": entropy_score,
            "state": "CRITICAL" if critical else "STABLE",
            "token_count": int(measurement["token_count"]),
            "reconciliation_proposed": critical,
            "reconciliation_triggered": False,
            "system_decay_established": False,
            "deterministic": True,
            "limitations": (
                "Token-distribution entropy does not measure truth, knowledge decay, "
                "or overall system health and cannot trigger reconciliation."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA116EntropyDetection(context).run(context)

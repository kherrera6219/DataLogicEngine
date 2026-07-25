"""KA-1074: deterministic field-level privacy transformation."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class PrivacyField(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_id: str = Field(min_length=1, max_length=500)
    value: str = Field(max_length=100_000)
    classification: Literal["public", "personal", "sensitive", "secret"]
    strategy: Literal["retain", "redact", "drop"] | None = None

    @model_validator(mode="after")
    def reject_sensitive_retention(self) -> PrivacyField:
        if self.classification != "public" and self.strategy == "retain":
            raise ValueError("non-public fields cannot use the retain strategy")
        return self


class KA1074Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "fields": [
                        {
                            "field_id": "display_name",
                            "value": "Ada",
                            "classification": "personal",
                            "strategy": "redact",
                        },
                        {
                            "field_id": "status",
                            "value": "active",
                            "classification": "public",
                        },
                    ]
                }
            ]
        },
    )

    fields: list[PrivacyField] = Field(min_length=1, max_length=2_000)

    @model_validator(mode="after")
    def validate_fields(self) -> KA1074Input:
        identifiers = [field.field_id for field in self.fields]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("privacy field IDs must be unique")
        if sum(len(field.value) for field in self.fields) > 2_000_000:
            raise ValueError("privacy input exceeds 2,000,000 characters")
        return self


class KA1074PrivacyPreserver(KnowledgeAlgorithm):
    """Remove non-public values without emitting them in metadata or logs."""

    input_schema = KA1074Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1074"

    def _run_logic(self, input_data: KA1074Input) -> dict[str, Any]:
        protected: dict[str, str] = {}
        dropped: list[str] = []
        applied: list[dict[str, str]] = []
        for field in sorted(input_data.fields, key=lambda item: item.field_id):
            strategy = field.strategy or (
                "retain" if field.classification == "public" else "redact"
            )
            if strategy == "drop":
                dropped.append(field.field_id)
            elif strategy == "redact":
                protected[field.field_id] = (
                    f"[REDACTED:{field.classification.upper()}]"
                )
            else:
                protected[field.field_id] = field.value
            applied.append(
                {
                    "field_id": field.field_id,
                    "classification": field.classification,
                    "strategy": strategy,
                }
            )
        return {
            "success": True,
            "status": "privacy_transformation_complete",
            "protected_fields": protected,
            "dropped_field_ids": dropped,
            "applied_strategies": applied,
            "non_public_value_exposed": False,
            "deterministic": True,
            "limitations": (
                "Classification and field boundaries are caller supplied. "
                "Redaction does not discover undeclared sensitive content."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1074PrivacyPreserver(context).run(context)

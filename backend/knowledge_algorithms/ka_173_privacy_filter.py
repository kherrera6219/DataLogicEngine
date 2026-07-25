"""KA-173: deterministic exact-value privacy filtering."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class PrivacyValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: Literal["name", "email", "phone", "address", "identifier", "secret"]
    value: str = Field(min_length=1, max_length=10_000)


class KA173Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "text": "Contact Alice at owner@example.com.",
                    "sensitive_values": [
                        {"label": "name", "value": "Alice"},
                        {"label": "email", "value": "owner@example.com"},
                    ],
                }
            ]
        },
    )

    text: str = Field(max_length=1_000_000)
    sensitive_values: list[PrivacyValue] = Field(
        min_length=1, max_length=10_000, exclude=True
    )
    replacement_format: Literal["typed", "generic"] = "typed"

    @model_validator(mode="after")
    def validate_values(self) -> KA173Input:
        values = [item.value for item in self.sensitive_values]
        if len(values) != len(set(values)):
            raise ValueError("sensitive values must be unique")
        return self


class KA173PrivacyFilter(KnowledgeAlgorithm):
    """Replace caller-declared sensitive values without returning source values."""

    input_schema = KA173Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-173"

    def _run_logic(self, input_data: KA173Input) -> dict[str, Any]:
        filtered = input_data.text
        counts: dict[str, int] = {}
        for item in sorted(
            input_data.sensitive_values, key=lambda row: (-len(row.value), row.label)
        ):
            count = filtered.count(item.value)
            if count:
                replacement = (
                    f"[REDACTED_{item.label.upper()}]"
                    if input_data.replacement_format == "typed"
                    else "[REDACTED]"
                )
                filtered = filtered.replace(item.value, replacement)
                counts[item.label] = counts.get(item.label, 0) + count
        return {
            "success": True,
            "status": "privacy_filtered",
            "filtered_text": filtered,
            "replacement_counts": dict(sorted(counts.items())),
            "source_values_returned": False,
            "source_modified": False,
            "deterministic": True,
            "limitations": (
                "Filtering replaces only exact caller-declared values and must be "
                "preceded by discovery/classification for unknown sensitive data."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA173PrivacyFilter(context).run(context)

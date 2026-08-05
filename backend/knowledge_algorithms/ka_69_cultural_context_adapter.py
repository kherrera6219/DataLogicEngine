"""KA-069: deterministic formatting guidance for an explicit locale group."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA069Input(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    culture: Literal[
        "global",
        "regional_na",
        "regional_eu",
        "regional_asia",
    ] = "global"
    text: str = Field(default="", max_length=100_000)
    numeric_values: dict[str, float] = Field(default_factory=dict)


class KA069CulturalContextAdapter(KnowledgeAlgorithm):
    """Return locale formatting guidance without inferring culture or rewriting text."""

    input_schema = KA069Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-069"

    def _run_logic(self, input_data: KA069Input) -> dict[str, Any]:
        locale_rules = {
            "global": ("neutral", ".", ",", 2),
            "regional_na": ("neutral", ".", ",", 2),
            "regional_eu": ("privacy_aware", ",", ".", 2),
            "regional_asia": ("neutral", ".", ",", 0),
        }
        framing, decimal_separator, thousands_separator, decimal_places = locale_rules[
            input_data.culture
        ]
        numeric_format = {
            key: {
                "value": value,
                "decimal_separator": decimal_separator,
                "thousands_separator": thousands_separator,
                "decimal_places": decimal_places,
            }
            for key, value in sorted(input_data.numeric_values.items())
        }
        return {
            "ka_id": "KA-069",
            "success": True,
            "status": "cultural_formatting_proposed",
            "culture_applied": input_data.culture,
            "framing": framing,
            "numeric_format_specifications": numeric_format,
            "locale_detected": False,
            "text_content_inspected": False,
            "text_content_returned": False,
            "content_rewritten": False,
            "profile_updated": False,
            "context_applied": False,
            "deterministic": True,
            "limitations": (
                "Culture must be explicit. The KA provides neutral formatting guidance "
                "and does not infer identity, stereotype users, or rewrite content."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA069CulturalContextAdapter(context).run(context)

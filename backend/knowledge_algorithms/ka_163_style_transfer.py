"""KA-163: deterministic bounded style normalization."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA163Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "text": "Utilize the system in order to complete the task.",
                    "target_style": "plain",
                }
            ]
        },
    )

    text: str = Field(min_length=1, max_length=100_000)
    target_style: Literal["plain", "formal", "concise"]


class KA163StyleTransfer(KnowledgeAlgorithm):
    """Apply transparent, fixed style transformations without content invention."""

    input_schema = KA163Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-163"

    def _run_logic(self, input_data: KA163Input) -> dict[str, Any]:
        transformed = re.sub(r"\s+", " ", input_data.text).strip()
        replacements = {
            "plain": {
                r"\butilize\b": "use",
                r"\bin order to\b": "to",
                r"\bcommence\b": "start",
            },
            "formal": {
                r"\bcan't\b": "cannot",
                r"\bwon't\b": "will not",
                r"\bdoesn't\b": "does not",
            },
            "concise": {
                r"\bin order to\b": "to",
                r"\bdue to the fact that\b": "because",
                r"\bat this point in time\b": "now",
            },
        }
        applied = []
        for pattern, replacement in replacements[input_data.target_style].items():
            transformed, count = re.subn(
                pattern, replacement, transformed, flags=re.IGNORECASE
            )
            if count:
                applied.append({"pattern": pattern, "count": count})
        return {
            "success": True,
            "status": "style_transferred",
            "styled_text": transformed,
            "target_style": input_data.target_style,
            "transformations": applied,
            "content_generated": False,
            "deterministic": True,
            "limitations": (
                "The fixed rules normalize a narrow style profile and do not "
                "guarantee tone, semantic preservation, or comprehensive rewriting."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA163StyleTransfer(context).run(context)

"""KA-161: evidence-backed translation assembly."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class TranslationSegment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segment_id: str = Field(min_length=1, max_length=200)
    source_text: str = Field(min_length=1, max_length=100_000)
    translated_text: str = Field(min_length=1, max_length=100_000)
    evidence_ref: str = Field(min_length=1, max_length=2_000)
    confidence: float = Field(ge=0, le=1)


class KA161Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "source_language": "en",
                    "target_language": "es",
                    "segments": [
                        {
                            "segment_id": "s1",
                            "source_text": "Hello",
                            "translated_text": "Hola",
                            "evidence_ref": "provider-output-1",
                            "confidence": 0.95,
                        }
                    ],
                }
            ]
        },
    )

    source_language: str = Field(pattern=r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?$")
    target_language: str = Field(pattern=r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?$")
    segments: list[TranslationSegment] = Field(min_length=1, max_length=10_000)
    minimum_confidence: float = Field(default=0.8, ge=0, le=1)

    @model_validator(mode="after")
    def validate_languages(self) -> KA161Input:
        if self.source_language.casefold() == self.target_language.casefold():
            raise ValueError("source and target languages must differ")
        return self


class KA161Translation(KnowledgeAlgorithm):
    """Validate and assemble translation segments with explicit provenance."""

    input_schema = KA161Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-161"

    def _run_logic(self, input_data: KA161Input) -> dict[str, Any]:
        rejected = [
            item.segment_id
            for item in input_data.segments
            if item.confidence < input_data.minimum_confidence
        ]
        return {
            "success": True,
            "status": "translation_evidence_evaluated",
            "accepted": not rejected,
            "translated_text": (
                "\n".join(item.translated_text for item in input_data.segments)
                if not rejected
                else None
            ),
            "segment_evidence": [
                {
                    "segment_id": item.segment_id,
                    "evidence_ref": item.evidence_ref,
                    "confidence": item.confidence,
                }
                for item in input_data.segments
            ],
            "rejected_segment_ids": rejected,
            "provider_called": False,
            "deterministic": True,
            "limitations": (
                "The KA validates and assembles supplied translations; a governed "
                "provider or approved translation memory must create the segments."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA161Translation(context).run(context)

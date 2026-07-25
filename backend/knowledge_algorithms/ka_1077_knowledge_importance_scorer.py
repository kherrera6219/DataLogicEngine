"""KA-1077: deterministic knowledge importance scoring."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ImportanceCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_id: str = Field(min_length=1, max_length=200)
    relevance: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    freshness: float = Field(ge=0, le=1)
    reuse_count: int = Field(ge=0, le=1_000_000)
    dependent_count: int = Field(ge=0, le=1_000_000)


class KA1077Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "candidates": [
                        {
                            "knowledge_id": "knowledge-1",
                            "relevance": 0.9,
                            "confidence": 0.8,
                            "freshness": 0.7,
                            "reuse_count": 20,
                            "dependent_count": 5,
                        }
                    ]
                }
            ]
        },
    )

    candidates: list[ImportanceCandidate] = Field(min_length=1, max_length=20_000)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1077Input:
        identifiers = [item.knowledge_id for item in self.candidates]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("knowledge IDs must be unique")
        return self


class KA1077KnowledgeImportanceScorer(KnowledgeAlgorithm):
    """Rank supplied knowledge using declared bounded operational signals."""

    input_schema = KA1077Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1077"

    def _run_logic(self, input_data: KA1077Input) -> dict[str, Any]:
        scores = []
        for item in input_data.candidates:
            reuse = min(item.reuse_count / 100, 1)
            dependencies = min(item.dependent_count / 20, 1)
            score = (
                item.relevance * 0.35
                + item.confidence * 0.2
                + item.freshness * 0.15
                + reuse * 0.2
                + dependencies * 0.1
            )
            scores.append(
                {
                    "knowledge_id": item.knowledge_id,
                    "importance_score": round(score, 8),
                    "components": {
                        "relevance": item.relevance,
                        "confidence": item.confidence,
                        "freshness": item.freshness,
                        "normalized_reuse": round(reuse, 8),
                        "normalized_dependents": round(dependencies, 8),
                    },
                }
            )
        scores.sort(
            key=lambda item: (-item["importance_score"], item["knowledge_id"])
        )
        return {
            "success": True,
            "status": "knowledge_importance_scored",
            "ranked_knowledge": scores,
            "scoring_method": "bounded_weighted_operational_signals",
            "deterministic": True,
            "limitations": (
                "Importance is an operational ranking of caller-supplied signals, "
                "not factual quality or intrinsic value."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1077KnowledgeImportanceScorer(context).run(context)

"""KA-1044: bounded deterministic composition of candidate hypotheses."""

from __future__ import annotations

import hashlib
from itertools import combinations
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.knowledge_algorithms.production_utils import normalized_tokens
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class CompositionSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1, max_length=200)
    statement: str = Field(min_length=1, max_length=20_000)
    concepts: list[str] = Field(min_length=1, max_length=100)
    evidence_refs: list[str] = Field(default_factory=list, max_length=500)
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_sets(self) -> CompositionSource:
        if len(self.concepts) != len(set(self.concepts)):
            raise ValueError("source concepts must be unique")
        if len(self.evidence_refs) != len(set(self.evidence_refs)):
            raise ValueError("evidence references must be unique")
        return self


class KA1044Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "composition_goal": "reduce incident recovery time",
                    "sources": [
                        {
                            "source_id": "runbook",
                            "statement": "Validated runbooks reduce operator delay.",
                            "concepts": ["operations", "recovery"],
                            "evidence_refs": ["evidence-1"],
                            "confidence": 0.9,
                        },
                        {
                            "source_id": "automation",
                            "statement": "Automated checks identify failed services.",
                            "concepts": ["automation", "recovery"],
                            "evidence_refs": ["evidence-2"],
                            "confidence": 0.8,
                        },
                    ],
                }
            ]
        },
    )

    composition_goal: str = Field(min_length=1, max_length=2_000)
    sources: list[CompositionSource] = Field(min_length=2, max_length=100)
    maximum_hypotheses: int = Field(default=10, ge=1, le=100)
    minimum_source_confidence: float = Field(default=0.5, ge=0, le=1)

    @model_validator(mode="after")
    def validate_source_ids(self) -> KA1044Input:
        identifiers = [item.source_id for item in self.sources]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("composition source IDs must be unique")
        return self


class KA1044CreativeKnowledgeComposer(KnowledgeAlgorithm):
    """Generate traceable candidate hypotheses without asserting they are true."""

    input_schema = KA1044Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1044"

    @staticmethod
    def _novelty(left: str, right: str) -> float:
        left_tokens = normalized_tokens(left)
        right_tokens = normalized_tokens(right)
        union = left_tokens | right_tokens
        similarity = 1.0 if not union else len(left_tokens & right_tokens) / len(union)
        return 1 - similarity

    def _run_logic(self, input_data: KA1044Input) -> dict[str, Any]:
        eligible = sorted(
            (
                item
                for item in input_data.sources
                if item.confidence >= input_data.minimum_source_confidence
            ),
            key=lambda item: item.source_id,
        )
        candidates: list[dict[str, Any]] = []
        for left, right in combinations(eligible, 2):
            novelty = self._novelty(left.statement, right.statement)
            shared_concepts = sorted(set(left.concepts) & set(right.concepts))
            confidence = (left.confidence + right.confidence) / 2
            composition_score = (confidence * 0.6) + (novelty * 0.3) + (
                (1.0 if shared_concepts else 0.0) * 0.1
            )
            source_ids = [left.source_id, right.source_id]
            digest = hashlib.sha256(
                f"{input_data.composition_goal}|{'|'.join(source_ids)}".encode()
            ).hexdigest()[:16]
            candidates.append(
                {
                    "hypothesis_id": f"hypothesis-{digest}",
                    "hypothesis": (
                        f"For the goal '{input_data.composition_goal}', evaluate "
                        f"whether combining '{left.statement}' with "
                        f"'{right.statement}' improves the outcome."
                    ),
                    "source_ids": source_ids,
                    "evidence_refs": sorted(
                        set(left.evidence_refs) | set(right.evidence_refs)
                    ),
                    "shared_concepts": shared_concepts,
                    "novelty_score": round(novelty, 8),
                    "composition_score": round(composition_score, 8),
                    "validation_status": "unverified_candidate",
                }
            )
        candidates.sort(
            key=lambda item: (
                -item["composition_score"],
                item["hypothesis_id"],
            )
        )
        selected = candidates[: input_data.maximum_hypotheses]
        return {
            "success": True,
            "status": "candidate_hypotheses_composed",
            "candidate_hypotheses": selected,
            "eligible_source_count": len(eligible),
            "candidate_count_before_limit": len(candidates),
            "truncated": len(candidates) > len(selected),
            "knowledge_persisted": False,
            "deterministic": True,
            "limitations": (
                "Compositions are traceable, deterministic research candidates, "
                "not factual conclusions. They require evidence validation "
                "before use or persistence."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1044CreativeKnowledgeComposer(context).run(context)

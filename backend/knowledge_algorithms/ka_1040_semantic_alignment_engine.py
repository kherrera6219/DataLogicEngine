"""KA-1040: deterministic semantic alignment proposal generation."""

from __future__ import annotations

import re
from itertools import combinations
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.knowledge_algorithms.production_utils import normalized_tokens
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


class SemanticConcept(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str = Field(min_length=1, max_length=200)
    label: str = Field(min_length=1, max_length=500)
    definition: str | None = Field(default=None, max_length=20_000)
    synonyms: list[str] = Field(default_factory=list, max_length=100)


class SuppliedSemanticSimilarity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    left_concept_id: str = Field(min_length=1, max_length=200)
    right_concept_id: str = Field(min_length=1, max_length=200)
    score: float = Field(ge=0, le=1)
    method: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def reject_self_pair(self) -> SuppliedSemanticSimilarity:
        if self.left_concept_id == self.right_concept_id:
            raise ValueError("semantic similarity requires two distinct concepts")
        return self


class KA1040Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "concepts": [
                        {
                            "concept_id": "customer",
                            "label": "Customer",
                            "synonyms": ["client"],
                        },
                        {
                            "concept_id": "client",
                            "label": "Client",
                            "synonyms": ["customer"],
                        },
                    ],
                    "alignment_threshold": 0.8,
                }
            ]
        },
    )

    concepts: list[SemanticConcept] = Field(min_length=2, max_length=500)
    supplied_similarities: list[SuppliedSemanticSimilarity] = Field(
        default_factory=list,
        max_length=124_750,
    )
    alignment_threshold: float = Field(default=0.8, ge=0, le=1)

    @model_validator(mode="after")
    def validate_identity(self) -> KA1040Input:
        concept_ids = [item.concept_id for item in self.concepts]
        if len(concept_ids) != len(set(concept_ids)):
            raise ValueError("concept IDs must be unique")
        known = set(concept_ids)
        pairs: list[tuple[str, str]] = []
        for metric in self.supplied_similarities:
            if (
                metric.left_concept_id not in known
                or metric.right_concept_id not in known
            ):
                raise ValueError("semantic similarity references an unknown concept")
            pairs.append(
                tuple(sorted((metric.left_concept_id, metric.right_concept_id)))
            )
        if len(pairs) != len(set(pairs)):
            raise ValueError("semantic similarity pairs must be unique")
        return self


class KA1040SemanticAlignmentEngine(KnowledgeAlgorithm):
    """Propose ontology alignments while preserving all source concepts."""

    input_schema = KA1040Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1040"

    @staticmethod
    def _normalized_term(value: str) -> str:
        return NON_ALNUM_RE.sub("", value.casefold())

    @staticmethod
    def _jaccard(left: set[str], right: set[str]) -> float:
        union = left | right
        return 1.0 if not union else len(left & right) / len(union)

    def _run_logic(self, input_data: KA1040Input) -> dict[str, Any]:
        concepts = {
            item.concept_id: item
            for item in sorted(input_data.concepts, key=lambda item: item.concept_id)
        }
        supplied = {
            tuple(sorted((item.left_concept_id, item.right_concept_id))): item
            for item in input_data.supplied_similarities
        }
        proposals: list[dict[str, Any]] = []
        evaluated_pairs = 0

        for left_id, right_id in combinations(concepts, 2):
            evaluated_pairs += 1
            left = concepts[left_id]
            right = concepts[right_id]
            left_terms = {
                self._normalized_term(value)
                for value in [left.label, *left.synonyms]
                if value.strip()
            }
            right_terms = {
                self._normalized_term(value)
                for value in [right.label, *right.synonyms]
                if value.strip()
            }
            exact_term_overlap = sorted((left_terms & right_terms) - {""})
            metric = supplied.get((left_id, right_id))
            if exact_term_overlap:
                score = 1.0
                method = "declared_term_overlap"
            elif metric is not None:
                score = metric.score
                method = f"supplied:{metric.method}"
            else:
                left_text = " ".join(
                    value
                    for value in [left.label, left.definition or "", *left.synonyms]
                    if value
                )
                right_text = " ".join(
                    value
                    for value in [right.label, right.definition or "", *right.synonyms]
                    if value
                )
                score = self._jaccard(
                    normalized_tokens(left_text),
                    normalized_tokens(right_text),
                )
                method = "token_jaccard"
            if score >= input_data.alignment_threshold:
                proposals.append(
                    {
                        "canonical_concept_id": min(left_id, right_id),
                        "aligned_concept_id": max(left_id, right_id),
                        "alignment_score": round(score, 8),
                        "method": method,
                        "shared_normalized_terms": exact_term_overlap,
                        "action": "propose_alias_alignment",
                    }
                )

        proposals.sort(
            key=lambda item: (
                -item["alignment_score"],
                item["canonical_concept_id"],
                item["aligned_concept_id"],
            )
        )
        return {
            "success": True,
            "status": "semantic_alignment_evaluated",
            "alignment_proposals": proposals,
            "evaluated_pair_count": evaluated_pairs,
            "alignment_count": len(proposals),
            "mutation_applied": False,
            "deterministic": True,
            "limitations": (
                "Alignment scores represent declared term overlap, bounded "
                "lexical similarity, or caller-supplied semantic evidence. An "
                "ontology owner must approve and apply aliases or merges."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1040SemanticAlignmentEngine(context).run(context)

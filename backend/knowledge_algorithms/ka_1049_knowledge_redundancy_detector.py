"""KA-1049: bounded exact and near-duplicate knowledge detection."""

from __future__ import annotations

import re
from itertools import combinations
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.knowledge_algorithms.production_utils import normalized_tokens
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

WHITESPACE_RE = re.compile(r"\s+")


class KnowledgeNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=100_000)


class SuppliedSimilarity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    left_node_id: str = Field(min_length=1, max_length=200)
    right_node_id: str = Field(min_length=1, max_length=200)
    score: float = Field(ge=0, le=1)
    method: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def reject_self_pair(self) -> SuppliedSimilarity:
        if self.left_node_id == self.right_node_id:
            raise ValueError("similarity pairs require two distinct nodes")
        return self


class KA1049Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "knowledge_nodes": [
                        {
                            "node_id": "node-a",
                            "content": "Validated evidence.",
                        },
                        {
                            "node_id": "node-b",
                            "content": "Different evidence.",
                        },
                    ]
                }
            ]
        },
    )

    knowledge_nodes: list[KnowledgeNode] = Field(
        min_length=2,
        max_length=250,
    )
    similarity_metrics: list[SuppliedSimilarity] = Field(
        default_factory=list,
        max_length=31_125,
    )
    similarity_threshold: float = Field(default=0.8, ge=0, le=1)

    @model_validator(mode="after")
    def validate_identity(self) -> KA1049Input:
        node_ids = [item.node_id for item in self.knowledge_nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("knowledge node IDs must be unique")
        if sum(len(item.content) for item in self.knowledge_nodes) > 2_000_000:
            raise ValueError("knowledge content exceeds 2,000,000 characters")
        known = set(node_ids)
        pairs = []
        for metric in self.similarity_metrics:
            if metric.left_node_id not in known or metric.right_node_id not in known:
                raise ValueError("similarity metric references an unknown node")
            pairs.append(tuple(sorted((metric.left_node_id, metric.right_node_id))))
        if len(pairs) != len(set(pairs)):
            raise ValueError("similarity metric pairs must be unique")
        return self


class KA1049KnowledgeRedundancyDetector(KnowledgeAlgorithm):
    """Identify merge candidates without mutating or deleting knowledge."""

    input_schema = KA1049Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1049"

    @staticmethod
    def _normalized_content(value: str) -> str:
        return WHITESPACE_RE.sub(" ", value.strip().casefold())

    @staticmethod
    def _jaccard(left: set[str], right: set[str]) -> float:
        union = left | right
        return 1.0 if not union else len(left & right) / len(union)

    def _run_logic(self, input_data: KA1049Input) -> dict[str, Any]:
        nodes = {
            item.node_id: item
            for item in sorted(
                input_data.knowledge_nodes,
                key=lambda item: item.node_id,
            )
        }
        supplied = {
            tuple(sorted((item.left_node_id, item.right_node_id))): item
            for item in input_data.similarity_metrics
        }
        normalized = {
            node_id: self._normalized_content(item.content)
            for node_id, item in nodes.items()
        }
        tokens = {
            node_id: normalized_tokens(item.content) for node_id, item in nodes.items()
        }

        evaluated: list[dict[str, Any]] = []
        for left_id, right_id in combinations(nodes, 2):
            pair = (left_id, right_id)
            exact = normalized[left_id] == normalized[right_id]
            metric = supplied.get(pair)
            if exact:
                score = 1.0
                method = "normalized_exact_match"
            elif metric is not None:
                score = metric.score
                method = f"supplied:{metric.method}"
            else:
                score = self._jaccard(tokens[left_id], tokens[right_id])
                method = "token_jaccard"
            evaluated.append(
                {
                    "left_node_id": left_id,
                    "right_node_id": right_id,
                    "redundancy_score": round(score, 8),
                    "method": method,
                    "exact_duplicate": exact,
                }
            )

        candidates = sorted(
            (
                item
                for item in evaluated
                if item["redundancy_score"] >= input_data.similarity_threshold
            ),
            key=lambda item: (
                -item["redundancy_score"],
                item["left_node_id"],
                item["right_node_id"],
            ),
        )
        return {
            "success": True,
            "status": "redundancy_evaluated",
            "merge_candidates": candidates,
            "redundancy_scores": evaluated,
            "evaluated_pair_count": len(evaluated),
            "mutation_applied": False,
            "deterministic": True,
            "limitations": (
                "Similarity indicates duplicate wording or caller-supplied "
                "semantic proximity, not factual equivalence. Merge or deletion "
                "requires owning-service validation and authorization."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1049KnowledgeRedundancyDetector(context).run(context)

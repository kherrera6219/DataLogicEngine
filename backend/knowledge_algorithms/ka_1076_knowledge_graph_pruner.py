"""KA-1076: bounded knowledge-graph pruning proposal."""

from __future__ import annotations

from collections import Counter
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class PrunableNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(min_length=1, max_length=200)
    importance: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    age_days: int = Field(ge=0, le=100_000)
    reuse_count: int = Field(ge=0, le=1_000_000)
    protected: bool = False


class GraphEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_node_id: str = Field(min_length=1, max_length=200)
    target_node_id: str = Field(min_length=1, max_length=200)


class KA1076Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "nodes": [
                        {
                            "node_id": "old",
                            "importance": 0.1,
                            "confidence": 0.2,
                            "age_days": 500,
                            "reuse_count": 0,
                        },
                        {
                            "node_id": "active",
                            "importance": 0.9,
                            "confidence": 0.9,
                            "age_days": 2,
                            "reuse_count": 10,
                        },
                    ],
                    "edges": [],
                }
            ]
        },
    )

    nodes: list[PrunableNode] = Field(min_length=1, max_length=20_000)
    edges: list[GraphEdge] = Field(default_factory=list, max_length=100_000)
    maximum_importance: float = Field(default=0.25, ge=0, le=1)
    maximum_confidence: float = Field(default=0.5, ge=0, le=1)
    minimum_age_days: int = Field(default=180, ge=0, le=100_000)
    maximum_reuse_count: int = Field(default=0, ge=0, le=1_000_000)

    @model_validator(mode="after")
    def validate_graph(self) -> KA1076Input:
        identifiers = [node.node_id for node in self.nodes]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("graph node IDs must be unique")
        known = set(identifiers)
        if any(
            edge.source_node_id not in known or edge.target_node_id not in known
            for edge in self.edges
        ):
            raise ValueError("graph edge references an unknown node")
        return self


class KA1076KnowledgeGraphPruner(KnowledgeAlgorithm):
    """Identify archive candidates while preserving protected dependencies."""

    input_schema = KA1076Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1076"

    def _run_logic(self, input_data: KA1076Input) -> dict[str, Any]:
        inbound = Counter(edge.target_node_id for edge in input_data.edges)
        candidates: list[dict[str, Any]] = []
        retained: list[dict[str, str]] = []
        for node in sorted(input_data.nodes, key=lambda item: item.node_id):
            criteria = (
                node.importance <= input_data.maximum_importance
                and node.confidence <= input_data.maximum_confidence
                and node.age_days >= input_data.minimum_age_days
                and node.reuse_count <= input_data.maximum_reuse_count
            )
            if criteria and not node.protected and inbound[node.node_id] == 0:
                candidates.append(
                    {
                        "node_id": node.node_id,
                        "action": "archive_candidate",
                        "reason": "low_value_stale_unreferenced",
                    }
                )
            elif criteria:
                retained.append(
                    {
                        "node_id": node.node_id,
                        "reason": (
                            "protected"
                            if node.protected
                            else "referenced_by_other_nodes"
                        ),
                    }
                )
        return {
            "success": True,
            "status": "graph_pruning_evaluated",
            "archive_candidates": candidates,
            "retained_low_value_nodes": retained,
            "candidate_count": len(candidates),
            "nodes_deleted": 0,
            "mutation_applied": False,
            "deterministic": True,
            "limitations": (
                "This produces archive candidates from supplied metrics. The "
                "graph owner must revalidate dependencies and apply any change."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1076KnowledgeGraphPruner(context).run(context)

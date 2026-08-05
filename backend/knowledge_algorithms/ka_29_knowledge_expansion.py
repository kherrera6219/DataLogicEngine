"""KA-029: bounded expansion of a caller-supplied graph snapshot."""

from __future__ import annotations

from collections import deque
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class GraphAdjacency(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(min_length=1, max_length=500)
    neighbor_ids: list[str] = Field(default_factory=list, max_length=2_000)


class KA029Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed_entities: list[str] = Field(min_length=1, max_length=1_000)
    adjacency: list[GraphAdjacency] = Field(default_factory=list, max_length=10_000)
    depth: int = Field(default=2, ge=1, le=5)
    max_nodes: int = Field(default=1_000, ge=1, le=10_000)

    @model_validator(mode="after")
    def validate_ids(self) -> KA029Input:
        node_ids = [item.node_id for item in self.adjacency]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("adjacency node IDs must be unique")
        if len(self.seed_entities) != len(set(self.seed_entities)):
            raise ValueError("seed entity IDs must be unique")
        return self


class KA029KnowledgeExpansion(KnowledgeAlgorithm):
    """Return reachable node IDs without reading or mutating a graph store."""

    input_schema = KA029Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-029"

    def _run_logic(self, input_data: KA029Input) -> dict[str, Any]:
        adjacency = {
            item.node_id: sorted(set(item.neighbor_ids)) for item in input_data.adjacency
        }
        queue = deque((seed, 0) for seed in sorted(input_data.seed_entities))
        visited: dict[str, int] = {}
        truncated = False
        while queue:
            node_id, distance = queue.popleft()
            if node_id in visited:
                continue
            if len(visited) >= input_data.max_nodes:
                truncated = True
                break
            visited[node_id] = distance
            if distance < input_data.depth:
                queue.extend((neighbor, distance + 1) for neighbor in adjacency.get(node_id, []))
        rows = [
            {"node_id": node_id, "distance": distance}
            for node_id, distance in sorted(visited.items(), key=lambda row: (row[1], row[0]))
        ]
        return {
            "success": True,
            "status": "graph_expansion_proposed",
            "expanded_nodes": rows,
            "traversed_depth": max(visited.values(), default=0),
            "node_count": len(rows),
            "truncated": truncated,
            "graph_store_read": False,
            "graph_mutation_applied": False,
            "deterministic": True,
            "limitations": (
                "Expansion is limited to the supplied adjacency snapshot; missing "
                "edges and nodes are not discovered or inferred."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA029KnowledgeExpansion(context).run(context)

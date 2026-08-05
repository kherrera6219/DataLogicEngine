"""KA-1092: bounded downstream knowledge-dependency impact audit."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class DependencyEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    upstream_id: str = Field(min_length=1, max_length=200)
    downstream_id: str = Field(min_length=1, max_length=200)


class KA1092Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "changed_knowledge_ids": ["a"],
                    "known_knowledge_ids": ["a", "b", "c"],
                    "dependencies": [
                        {"upstream_id": "a", "downstream_id": "b"},
                        {"upstream_id": "b", "downstream_id": "c"},
                    ],
                    "dependency_results": {
                        "KA-025": {
                            "graph": {
                                "edges": [
                                    {"from": "a", "to": "b"},
                                    {"from": "b", "to": "c"},
                                ]
                            }
                        }
                    },
                }
            ]
        },
    )

    changed_knowledge_ids: list[str] = Field(min_length=1, max_length=1_000)
    known_knowledge_ids: list[str] = Field(min_length=1, max_length=50_000)
    dependencies: list[DependencyEdge] = Field(max_length=200_000)
    maximum_depth: int = Field(default=20, ge=1, le=100)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_graph(self) -> KA1092Input:
        known = set(self.known_knowledge_ids)
        if len(known) != len(self.known_knowledge_ids):
            raise ValueError("known knowledge IDs must be unique")
        if not set(self.changed_knowledge_ids) <= known:
            raise ValueError("changed knowledge IDs must be known")
        if any(
            edge.upstream_id not in known or edge.downstream_id not in known
            for edge in self.dependencies
        ):
            raise ValueError("dependency references an unknown knowledge ID")
        return self


class KA1092KnowledgeDependencyAuditor(KnowledgeAlgorithm):
    """Trace bounded downstream impact without changing dependency state."""

    input_schema = KA1092Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1092"

    def _run_logic(self, input_data: KA1092Input) -> dict[str, Any]:
        mapping = input_data.dependency_results.get("KA-025")
        declared_edges = {
            (item.upstream_id, item.downstream_id) for item in input_data.dependencies
        }
        dependency_consumed = None
        if isinstance(mapping, dict):
            mapped_edges = {
                (str(item.get("from")), str(item.get("to")))
                for item in mapping.get("graph", {}).get("edges", [])
                if isinstance(item, dict)
            }
            if mapped_edges != declared_edges:
                raise ValueError(
                    "KA-025 dependency mapping does not match declared edges"
                )
            dependency_consumed = "KA-025"
        graph: dict[str, list[str]] = defaultdict(list)
        for edge in input_data.dependencies:
            graph[edge.upstream_id].append(edge.downstream_id)
        for values in graph.values():
            values.sort()
        impacts: dict[tuple[str, str], int] = {}
        truncated = False
        for changed_id in sorted(set(input_data.changed_knowledge_ids)):
            queue = deque([(changed_id, 0)])
            seen = {changed_id}
            while queue:
                current, depth = queue.popleft()
                if depth >= input_data.maximum_depth:
                    if graph[current]:
                        truncated = True
                    continue
                for downstream in graph[current]:
                    if downstream in seen:
                        continue
                    seen.add(downstream)
                    impacts[(changed_id, downstream)] = depth + 1
                    queue.append((downstream, depth + 1))
        rows = [
            {
                "changed_knowledge_id": changed,
                "affected_knowledge_id": affected,
                "minimum_depth": depth,
            }
            for (changed, affected), depth in sorted(impacts.items())
        ]
        return {
            "success": True,
            "status": "knowledge_dependencies_audited",
            "downstream_impacts": rows,
            "affected_knowledge_ids": sorted(
                {row["affected_knowledge_id"] for row in rows}
            ),
            "truncated_at_maximum_depth": truncated,
            "dependency_consumed": dependency_consumed,
            "mapping_consistent": dependency_consumed == "KA-025",
            "mutation_applied": False,
            "deterministic": True,
            "limitations": (
                "Impact means graph reachability from declared dependencies; it "
                "does not establish runtime use or the severity of a change."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1092KnowledgeDependencyAuditor(context).run(context)

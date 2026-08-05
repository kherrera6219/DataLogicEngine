"""KA-1042: bounded contradiction impact propagation over a dependency graph."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ContradictionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conflict_id: str = Field(min_length=1, max_length=200)
    node_id: str = Field(min_length=1, max_length=200)
    severity: float = Field(ge=0, le=1)
    statement: str | None = Field(default=None, max_length=5_000)


class DependencyEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    upstream: str = Field(min_length=1, max_length=200)
    downstream: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def reject_self_edge(self) -> DependencyEdge:
        if self.upstream == self.downstream:
            raise ValueError("dependency self-edges are not allowed")
        return self


class KA1042Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "conflicts": [
                        {
                            "conflict_id": "conflict-1",
                            "node_id": "claim-a",
                            "severity": 0.8,
                        }
                    ],
                    "dependency_graph": [
                        {
                            "upstream": "claim-a",
                            "downstream": "claim-b",
                        }
                    ],
                }
            ]
        },
    )

    conflicts: list[ContradictionRecord] = Field(default_factory=list, max_length=100)
    dependency_graph: list[DependencyEdge] = Field(
        default_factory=list,
        max_length=5_000,
    )
    maximum_depth: int = Field(default=20, ge=1, le=100)
    maximum_paths_per_conflict: int = Field(default=500, ge=1, le=5_000)
    decay_per_hop: float = Field(default=0.85, ge=0, le=1)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_identity(self) -> KA1042Input:
        conflict_ids = [item.conflict_id for item in self.conflicts]
        if len(conflict_ids) != len(set(conflict_ids)):
            raise ValueError("conflict IDs must be unique")
        edge_pairs = [
            (item.upstream, item.downstream) for item in self.dependency_graph
        ]
        if len(edge_pairs) != len(set(edge_pairs)):
            raise ValueError("dependency edges must be unique")
        return self


class KA1042ContradictionPropagationAnalysis(KnowledgeAlgorithm):
    """Trace bounded downstream impact without mutating graph state."""

    input_schema = KA1042Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1042"

    @staticmethod
    def _cycle_detected(edges: list[DependencyEdge]) -> bool:
        adjacency: dict[str, set[str]] = defaultdict(set)
        indegree: dict[str, int] = defaultdict(int)
        nodes: set[str] = set()
        for edge in edges:
            nodes.update((edge.upstream, edge.downstream))
            if edge.downstream not in adjacency[edge.upstream]:
                adjacency[edge.upstream].add(edge.downstream)
                indegree[edge.downstream] += 1
            indegree.setdefault(edge.upstream, 0)
        queue = deque(sorted(node for node in nodes if indegree[node] == 0))
        visited = 0
        while queue:
            node = queue.popleft()
            visited += 1
            for downstream in sorted(adjacency[node]):
                indegree[downstream] -= 1
                if indegree[downstream] == 0:
                    queue.append(downstream)
        return visited != len(nodes)

    def _run_logic(self, input_data: KA1042Input) -> dict[str, Any]:
        conflicts = list(input_data.conflicts)
        if not conflicts:
            dependency_conflicts = (
                input_data.dependency_results.get("KA-026", {}).get("conflicts") or []
            )
            conflicts = [
                ContradictionRecord(
                    conflict_id=str(row.get("f1_id") or f"conflict-{index}"),
                    node_id=str(row.get("f1_id") or f"claim-{index}"),
                    severity=float(row.get("severity") or 0.0),
                )
                for index, row in enumerate(dependency_conflicts, start=1)
                if isinstance(row, dict)
            ]
        adjacency: dict[str, list[str]] = defaultdict(list)
        for edge in input_data.dependency_graph:
            adjacency[edge.upstream].append(edge.downstream)
        for values in adjacency.values():
            values.sort()

        affected_paths: list[dict[str, Any]] = []
        impacts: dict[str, dict[str, Any]] = {}
        truncated = False
        for conflict in sorted(
            conflicts,
            key=lambda item: item.conflict_id,
        ):
            queue: deque[tuple[str, list[str]]] = deque(
                [(conflict.node_id, [conflict.node_id])]
            )
            best_depth = {conflict.node_id: 0}
            emitted = 0
            while queue:
                node, path = queue.popleft()
                depth = len(path) - 1
                if depth:
                    impact = round(
                        conflict.severity * (input_data.decay_per_hop**depth),
                        8,
                    )
                    affected_paths.append(
                        {
                            "conflict_id": conflict.conflict_id,
                            "target_node": node,
                            "path": path,
                            "depth": depth,
                            "impact": impact,
                        }
                    )
                    emitted += 1
                    current = impacts.get(node)
                    if current is None or impact > current["impact"]:
                        impacts[node] = {
                            "node_id": node,
                            "impact": impact,
                            "source_conflict_id": conflict.conflict_id,
                            "depth": depth,
                        }
                    if emitted >= input_data.maximum_paths_per_conflict:
                        truncated = bool(queue or adjacency.get(node))
                        break
                if depth >= input_data.maximum_depth:
                    if adjacency.get(node):
                        truncated = True
                    continue
                for downstream in adjacency.get(node, []):
                    candidate_depth = depth + 1
                    if candidate_depth >= best_depth.get(
                        downstream,
                        input_data.maximum_depth + 1,
                    ):
                        continue
                    best_depth[downstream] = candidate_depth
                    queue.append((downstream, [*path, downstream]))

        priority_fixes = sorted(
            impacts.values(),
            key=lambda item: (
                -item["impact"],
                item["depth"],
                item["node_id"],
            ),
        )
        return {
            "success": True,
            "status": "contradiction_impact_traced",
            "affected_paths": affected_paths,
            "priority_fixes": priority_fixes,
            "affected_node_count": len(impacts),
            "cycle_detected": self._cycle_detected(input_data.dependency_graph),
            "truncated": truncated,
            "deterministic": True,
            "dependencies_consumed": sorted(input_data.dependency_results),
            "corrections_applied": 0,
            "limitations": (
                "Impact is a transparent severity-decay heuristic over the "
                "supplied dependency graph. It does not prove that a downstream "
                "claim is false or apply a correction."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1042ContradictionPropagationAnalysis(context).run(context)

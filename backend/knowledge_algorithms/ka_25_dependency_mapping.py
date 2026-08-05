"""
KA-025: Dependency Mapping
Purpose: Map and track Directed Acyclic Graphs (DAGs) of claims, evidence, and logical dependencies.
"""

import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA025Input(BaseModel):
    nodes: List[Dict[str, Any]] = Field(
        default_factory=list, description="Nodes with dependencies to map"
    )


class KA025DependencyMapping(KnowledgeAlgorithm):
    """
    KA-025: Logical dependency tracking and DAG validation engine.
    """

    input_schema = KA025Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-025"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "ka_25_config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA025Input) -> Dict[str, Any]:
        nodes = input_data.nodes
        self.log_execution_step("Mapping Dependencies", {"node_count": len(nodes)})

        node_ids = {str(node.get("id")) for node in nodes if node.get("id") is not None}
        adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
        edges = []
        unknown_dependencies = []
        for node in nodes:
            node_id = node.get("id")
            if node_id is None:
                continue
            normalized_id = str(node_id)
            for dependency in node.get("deps", []):
                normalized_dependency = str(dependency)
                edges.append({"from": normalized_dependency, "to": normalized_id})
                if normalized_dependency not in node_ids:
                    unknown_dependencies.append(
                        {
                            "node_id": normalized_id,
                            "dependency_id": normalized_dependency,
                        }
                    )
                    continue
                adjacency[normalized_dependency].append(normalized_id)

        is_dag, depth, cycle = self._measure_dag(adjacency)
        return {
            "success": True,
            "status": "dependency_graph_measured",
            "graph": {"nodes": nodes, "edges": edges},
            "meta": {
                "depth": depth,
                "is_dag": is_dag,
                "cycle": cycle,
                "unknown_dependencies": unknown_dependencies,
                "measurement_status": "measured",
            },
            "graph_mutation_applied": False,
            "deterministic": True,
            "limitations": (
                "The graph reflects declared node dependencies only; acyclicity "
                "does not prove runtime causality or evidence validity."
            ),
        }

    @staticmethod
    def _measure_dag(
        adjacency: dict[str, list[str]],
    ) -> tuple[bool, int | None, list[str]]:
        visiting: set[str] = set()
        visited: set[str] = set()
        path: list[str] = []
        depths: dict[str, int] = {}

        def visit(node_id: str) -> tuple[bool, list[str]]:
            if node_id in visiting:
                start = path.index(node_id)
                return False, path[start:] + [node_id]
            if node_id in visited:
                return True, []
            visiting.add(node_id)
            path.append(node_id)
            max_child_depth = 0
            for child_id in adjacency.get(node_id, []):
                acyclic, cycle = visit(child_id)
                if not acyclic:
                    return False, cycle
                max_child_depth = max(max_child_depth, depths[child_id])
            path.pop()
            visiting.remove(node_id)
            visited.add(node_id)
            depths[node_id] = max_child_depth + 1
            return True, []

        for node_id in sorted(adjacency):
            acyclic, cycle = visit(node_id)
            if not acyclic:
                return False, None, cycle
        return True, max(depths.values(), default=0), []


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA025DependencyMapping(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-025 Failed: {e}")
        return {"success": False, "error": str(e)}

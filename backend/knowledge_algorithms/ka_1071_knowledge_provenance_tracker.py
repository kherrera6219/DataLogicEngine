"""KA-1071: validate and trace an evidence provenance graph."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ProvenanceNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(min_length=1, max_length=200)
    node_type: Literal["source", "evidence", "transformation", "claim"]
    source_ref: str = Field(min_length=1, max_length=2_000)
    parent_node_ids: list[str] = Field(default_factory=list, max_length=100)
    content_sha256: str | None = Field(
        default=None,
        pattern=r"^[a-fA-F0-9]{64}$",
    )

    @model_validator(mode="after")
    def validate_parents(self) -> ProvenanceNode:
        if self.node_id in self.parent_node_ids:
            raise ValueError("a provenance node cannot be its own parent")
        if len(self.parent_node_ids) != len(set(self.parent_node_ids)):
            raise ValueError("parent node IDs must be unique")
        return self


class KA1071Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "knowledge_id": "knowledge-1",
                    "nodes": [
                        {
                            "node_id": "source",
                            "node_type": "source",
                            "source_ref": "report.pdf",
                        },
                        {
                            "node_id": "claim",
                            "node_type": "claim",
                            "source_ref": "claim:1",
                            "parent_node_ids": ["source"],
                        },
                    ],
                }
            ]
        },
    )

    knowledge_id: str = Field(min_length=1, max_length=200)
    nodes: list[ProvenanceNode] = Field(min_length=1, max_length=10_000)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1071Input:
        identifiers = [node.node_id for node in self.nodes]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("provenance node IDs must be unique")
        if self.dependency_results and set(self.dependency_results) != {"KA-018"}:
            raise ValueError("KA-1071 requires the exact KA-018 dependency result")
        return self


class KA1071KnowledgeProvenanceTracker(KnowledgeAlgorithm):
    """Return graph integrity and source reachability without persisting data."""

    input_schema = KA1071Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1071"

    def _run_logic(self, input_data: KA1071Input) -> dict[str, Any]:
        nodes = {node.node_id: node for node in input_data.nodes}
        known = set(nodes)
        missing = sorted(
            {
                parent
                for node in input_data.nodes
                for parent in node.parent_node_ids
                if parent not in known
            }
        )
        children: dict[str, list[str]] = defaultdict(list)
        indegree = {node_id: 0 for node_id in known}
        for node in input_data.nodes:
            for parent in node.parent_node_ids:
                if parent in known:
                    children[parent].append(node.node_id)
                    indegree[node.node_id] += 1
        ready = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
        ordered: list[str] = []
        while ready:
            node_id = ready.pop(0)
            ordered.append(node_id)
            for child in sorted(children[node_id]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
                    ready.sort()
        cycle_nodes = sorted(known - set(ordered))
        source_ids = sorted(
            node.node_id for node in input_data.nodes if node.node_type == "source"
        )
        claim_ids = sorted(
            node.node_id for node in input_data.nodes if node.node_type == "claim"
        )

        reachable = set(source_ids)
        for node_id in ordered:
            if node_id in reachable:
                reachable.update(children[node_id])
        ungrounded_claims = sorted(set(claim_ids) - reachable)
        source_measurement = input_data.dependency_results.get("KA-018", {})
        measured_source_id = source_measurement.get("source_id")
        dependency_matches = not source_measurement or measured_source_id in {
            node.source_ref for node in input_data.nodes if node.node_type == "source"
        }
        complete = (
            not missing
            and not cycle_nodes
            and not ungrounded_claims
            and dependency_matches
        )
        return {
            "success": True,
            "status": "provenance_valid" if complete else "provenance_incomplete",
            "knowledge_id": input_data.knowledge_id,
            "provenance_complete": complete,
            "source_node_ids": source_ids,
            "claim_node_ids": claim_ids,
            "topological_node_order": ordered,
            "missing_parent_node_ids": missing,
            "cycle_node_ids": cycle_nodes,
            "ungrounded_claim_node_ids": ungrounded_claims,
            "dependency_source_matched": dependency_matches,
            "dependency_consumed": "KA-018" if source_measurement else None,
            "hashed_node_count": sum(bool(node.content_sha256) for node in input_data.nodes),
            "provenance_persisted": False,
            "deterministic": True,
            "limitations": (
                "This validates declared graph structure and source reachability; "
                "it does not authenticate sources or persist provenance."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1071KnowledgeProvenanceTracker(context).run(context)

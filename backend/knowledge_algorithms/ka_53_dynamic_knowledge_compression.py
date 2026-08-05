"""KA-053: deterministic knowledge-compression proposal generation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.production_utils import stable_identifier
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA053Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_segments: list[dict[str, Any]] = Field(default_factory=list, max_length=5_000)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA053DynamicKnowledgeCompression(KnowledgeAlgorithm):
    """Propose ID mappings without reading or changing a graph store."""

    input_schema = KA053Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-053"

    def _run_logic(self, input_data: KA053Input) -> dict[str, Any]:
        proposals = []
        total_nodes = 0
        for index, segment in enumerate(input_data.graph_segments, start=1):
            node_ids = sorted(
                {
                    str(node.get("id"))
                    for node in segment.get("nodes", [])
                    if isinstance(node, dict) and node.get("id")
                }
            )
            total_nodes += len(node_ids)
            if len(node_ids) < 2:
                continue
            proposals.append(
                {
                    "proposal_id": stable_identifier(
                        "compression", {"index": index, "node_ids": node_ids}
                    ),
                    "source_node_ids": node_ids,
                    "target_node_id": stable_identifier("compressed-node", node_ids),
                    "requires_semantic_equivalence_review": True,
                }
            )
        return {
            "success": True,
            "status": "compression_proposals_created",
            "compression_proposals": proposals,
            "proposal_count": len(proposals),
            "source_node_count": total_nodes,
            "projected_node_reduction": sum(
                len(item["source_node_ids"]) - 1 for item in proposals
            ),
            "dependencies_consumed": sorted(input_data.dependency_results),
            "graph_store_read": False,
            "compression_applied": False,
            "deterministic": True,
            "limitations": (
                "Shared segment membership does not establish semantic equivalence. "
                "The owner must validate and transact any merge."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA053DynamicKnowledgeCompression(context).run(context)

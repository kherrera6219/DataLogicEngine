"""KA-054: bounded cross-lingual alignment proposal generation."""

from __future__ import annotations

from itertools import combinations
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.production_utils import stable_identifier
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA054Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    multilingual_sources: list[dict[str, Any]] = Field(
        default_factory=list, max_length=1_000
    )
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA054CrossLingualKnowledgeFusion(KnowledgeAlgorithm):
    """Match declared concept IDs without translating or merging content."""

    input_schema = KA054Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-054"

    def _run_logic(self, input_data: KA054Input) -> dict[str, Any]:
        alignments = []
        sources = sorted(
            input_data.multilingual_sources,
            key=lambda row: (
                str(row.get("language") or row.get("lang") or ""),
                str(row.get("source_id") or ""),
            ),
        )
        for left, right in combinations(sources, 2):
            left_language = str(left.get("language") or left.get("lang") or "unknown")
            right_language = str(
                right.get("language") or right.get("lang") or "unknown"
            )
            left_nodes = {
                str(node.get("concept_id")): str(
                    node.get("id") or node.get("concept_id")
                )
                for node in left.get("nodes", [])
                if isinstance(node, dict) and node.get("concept_id")
            }
            right_nodes = {
                str(node.get("concept_id")): str(
                    node.get("id") or node.get("concept_id")
                )
                for node in right.get("nodes", [])
                if isinstance(node, dict) and node.get("concept_id")
            }
            for concept_id in sorted(set(left_nodes) & set(right_nodes)):
                alignments.append(
                    {
                        "alignment_id": stable_identifier(
                            "cross-lingual",
                            {
                                "concept_id": concept_id,
                                "languages": sorted([left_language, right_language]),
                            },
                        ),
                        "concept_id": concept_id,
                        "source_node_ids": sorted(
                            [left_nodes[concept_id], right_nodes[concept_id]]
                        ),
                        "languages": sorted([left_language, right_language]),
                        "basis": "declared_concept_identity",
                        "requires_translation_review": True,
                    }
                )
        return {
            "success": True,
            "status": "cross_lingual_alignments_proposed",
            "alignment_records": alignments,
            "alignment_count": len(alignments),
            "dependencies_consumed": sorted(input_data.dependency_results),
            "translation_performed": False,
            "fusion_applied": False,
            "deterministic": True,
            "limitations": (
                "Matching declared concept IDs does not prove equivalent meaning "
                "across languages. No translation, trust score, or merge is applied."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA054CrossLingualKnowledgeFusion(context).run(context)

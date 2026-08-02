"""KA-076: deterministic exact-key resolution for ingestion metadata."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.ingestion_pipeline_utils import (
    canonical_record,
    dependency_records,
)
from backend.knowledge_algorithms.production_utils import (
    load_config,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA076ResolutionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[Any] = Field(default_factory=list, max_length=1_000)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA076EntityResolution(KnowledgeAlgorithm):
    input_schema = KA076ResolutionInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-076"
        self.config = load_config(__file__, "ka_76_config.json")

    def _run_logic(self, input_data: KA076ResolutionInput) -> dict[str, Any]:
        records = dependency_records(
            input_data.dependency_results,
            "KA-075",
            "mapped_records",
            input_data.records,
        )
        matching_keys = list(
            self.config.get("exact_matching_keys") or ["record_id", "source_sha256"]
        )
        entities: dict[str, dict[str, Any]] = {}
        entity_fingerprints: dict[str, str] = {}
        exact_duplicates = 0
        conflicts: list[dict[str, Any]] = []
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            identity = next(
                (
                    f"{key}:{record[key]}"
                    for key in matching_keys
                    if record.get(key) not in (None, "")
                ),
                stable_identifier("record", {"index": index, "record": record}),
            )
            fingerprint = canonical_record(record)
            if identity not in entities:
                entities[identity] = dict(record)
                entity_fingerprints[identity] = fingerprint
            elif entity_fingerprints[identity] == fingerprint:
                exact_duplicates += 1
            else:
                conflicts.append(
                    {
                        "identity_sha256": stable_identifier(
                            "identity", identity, length=32
                        ),
                        "reason": "same_exact_key_different_record",
                    }
                )

        resolved_records = list(entities.values())
        self.log_execution_step(
            "Resolved exact ingestion identities",
            {"unique": len(resolved_records), "conflicts": len(conflicts)},
        )
        return {
            "success": True,
            "resolution_allowed": not conflicts,
            "resolved_records": resolved_records,
            "unique_entities_count": len(resolved_records),
            "exact_duplicates_removed": exact_duplicates,
            "conflicts": conflicts,
            "strategy": "deterministic_exact_key",
            "fuzzy_matching_performed": False,
            "dependency_consumed": "KA-075" in input_data.dependency_results,
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA076EntityResolution(context).run(context)

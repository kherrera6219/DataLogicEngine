"""KA-078: produce a bounded archive-eligibility proposal."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.ingestion_pipeline_utils import dependency_records
from backend.knowledge_algorithms.production_utils import (
    load_config,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA078ArchivalInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[Any] = Field(default_factory=list, max_length=1_000)
    record_ids: list[str] = Field(default_factory=list, max_length=1_000)
    archive_requested: bool = False
    record_age_days_by_id: dict[str, int] = Field(default_factory=dict)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA078DataArchival(KnowledgeAlgorithm):
    input_schema = KA078ArchivalInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-078"
        self.config = load_config(__file__, "ka_78_config.json")

    def _run_logic(self, input_data: KA078ArchivalInput) -> dict[str, Any]:
        records = dependency_records(
            input_data.dependency_results,
            "KA-077",
            "enriched_records",
            input_data.records,
        )
        dependency_ids = [
            str(record.get("record_id"))
            for record in records
            if isinstance(record, dict) and record.get("record_id") not in (None, "")
        ]
        evaluated_ids = sorted(set(dependency_ids or input_data.record_ids))
        retention_days = int(self.config.get("retention_policy_days", 180))
        eligible_ids = [
            record_id
            for record_id in evaluated_ids
            if input_data.archive_requested
            and int(input_data.record_age_days_by_id.get(record_id, 0))
            >= retention_days
        ]
        destination = str(
            self.config.get("archive_destination", "app_owned_object_archive")
        )
        proposal_id = stable_identifier(
            "archive_eligibility",
            {
                "record_ids": evaluated_ids,
                "eligible_ids": eligible_ids,
                "destination": destination,
                "retention_days": retention_days,
            },
            length=32,
        )
        self.log_execution_step(
            "Evaluated archive eligibility",
            {"evaluated": len(evaluated_ids), "eligible": len(eligible_ids)},
        )
        return {
            "success": True,
            "proposal_id": proposal_id,
            "evaluated_record_ids": evaluated_ids,
            "eligible_record_ids": eligible_ids,
            "eligible_record_count": len(eligible_ids),
            "records_archived": 0,
            "applied": False,
            "authoritative_service": "RetentionService",
            "effect_prerequisite": "explicit_request_age_verification_and_cross_store_receipt",
            "destination": destination,
            "retention_days": retention_days,
            "retention_policy_status": "proposed",
            "compression_status": "not_applied",
            "encryption_status": "not_applied",
            "storage_saved_bytes": 0,
            "dependency_consumed": "KA-077" in input_data.dependency_results,
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA078DataArchival(context).run(context)

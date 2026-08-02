"""KA-072: deterministic, local ingestion-metadata cleaning."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.ingestion_pipeline_utils import (
    canonical_record,
    dependency_records,
)
from backend.knowledge_algorithms.production_utils import load_config
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA072CleaningInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[Any] = Field(default_factory=list, max_length=1_000)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA072DataCleaning(KnowledgeAlgorithm):
    input_schema = KA072CleaningInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-072"
        self.config = load_config(__file__, "ka_72_config.json")

    def _run_logic(self, input_data: KA072CleaningInput) -> dict[str, Any]:
        records = dependency_records(
            input_data.dependency_results,
            "KA-071",
            "admitted_records",
            input_data.records,
        )
        cleaned_records: list[dict[str, Any]] = []
        fingerprints: set[str] = set()
        invalid_count = 0
        duplicate_count = 0
        trimmed_fields = 0
        null_fields_removed = 0
        for record in records:
            if not isinstance(record, dict) or not record:
                invalid_count += 1
                continue
            cleaned: dict[str, Any] = {}
            for key, value in record.items():
                if value is None:
                    null_fields_removed += 1
                    continue
                if isinstance(value, str):
                    normalized = value.strip()
                    if normalized != value:
                        trimmed_fields += 1
                    cleaned[str(key)] = normalized
                else:
                    cleaned[str(key)] = value
            fingerprint = canonical_record(cleaned)
            if fingerprint in fingerprints:
                duplicate_count += 1
                continue
            fingerprints.add(fingerprint)
            cleaned_records.append(cleaned)

        self.log_execution_step(
            "Cleaned ingestion metadata",
            {"input": len(records), "cleaned": len(cleaned_records)},
        )
        return {
            "success": True,
            "cleaned_records": cleaned_records,
            "source_record_count": len(records),
            "cleaned_count": len(cleaned_records),
            "dropped_count": invalid_count + duplicate_count,
            "invalid_records_dropped": invalid_count,
            "exact_duplicates_removed": duplicate_count,
            "trimmed_fields": trimmed_fields,
            "null_fields_removed": null_fields_removed,
            "ops_performed": [
                "shallow_whitespace_trim",
                "null_field_removal",
                "exact_record_deduplication",
            ],
            "dependency_consumed": "KA-071" in input_data.dependency_results,
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA072DataCleaning(context).run(context)

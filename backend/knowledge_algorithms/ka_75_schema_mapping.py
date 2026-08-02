"""KA-075: explicit local schema mapping for admitted records."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.ingestion_pipeline_utils import dependency_records
from backend.knowledge_algorithms.production_utils import load_config
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA075MappingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[Any] = Field(default_factory=list, max_length=1_000)
    target_schema: str = Field("knowledge_source", min_length=1, max_length=100)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA075SchemaMapping(KnowledgeAlgorithm):
    input_schema = KA075MappingInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-075"
        self.config = load_config(__file__, "ka_75_config.json")

    def _run_logic(self, input_data: KA075MappingInput) -> dict[str, Any]:
        records = dependency_records(
            input_data.dependency_results,
            "KA-074",
            "valid_records",
            input_data.records,
        )
        schemas = self.config.get("canonical_schemas") or {}
        canonical_fields = schemas.get(input_data.target_schema)
        if not isinstance(canonical_fields, list) or not canonical_fields:
            raise ValueError(f"unknown canonical schema: {input_data.target_schema}")
        mapped_records: list[dict[str, Any]] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            mapped: dict[str, Any] = {}
            for field in canonical_fields:
                if field in record:
                    mapped[field] = record[field]
                elif f"src_{field}" in record:
                    mapped[field] = record[f"src_{field}"]
                else:
                    mapped[field] = None
            mapped_records.append(mapped)

        self.log_execution_step(
            "Mapped admitted records",
            {"target": input_data.target_schema, "count": len(mapped_records)},
        )
        return {
            "success": True,
            "mapped_records": mapped_records,
            "records_mapped": len(mapped_records),
            "target_schema": input_data.target_schema,
            "fields_aligned": list(canonical_fields),
            "dependency_consumed": "KA-074" in input_data.dependency_results,
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA075SchemaMapping(context).run(context)

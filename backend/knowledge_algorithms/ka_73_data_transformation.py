"""KA-073: normalize secure-ingestion metadata types."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.ingestion_pipeline_utils import dependency_records
from backend.knowledge_algorithms.production_utils import load_config
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA073TransformationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[Any] = Field(default_factory=list, max_length=1_000)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA073DataTransformation(KnowledgeAlgorithm):
    input_schema = KA073TransformationInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-073"
        self.config = load_config(__file__, "ka_73_config.json")

    def _run_logic(self, input_data: KA073TransformationInput) -> dict[str, Any]:
        records = dependency_records(
            input_data.dependency_results,
            "KA-072",
            "cleaned_records",
            input_data.records,
        )
        transformed: list[dict[str, Any]] = []
        conversion_failures: list[dict[str, Any]] = []
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                conversion_failures.append(
                    {"record_index": index, "field": "record", "reason": "not_object"}
                )
                continue
            normalized = dict(record)
            for field in ("record_id", "relative_path", "detected_type"):
                if field in normalized:
                    normalized[field] = str(normalized[field]).strip()
            if "detected_type" in normalized:
                normalized["detected_type"] = normalized["detected_type"].lower()
            if "source_sha256" in normalized:
                normalized["source_sha256"] = (
                    str(normalized["source_sha256"]).strip().lower()
                )
            if "size_bytes" in normalized and not isinstance(
                normalized["size_bytes"], bool
            ):
                try:
                    normalized["size_bytes"] = int(normalized["size_bytes"])
                except (TypeError, ValueError):
                    conversion_failures.append(
                        {
                            "record_index": index,
                            "field": "size_bytes",
                            "reason": "integer_conversion_failed",
                        }
                    )
            transformed.append(normalized)

        self.log_execution_step(
            "Normalized ingestion metadata",
            {"count": len(transformed), "failures": len(conversion_failures)},
        )
        return {
            "success": True,
            "transformed_records": transformed,
            "records_transformed": len(transformed),
            "target_schema": self.config.get(
                "target_schema", "dle.secure-ingestion-metadata.v1"
            ),
            "transformation_applied": [
                "string_trim",
                "detected_type_lowercase",
                "sha256_lowercase",
                "size_bytes_integer",
            ],
            "conversion_failures": conversion_failures,
            "dependency_consumed": "KA-072" in input_data.dependency_results,
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA073DataTransformation(context).run(context)

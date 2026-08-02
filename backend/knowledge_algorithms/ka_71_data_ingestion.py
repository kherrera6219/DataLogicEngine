"""KA-071: validate a bounded local-file ingestion proposal."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.production_utils import (
    load_config,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA071IngestionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: Literal["local_file"] = "local_file"
    payload: list[dict[str, Any]] = Field(default_factory=list, max_length=1_000)


class KA071DataIngestion(KnowledgeAlgorithm):
    """Admit secure-acquisition metadata without applying an ingestion effect."""

    input_schema = KA071IngestionInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-071"
        self.config = load_config(__file__, "ka_71_config.json")

    def _run_logic(self, input_data: KA071IngestionInput) -> dict[str, Any]:
        required_fields = tuple(
            self.config.get(
                "required_metadata_fields",
                (
                    "record_id",
                    "relative_path",
                    "source_sha256",
                    "size_bytes",
                    "detected_type",
                ),
            )
        )
        admitted: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for index, source_record in enumerate(input_data.payload):
            record = dict(source_record)
            missing = [
                field
                for field in required_fields
                if field not in record or record[field] in (None, "")
            ]
            if missing:
                raise ValueError(
                    f"record {index} is missing required metadata: " + ",".join(missing)
                )
            record_id = str(record["record_id"])
            if record_id in seen_ids:
                raise ValueError(f"duplicate ingestion record_id: {record_id}")
            seen_ids.add(record_id)
            admitted.append(record)

        proposal_id = stable_identifier(
            "ingestion_admission",
            {
                "source_type": input_data.source_type,
                "records": admitted,
            },
            length=32,
        )
        self.log_execution_step(
            "Validated local ingestion proposal",
            {"source": input_data.source_type, "count": len(admitted)},
        )
        return {
            "success": True,
            "proposal_id": proposal_id,
            "admitted_records": admitted,
            "admitted_record_count": len(admitted),
            "records_ingested": 0,
            "applied": False,
            "source_type": input_data.source_type,
            "authoritative_service": "LocalKnowledgeIngestionService",
            "effect_prerequisite": "secure_acquisition_and_sql_job_commit",
            "limitation": "Admission validates metadata only; it does not write records.",
        }

    def _fallback_logic(
        self,
        input_data: KA071IngestionInput,
        error: Exception,
    ) -> dict[str, Any]:
        return {
            "success": False,
            "records_ingested": 0,
            "applied": False,
            "fallback_active": True,
            "error_code": "INGESTION_ADMISSION_FAILED",
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA071DataIngestion(context).run(context)

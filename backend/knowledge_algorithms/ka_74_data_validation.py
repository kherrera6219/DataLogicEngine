"""KA-074: fail-closed validation for secure-ingestion metadata."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.ingestion_pipeline_utils import dependency_records
from backend.knowledge_algorithms.production_utils import (
    load_config,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA074ValidationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[Any] = Field(default_factory=list, max_length=1_000)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA074DataValidation(KnowledgeAlgorithm):
    input_schema = KA074ValidationInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-074"
        self.config = load_config(__file__, "ka_74_config.json")

    def _run_logic(self, input_data: KA074ValidationInput) -> dict[str, Any]:
        records = dependency_records(
            input_data.dependency_results,
            "KA-073",
            "transformed_records",
            input_data.records,
        )
        valid_records: list[dict[str, Any]] = []
        invalid_summaries: list[dict[str, Any]] = []
        rules = list(self.config.get("validation_rules") or [])
        for index, record in enumerate(records):
            errors: list[str] = []
            if not isinstance(record, dict):
                errors.append("record_not_object")
                record_id = stable_identifier("invalid_record", {"index": index})
            else:
                record_id = str(
                    record.get("record_id")
                    or stable_identifier("invalid_record", {"index": index})
                )
                for rule in rules:
                    field = str(rule.get("field") or "")
                    constraint = rule.get("constraint")
                    value = record.get(field)
                    if constraint == "required" and value in (None, ""):
                        errors.append(f"{field}:required")
                    elif constraint == "range" and value is not None:
                        if isinstance(value, bool) or not isinstance(
                            value, (int, float)
                        ):
                            errors.append(f"{field}:number_required")
                        elif not (
                            float(rule.get("min", 0))
                            <= float(value)
                            <= float(rule.get("max", value))
                        ):
                            errors.append(f"{field}:out_of_range")
                    elif (
                        constraint == "regex"
                        and value is not None
                        and re.fullmatch(str(rule.get("pattern") or ".*"), str(value))
                        is None
                    ):
                        errors.append(f"{field}:format_invalid")
            if errors:
                invalid_summaries.append(
                    {"record_id": record_id, "errors": sorted(errors)}
                )
            else:
                valid_records.append(dict(record))

        admission_allowed = not invalid_summaries
        self.log_execution_step(
            "Validated ingestion metadata",
            {"total": len(records), "admission_allowed": admission_allowed},
        )
        return {
            "success": True,
            "admission_allowed": admission_allowed,
            "valid_records": valid_records,
            "validation_summary": {
                "total": len(records),
                "valid": len(valid_records),
                "invalid": len(invalid_summaries),
            },
            "quarantined": invalid_summaries,
            "quarantine_contains_source_content": False,
            "dependency_consumed": "KA-073" in input_data.dependency_results,
        }

    def _fallback_logic(
        self,
        input_data: KA074ValidationInput,
        error: Exception,
    ) -> dict[str, Any]:
        return {
            "success": False,
            "admission_allowed": False,
            "valid_records": [],
            "validation_summary": {
                "total": len(input_data.records),
                "valid": 0,
                "invalid": len(input_data.records),
            },
            "quarantined": [],
            "quarantine_contains_source_content": False,
            "fallback_active": True,
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA074DataValidation(context).run(context)

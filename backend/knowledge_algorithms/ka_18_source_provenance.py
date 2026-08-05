"""KA-018: deterministic source-provenance evidence measurement."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ProvenanceCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    check_id: str = Field(min_length=1, max_length=200)
    status: str = Field(pattern=r"^(passed|failed)$")
    authority_ref: str = Field(min_length=1, max_length=2_000)


class KA018Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "source_id": "source-1",
                    "source_type": "local_document",
                    "content_sha256": "a" * 64,
                    "provenance_checks": [],
                }
            ]
        },
    )

    source_id: str = Field(default="unspecified", min_length=1, max_length=500)
    source_type: str = Field(default="unverified", min_length=1, max_length=200)
    content_sha256: str = Field(default="0" * 64, pattern=r"^[0-9a-f]{64}$")
    provenance_checks: list[ProvenanceCheck] = Field(
        default_factory=list, max_length=1_000
    )

    @model_validator(mode="after")
    def validate_check_ids(self) -> KA018Input:
        ids = [item.check_id for item in self.provenance_checks]
        if len(ids) != len(set(ids)):
            raise ValueError("provenance check IDs must be unique")
        return self


class KA018SourceProvenance(KnowledgeAlgorithm):
    """Summarize supplied provenance checks without inferring source trust."""

    input_schema = KA018Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-018"

    def _run_logic(self, input_data: KA018Input) -> dict[str, Any]:
        checks = [
            {
                "check_id": item.check_id,
                "status": item.status,
                "authority_ref": item.authority_ref,
            }
            for item in sorted(
                input_data.provenance_checks, key=lambda item: item.check_id
            )
        ]
        passed = sum(item["status"] == "passed" for item in checks)
        measured_ratio = round(passed / len(checks), 8) if checks else None
        identity = {
            "source_id": input_data.source_id,
            "source_type": input_data.source_type,
            "content_sha256": input_data.content_sha256,
            "checks": checks,
        }
        return {
            "success": True,
            "status": (
                "provenance_measured"
                if checks and input_data.source_id != "unspecified"
                else "provenance_evidence_required"
            ),
            "source_id": input_data.source_id,
            "source_type": input_data.source_type,
            "content_sha256": input_data.content_sha256,
            "checks": checks,
            "passed_check_ratio": measured_ratio,
            "all_supplied_checks_passed": bool(checks) and passed == len(checks),
            "source_trust_established": False,
            "trace_sha256": hashlib.sha256(
                json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "deterministic": True,
            "limitations": (
                "The result summarizes supplied authority references and does not "
                "authenticate a source or establish factual trust."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA018SourceProvenance(context).run(context)

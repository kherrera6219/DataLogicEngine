"""KA-174: deterministic current-state compliance check."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ComplianceControl(BaseModel):
    model_config = ConfigDict(extra="forbid")

    control_id: str = Field(min_length=1, max_length=200)
    applicability: Literal["applicable", "not_applicable"]
    implementation_status: Literal["implemented", "partial", "missing"]
    required_evidence_types: list[str] = Field(default_factory=list, max_length=1_000)
    evidence: dict[str, list[str]] = Field(default_factory=dict)
    exception_ref: str | None = Field(default=None, max_length=2_000)


class KA174Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "controls": [
                        {
                            "control_id": "AC-1",
                            "applicability": "applicable",
                            "implementation_status": "implemented",
                            "required_evidence_types": ["test"],
                            "evidence": {"test": ["test-report-1"]},
                        }
                    ]
                }
            ]
        },
    )

    controls: list[ComplianceControl] = Field(min_length=1, max_length=100_000)

    @model_validator(mode="after")
    def validate_ids(self) -> KA174Input:
        identifiers = [item.control_id for item in self.controls]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("control IDs must be unique")
        return self


class KA174ComplianceCheck(KnowledgeAlgorithm):
    """Check current declared control state without certification claims."""

    input_schema = KA174Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-174"

    def _run_logic(self, input_data: KA174Input) -> dict[str, Any]:
        assessments = []
        for item in sorted(input_data.controls, key=lambda row: row.control_id):
            missing_evidence = sorted(
                evidence_type
                for evidence_type in item.required_evidence_types
                if not item.evidence.get(evidence_type)
            )
            if item.applicability == "not_applicable":
                status = "not_applicable" if item.exception_ref else "fail"
                reasons = [] if item.exception_ref else ["exception_evidence_missing"]
            else:
                reasons = []
                if item.implementation_status != "implemented":
                    reasons.append(f"implementation_{item.implementation_status}")
                if missing_evidence:
                    reasons.append("required_evidence_missing")
                status = "pass" if not reasons else "fail"
            assessments.append(
                {
                    "control_id": item.control_id,
                    "status": status,
                    "reasons": reasons,
                    "missing_evidence_types": missing_evidence,
                }
            )
        return {
            "success": True,
            "status": "current_compliance_checked",
            "assessments": assessments,
            "all_applicable_controls_pass": all(
                row["status"] in {"pass", "not_applicable"} for row in assessments
            ),
            "certification_claimed": False,
            "deterministic": True,
            "limitations": (
                "This is an evidence-presence check, not legal interpretation, "
                "audit attestation, certification, or regression comparison."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA174ComplianceCheck(context).run(context)

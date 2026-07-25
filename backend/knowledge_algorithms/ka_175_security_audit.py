"""KA-175: deterministic security-control audit."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class SecurityControlEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    control_id: str = Field(min_length=1, max_length=200)
    control_family: Literal[
        "access", "encryption", "logging", "patching", "backup", "network"
    ]
    enabled: bool
    tested: bool
    evidence_refs: list[str] = Field(default_factory=list, max_length=1_000)
    severity_if_missing: Literal["low", "medium", "high", "critical"]


class KA175Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "controls": [
                        {
                            "control_id": "AC-1",
                            "control_family": "access",
                            "enabled": True,
                            "tested": True,
                            "evidence_refs": ["test-1"],
                            "severity_if_missing": "critical",
                        }
                    ]
                }
            ]
        },
    )

    controls: list[SecurityControlEvidence] = Field(
        min_length=1, max_length=100_000
    )


class KA175SecurityAudit(KnowledgeAlgorithm):
    """Audit supplied security-control state without scanning or exploitation."""

    input_schema = KA175Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-175"

    def _run_logic(self, input_data: KA175Input) -> dict[str, Any]:
        findings = []
        for item in sorted(input_data.controls, key=lambda row: row.control_id):
            reasons = []
            if not item.enabled:
                reasons.append("control_disabled")
            if not item.tested:
                reasons.append("control_not_tested")
            if not item.evidence_refs:
                reasons.append("evidence_missing")
            if reasons:
                findings.append(
                    {
                        "control_id": item.control_id,
                        "control_family": item.control_family,
                        "severity": item.severity_if_missing,
                        "reasons": reasons,
                    }
                )
        return {
            "success": True,
            "status": "security_controls_audited",
            "audit_passed": not findings,
            "findings": findings,
            "scans_executed": 0,
            "deterministic": True,
            "limitations": (
                "The audit checks declared control evidence; it is distinct from "
                "threat modeling, vulnerability scanning, and adversarial testing."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA175SecurityAudit(context).run(context)

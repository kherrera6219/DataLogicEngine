"""KA-1090: deterministic compliance-baseline regression validation."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ControlResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    control_id: str = Field(min_length=1, max_length=200)
    status: Literal["pass", "fail", "not_applicable", "not_tested"]
    evidence_refs: list[str] = Field(default_factory=list, max_length=500)


class KA1090Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "baseline": [
                        {
                            "control_id": "AC-1",
                            "status": "pass",
                            "evidence_refs": ["baseline-1"],
                        }
                    ],
                    "candidate": [
                        {
                            "control_id": "AC-1",
                            "status": "fail",
                            "evidence_refs": ["candidate-1"],
                        }
                    ],
                }
            ]
        },
    )

    baseline: list[ControlResult] = Field(min_length=1, max_length=20_000)
    candidate: list[ControlResult] = Field(min_length=1, max_length=20_000)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1090Input:
        for collection in (self.baseline, self.candidate):
            identifiers = [item.control_id for item in collection]
            if len(identifiers) != len(set(identifiers)):
                raise ValueError("control IDs must be unique within each result set")
        return self


class KA1090ComplianceRegressionValidator(KnowledgeAlgorithm):
    """Detect pass-to-nonpass and evidence-loss regressions."""

    input_schema = KA1090Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1090"

    def _run_logic(self, input_data: KA1090Input) -> dict[str, Any]:
        baseline = {item.control_id: item for item in input_data.baseline}
        candidate = {item.control_id: item for item in input_data.candidate}
        regressions = []
        for control_id in sorted(baseline):
            before = baseline[control_id]
            after = candidate.get(control_id)
            reasons = []
            if after is None:
                reasons.append("control_missing")
            else:
                if before.status == "pass" and after.status != "pass":
                    reasons.append(f"pass_to_{after.status}")
                if before.evidence_refs and not after.evidence_refs:
                    reasons.append("evidence_removed")
            if reasons:
                regressions.append(
                    {
                        "control_id": control_id,
                        "baseline_status": before.status,
                        "candidate_status": after.status if after else "missing",
                        "reasons": reasons,
                    }
                )
        return {
            "success": True,
            "status": "compliance_regression_evaluated",
            "regression_detected": bool(regressions),
            "regressions": regressions,
            "new_control_ids": sorted(candidate.keys() - baseline.keys()),
            "candidate_accepted": not regressions,
            "deterministic": True,
            "limitations": (
                "This validates declared control-result regression only; it is "
                "not a legal opinion or independent evidence assessment."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1090ComplianceRegressionValidator(context).run(context)

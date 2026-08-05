"""KA-027: deterministic ethical-impact review of declared risk evidence."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class EthicalRiskFactor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    factor_id: str = Field(min_length=1, max_length=200)
    category: Literal["bias", "privacy", "harm", "equity", "rights", "other"]
    severity: float = Field(ge=0, le=1)
    evidence_refs: list[str] = Field(default_factory=list, max_length=1_000)


class KA027Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "recommendation": "Proceed only after owner review.",
                    "risk_factors": [
                        {
                            "factor_id": "risk-1",
                            "category": "harm",
                            "severity": 0.8,
                            "evidence_refs": ["trace-1"],
                        }
                    ],
                }
            ]
        },
    )

    recommendation: str = Field(min_length=1, max_length=100_000)
    has_linguistic_bias: bool = False
    risk_factors: list[EthicalRiskFactor] = Field(
        default_factory=list, max_length=10_000
    )
    critical_threshold: float = Field(default=0.7, ge=0, le=1)


class KA027EthicalImpactAnalysis(KnowledgeAlgorithm):
    """Assess declared ethical-risk measurements without scanning prose."""

    input_schema = KA027Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-027"

    def _run_logic(self, input_data: KA027Input) -> dict[str, Any]:
        findings = []
        for item in sorted(input_data.risk_factors, key=lambda row: row.factor_id):
            findings.append(
                {
                    "factor_id": item.factor_id,
                    "category": item.category,
                    "severity": item.severity,
                    "evidence_refs": sorted(set(item.evidence_refs)),
                    "evidence_present": bool(item.evidence_refs),
                }
            )
        if input_data.has_linguistic_bias:
            findings.append(
                {
                    "factor_id": "linguistic-bias-signal",
                    "category": "bias",
                    "severity": 0.2,
                    "evidence_refs": ["KA-010"],
                    "evidence_present": True,
                }
            )
        verified_scores = [
            float(row["severity"]) for row in findings if row["evidence_present"]
        ]
        score = max(verified_scores, default=0.0)
        critical = score >= input_data.critical_threshold
        return {
            "success": True,
            "status": "CRITICAL_FAILURE" if critical else "PASSED",
            "ethics_score": round(score, 8),
            "findings": findings,
            "review_recommended": bool(findings),
            "recommendation_content_returned": False,
            "ethical_acceptability_established": False,
            "actions_applied": 0,
            "deterministic": True,
            "limitations": (
                "This evaluates caller-declared risk factors and evidence links. "
                "It does not infer ethics from prose or establish acceptability."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA027EthicalImpactAnalysis(context).run(context)

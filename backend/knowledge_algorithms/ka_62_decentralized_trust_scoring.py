"""KA-062: deterministic trust-eligibility measurement from provenance evidence."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA062Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(default="unspecified", min_length=1, max_length=500)
    signature_verified: bool = False
    authority_verified: bool = False
    independently_corrobated: bool = False
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_dependency(self) -> KA062Input:
        if self.dependency_results and set(self.dependency_results) != {"KA-018"}:
            raise ValueError("KA-062 requires the exact KA-018 dependency result")
        provenance = self.dependency_results.get("KA-018", {})
        if provenance and provenance.get("source_id") != self.source_id:
            raise ValueError("KA-018 source_id must match the trust candidate")
        return self


class KA062DecentralizedTrustScoring(KnowledgeAlgorithm):
    """Measure observed trust criteria without asserting source truth."""

    input_schema = KA062Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-062"

    def _run_logic(self, input_data: KA062Input) -> dict[str, Any]:
        provenance = input_data.dependency_results.get("KA-018", {})
        criteria = {
            "authority_verified": input_data.authority_verified,
            "independently_corrobated": input_data.independently_corrobated,
            "provenance_checks_passed": bool(
                provenance.get("all_supplied_checks_passed")
            ),
            "signature_verified": input_data.signature_verified,
        }
        passed = sum(criteria.values())
        return {
            "success": True,
            "status": "trust_evidence_measured",
            "source_id": input_data.source_id,
            "criteria": criteria,
            "observed_criterion_ratio": round(passed / len(criteria), 8),
            "commitment_eligible": passed == len(criteria),
            "dependency_consumed": "KA-018" if provenance else None,
            "source_trust_established": False,
            "effects_applied": 0,
            "deterministic": True,
            "limitations": (
                "The result measures declared, supplied observations and does not "
                "authenticate the source or establish factual correctness."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA062DecentralizedTrustScoring(context).run(context)

"""KA-1110: deterministic cross-domain coupling risk analysis."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class DomainLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    link_id: str = Field(min_length=1, max_length=200)
    source_domain: str = Field(min_length=1, max_length=200)
    target_domain: str = Field(min_length=1, max_length=200)
    sensitivity: Literal["low", "medium", "high", "critical"]
    authorized: bool
    planned_capability_ids: list[str] = Field(default_factory=list, max_length=1_000)


class KA1110Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "links": [
                        {
                            "link_id": "link-1",
                            "source_domain": "public",
                            "target_domain": "restricted",
                            "sensitivity": "critical",
                            "authorized": False,
                            "planned_capability_ids": ["KA-001"],
                        }
                    ]
                }
            ]
        },
    )

    links: list[DomainLink] = Field(min_length=1, max_length=100_000)
    blocked_capability_pairs: list[tuple[str, str]] = Field(
        default_factory=list, max_length=10_000
    )
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_dependencies(self) -> KA1110Input:
        if self.dependency_results and set(self.dependency_results) != {
            "KA-005",
            "KA-1107",
        }:
            raise ValueError("dependency_results must contain KA-005 and KA-1107")
        return self


class KA1110CrossDomainCouplingRiskAnalyzer(KnowledgeAlgorithm):
    """Score declared coupling pathways and identify combinations to block."""

    input_schema = KA1110Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1110"

    def _run_logic(self, input_data: KA1110Input) -> dict[str, Any]:
        boundary_allowed = input_data.dependency_results.get("KA-1107", {}).get(
            "plan_allowed", True
        ) is True
        query_class = input_data.dependency_results.get("KA-005", {}).get(
            "category"
        )
        weights = {"low": 0.1, "medium": 0.35, "high": 0.7, "critical": 1.0}
        blocked_pairs = {
            tuple(sorted(pair)) for pair in input_data.blocked_capability_pairs
        }
        assessments = []
        for item in sorted(input_data.links, key=lambda row: row.link_id):
            reasons = []
            score = weights[item.sensitivity]
            if item.source_domain != item.target_domain:
                reasons.append("cross_domain")
                score += 0.15
            if not item.authorized:
                reasons.append("not_authorized")
                score += 0.35
            if not boundary_allowed:
                reasons.append("reasoning_boundary_denied")
                score = 1.0
            used = sorted(set(item.planned_capability_ids))
            prohibited = sorted(
                pair
                for pair in blocked_pairs
                if pair[0] in used and pair[1] in used
            )
            if prohibited:
                reasons.append("blocked_capability_combination")
                score = 1.0
            score = min(score, 1.0)
            assessments.append(
                {
                    "link_id": item.link_id,
                    "risk_score": round(score, 8),
                    "decision": "block" if score >= 0.75 else "review",
                    "reasons": reasons,
                    "blocked_capability_pairs": prohibited,
                }
            )
        return {
            "success": True,
            "status": "cross_domain_coupling_assessed",
            "assessments": assessments,
            "blocks_applied": 0,
            "query_class_consumed": query_class,
            "dependencies_consumed": sorted(input_data.dependency_results),
            "deterministic": True,
            "limitations": (
                "Scores are policy heuristics over declared links and do not "
                "discover undeclared dependencies or enforce network isolation."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1110CrossDomainCouplingRiskAnalyzer(context).run(context)

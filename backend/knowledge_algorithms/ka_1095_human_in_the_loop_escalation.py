"""KA-1095: deterministic human-review escalation decisions."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class EscalationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1, max_length=200)
    risk_class: Literal["low", "medium", "high", "critical"]
    confidence: float = Field(ge=0, le=1)
    irreversible_effect: bool = False
    policy_exception: bool = False
    affected_subject_count: int = Field(ge=0, le=1_000_000_000)


class KA1095Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "cases": [
                        {
                            "case_id": "case-1",
                            "risk_class": "high",
                            "confidence": 0.4,
                            "irreversible_effect": True,
                            "affected_subject_count": 10,
                        }
                    ]
                }
            ]
        },
    )

    cases: list[EscalationCase] = Field(min_length=1, max_length=20_000)
    minimum_confidence: float = Field(default=0.7, ge=0, le=1)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1095Input:
        identifiers = [item.case_id for item in self.cases]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("case IDs must be unique")
        return self


class KA1095HumanInTheLoopEscalation(KnowledgeAlgorithm):
    """Select review level without dispatching or approving a case."""

    input_schema = KA1095Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1095"

    def _run_logic(self, input_data: KA1095Input) -> dict[str, Any]:
        risk_score = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        decisions = []
        for item in sorted(input_data.cases, key=lambda row: row.case_id):
            reasons = []
            if item.confidence < input_data.minimum_confidence:
                reasons.append("low_confidence")
            if risk_score[item.risk_class] >= 3:
                reasons.append(f"{item.risk_class}_risk")
            if item.irreversible_effect:
                reasons.append("irreversible_effect")
            if item.policy_exception:
                reasons.append("policy_exception")
            if item.affected_subject_count >= 100:
                reasons.append("large_affected_population")
            if item.risk_class == "critical" or item.policy_exception:
                level = "owner_and_specialist"
            elif reasons:
                level = "specialist"
            else:
                level = "none"
            decisions.append(
                {
                    "case_id": item.case_id,
                    "escalation_required": level != "none",
                    "review_level": level,
                    "reasons": reasons,
                    "priority": risk_score[item.risk_class],
                }
            )
        decisions.sort(key=lambda item: (-item["priority"], item["case_id"]))
        return {
            "success": True,
            "status": "human_escalation_evaluated",
            "decisions": decisions,
            "reviews_dispatched": 0,
            "decision_applied": False,
            "deterministic": True,
            "limitations": (
                "This determines review requirements only. It does not contact "
                "reviewers, grant approval, or apply the underlying action."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1095HumanInTheLoopEscalation(context).run(context)

"""KA-034: deterministic evaluation of declared adversarial test cases."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class AdversarialCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1, max_length=200)
    target_assumption: str = Field(min_length=1, max_length=2_000)
    attack_class: Literal[
        "misinformation",
        "logical_injection",
        "persona_manipulation",
        "context_poisoning",
        "privacy_exposure",
    ]
    expected_control_ids: list[str] = Field(min_length=1, max_length=100)
    observed_control_ids: list[str] = Field(default_factory=list, max_length=100)
    observed_outcome: Literal["blocked", "contained", "escaped", "not_executed"]


class KA034Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1, max_length=200)
    cases: list[AdversarialCase] = Field(min_length=1, max_length=1_000)

    @model_validator(mode="after")
    def validate_unique_ids(self) -> KA034Input:
        case_ids = [item.case_id for item in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("adversarial case IDs must be unique")
        return self


class KA034AdversarialReasoning(KnowledgeAlgorithm):
    """Evaluate observed test outcomes without inventing attacks or evidence."""

    input_schema = KA034Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-034"

    def _run_logic(self, input_data: KA034Input) -> dict[str, Any]:
        results = []
        for case in sorted(input_data.cases, key=lambda item: item.case_id):
            missing_controls = sorted(
                set(case.expected_control_ids) - set(case.observed_control_ids)
            )
            passed = (
                case.observed_outcome in {"blocked", "contained"}
                and not missing_controls
            )
            results.append(
                {
                    "case_id": case.case_id,
                    "target_assumption": case.target_assumption,
                    "attack_class": case.attack_class,
                    "observed_outcome": case.observed_outcome,
                    "missing_control_ids": missing_controls,
                    "decision": "pass" if passed else "fail",
                }
            )
        failed_ids = [row["case_id"] for row in results if row["decision"] == "fail"]
        return {
            "success": True,
            "status": "adversarial_cases_evaluated",
            "scenario_id": input_data.scenario_id,
            "case_results": results,
            "failed_case_ids": failed_ids,
            "robustness_decision": "pass" if not failed_ids else "fail",
            "attacks_executed": False,
            "effects_applied": 0,
            "deterministic": True,
            "limitations": (
                "This evaluates caller-supplied test observations only; it does not "
                "execute attacks, discover vulnerabilities, or establish security."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA034AdversarialReasoning(context).run(context)

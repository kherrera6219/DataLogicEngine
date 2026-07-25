"""KA-177: deterministic typed policy-rule enforcement."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class PolicyRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(min_length=1, max_length=200)
    attribute: str = Field(min_length=1, max_length=200)
    operator: Literal["equals", "not_equals", "in", "not_in", "gte", "lte"]
    expected: str | float | bool | list[str]
    effect: Literal["allow", "deny"]


class KA177Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "attributes": {"risk": "high", "owner_approved": False},
                    "rules": [
                        {
                            "rule_id": "deny-high",
                            "attribute": "risk",
                            "operator": "equals",
                            "expected": "high",
                            "effect": "deny",
                        }
                    ],
                }
            ]
        },
    )

    attributes: dict[str, str | float | bool | list[str]]
    rules: list[PolicyRule] = Field(min_length=1, max_length=10_000)
    default_effect: Literal["allow", "deny"] = "deny"


class KA177PolicyEnforcement(KnowledgeAlgorithm):
    """Evaluate a restricted rule language with deny-overrides semantics."""

    input_schema = KA177Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-177"

    @staticmethod
    def _matches(actual: Any, operator: str, expected: Any) -> bool:
        if operator == "equals":
            return actual == expected
        if operator == "not_equals":
            return actual != expected
        if operator == "in":
            return actual in expected if isinstance(expected, list) else False
        if operator == "not_in":
            return actual not in expected if isinstance(expected, list) else False
        if operator in {"gte", "lte"}:
            if not isinstance(actual, (int, float)) or isinstance(actual, bool):
                return False
            if not isinstance(expected, (int, float)) or isinstance(expected, bool):
                return False
            return actual >= expected if operator == "gte" else actual <= expected
        return False

    def _run_logic(self, input_data: KA177Input) -> dict[str, Any]:
        matched = []
        for rule in sorted(input_data.rules, key=lambda row: row.rule_id):
            if rule.attribute in input_data.attributes and self._matches(
                input_data.attributes[rule.attribute], rule.operator, rule.expected
            ):
                matched.append({"rule_id": rule.rule_id, "effect": rule.effect})
        effect = (
            "deny"
            if any(row["effect"] == "deny" for row in matched)
            else "allow"
            if any(row["effect"] == "allow" for row in matched)
            else input_data.default_effect
        )
        return {
            "success": True,
            "status": "policy_enforced",
            "decision": effect,
            "matched_rules": matched,
            "deny_overrides": True,
            "effect_applied": False,
            "deterministic": True,
            "limitations": (
                "The restricted rule language evaluates supplied attributes; the "
                "owning service must apply the deny or allow decision."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA177PolicyEnforcement(context).run(context)

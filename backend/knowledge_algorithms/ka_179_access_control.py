"""KA-179: deterministic attribute-and-role access control."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class AccessRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(min_length=1, max_length=200)
    actions: list[str] = Field(min_length=1, max_length=1_000)
    resource_types: list[str] = Field(min_length=1, max_length=1_000)
    required_roles: list[str] = Field(default_factory=list, max_length=1_000)
    required_attributes: dict[str, str] = Field(default_factory=dict)
    effect: str = Field(pattern=r"^(allow|deny)$")


class KA179Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "subject_id": "owner",
                    "roles": ["owner"],
                    "attributes": {"tenant": "local"},
                    "action": "read",
                    "resource_type": "trace",
                    "rules": [
                        {
                            "rule_id": "owner-read",
                            "actions": ["read"],
                            "resource_types": ["trace"],
                            "required_roles": ["owner"],
                            "required_attributes": {"tenant": "local"},
                            "effect": "allow",
                        }
                    ],
                }
            ]
        },
    )

    subject_id: str = Field(min_length=1, max_length=200)
    roles: list[str] = Field(default_factory=list, max_length=1_000)
    attributes: dict[str, str] = Field(default_factory=dict)
    action: str = Field(min_length=1, max_length=200)
    resource_type: str = Field(min_length=1, max_length=200)
    rules: list[AccessRule] = Field(min_length=1, max_length=10_000)


class KA179AccessControl(KnowledgeAlgorithm):
    """Evaluate access rules with deny-overrides and default-deny semantics."""

    input_schema = KA179Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-179"

    def _run_logic(self, input_data: KA179Input) -> dict[str, Any]:
        matched = []
        roles = set(input_data.roles)
        for rule in sorted(input_data.rules, key=lambda row: row.rule_id):
            if input_data.action not in rule.actions:
                continue
            if input_data.resource_type not in rule.resource_types:
                continue
            if not set(rule.required_roles).issubset(roles):
                continue
            if any(
                input_data.attributes.get(key) != value
                for key, value in rule.required_attributes.items()
            ):
                continue
            matched.append({"rule_id": rule.rule_id, "effect": rule.effect})
        decision = (
            "deny"
            if any(row["effect"] == "deny" for row in matched)
            else "allow"
            if any(row["effect"] == "allow" for row in matched)
            else "deny"
        )
        return {
            "success": True,
            "status": "access_control_evaluated",
            "subject_id": input_data.subject_id,
            "decision": decision,
            "matched_rules": matched,
            "default_deny": True,
            "access_applied": False,
            "deterministic": True,
            "limitations": (
                "The KA evaluates supplied identity attributes and rules; the "
                "resource service must authenticate the subject and enforce access."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA179AccessControl(context).run(context)

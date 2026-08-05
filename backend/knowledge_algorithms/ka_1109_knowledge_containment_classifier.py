"""KA-1109: deterministic knowledge-persistence containment classification."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KnowledgeCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_id: str = Field(min_length=1, max_length=200)
    declared_sensitivity: Literal[
        "public", "internal", "restricted", "prohibited"
    ]
    contains_personal_data: bool = False
    consent_verified: bool = False
    redistribution_allowed: bool = True
    risk_signals: list[
        Literal[
            "credential",
            "secret",
            "regulated",
            "malware",
            "prompt_injection",
            "unknown_origin",
        ]
    ] = Field(default_factory=list, max_length=100)


class KA1109Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "candidates": [
                        {
                            "knowledge_id": "knowledge-1",
                            "declared_sensitivity": "restricted",
                            "contains_personal_data": True,
                            "consent_verified": False,
                        }
                    ]
                }
            ]
        },
    )

    candidates: list[KnowledgeCandidate] = Field(min_length=1, max_length=10_000)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1109Input:
        identifiers = [item.knowledge_id for item in self.candidates]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("knowledge IDs must be unique")
        if self.dependency_results and set(self.dependency_results) != {"KA-024", "KA-1074"}:
            raise ValueError("KA-1109 requires exact KA-024 and KA-1074 results")
        return self


class KA1109KnowledgeContainmentClassifier(KnowledgeAlgorithm):
    """Classify persistence safety without applying a Layer-10 store decision."""

    input_schema = KA1109Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1109"

    def _run_logic(self, input_data: KA1109Input) -> dict[str, Any]:
        dependencies_present = bool(input_data.dependency_results)
        policy_approved = not dependencies_present or bool(
            input_data.dependency_results["KA-024"].get("is_approved")
        )
        privacy_safe = not dependencies_present or not bool(
            input_data.dependency_results["KA-1074"].get(
                "non_public_value_exposed", True
            )
        )
        decisions = []
        for item in sorted(input_data.candidates, key=lambda row: row.knowledge_id):
            reasons = []
            never = False
            if not policy_approved:
                reasons.append("truthgate_policy_not_approved")
                never = True
            if not privacy_safe:
                reasons.append("privacy_transformation_not_safe")
                never = True
            if item.declared_sensitivity == "prohibited":
                reasons.append("declared_prohibited")
                never = True
            if {"credential", "secret", "malware"} & set(item.risk_signals):
                reasons.append("prohibited_risk_signal")
                never = True
            if item.contains_personal_data and not item.consent_verified:
                reasons.append("personal_data_without_verified_consent")
                never = True
            if never:
                containment_class = "never_persist"
            elif (
                item.declared_sensitivity in {"internal", "restricted"}
                or not item.redistribution_allowed
                or "regulated" in item.risk_signals
                or "unknown_origin" in item.risk_signals
                or "prompt_injection" in item.risk_signals
            ):
                containment_class = "restricted"
            else:
                containment_class = "public"
            decisions.append(
                {
                    "knowledge_id": item.knowledge_id,
                    "containment_class": containment_class,
                    "persistence_rule": (
                        "deny"
                        if containment_class == "never_persist"
                        else "restricted_store_only"
                        if containment_class == "restricted"
                        else "approved_public_store"
                    ),
                    "reasons": reasons,
                }
            )
        return {
            "success": True,
            "status": "knowledge_containment_classified",
            "decisions": decisions,
            "persistence_actions_applied": 0,
            "dependencies_consumed": ["KA-024", "KA-1074"] if dependencies_present else [],
            "deterministic": True,
            "limitations": (
                "This advisory classifier does not inspect raw content or apply "
                "the owning Layer-10 persistence decision."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1109KnowledgeContainmentClassifier(context).run(context)

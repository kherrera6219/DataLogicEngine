"""KA-1099: deterministic full-system component integrity audit."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ComponentIntegrity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component_id: str = Field(min_length=1, max_length=200)
    status: Literal["ready", "degraded", "failed", "unknown"]
    expected_sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    observed_sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    required_dependency_ids: list[str] = Field(default_factory=list, max_length=1_000)


class KA1099Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "components": [
                        {"component_id": "api", "status": "ready"},
                        {
                            "component_id": "worker",
                            "status": "ready",
                            "required_dependency_ids": ["api"],
                        },
                    ]
                }
            ]
        },
    )

    components: list[ComponentIntegrity] = Field(min_length=1, max_length=20_000)

    @model_validator(mode="after")
    def validate_components(self) -> KA1099Input:
        identifiers = [item.component_id for item in self.components]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("component IDs must be unique")
        known = set(identifiers)
        if any(
            dependency not in known
            for item in self.components
            for dependency in item.required_dependency_ids
        ):
            raise ValueError("component dependency is unknown")
        return self


class KA1099SystemIntegrityAuditor(KnowledgeAlgorithm):
    """Audit declared component state, hashes, and dependency readiness."""

    input_schema = KA1099Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1099"

    def _run_logic(self, input_data: KA1099Input) -> dict[str, Any]:
        components = {item.component_id: item for item in input_data.components}
        findings = []
        for item in sorted(input_data.components, key=lambda row: row.component_id):
            reasons = []
            if item.status != "ready":
                reasons.append(f"status_{item.status}")
            if (
                item.expected_sha256
                and item.observed_sha256
                and item.expected_sha256.casefold() != item.observed_sha256.casefold()
            ):
                reasons.append("hash_mismatch")
            if item.expected_sha256 and not item.observed_sha256:
                reasons.append("observed_hash_missing")
            unavailable = sorted(
                dependency
                for dependency in item.required_dependency_ids
                if components[dependency].status != "ready"
            )
            if unavailable:
                reasons.append("dependency_not_ready")
            if reasons:
                findings.append(
                    {
                        "component_id": item.component_id,
                        "reasons": reasons,
                        "unavailable_dependency_ids": unavailable,
                    }
                )
        return {
            "success": True,
            "status": "system_integrity_audited",
            "integrity_valid": not findings,
            "findings": findings,
            "component_count": len(input_data.components),
            "measurement_status": "declared_component_evidence",
            "deterministic": True,
            "limitations": (
                "This audits supplied component evidence and is distinct from "
                "knowledge-record integrity or a live security scan."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1099SystemIntegrityAuditor(context).run(context)

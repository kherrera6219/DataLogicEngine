"""KA-136: deterministic design-time threat model analysis."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ThreatAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: str = Field(min_length=1, max_length=200)
    criticality: Literal["low", "medium", "high", "critical"]
    stores_sensitive_data: bool = False
    privileged: bool = False


class ThreatDataFlow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    flow_id: str = Field(min_length=1, max_length=200)
    source_asset_id: str = Field(min_length=1, max_length=200)
    target_asset_id: str = Field(min_length=1, max_length=200)
    crosses_trust_boundary: bool
    authenticated: bool
    encrypted: bool
    integrity_protected: bool


class KA136Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "assets": [
                        {
                            "asset_id": "gateway",
                            "criticality": "critical",
                            "privileged": True,
                        },
                        {
                            "asset_id": "store",
                            "criticality": "critical",
                            "stores_sensitive_data": True,
                        },
                    ],
                    "data_flows": [
                        {
                            "flow_id": "flow-1",
                            "source_asset_id": "gateway",
                            "target_asset_id": "store",
                            "crosses_trust_boundary": True,
                            "authenticated": True,
                            "encrypted": False,
                            "integrity_protected": True,
                        }
                    ],
                }
            ]
        },
    )

    assets: list[ThreatAsset] = Field(min_length=1, max_length=10_000)
    data_flows: list[ThreatDataFlow] = Field(default_factory=list, max_length=100_000)

    @model_validator(mode="after")
    def validate_graph(self) -> KA136Input:
        identifiers = [item.asset_id for item in self.assets]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("asset IDs must be unique")
        known = set(identifiers)
        if any(
            flow.source_asset_id not in known or flow.target_asset_id not in known
            for flow in self.data_flows
        ):
            raise ValueError("data flow references an unknown asset")
        return self


class KA136ThreatModelAgent(KnowledgeAlgorithm):
    """Derive bounded threat-model findings from declared architecture."""

    input_schema = KA136Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-136"

    def _run_logic(self, input_data: KA136Input) -> dict[str, Any]:
        assets = {item.asset_id: item for item in input_data.assets}
        findings = []
        for flow in sorted(input_data.data_flows, key=lambda row: row.flow_id):
            severity = (
                "critical"
                if "critical"
                in {
                    assets[flow.source_asset_id].criticality,
                    assets[flow.target_asset_id].criticality,
                }
                else "high"
            )
            checks = (
                ("spoofing", not flow.authenticated, "require_authentication"),
                ("information_disclosure", not flow.encrypted, "require_encryption"),
                (
                    "tampering",
                    not flow.integrity_protected,
                    "require_integrity_protection",
                ),
            )
            for threat, present, mitigation in checks:
                if present and flow.crosses_trust_boundary:
                    findings.append(
                        {
                            "flow_id": flow.flow_id,
                            "threat": threat,
                            "severity": severity,
                            "proposed_mitigation": mitigation,
                        }
                    )
        return {
            "success": True,
            "status": "threat_model_evaluated",
            "findings": findings,
            "threats_present": bool(findings),
            "tests_or_controls_applied": 0,
            "deterministic": True,
            "limitations": (
                "This design-time analysis covers declared assets and flows only; "
                "it is not runtime threat detection or penetration testing."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA136ThreatModelAgent(context).run(context)

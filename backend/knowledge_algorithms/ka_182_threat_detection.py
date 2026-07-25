"""KA-182: deterministic runtime security-signal detection."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ThreatSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal_id: str = Field(min_length=1, max_length=200)
    signal_type: Literal[
        "authentication_failure",
        "privilege_change",
        "malware_indicator",
        "data_exfiltration",
        "policy_bypass",
    ]
    observed_count: int = Field(ge=0, le=1_000_000_000)
    threshold: int = Field(ge=1, le=1_000_000_000)
    source_ref: str = Field(min_length=1, max_length=2_000)
    trusted_source: bool


class KA182Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "signals": [
                        {
                            "signal_id": "s1",
                            "signal_type": "authentication_failure",
                            "observed_count": 10,
                            "threshold": 5,
                            "source_ref": "security-log-1",
                            "trusted_source": True,
                        }
                    ]
                }
            ]
        },
    )

    signals: list[ThreatSignal] = Field(min_length=1, max_length=100_000)


class KA182ThreatDetection(KnowledgeAlgorithm):
    """Turn trusted threshold observations into unapplied threat alerts."""

    input_schema = KA182Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-182"

    def _run_logic(self, input_data: KA182Input) -> dict[str, Any]:
        alerts = []
        for item in sorted(input_data.signals, key=lambda row: row.signal_id):
            if item.trusted_source and item.observed_count >= item.threshold:
                severity = (
                    "critical"
                    if item.signal_type in {"malware_indicator", "data_exfiltration"}
                    else "high"
                )
                alerts.append(
                    {
                        "signal_id": item.signal_id,
                        "signal_type": item.signal_type,
                        "severity": severity,
                        "source_ref": item.source_ref,
                        "proposed_action": "contain_and_investigate",
                    }
                )
        return {
            "success": True,
            "status": "threat_signals_evaluated",
            "threat_detected": bool(alerts),
            "alerts": alerts,
            "actions_applied": 0,
            "deterministic": True,
            "limitations": (
                "Threshold detection uses supplied trusted observations and is "
                "distinct from design-time threat modeling or a live sensor."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA182ThreatDetection(context).run(context)

"""KA-1112: deterministic system self-introspection audit."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class SystemBehaviorWindow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    window_id: str = Field(min_length=1, max_length=200)
    chaos_plan_count: int = Field(ge=0, le=1_000_000_000)
    unapproved_chaos_count: int = Field(ge=0, le=1_000_000_000)
    human_override_count: int = Field(ge=0, le=1_000_000_000)
    override_without_reason_count: int = Field(ge=0, le=1_000_000_000)
    drift_alert_count: int = Field(ge=0, le=1_000_000_000)
    unresolved_drift_count: int = Field(ge=0, le=1_000_000_000)


class KA1112Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "windows": [
                        {
                            "window_id": "window-1",
                            "chaos_plan_count": 2,
                            "unapproved_chaos_count": 0,
                            "human_override_count": 3,
                            "override_without_reason_count": 1,
                            "drift_alert_count": 1,
                            "unresolved_drift_count": 1,
                        }
                    ]
                }
            ]
        },
    )

    windows: list[SystemBehaviorWindow] = Field(min_length=1, max_length=10_000)


class KA1112SystemSelfIntrospectionAuditor(KnowledgeAlgorithm):
    """Audit structured chaos, override, and drift governance counters."""

    input_schema = KA1112Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1112"

    def _run_logic(self, input_data: KA1112Input) -> dict[str, Any]:
        findings = []
        for item in sorted(input_data.windows, key=lambda row: row.window_id):
            if item.unapproved_chaos_count:
                findings.append(
                    {
                        "window_id": item.window_id,
                        "finding": "unapproved_chaos_activity",
                        "severity": "critical",
                        "proposed_action": "contain_and_investigate",
                    }
                )
            if item.override_without_reason_count:
                findings.append(
                    {
                        "window_id": item.window_id,
                        "finding": "override_reason_missing",
                        "severity": "high",
                        "proposed_action": "require_override_review",
                    }
                )
            if item.unresolved_drift_count:
                findings.append(
                    {
                        "window_id": item.window_id,
                        "finding": "goal_drift_unresolved",
                        "severity": "critical",
                        "proposed_action": "block_evolution_and_review",
                    }
                )
        return {
            "success": True,
            "status": "system_self_introspection_audited",
            "audit_passed": not findings,
            "findings": findings,
            "governance_actions_applied": 0,
            "deterministic": True,
            "limitations": (
                "The audit relies on supplied structured counters and does not "
                "read logs, inspect processes, or apply governance actions."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1112SystemSelfIntrospectionAuditor(context).run(context)

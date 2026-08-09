"""Canonical CP19-I subsystem dispatch and authoritative effect receipts.

This adapter extends the one manifest/controller boundary to simulation, MCP,
providers, security, and operations. Knowledge Algorithms may validate or
propose effects; only an owning service can bind a proposal to an applied
receipt.
"""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable

from backend.governed_execution.knowledge_lifecycle import (
    KnowledgeLifecycleCoordinator,
    KnowledgeLifecycleError,
)
from backend.knowledge_algorithms.controller import CanonicalKAController


class ExtendedSubsystemError(KnowledgeLifecycleError):
    """Raised when CP19-I dispatch or receipt binding fails closed."""


@dataclass(slots=True)
class AuthoritativeEffectReceipt:
    """Evidence that an owning service, not a KA, applied one effect."""

    service: str
    operation: str
    resource_id: str
    request_sha256: str
    result_sha256: str
    idempotency_key: str
    status: str = "applied"
    receipt_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    applied_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    ka_plan_id: str | None = None
    ka_proposal_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for name in (
            "service",
            "operation",
            "resource_id",
            "request_sha256",
            "result_sha256",
            "idempotency_key",
        ):
            if not str(getattr(self, name) or "").strip():
                raise ExtendedSubsystemError(f"Effect receipt requires {name}")
        for name in ("request_sha256", "result_sha256"):
            value = str(getattr(self, name))
            if len(value) != 64 or any(
                character not in "0123456789abcdef" for character in value.lower()
            ):
                raise ExtendedSubsystemError(f"Effect receipt {name} must be SHA-256")
        if self.status != "applied":
            raise ExtendedSubsystemError(
                "Applied effect receipts require status=applied"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "dle.authoritative-effect-receipt.v1",
            **asdict(self),
        }


class ExtendedSubsystemCoordinator(KnowledgeLifecycleCoordinator):
    """Manifest-governed adapter for CP19-I owner and consumer operations."""

    def __init__(
        self,
        *,
        ka_controller: CanonicalKAController | None = None,
    ) -> None:
        super().__init__(
            ka_controller=ka_controller,
            registry_key="extended_subsystem_execution_registry",
            workflow_phase="cp19i",
        )

    @staticmethod
    def sha256_payload(payload: Any) -> str:
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def bind_effect_receipt(
        self,
        *,
        service: str,
        operation: str,
        resource_id: str,
        request_payload: Any,
        result_payload: Any,
        idempotency_key: str,
        ka_execution: Any | None = None,
        proposal_ids: list[str] | None = None,
    ) -> AuthoritativeEffectReceipt:
        """Bind a completed service effect to its KA plan and content hashes."""
        return AuthoritativeEffectReceipt(
            service=service,
            operation=operation,
            resource_id=resource_id,
            request_sha256=self.sha256_payload(request_payload),
            result_sha256=self.sha256_payload(result_payload),
            idempotency_key=idempotency_key,
            ka_plan_id=(
                str(ka_execution.plan.plan_id) if ka_execution is not None else None
            ),
            ka_proposal_ids=sorted(
                {str(value) for value in (proposal_ids or []) if value}
            ),
        )

    @staticmethod
    def execution_outputs(execution: Any) -> dict[str, dict[str, Any]]:
        return {
            canonical_id: dict(result.get("output") or {})
            for canonical_id, result in execution.results.items()
        }

    @staticmethod
    def lifecycle_evidence(execution: Any) -> dict[str, Any]:
        """Return content-free durable evidence for an owning service ledger."""
        return {
            "schema_version": "dle.ka-lifecycle-evidence.v1",
            "owner": execution.owner,
            "operation": execution.operation,
            "plan_id": execution.plan.plan_id,
            "manifest_version": execution.plan.manifest_version,
            "status": execution.report.status.value,
            "selected_ids": list(execution.plan.selected_ids),
            "executed_ids": list(execution.executed_ids),
            "execution_order": list(execution.plan.execution_order),
            "required_failure": execution.report.required_failure,
        }

    def analyze_observability_snapshot(
        self,
        *,
        diagnostics: dict[str, Any],
        route_measurements: list[dict[str, Any]],
        request_id: str,
        principal_id: str | None,
        concurrency_reference: int = 8,
    ) -> Any:
        """Analyze one measured, content-free application diagnostic snapshot."""
        requests = dict(diagnostics.get("requests") or {})
        total_requests = max(0, int(requests.get("total") or 0))
        inflight_requests = max(0, int(requests.get("inflight") or 0))
        uptime_seconds = max(0.0, float(requests.get("uptime_seconds") or 0.0))
        concurrency_reference = max(1, min(int(concurrency_reference), 1_024))
        profile_samples = [
            {
                "duration_ms": max(0.0, float(row.get("duration_ms") or 0.0)),
                "calls": max(0, int(row.get("calls") or 0)),
                "hotspot": str(row.get("route") or "measured_route")[:500],
            }
            for row in route_measurements[:100]
        ]
        if not profile_samples:
            profile_samples = [
                {
                    "duration_ms": uptime_seconds * 1_000.0,
                    "calls": total_requests,
                    "hotspot": "application_runtime_uptime",
                }
            ]
        status = str(diagnostics.get("status") or "unknown")
        alert_level = "info" if status == "ok" else "warning"
        run_id = f"observability:{request_id}"
        execution = self.execute_operation_sync(
            owner="security_operations_lifecycle",
            operation="observability",
            requested_ids=[
                "KA-091",
                "KA-092",
                "KA-094",
                "KA-095",
                "KA-098",
                "KA-099",
                "KA-100",
            ],
            ka_inputs={
                "KA-091": {
                    "data": {
                        "requests_total": total_requests,
                        "requests_inflight": inflight_requests,
                        "uptime_seconds": round(uptime_seconds, 6),
                    },
                    "viz_type": "bar",
                    "title": "Application diagnostics",
                },
                "KA-092": {
                    "dashboard_id": "application_diagnostics",
                    "widgets": [
                        {
                            "widget_id": "runtime_status",
                            "label": "Runtime status",
                            "value": status,
                            "status": "measured",
                        },
                        {
                            "widget_id": "requests_total",
                            "label": "Requests total",
                            "value": total_requests,
                            "status": "measured",
                        },
                        {
                            "widget_id": "requests_inflight",
                            "label": "Requests in flight",
                            "value": inflight_requests,
                            "status": "measured",
                        },
                    ],
                },
                "KA-094": {
                    "report_name": "application_diagnostics",
                    "output_format": "json",
                    "sections": {
                        name: True
                        for name in (
                            "config",
                            "database",
                            "external_telemetry",
                            "logging",
                            "requests",
                            "runtime",
                            "support_bundle",
                        )
                        if name in diagnostics
                    },
                },
                "KA-095": {
                    "event": f"application_diagnostics_status:{status}",
                    "level": alert_level,
                    "source": "authenticated_diagnostics",
                },
                "KA-098": {
                    "target": "application_http_runtime",
                    "samples": profile_samples,
                },
                "KA-099": {
                    "error_context": f"application_diagnostics_status:{status}",
                    "system_metrics": {
                        "requests_total": total_requests,
                        "requests_inflight": inflight_requests,
                        "uptime_seconds": round(uptime_seconds, 6),
                    },
                },
                "KA-100": {
                    "load_profile": min(
                        1.0,
                        inflight_requests / concurrency_reference,
                    ),
                    "current_worker_limit": concurrency_reference,
                },
            },
            request_id=request_id,
            run_id=run_id,
            max_effects=0,
            session_id=request_id,
            principal_id=principal_id,
            tier="authenticated_local_diagnostics",
            layer="operations",
            required=True,
        )
        self.observability_decision(execution)
        return execution

    @classmethod
    def observability_decision(cls, execution: Any) -> dict[str, Any]:
        """Validate and expose the content-free observability advisory result."""
        required_ids = {
            "KA-091",
            "KA-092",
            "KA-094",
            "KA-095",
            "KA-098",
            "KA-099",
            "KA-100",
        }
        outputs = cls.execution_outputs(execution)
        missing = sorted(required_ids - set(outputs))
        if missing:
            raise ExtendedSubsystemError(
                "Observability analysis omitted required KAs: " + ",".join(missing)
            )
        if outputs["KA-091"].get("rendered") is not False:
            raise ExtendedSubsystemError("Visualization must remain renderer-neutral")
        if outputs["KA-092"].get("rendered") is not False:
            raise ExtendedSubsystemError("Dashboard must remain renderer-neutral")
        if outputs["KA-094"].get("artifact_created") is not False:
            raise ExtendedSubsystemError("Reporting KA cannot claim an artifact")
        if outputs["KA-095"].get("alert_triggered") is not False:
            raise ExtendedSubsystemError("Alerting KA cannot claim delivery")
        if outputs["KA-099"].get("remote_port_active") is not False:
            raise ExtendedSubsystemError("Debugging KA cannot open a remote port")
        if outputs["KA-100"].get("optimization_applied") is not False:
            raise ExtendedSubsystemError("Optimization KA cannot mutate the runtime")
        return {
            "schema_version": "dle.observability-advisory.v1",
            "status": "analyzed",
            "lifecycle": cls.lifecycle_evidence(execution),
            "outputs": outputs,
            "effects_applied": 0,
            "content_policy": "measured_content_free_diagnostics_only",
        }

    def admit_mcp_tool(
        self,
        *,
        execution_id: str,
        principal_id: str,
        server_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        required_scopes: set[str],
        consent_approved: bool,
        crosses_trust_boundary: bool = False,
        connector_authenticated: bool = True,
        connector_encrypted: bool = True,
        connector_integrity_protected: bool = True,
    ) -> Any:
        """Run security/operations proposals before an MCP tool side effect."""
        argument_text = json.dumps(
            arguments,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        scopes_satisfied = bool(required_scopes)
        destructive_scope = any(
            str(scope).lower().endswith((":write", ":delete", ":admin"))
            for scope in required_scopes
        )
        execution = self.execute_operation_sync(
            owner="mcp_connectors",
            operation="admission",
            requested_ids=[
                "KA-022",
                "KA-136",
                "KA-137",
                "KA-177",
                "KA-179",
            ],
            ka_inputs={
                "KA-022": {
                    "recommendation": (
                        f"Execute MCP tool {tool_name} on connector {server_id}"
                    ),
                    "impact_scores": {
                        "technical": 0.6 if destructive_scope else 0.2,
                        "security": 0.8 if destructive_scope else 0.3,
                        "compliance": 0.8 if destructive_scope else 0.2,
                        "financial": 0.6 if destructive_scope else 0.0,
                        "schedule": 0.6 if destructive_scope else 0.0,
                        "reputational": 0.8 if destructive_scope else 0.0,
                    },
                },
                "KA-136": {
                    "assets": [
                        {
                            "asset_id": "mcp_gateway",
                            "criticality": "critical",
                            "privileged": True,
                        },
                        {
                            "asset_id": f"connector:{server_id}",
                            "criticality": "high",
                            "stores_sensitive_data": True,
                        },
                    ],
                    "data_flows": [
                        {
                            "flow_id": f"tool:{tool_name}",
                            "source_asset_id": "mcp_gateway",
                            "target_asset_id": f"connector:{server_id}",
                            "crosses_trust_boundary": bool(crosses_trust_boundary),
                            "authenticated": bool(connector_authenticated),
                            "encrypted": bool(connector_encrypted),
                            "integrity_protected": bool(connector_integrity_protected),
                        }
                    ],
                },
                "KA-137": {
                    "documents": [
                        {
                            "document_id": "mcp_tool_arguments",
                            "text": argument_text.replace('"', "")[:1_000_000],
                        }
                    ],
                    "detect_types": ["api_key", "ssn"],
                },
                "KA-177": {
                    "attributes": {
                        "consent_approved": bool(consent_approved),
                        "scopes_satisfied": scopes_satisfied,
                    },
                    "rules": [
                        {
                            "rule_id": "deny-without-consent",
                            "attribute": "consent_approved",
                            "operator": "equals",
                            "expected": False,
                            "effect": "deny",
                        },
                        {
                            "rule_id": "deny-without-scopes",
                            "attribute": "scopes_satisfied",
                            "operator": "equals",
                            "expected": False,
                            "effect": "deny",
                        },
                        {
                            "rule_id": "allow-governed-mcp",
                            "attribute": "consent_approved",
                            "operator": "equals",
                            "expected": True,
                            "effect": "allow",
                        },
                    ],
                    "default_effect": "deny",
                },
                "KA-179": {
                    "subject_id": principal_id,
                    "roles": ["mcp_executor"],
                    "attributes": {"connector": server_id},
                    "action": "execute",
                    "resource_type": "mcp_tool",
                    "rules": [
                        {
                            "rule_id": "mcp-executor",
                            "actions": ["execute"],
                            "resource_types": ["mcp_tool"],
                            "required_roles": ["mcp_executor"],
                            "required_attributes": {"connector": server_id},
                            "effect": "allow",
                        }
                    ],
                },
            },
            request_id=f"mcp-admission:{execution_id}",
            run_id=execution_id,
            max_effects=2,
            session_id=execution_id,
            principal_id=principal_id,
            tier="external_connector",
            layer="mcp_gateway",
            service_capabilities={
                "policy_decision_service",
                "operations_control_service",
            },
            required=True,
        )
        outputs = self.execution_outputs(execution)
        sensitive_types = {
            str(row.get("data_type"))
            for row in outputs.get("KA-137", {}).get("findings", [])
            if isinstance(row, dict)
        }
        blockers = []
        if outputs.get("KA-022", {}).get("mitigation_required"):
            blockers.append("risk_mitigation_required")
        if outputs.get("KA-136", {}).get("threats_present"):
            blockers.append("threat_model_findings")
        if outputs.get("KA-177", {}).get("decision") != "allow":
            blockers.append("policy_denied")
        if outputs.get("KA-179", {}).get("decision") != "allow":
            blockers.append("access_denied")
        if "api_key" in sensitive_types:
            blockers.append("credential_in_tool_arguments")
        if blockers:
            raise ExtendedSubsystemError(
                "MCP KA admission blocked: " + ",".join(sorted(blockers))
            )
        return execution

    def validate_mcp_result(
        self,
        *,
        execution_id: str,
        principal_id: str,
        tool_name: str,
        governed_result: dict[str, Any],
    ) -> Any:
        """Record post-call security, audit, and operations proposals."""
        content = str(governed_result.get("content") or "")
        prompt_risk = bool(governed_result.get("prompt_injection_risk"))
        return self.execute_operation_sync(
            owner="mcp_connectors",
            operation="result_validation",
            requested_ids=[
                "KA-010",
                "KA-096",
                "KA-097",
                "KA-175",
                "KA-182",
            ],
            ka_inputs={
                "KA-010": {"content": content[:1_000_000]},
                "KA-096": {
                    "logs": [
                        {
                            "event": "mcp_tool_result",
                            "tool": tool_name,
                            "result_sha256": governed_result.get("sha256"),
                            "prompt_injection_risk": prompt_risk,
                        }
                    ]
                },
                "KA-097": {
                    "event_data": {
                        "type": "mcp_tool_result",
                        "execution_id": execution_id,
                        "tool": tool_name,
                        "result_sha256": governed_result.get("sha256"),
                        "trust": governed_result.get("trust"),
                    },
                    "actor_id": principal_id,
                },
                "KA-175": {
                    "controls": [
                        {
                            "control_id": "MCP-SCOPE",
                            "control_family": "access",
                            "enabled": True,
                            "tested": True,
                            "evidence_refs": [execution_id],
                            "severity_if_missing": "critical",
                        },
                        {
                            "control_id": "MCP-RESULT-GOVERNANCE",
                            "control_family": "logging",
                            "enabled": True,
                            "tested": not prompt_risk,
                            "evidence_refs": [str(governed_result.get("sha256") or "")],
                            "severity_if_missing": "high",
                        },
                    ]
                },
                "KA-182": {
                    "signals": [
                        {
                            "signal_id": "mcp-prompt-injection",
                            "signal_type": "policy_bypass",
                            "observed_count": int(prompt_risk),
                            "threshold": 1,
                            "source_ref": execution_id,
                            "trusted_source": True,
                        }
                    ]
                },
            },
            request_id=f"mcp-result:{execution_id}",
            run_id=execution_id,
            max_effects=0,
            session_id=execution_id,
            principal_id=principal_id,
            tier="external_connector",
            layer="mcp_gateway",
            required=True,
        )

    @staticmethod
    def mcp_result_governance_decision(execution: Any) -> dict[str, Any]:
        """Consume MCP result KAs into the owning route's release decision."""
        outputs = ExtendedSubsystemCoordinator.execution_outputs(execution)
        bias = outputs.get("KA-010", {})
        logging_result = outputs.get("KA-096", {})
        audit = outputs.get("KA-097", {})
        security_audit = outputs.get("KA-175", {})
        threat = outputs.get("KA-182", {})

        blockers = []
        if security_audit.get("audit_passed") is not True:
            blockers.append("security_control_audit_failed")
        if threat.get("threat_detected") is True:
            blockers.append("threat_detected")
        if logging_result.get("logs_processed") != 1:
            blockers.append("logging_validation_failed")
        if not audit.get("audit_id") or not audit.get("content_sha256"):
            blockers.append("audit_proposal_missing")

        return {
            "schema_version": "dle.mcp-result-governance.v1",
            "release_allowed": not blockers,
            "blockers": sorted(blockers),
            "requires_human_review": bool(bias.get("is_biased")),
            "bias_score": float(bias.get("bias_score") or 0.0),
            "security_audit_passed": bool(security_audit.get("audit_passed")),
            "threat_detected": bool(threat.get("threat_detected")),
            "logging_backend": str(logging_result.get("backend") or ""),
            "audit_id": str(audit.get("audit_id") or ""),
            "audit_content_sha256": str(audit.get("content_sha256") or ""),
        }

    def plan_mcp_recovery(
        self,
        *,
        execution_id: str,
        principal_id: str,
        server_id: str,
        operation: str,
        error_code: str,
        failures: int,
        successes: int,
        effect_already_applied: bool,
    ) -> Any:
        """Build the fail-closed MCP recovery plan after a real route failure."""
        incident_type = (
            "policy_violation"
            if error_code.startswith("MCP_KA_")
            else "service_disruption"
        )
        severity = "high" if effect_already_applied else "medium"
        return self.execute_operation_sync(
            owner="mcp_connectors",
            operation="recovery",
            requested_ids=["KA-106", "KA-184"],
            ka_inputs={
                "KA-106": {
                    "operation": "network",
                    "failures": max(1, int(failures)),
                    "successes": max(0, int(successes)),
                    "dependency_status": {
                        f"connector:{server_id}": "failed",
                    },
                },
                "KA-184": {
                    "incidents": [
                        {
                            "incident_id": f"mcp:{execution_id}",
                            "severity": severity,
                            "incident_type": incident_type,
                            "affected_asset_refs": [
                                "mcp_gateway",
                                f"connector:{server_id}",
                                f"operation:{operation}",
                            ],
                            "owner_assigned": True,
                            "containment_ready": True,
                            "evidence_preservation_ready": True,
                        }
                    ]
                },
            },
            request_id=f"mcp-recovery:{execution_id}",
            run_id=execution_id,
            max_effects=1,
            session_id=execution_id,
            principal_id=principal_id,
            tier="external_connector",
            layer="mcp_recovery",
            service_capabilities={"operations_control_service"},
            required=True,
        )

    @staticmethod
    def mcp_recovery_decision(execution: Any) -> dict[str, Any]:
        """Consume the recovery KAs without claiming that a plan was applied."""
        outputs = ExtendedSubsystemCoordinator.execution_outputs(execution)
        fault_tolerance = outputs.get("KA-106", {})
        incident_response = outputs.get("KA-184", {})
        plans = incident_response.get("plans")
        if not isinstance(plans, list) or len(plans) != 1:
            raise ExtendedSubsystemError(
                "MCP recovery requires exactly one incident-response plan"
            )
        plan = plans[0]
        if plan.get("decision") != "activate_plan":
            raise ExtendedSubsystemError("MCP recovery plan is not actionable")
        circuit_state = str(fault_tolerance.get("circuit_state") or "")
        if circuit_state not in {"OPEN", "HALF_OPEN", "CLOSED"}:
            raise ExtendedSubsystemError("MCP recovery circuit state is invalid")
        return {
            "schema_version": "dle.mcp-recovery-plan.v1",
            "status": "planned",
            "automatic_retry_allowed": False,
            "circuit_state": circuit_state,
            "circuit_reason": str(fault_tolerance.get("circuit_reason") or ""),
            "fallback_engaged": bool(fault_tolerance.get("fallback_engaged")),
            "recommended_retry_policy": dict(
                fault_tolerance.get("retry_policy_applied") or {}
            ),
            "incident_id": str(plan.get("incident_id") or ""),
            "incident_decision": str(plan.get("decision") or ""),
            "proposed_steps": list(plan.get("ordered_steps") or []),
            "actions_applied": int(incident_response.get("actions_applied") or 0),
        }

    async def plan_provider_request(
        self,
        *,
        request_id: str,
        trace_id: str,
        principal_id: str | None,
        messages: list[dict[str, Any]],
        token_budget: int,
    ) -> Any:
        """Validate provider context selection before any external call."""
        elements = []
        required_ids = []
        for index, message in enumerate(messages):
            element_id = f"message-{index}"
            role = str(message.get("role") or "user")
            required = role == "system" or index == len(messages) - 1
            if required:
                required_ids.append(element_id)
            elements.append(
                {
                    "element_id": element_id,
                    "token_count": max(
                        1,
                        len(str(message.get("content") or "")) // 4,
                    ),
                    "relevance": 1.0 if required else 0.8,
                    "priority": 2.0 if required else 1.0,
                    "required": required,
                    "content_ref": f"{trace_id}:{element_id}",
                }
            )
        if not elements:
            raise ExtendedSubsystemError("Provider request has no context")
        execution = await self.execute_operation(
            owner="provider_gateway",
            operation="request_governance",
            requested_ids=["KA-1072"],
            ka_inputs={
                "KA-1072": {
                    "context_elements": elements,
                    "token_budget": max(1, min(int(token_budget), 2_000_000)),
                }
            },
            request_id=f"provider-plan:{request_id}",
            run_id=trace_id,
            max_effects=0,
            session_id=trace_id,
            principal_id=principal_id,
            tier="provider_gateway",
            layer="provider_execution",
            required=True,
        )
        selected = set(
            self.execution_outputs(execution)
            .get("KA-1072", {})
            .get("selected_element_ids", [])
        )
        if not set(required_ids).issubset(selected):
            raise ExtendedSubsystemError(
                "Provider required context exceeds the declared budget"
            )
        return execution

    async def monitor_provider_result(
        self,
        *,
        request_id: str,
        trace_id: str,
        principal_id: str | None,
        duration_ms: int,
    ) -> Any:
        """Evaluate measured provider latency without inventing quality labels."""
        return await self.execute_operation(
            owner="provider_gateway",
            operation="response_monitoring",
            requested_ids=["KA-084"],
            ka_inputs={
                "KA-084": {
                    "live_metrics": {"p99_latency": max(0, int(duration_ms))},
                    "baseline_metrics": {},
                }
            },
            request_id=f"provider-monitor:{request_id}",
            run_id=trace_id,
            max_effects=0,
            session_id=trace_id,
            principal_id=principal_id,
            tier="provider_gateway",
            layer="provider_execution",
            required=True,
        )

    @staticmethod
    def provider_monitoring_decision(execution: Any) -> dict[str, Any]:
        """Consume measured provider monitoring without claiming an alert effect."""
        output = ExtendedSubsystemCoordinator.execution_outputs(execution).get(
            "KA-084",
            {},
        )
        anomalies = output.get("anomalies")
        metric_deltas = output.get("metric_deltas")
        if not isinstance(anomalies, list) or not isinstance(metric_deltas, dict):
            raise ExtendedSubsystemError("Provider monitoring output is incomplete")
        health_score = output.get("health_score")
        if not isinstance(health_score, (int, float)):
            raise ExtendedSubsystemError("Provider monitoring health score is invalid")
        return {
            "schema_version": "dle.provider-monitoring-decision.v1",
            "status": "measured",
            "drift_detected": bool(output.get("drift_detected")),
            "anomalies": [str(value) for value in anomalies],
            "metric_deltas": dict(metric_deltas),
            "health_score": float(health_score),
            "alert_recommended": bool(output.get("alert_recommended")),
            "notification_applied": False,
        }

    def execute_external_research(
        self,
        *,
        request_id: str,
        principal_id: str,
        sub_question: str,
        allowed_domains: list[str],
        maximum_sources: int,
        timebox_seconds: int,
        connector_id: str,
        authentication_verified: bool,
        policy_approved: bool,
        rate_limit_allowed: bool,
        connector_approved: bool,
        human_approved: bool,
        connector_call: Callable[[dict[str, Any]], dict[str, Any]],
        record_receipt: Callable[[dict[str, Any]], str],
        cancelled: bool = False,
    ) -> dict[str, Any]:
        """Run bounded external research through the provider owner and ledger."""
        if cancelled:
            raise ExtendedSubsystemError("External research request was cancelled")
        execution = self.execute_operation_sync(
            owner="provider_gateway",
            operation="external_research",
            requested_ids=["KA-111", "KA-1114"],
            ka_inputs={
                "KA-111": {
                    "path": "/internal/research",
                    "method": "POST",
                    "principal_id": principal_id,
                    "authentication_verified": authentication_verified,
                    "policy_approved": policy_approved,
                    "rate_limit_allowed": rate_limit_allowed,
                    "rate_limit_remaining": 1,
                    "route_target": connector_id,
                },
                "KA-1114": {
                    "sub_question": sub_question,
                    "allowed_domains": allowed_domains,
                    "maximum_sources": maximum_sources,
                    "timebox_seconds": timebox_seconds,
                    "connector_id": connector_id,
                    "connector_approved": connector_approved,
                    "policy_approved": policy_approved,
                    "human_approved": human_approved,
                },
            },
            request_id=request_id,
            run_id=f"external-research:{request_id}",
            max_effects=2,
            principal_id=principal_id,
            tier="provider_gateway",
            layer="external_research",
            service_capabilities={"provider_gateway_service"},
        )
        outputs = self.execution_outputs(execution)
        if outputs["KA-111"].get("decision") != "admit":
            raise ExtendedSubsystemError("Gateway admission blocked external research")
        research = outputs["KA-1114"]
        if research.get("decision") != "admit":
            raise ExtendedSubsystemError("Research policy blocked external research")
        request_payload = dict(research.get("research_request") or {})
        result = connector_call(request_payload)
        if not isinstance(result, dict):
            raise ExtendedSubsystemError(
                "Research connector returned an invalid result"
            )
        citations = result.get("citations")
        if not isinstance(citations, list) or not citations:
            raise ExtendedSubsystemError("Research result requires citations")
        if len(citations) > maximum_sources:
            raise ExtendedSubsystemError("Research result exceeded the source budget")
        allowed = {domain.casefold() for domain in allowed_domains}
        for citation in citations:
            if not isinstance(citation, dict):
                raise ExtendedSubsystemError(
                    "Research result returned an invalid citation"
                )
            domain = str(citation.get("domain") or "").casefold()
            if domain not in allowed:
                raise ExtendedSubsystemError("Research result used a disallowed domain")
        proposal_ids = [
            str(outputs[canonical_id]["effect_proposal"]["effect_id"])
            for canonical_id in ("KA-111", "KA-1114")
            if isinstance(outputs[canonical_id].get("effect_proposal"), dict)
        ]
        receipt = self.bind_effect_receipt(
            service="ProviderGatewayService",
            operation="external_research:connector_call",
            resource_id=str(research["request_id"]),
            request_payload=request_payload,
            result_payload=result,
            idempotency_key=request_id,
            ka_execution=execution,
            proposal_ids=proposal_ids,
        )
        ledger_record_id = str(record_receipt(receipt.to_dict()) or "").strip()
        if not ledger_record_id:
            raise ExtendedSubsystemError("Research receipt was not durably recorded")
        return {
            "execution": execution,
            "result": result,
            "receipt": receipt,
            "ledger_record_id": ledger_record_id,
        }

    def execute_delivery_boundary(
        self,
        *,
        request_id: str,
        principal_id: str,
        ka_inputs: dict[str, dict[str, Any]],
        delivery_call: Callable[[dict[str, Any]], dict[str, Any]],
        record_receipt: Callable[[dict[str, Any]], str],
    ) -> dict[str, Any]:
        """Apply reviewed delivery proposals only through OperationsControlService."""
        requested_ids = ["KA-093", "KA-110", "KA-112", "KA-114", "KA-115"]
        execution = self.execute_operation_sync(
            owner="security_operations_lifecycle",
            operation="messaging",
            requested_ids=requested_ids,
            ka_inputs=ka_inputs,
            request_id=request_id,
            run_id=f"delivery:{request_id}",
            max_effects=len(requested_ids),
            principal_id=principal_id,
            tier="operations",
            layer="delivery",
            service_capabilities={"operations_control_service"},
        )
        outputs = self.execution_outputs(execution)
        applied = []
        for canonical_id in requested_ids:
            proposal = outputs[canonical_id].get("effect_proposal")
            if not isinstance(proposal, dict):
                continue
            result = delivery_call(dict(proposal))
            if not isinstance(result, dict) or result.get("status") not in {
                "enqueued",
                "delivered",
            }:
                raise ExtendedSubsystemError("Delivery service did not apply proposal")
            resource_id = str(result.get("record_id") or "").strip()
            if not resource_id:
                raise ExtendedSubsystemError(
                    "Delivery result requires a durable record ID"
                )
            receipt = self.bind_effect_receipt(
                service="OperationsControlService",
                operation=str(proposal.get("kind") or "delivery"),
                resource_id=resource_id,
                request_payload=proposal,
                result_payload=result,
                idempotency_key=f"{request_id}:{proposal['effect_id']}",
                ka_execution=execution,
                proposal_ids=[str(proposal["effect_id"])],
            )
            ledger_record_id = str(record_receipt(receipt.to_dict()) or "").strip()
            if not ledger_record_id:
                raise ExtendedSubsystemError(
                    "Delivery receipt was not durably recorded"
                )
            applied.append(
                {
                    "canonical_id": canonical_id,
                    "result": result,
                    "receipt": receipt,
                    "ledger_record_id": ledger_record_id,
                }
            )
        return {"execution": execution, "applied": applied}

    def plan_simulation(
        self,
        *,
        simulation_id: str,
        principal_id: str,
        scenario: Any,
    ) -> Any:
        """Run the complete canonical simulation planning chain."""
        plan = scenario.plan
        context = dict(scenario.context or {})
        estimates = dict(context.get("resource_estimates") or {})
        estimated_duration_ms = float(
            estimates.get("duration_ms", scenario.timeout_seconds * 1_000)
        )
        estimated_tokens = int(estimates.get("tokens", plan.max_output_tokens))
        estimated_cost = float(estimates.get("cost_units", scenario.max_cost_usd or 0))
        estimated_memory = float(estimates.get("peak_memory_mb", 256))
        simulation_capabilities = ["KA-042", "KA-070", "KA-1091"]
        planned_steps = [
            {
                "step_id": f"simulation-{index}",
                "capability_id": canonical_id,
                "layer": "L7",
                "query_class": "simulation",
            }
            for index, canonical_id in enumerate(
                simulation_capabilities,
                start=1,
            )
        ]
        orchestration_pipeline = [
            {
                "ka_id": row["capability_id"],
                "depends_on": ([] if index == 0 else [f"step_{index}"]),
            }
            for index, row in enumerate(planned_steps)
        ]
        provider_steps = [
            {
                "step_id": (
                    "contextualize"
                    if index == 1
                    else (
                        "synthesis"
                        if index == plan.max_provider_calls
                        else f"debate_{index - 1}"
                    )
                ),
                "iterations": 1,
                "estimated_ms_per_iteration": (
                    estimated_duration_ms / plan.max_provider_calls
                ),
                "estimated_tokens_per_iteration": math.ceil(
                    max(estimated_tokens, plan.max_output_tokens)
                    / plan.max_provider_calls
                ),
                "estimated_peak_memory_mb": estimated_memory,
                "estimated_cost_per_iteration": (
                    estimated_cost / plan.max_provider_calls
                ),
            }
            for index in range(1, plan.max_provider_calls + 1)
        ]
        available = sorted(
            canonical_id
            for canonical_id, definition in self.ka_controller.manifest.entries.items()
            if definition.admission.production_enabled
        )
        return self.execute_operation_sync(
            owner="simulation",
            operation="planning",
            requested_ids=None,
            ka_inputs={
                "KA-004": {"query": scenario.query},
                "KA-005": {"query": scenario.query},
                "KA-031": {
                    "query": scenario.query,
                    "query_class": "COUNTERFACTUAL",
                    "complexity_tier": scenario.depth.value,
                    "policy_flags": ["local_first"],
                    "available_kas": available,
                    "budget": {"max_kas": 10},
                },
                "KA-036": {
                    "problem": scenario.query,
                    "declared_step_count": len(orchestration_pipeline),
                    "dependency_count": len(orchestration_pipeline) - 1,
                    "observed_latencies_ms": [],
                },
                "KA-032": {
                    "pipeline": orchestration_pipeline,
                    "simulation_state": {"completed_steps": []},
                    "exit_criteria": {
                        "min_completed": len(orchestration_pipeline),
                        "max_failures": 0,
                    },
                },
                "KA-037": {
                    "priority": "normal",
                    "task_type": "orchestration",
                    "complexity": scenario.depth.value,
                    "input_size": len(scenario.query),
                    "expected_steps": plan.max_provider_calls,
                    "latency_target_ms": scenario.timeout_seconds * 1_000,
                },
                "KA-1080": {
                    "planned_steps": provider_steps,
                    "contingency_ratio": 0,
                },
                "KA-1081": {
                    "estimated_duration_ms": estimated_duration_ms,
                    "estimated_tokens": estimated_tokens,
                    "estimated_cost_units": estimated_cost,
                    "estimated_peak_memory_mb": estimated_memory,
                    "recursion_depth": 0,
                    "concurrency": 1,
                    "maximum_duration_ms": scenario.timeout_seconds * 1_000,
                    "maximum_tokens": scenario.max_total_tokens,
                    "maximum_cost_units": (
                        scenario.max_cost_usd
                        if scenario.max_cost_usd is not None
                        else 1_000_000_000
                    ),
                    "maximum_peak_memory_mb": 4_096,
                    "maximum_recursion_depth": 0,
                    "maximum_concurrency": 1,
                },
                "KA-1073": {
                    "utterance": scenario.query,
                    "candidate_intents": [
                        {
                            "intent_id": "COUNTERFACTUAL",
                            "description": "Counterfactual simulation",
                            "keywords": [
                                "simulate",
                                "simulation",
                                "counterfactual",
                                "scenario",
                            ],
                            "required_slots": [],
                        },
                        {
                            "intent_id": "GENERAL",
                            "description": "General analysis",
                            "keywords": ["assess", "evaluate", "review"],
                            "required_slots": [],
                        },
                    ],
                    "minimum_match": 0.0,
                    "ambiguity_margin": 0.0,
                },
                "KA-1107": {
                    "planned_steps": planned_steps,
                    "allowed_capability_ids": simulation_capabilities,
                    "allowed_layers": ["L7"],
                    "allowed_query_classes": ["simulation"],
                },
                "KA-113": {"query": scenario.query},
            },
            request_id=f"simulation-plan:{simulation_id}",
            run_id=simulation_id,
            max_effects=1,
            session_id=simulation_id,
            principal_id=principal_id,
            tier=scenario.depth.value,
            layer="simulation_job",
            service_capabilities={"simulation_job_service"},
            required=True,
        )

    @staticmethod
    def simulation_resource_limits(
        execution: Any,
        *,
        scenario: Any,
    ) -> dict[str, Any]:
        """Translate canonical allocation into limits enforced by the job."""
        outputs = ExtendedSubsystemCoordinator.execution_outputs(execution)
        allocation = outputs.get("KA-037", {})
        allocated_tokens = max(0, int(allocation.get("token_budget") or 0))
        return {
            "max_total_tokens": min(
                int(scenario.max_total_tokens),
                allocated_tokens,
            ),
            "allocated_token_budget": allocated_tokens,
            "allocated_timeout_ms": max(
                0,
                int(allocation.get("timeout_ms") or 0),
            ),
            "execution_queue": str(allocation.get("execution_queue") or "unallocated"),
        }

    @staticmethod
    def simulation_plan_allowed(
        execution: Any,
        *,
        scenario: Any | None = None,
    ) -> tuple[bool, list[str]]:
        """Interpret semantic gates after the execution itself succeeds."""
        blockers: list[str] = []
        outputs = {
            canonical_id: dict(result.get("output") or {})
            for canonical_id, result in execution.results.items()
        }
        if not outputs.get("KA-004", {}).get("is_valid", False):
            blockers.append("input_validation_blocked")
        if not outputs.get("KA-1081", {}).get("allowed", False):
            blockers.extend(
                f"budget:{row.get('budget')}"
                for row in outputs.get("KA-1081", {}).get("violations", [])
            )
        if not outputs.get("KA-1107", {}).get("plan_allowed", False):
            blockers.append("reasoning_boundary_blocked")
        if outputs.get("KA-032", {}).get("final_status") != "COMPLETED":
            blockers.append("simulation_plan_not_completed")
        allocation = outputs.get("KA-037", {})
        allocated_tokens = int(allocation.get("token_budget") or 0)
        required_tokens = (
            int(scenario.plan.max_output_tokens) if scenario is not None else 1
        )
        effective_tokens = (
            min(
                int(scenario.max_total_tokens),
                allocated_tokens,
            )
            if scenario is not None
            else allocated_tokens
        )
        if effective_tokens < required_tokens:
            blockers.append("resource_allocation_below_plan_minimum")
        if outputs.get("KA-1081", {}).get("estimate_source") != "KA-1080_dependency":
            blockers.append("cost_estimate_not_consumed")
        return not blockers, sorted(set(blockers))

    def plan_simulation_counterfactual(
        self,
        *,
        simulation_id: str,
        principal_id: str,
        scenario: Any,
    ) -> Any:
        """Project the scenario before the owning job starts provider work."""
        settings = dict((scenario.context or {}).get("counterfactual") or {})
        baseline = dict(settings.get("baseline") or {})
        change = settings.get("change")
        if change is None:
            change = {"scenario_query": scenario.query}
        hypotheticals = list(settings.get("hypotheticals") or [])
        relationships = dict(settings.get("relationships") or {})
        graph = dict(settings.get("graph") or {})
        return self.execute_operation_sync(
            owner="simulation",
            operation="counterfactual",
            requested_ids=["KA-042", "KA-070"],
            ka_inputs={
                "KA-042": {
                    "scenario": scenario.query,
                    "change": change,
                    "baseline": baseline,
                    "relationships": relationships,
                },
                "KA-070": {
                    "hypotheticals": hypotheticals,
                    "graph": graph,
                },
            },
            request_id=f"simulation-counterfactual:{simulation_id}",
            run_id=simulation_id,
            max_effects=1,
            session_id=simulation_id,
            principal_id=principal_id,
            tier=scenario.depth.value,
            layer="simulation_job",
            service_capabilities={"simulation_job_service"},
            required=True,
        )

    @staticmethod
    def simulation_counterfactual_context(execution: Any) -> dict[str, Any]:
        """Return the bounded canonical projection consumed by the engine."""
        outputs = ExtendedSubsystemCoordinator.execution_outputs(execution)
        projection = outputs.get("KA-042", {})
        ripple = outputs.get("KA-070", {})
        if not projection.get("success") or not ripple.get("success"):
            raise ExtendedSubsystemError(
                "Canonical counterfactual projection did not complete"
            )
        if not ripple.get("local_projection_consumed"):
            raise ExtendedSubsystemError(
                "Graph counterfactual did not consume the local projection"
            )
        return {
            "schema_version": "dle.simulation-counterfactual-context.v1",
            "local_projection": projection,
            "graph_projection": ripple,
            "ka_lifecycle": ExtendedSubsystemCoordinator.lifecycle_evidence(execution),
        }

    def plan_simulation_outcome(
        self,
        *,
        simulation_id: str,
        principal_id: str,
        status: str,
        summary: str,
        significance: float,
    ) -> Any:
        """Create the proposal that precedes authoritative artifact writes."""
        return self.execute_operation_sync(
            owner="simulation",
            operation="outcome_archive",
            requested_ids=["KA-1091"],
            ka_inputs={
                "KA-1091": {
                    "outcomes": [
                        {
                            "scenario_id": simulation_id,
                            "outcome_id": f"{simulation_id}:result",
                            "status": status,
                            "significance": max(
                                0,
                                min(1, float(significance)),
                            ),
                            "summary": str(summary)[:50_000],
                            "artifact_refs": [],
                        }
                    ],
                    "minimum_significance": 0,
                }
            },
            request_id=f"simulation-outcome:{simulation_id}",
            run_id=simulation_id,
            max_effects=1,
            session_id=simulation_id,
            principal_id=principal_id,
            tier="simulation",
            layer="simulation_job",
            service_capabilities={"simulation_job_service"},
            required=True,
        )

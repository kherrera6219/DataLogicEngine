"""Canonical CP19-I subsystem dispatch and authoritative effect receipts.

This adapter extends the one manifest/controller boundary to simulation, MCP,
providers, security, and operations. Knowledge Algorithms may validate or
propose effects; only an owning service can bind a proposal to an applied
receipt.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

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
    ) -> Any:
        """Run security/operations proposals before an MCP tool side effect."""
        argument_text = json.dumps(
            arguments,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        scopes_satisfied = bool(required_scopes)
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
                        "technical": 0.2,
                        "security": 0.3,
                        "compliance": 0.2,
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
                            "crosses_trust_boundary": False,
                            "authenticated": True,
                            "encrypted": True,
                            "integrity_protected": True,
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
                            "tested": True,
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
                "estimated_tokens_per_iteration": plan.max_tokens_per_call,
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
    def simulation_plan_allowed(execution: Any) -> tuple[bool, list[str]]:
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
        return not blockers, sorted(set(blockers))

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

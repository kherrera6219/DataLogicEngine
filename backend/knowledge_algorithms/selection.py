"""Manifest-driven KA selection plans and bounded dependency execution."""

from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import re
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.contracts import (
    KAExecutionContext,
    KAExecutionError,
    KAExecutionMode,
    KAExecutionRequest,
    KAExecutionResult,
    KAExecutionState,
    KAFailureCode,
    KAOutcomeType,
    utc_now,
)
from backend.knowledge_algorithms.manifest import (
    KADefinition,
    KAManifest,
    load_manifest,
)


class KAPlanDisposition(StrEnum):
    SELECTED = "selected"
    DENIED = "denied"
    UNAVAILABLE = "unavailable"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class KAPlanRole(StrEnum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    DEPENDENCY = "dependency"
    NOT_APPLICABLE = "not_applicable"


class KATraceState(StrEnum):
    PLANNED = "planned"
    CANDIDATE = "candidate"
    SELECTED = "selected"
    ADMITTED = "admitted"
    DEPENDENCY = "dependency"
    EXECUTING = "executing"
    EXECUTED = "executed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    EFFECT_PROPOSED = "effect_proposed"
    EFFECT_APPLIED = "effect_applied"
    EFFECT_FAILED = "effect_failed"
    ROLLED_BACK = "rolled_back"


class KAPlanExecutionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    DRY_RUN = "dry_run"


class KATraceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    state: KATraceState
    at: datetime = Field(default_factory=utc_now)
    reason: str
    result_trace_id: str | None = None


class KAPlanEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canonical_id: str
    name: str
    primary_owner: str
    stage: str
    disposition: KAPlanDisposition
    role: KAPlanRole
    required: bool = False
    dependencies: list[str] = Field(default_factory=list)
    dependency_result_contract: str
    dependency_input_field: str
    effect_class: str
    effect_port: str | None = None
    estimated_ms: int = Field(ge=1)
    reason: str
    events: list[KATraceEvent] = Field(default_factory=list)


class KASelectionRequest(BaseModel):
    """Normalized selector input for product and subsystem callers."""

    model_config = ConfigDict(extra="forbid")

    normalized_intent: list[str] = Field(default_factory=list)
    coordinate_17: dict[str, Any] = Field(default_factory=dict)
    domain: str | None = None
    tiers: list[str] = Field(default_factory=list)
    layers: list[str] = Field(default_factory=list)
    personas: list[str] = Field(default_factory=list)
    evidence_state: dict[str, Any] = Field(default_factory=dict)
    risk_classes: list[str] = Field(default_factory=list)
    owners: list[str] = Field(default_factory=list)
    stages: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    requested_ids: list[str] = Field(default_factory=list)
    excluded_ids: list[str] = Field(default_factory=list)
    service_capabilities: set[str] = Field(default_factory=set)
    prior_results: dict[str, KAExecutionResult] = Field(default_factory=dict)
    shared_input: dict[str, Any] = Field(default_factory=dict)
    ka_inputs: dict[str, dict[str, Any]] = Field(default_factory=dict)
    context: KAExecutionContext = Field(default_factory=KAExecutionContext)
    mode: KAExecutionMode = KAExecutionMode.PRODUCTION


class KASelectionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "dle.ka-selection-plan.v1"
    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    manifest_version: str
    request_id: str
    run_id: str
    mode: KAExecutionMode
    created_at: datetime = Field(default_factory=utc_now)
    entries: dict[str, KAPlanEntry]
    execution_order: list[list[str]] = Field(default_factory=list)
    estimated_critical_path_ms: int = Field(default=0, ge=0)
    selected_count: int = Field(default=0, ge=0)
    dependency_count: int = Field(default=0, ge=0)
    effect_proposal_count: int = Field(default=0, ge=0)
    valid: bool
    validation_errors: list[str] = Field(default_factory=list)

    @property
    def selected_ids(self) -> list[str]:
        return sorted(
            canonical_id
            for canonical_id, entry in self.entries.items()
            if entry.disposition == KAPlanDisposition.SELECTED
        )


class KANodeTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canonical_id: str
    parent_ids: list[str] = Field(default_factory=list)
    events: list[KATraceEvent] = Field(default_factory=list)


class KAPlanExecutionReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "dle.ka-plan-execution-report.v1"
    plan_id: str
    manifest_version: str
    request_id: str
    run_id: str
    status: KAPlanExecutionStatus
    started_at: datetime
    completed_at: datetime
    duration_ms: float = Field(ge=0.0)
    results: dict[str, KAExecutionResult] = Field(default_factory=dict)
    traces: dict[str, KANodeTrace] = Field(default_factory=dict)
    required_failure: str | None = None


class TypedCanonicalController(Protocol):
    def execute(
        self,
        request: KAExecutionRequest | dict[str, Any],
        *,
        allow_scoped_alias: bool = False,
    ) -> KAExecutionResult: ...


class KAPlanValidationError(ValueError):
    """Raised when an invalid or blocked plan is submitted for execution."""


class _RequiredNodeFailure(RuntimeError):
    def __init__(self, canonical_id: str):
        super().__init__(canonical_id)
        self.canonical_id = canonical_id


def _event(state: KATraceState, reason: str) -> KATraceEvent:
    return KATraceEvent(state=state, reason=reason)


def _tokens(values: list[str]) -> set[str]:
    return {
        token
        for value in values
        for token in re.findall(r"[a-z0-9]+", str(value).lower())
        if len(token) > 1
    }


class ManifestKASelector:
    """Build one deterministic selector plan from the canonical manifest."""

    def __init__(self, manifest: KAManifest | None = None):
        self.manifest = manifest or load_manifest()

    def plan(
        self, request: KASelectionRequest | dict[str, Any]
    ) -> KASelectionPlan:
        if not isinstance(request, KASelectionRequest):
            request = KASelectionRequest.model_validate(request)

        errors: list[str] = []
        requested = self._resolve_ids(request.requested_ids, "requested", errors)
        excluded = self._resolve_ids(request.excluded_ids, "excluded", errors)
        policy = request.context.policy_decisions
        denied = self._resolve_ids(
            list(policy.get("denied_ka_ids", [])),
            "policy denied",
            errors,
        )
        allowed_values = list(policy.get("allowed_ka_ids", []))
        allowed = (
            self._resolve_ids(allowed_values, "policy allowed", errors)
            if allowed_values
            else None
        )
        policy_required = self._resolve_ids(
            list(policy.get("required_ka_ids", [])),
            "policy required",
            errors,
        )

        candidate_reasons: dict[str, str] = {}
        for canonical_id, definition in self.manifest.entries.items():
            reasons = self._match_reasons(
                definition=definition,
                request=request,
                requested=requested,
            )
            if reasons:
                candidate_reasons[canonical_id] = ",".join(reasons)
        for canonical_id in policy_required:
            candidate_reasons.setdefault(canonical_id, "policy_required")

        roots = set(candidate_reasons)
        dependencies = self._dependency_closure(roots)
        dependency_ids = dependencies - roots
        selected_scope = roots | dependencies
        entries: dict[str, KAPlanEntry] = {}

        for canonical_id, definition in sorted(self.manifest.entries.items()):
            events = [_event(KATraceState.PLANNED, "manifest_considered")]
            role = KAPlanRole.NOT_APPLICABLE
            disposition = KAPlanDisposition.SKIPPED
            reason = "selector_predicates_not_matched"
            required = False

            if canonical_id in roots:
                events.append(
                    _event(
                        KATraceState.CANDIDATE,
                        candidate_reasons[canonical_id],
                    )
                )
                required = (
                    canonical_id in requested
                    or canonical_id in policy_required
                    or definition.integration.required_or_optional
                    == "required_when_stage_applicable"
                )
                role = (
                    KAPlanRole.REQUIRED if required else KAPlanRole.OPTIONAL
                )
                disposition = KAPlanDisposition.SELECTED
                reason = candidate_reasons[canonical_id]
            elif canonical_id in dependency_ids:
                role = KAPlanRole.DEPENDENCY
                required = True
                disposition = KAPlanDisposition.SELECTED
                reason = "transitive_manifest_dependency"
                events.append(
                    _event(KATraceState.DEPENDENCY, reason)
                )

            if canonical_id in selected_scope:
                disposition, reason = self._admit(
                    definition=definition,
                    request=request,
                    canonical_id=canonical_id,
                    current=disposition,
                    reason=reason,
                    excluded=excluded,
                    denied=denied,
                    allowed=allowed,
                )
                events.append(
                    _event(
                        {
                            KAPlanDisposition.SELECTED: KATraceState.SELECTED,
                            KAPlanDisposition.DENIED: KATraceState.BLOCKED,
                            KAPlanDisposition.UNAVAILABLE: (
                                KATraceState.UNAVAILABLE
                            ),
                            KAPlanDisposition.SKIPPED: KATraceState.SKIPPED,
                            KAPlanDisposition.BLOCKED: KATraceState.BLOCKED,
                        }[disposition],
                        reason,
                    )
                )
            else:
                events.append(_event(KATraceState.SKIPPED, reason))

            entries[canonical_id] = KAPlanEntry(
                canonical_id=canonical_id,
                name=definition.name,
                primary_owner=definition.integration.primary_owner,
                stage=definition.integration.stage,
                disposition=disposition,
                role=role,
                required=required,
                dependencies=list(definition.contract.dependencies),
                dependency_result_contract=(
                    definition.contract.dependency_result_contract
                ),
                dependency_input_field=(
                    definition.contract.dependency_input_field
                ),
                effect_class=definition.contract.effect_class,
                effect_port=definition.integration.effect_port,
                estimated_ms=definition.contract.performance_budget_ms,
                reason=reason,
                events=events,
            )

        self._propagate_dependency_blocks(entries, request.prior_results)
        graph_nodes = {
            canonical_id
            for canonical_id, entry in entries.items()
            if entry.disposition == KAPlanDisposition.SELECTED
        }
        execution_order, graph_errors = self._execution_order(graph_nodes)
        errors.extend(graph_errors)
        errors.extend(
            self._validate_budget(
                request=request,
                entries=entries,
                roots=roots,
                graph_nodes=graph_nodes,
                execution_order=execution_order,
            )
        )

        required_blocked = sorted(
            canonical_id
            for canonical_id, entry in entries.items()
            if entry.required
            and entry.disposition
            in {
                KAPlanDisposition.BLOCKED,
                KAPlanDisposition.DENIED,
                KAPlanDisposition.UNAVAILABLE,
            }
        )
        if required_blocked:
            errors.append(
                "required algorithms not admitted: "
                + ", ".join(required_blocked)
            )

        if errors:
            for entry in entries.values():
                if entry.disposition == KAPlanDisposition.SELECTED:
                    entry.disposition = KAPlanDisposition.BLOCKED
                    entry.reason = "plan_validation_failed"
                    entry.events.append(
                        _event(
                            KATraceState.BLOCKED,
                            "plan_validation_failed",
                        )
                    )
            execution_order = []

        selected_entries = [
            entry
            for entry in entries.values()
            if entry.disposition == KAPlanDisposition.SELECTED
        ]
        return KASelectionPlan(
            manifest_version=self.manifest.manifest_version,
            request_id=request.context.request_id,
            run_id=request.context.run_id,
            mode=request.mode,
            entries=entries,
            execution_order=execution_order,
            estimated_critical_path_ms=self._critical_path_ms(
                graph_nodes, execution_order
            ),
            selected_count=len(selected_entries),
            dependency_count=sum(
                entry.role == KAPlanRole.DEPENDENCY
                and entry.disposition == KAPlanDisposition.SELECTED
                for entry in entries.values()
            ),
            effect_proposal_count=sum(
                entry.effect_class == "effect_oriented_review_required"
                and entry.disposition == KAPlanDisposition.SELECTED
                for entry in entries.values()
            ),
            valid=not errors,
            validation_errors=sorted(set(errors)),
        )

    def _resolve_ids(
        self,
        values: list[str],
        label: str,
        errors: list[str],
    ) -> set[str]:
        resolved: set[str] = set()
        for value in values:
            try:
                resolved.add(self.manifest.resolve_id(value))
            except KeyError:
                errors.append(f"unknown {label} KA: {value}")
        return resolved

    def _match_reasons(
        self,
        *,
        definition: KADefinition,
        request: KASelectionRequest,
        requested: set[str],
    ) -> list[str]:
        reasons: list[str] = []
        if definition.canonical_id in requested:
            reasons.append("explicit_capability_request")
        if request.owners and definition.integration.primary_owner in set(
            request.owners
        ):
            reasons.append("primary_owner")
        if request.stages and definition.integration.stage in set(
            request.stages
        ):
            reasons.append("integration_stage")
        if request.categories and set(request.categories) & set(
            definition.contract.categories
        ):
            reasons.append("category")
        if request.layers and set(request.layers) & set(
            definition.contract.layers
        ):
            reasons.append("layer")
        if request.personas and set(request.personas) & set(
            definition.contract.personas
        ):
            reasons.append("persona")
        if request.risk_classes and set(request.risk_classes) & set(
            definition.contract.risk_classes
        ):
            reasons.append("risk_class")

        request_tokens = _tokens(
            [
                *request.normalized_intent,
                request.domain or "",
                *(
                    str(value)
                    for value in request.coordinate_17.values()
                    if isinstance(value, (str, int, float, bool))
                ),
            ]
        )
        definition_tokens = _tokens(
            [
                definition.canonical_id,
                definition.name,
                definition.purpose or "",
                *definition.contract.categories,
                *definition.contract.triggers,
            ]
        )
        if request_tokens and request_tokens & definition_tokens:
            reasons.append("intent_domain_coordinate")
        return reasons

    def _dependency_closure(self, roots: set[str]) -> set[str]:
        closure: set[str] = set()
        pending = sorted(roots)
        while pending:
            canonical_id = pending.pop()
            if canonical_id in closure:
                continue
            closure.add(canonical_id)
            pending.extend(
                self.manifest.entries[
                    canonical_id
                ].contract.dependencies
            )
        return closure

    @staticmethod
    def _live_capabilities(request: KASelectionRequest) -> set[str]:
        declared = set(request.service_capabilities)
        declared.update(
            key
            for key, value in request.context.capability_state.items()
            if bool(value)
        )
        return declared

    def _admit(
        self,
        *,
        definition: KADefinition,
        request: KASelectionRequest,
        canonical_id: str,
        current: KAPlanDisposition,
        reason: str,
        excluded: set[str],
        denied: set[str],
        allowed: set[str] | None,
    ) -> tuple[KAPlanDisposition, str]:
        if definition.integration.required_or_optional == "reserved_disabled":
            return KAPlanDisposition.DENIED, "reserved_disabled"
        if canonical_id in excluded:
            return KAPlanDisposition.SKIPPED, "explicitly_excluded"
        if canonical_id in denied:
            return KAPlanDisposition.DENIED, "policy_denied"
        if allowed is not None and canonical_id not in allowed:
            return KAPlanDisposition.DENIED, "not_in_policy_allow_list"
        denied_stages = set(
            request.context.policy_decisions.get("denied_stages", [])
        )
        if definition.integration.stage in denied_stages:
            return KAPlanDisposition.DENIED, "stage_denied_by_policy"
        if request.mode == KAExecutionMode.PRODUCTION:
            if not definition.admission.production_enabled:
                return (
                    KAPlanDisposition.UNAVAILABLE,
                    "not_production_qualified",
                )
            if (
                definition.contract.effect_class
                == "effect_oriented_review_required"
                and definition.integration.effect_port
                not in self._live_capabilities(request)
            ):
                return (
                    KAPlanDisposition.UNAVAILABLE,
                    "authoritative_effect_service_unavailable",
                )
        if definition.implementation.entrypoint is None:
            return (
                KAPlanDisposition.UNAVAILABLE,
                "implementation_unavailable",
            )
        prior = request.prior_results.get(canonical_id)
        if prior is not None and prior.success:
            return KAPlanDisposition.SKIPPED, "satisfied_by_prior_result"
        return current, reason

    @staticmethod
    def _propagate_dependency_blocks(
        entries: dict[str, KAPlanEntry],
        prior_results: dict[str, KAExecutionResult],
    ) -> None:
        changed = True
        while changed:
            changed = False
            for entry in entries.values():
                if entry.disposition != KAPlanDisposition.SELECTED:
                    continue
                unavailable = [
                    dependency
                    for dependency in entry.dependencies
                    if not (
                        entries[dependency].disposition
                        == KAPlanDisposition.SELECTED
                        or (
                            entries[dependency].reason
                            == "satisfied_by_prior_result"
                            and prior_results.get(dependency) is not None
                            and prior_results[dependency].success
                        )
                    )
                ]
                if unavailable:
                    entry.disposition = KAPlanDisposition.BLOCKED
                    entry.reason = (
                        "dependency_not_admitted:" + ",".join(unavailable)
                    )
                    entry.events.append(
                        _event(KATraceState.BLOCKED, entry.reason)
                    )
                    changed = True

    def _execution_order(
        self, nodes: set[str]
    ) -> tuple[list[list[str]], list[str]]:
        remaining = set(nodes)
        completed: set[str] = set()
        order: list[list[str]] = []
        while remaining:
            ready = sorted(
                node
                for node in remaining
                if not (
                    set(
                        self.manifest.entries[
                            node
                        ].contract.dependencies
                    )
                    & remaining
                )
            )
            if not ready:
                cycle = self._find_cycle(remaining)
                return [], [
                    "dependency cycle detected: " + " -> ".join(cycle)
                ]
            order.append(ready)
            remaining.difference_update(ready)
            completed.update(ready)
        return order, []

    def _find_cycle(self, nodes: set[str]) -> list[str]:
        visiting: set[str] = set()
        visited: set[str] = set()
        path: list[str] = []

        def visit(node: str) -> list[str] | None:
            if node in visiting:
                start = path.index(node)
                return path[start:] + [node]
            if node in visited:
                return None
            visiting.add(node)
            path.append(node)
            for dependency in self.manifest.entries[
                node
            ].contract.dependencies:
                if dependency in nodes:
                    cycle = visit(dependency)
                    if cycle:
                        return cycle
            path.pop()
            visiting.remove(node)
            visited.add(node)
            return None

        for node in sorted(nodes):
            cycle = visit(node)
            if cycle:
                return cycle
        return []

    def _validate_budget(
        self,
        *,
        request: KASelectionRequest,
        entries: dict[str, KAPlanEntry],
        roots: set[str],
        graph_nodes: set[str],
        execution_order: list[list[str]],
    ) -> list[str]:
        budget = request.context.budget
        errors: list[str] = []
        dependency_count = len(graph_nodes - roots)
        if dependency_count > budget.max_dependency_executions:
            errors.append(
                "dependency execution budget exceeded: "
                f"{dependency_count}>{budget.max_dependency_executions}"
            )
        if len(graph_nodes) > budget.max_selected_algorithms:
            errors.append(
                "selected algorithm budget exceeded: "
                f"{len(graph_nodes)}>{budget.max_selected_algorithms}"
            )
        effect_count = sum(
            entries[canonical_id].effect_class
            == "effect_oriented_review_required"
            for canonical_id in graph_nodes
        )
        if effect_count > budget.max_effects:
            errors.append(
                "effect proposal budget exceeded: "
                f"{effect_count}>{budget.max_effects}"
            )
        for canonical_id in sorted(graph_nodes):
            fan_out = len(entries[canonical_id].dependencies)
            if fan_out > budget.max_fan_out:
                errors.append(
                    f"{canonical_id} fan-out exceeds budget: "
                    f"{fan_out}>{budget.max_fan_out}"
                )
        if len(execution_order) > budget.max_recursion_depth + 1:
            errors.append(
                "dependency depth budget exceeded: "
                f"{len(execution_order) - 1}>"
                f"{budget.max_recursion_depth}"
            )
        critical_path = self._critical_path_ms(
            graph_nodes, execution_order
        )
        if critical_path > budget.deadline_ms:
            errors.append(
                "critical path deadline budget exceeded: "
                f"{critical_path}>{budget.deadline_ms}"
            )
        input_bytes = len(
            json.dumps(
                {
                    "shared_input": request.shared_input,
                    "ka_inputs": request.ka_inputs,
                },
                default=str,
            ).encode("utf-8")
        )
        if input_bytes > budget.max_input_bytes:
            errors.append(
                "selector input budget exceeded: "
                f"{input_bytes}>{budget.max_input_bytes}"
            )
        return errors

    def _critical_path_ms(
        self,
        nodes: set[str],
        execution_order: list[list[str]],
    ) -> int:
        if not nodes or not execution_order:
            return 0
        cost: dict[str, int] = {}
        for layer in execution_order:
            for canonical_id in layer:
                dependencies = (
                    set(
                        self.manifest.entries[
                            canonical_id
                        ].contract.dependencies
                    )
                    & nodes
                )
                cost[canonical_id] = self.manifest.entries[
                    canonical_id
                ].contract.performance_budget_ms + max(
                    (cost[dependency] for dependency in dependencies),
                    default=0,
                )
        return max(cost.values(), default=0)


class KAPlanExecutor:
    """Execute an admitted plan with bounded structured concurrency."""

    def __init__(self, controller: TypedCanonicalController):
        self.controller = controller

    async def execute(
        self,
        plan: KASelectionPlan,
        request: KASelectionRequest | dict[str, Any],
        *,
        cancellation_check: Callable[[], bool] | None = None,
    ) -> KAPlanExecutionReport:
        if not isinstance(request, KASelectionRequest):
            request = KASelectionRequest.model_validate(request)
        if not plan.valid:
            raise KAPlanValidationError(
                "; ".join(plan.validation_errors)
                or "selection plan is invalid"
            )
        if plan.request_id != request.context.request_id:
            raise KAPlanValidationError(
                "plan and execution request identities differ"
            )

        started_at = datetime.now(UTC)
        started = time.perf_counter()
        traces = {
            canonical_id: KANodeTrace(
                canonical_id=canonical_id,
                parent_ids=list(entry.dependencies),
                events=list(entry.events),
            )
            for canonical_id, entry in plan.entries.items()
        }
        results = dict(request.prior_results)

        if request.mode == KAExecutionMode.DRY_RUN:
            return self._report(
                plan=plan,
                status=KAPlanExecutionStatus.DRY_RUN,
                started_at=started_at,
                started=started,
                results=results,
                traces=traces,
            )
        if request.context.cancellation_requested or (
            cancellation_check is not None and cancellation_check()
        ):
            for canonical_id in plan.selected_ids:
                traces[canonical_id].events.append(
                    _event(
                        KATraceState.CANCELLED,
                        "cancellation_requested_before_execution",
                    )
                )
            return self._report(
                plan=plan,
                status=KAPlanExecutionStatus.CANCELLED,
                started_at=started_at,
                started=started,
                results=results,
                traces=traces,
            )

        deadline_at = datetime.now(UTC) + timedelta(
            milliseconds=request.context.budget.deadline_ms
        )
        required_failure: str | None = None
        any_optional_failure = False
        try:
            async with asyncio.timeout(
                request.context.budget.deadline_ms / 1000
            ):
                for layer in plan.execution_order:
                    if (
                        cancellation_check is not None
                        and cancellation_check()
                    ):
                        for canonical_id in plan.selected_ids:
                            if canonical_id not in results:
                                traces[canonical_id].events.append(
                                    _event(
                                        KATraceState.CANCELLED,
                                        "durable_cancellation_requested",
                                    )
                                )
                        return self._report(
                            plan=plan,
                            status=KAPlanExecutionStatus.CANCELLED,
                            started_at=started_at,
                            started=started,
                            results=results,
                            traces=traces,
                        )
                    executable = [
                        canonical_id
                        for canonical_id in layer
                        if self._dependencies_succeeded(
                            plan.entries[canonical_id], results
                        )
                    ]
                    blocked = sorted(set(layer) - set(executable))
                    for canonical_id in blocked:
                        traces[canonical_id].events.append(
                            _event(
                                KATraceState.BLOCKED,
                                "dependency_execution_failed",
                            )
                        )
                        if plan.entries[canonical_id].required:
                            required_failure = canonical_id
                    if required_failure:
                        break

                    pure = [
                        canonical_id
                        for canonical_id in executable
                        if plan.entries[canonical_id].effect_class
                        != "effect_oriented_review_required"
                    ]
                    effects = sorted(set(executable) - set(pure))
                    batch_required_failure, batch_optional_failure = (
                        await self._execute_pure_batch(
                            canonical_ids=pure,
                            plan=plan,
                            request=request,
                            results=results,
                            traces=traces,
                            deadline_at=deadline_at,
                        )
                    )
                    required_failure = (
                        required_failure or batch_required_failure
                    )
                    any_optional_failure = (
                        any_optional_failure or batch_optional_failure
                    )
                    if (
                        cancellation_check is not None
                        and cancellation_check()
                    ):
                        for canonical_id in plan.selected_ids:
                            if canonical_id not in results:
                                traces[canonical_id].events.append(
                                    _event(
                                        KATraceState.CANCELLED,
                                        "durable_cancellation_requested",
                                    )
                                )
                        return self._report(
                            plan=plan,
                            status=KAPlanExecutionStatus.CANCELLED,
                            started_at=started_at,
                            started=started,
                            results=results,
                            traces=traces,
                        )
                    if required_failure:
                        break
                    for canonical_id in effects:
                        result = await self._execute_node(
                            canonical_id=canonical_id,
                            plan=plan,
                            request=request,
                            results=results,
                            traces=traces,
                            deadline_at=deadline_at,
                        )
                        if not result.success:
                            if plan.entries[canonical_id].required:
                                required_failure = canonical_id
                                break
                            any_optional_failure = True
                    if required_failure:
                        break
        except TimeoutError:
            for canonical_id in plan.selected_ids:
                if canonical_id not in results:
                    traces[canonical_id].events.append(
                        _event(
                            KATraceState.TIMED_OUT,
                            "request_deadline_exceeded",
                        )
                    )
            return self._report(
                plan=plan,
                status=KAPlanExecutionStatus.TIMED_OUT,
                started_at=started_at,
                started=started,
                results=results,
                traces=traces,
                required_failure=required_failure,
            )
        except asyncio.CancelledError:
            for canonical_id in plan.selected_ids:
                if canonical_id not in results:
                    traces[canonical_id].events.append(
                        _event(
                            KATraceState.CANCELLED,
                            "parent_task_cancelled",
                        )
                    )
            raise

        if required_failure:
            for canonical_id in plan.selected_ids:
                if canonical_id not in results and not any(
                    event.state
                    in {
                        KATraceState.BLOCKED,
                        KATraceState.CANCELLED,
                    }
                    for event in traces[canonical_id].events
                ):
                    traces[canonical_id].events.append(
                        _event(
                            KATraceState.BLOCKED,
                            f"required_failure:{required_failure}",
                        )
                    )
            status = KAPlanExecutionStatus.BLOCKED
        elif any_optional_failure:
            status = KAPlanExecutionStatus.PARTIAL
        else:
            status = KAPlanExecutionStatus.SUCCEEDED
        return self._report(
            plan=plan,
            status=status,
            started_at=started_at,
            started=started,
            results=results,
            traces=traces,
            required_failure=required_failure,
        )

    async def _execute_pure_batch(
        self,
        *,
        canonical_ids: list[str],
        plan: KASelectionPlan,
        request: KASelectionRequest,
        results: dict[str, KAExecutionResult],
        traces: dict[str, KANodeTrace],
        deadline_at: datetime,
    ) -> tuple[str | None, bool]:
        if not canonical_ids:
            return None, False
        semaphore = asyncio.Semaphore(
            request.context.budget.max_parallelism
        )
        required_failure: str | None = None

        async def worker(canonical_id: str) -> None:
            async with semaphore:
                result = await self._execute_node(
                    canonical_id=canonical_id,
                    plan=plan,
                    request=request,
                    results=results,
                    traces=traces,
                    deadline_at=deadline_at,
                )
                if (
                    not result.success
                    and plan.entries[canonical_id].required
                ):
                    raise _RequiredNodeFailure(canonical_id)

        try:
            async with asyncio.TaskGroup() as group:
                for canonical_id in canonical_ids:
                    group.create_task(worker(canonical_id))
        except* _RequiredNodeFailure as failure_group:
            required_failure = min(
                failure.canonical_id
                for failure in failure_group.exceptions
                if isinstance(failure, _RequiredNodeFailure)
            )

        optional_failure = any(
            canonical_id in results
            and not results[canonical_id].success
            and not plan.entries[canonical_id].required
            for canonical_id in canonical_ids
        )
        return required_failure, optional_failure

    async def _execute_node(
        self,
        *,
        canonical_id: str,
        plan: KASelectionPlan,
        request: KASelectionRequest,
        results: dict[str, KAExecutionResult],
        traces: dict[str, KANodeTrace],
        deadline_at: datetime,
    ) -> KAExecutionResult:
        entry = plan.entries[canonical_id]
        trace = traces[canonical_id]
        trace.events.append(_event(KATraceState.ADMITTED, entry.reason))
        trace.events.append(
            _event(KATraceState.EXECUTING, "controller_dispatch")
        )
        payload = dict(request.shared_input)
        payload.update(request.ka_inputs.get(canonical_id, {}))
        if entry.dependencies and self._implementation_accepts_field(
            canonical_id,
            entry.dependency_input_field,
        ):
            payload[entry.dependency_input_field] = {
                dependency: results[dependency].output
                for dependency in entry.dependencies
                if dependency in results and results[dependency].success
            }
        node_context = request.context.model_copy(
            deep=True,
            update={"deadline_at": deadline_at},
        )
        execution_request = KAExecutionRequest(
            ka_id=canonical_id,
            input=payload,
            context=node_context,
            mode=request.mode,
        )
        timeout_seconds = min(
            entry.estimated_ms / 1000,
            max(
                (deadline_at - datetime.now(UTC)).total_seconds(),
                0.001,
            ),
        )
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self.controller.execute,
                    execution_request,
                ),
                timeout=timeout_seconds,
            )
        except TimeoutError:
            result = self._timeout_result(
                canonical_id=canonical_id,
                plan=plan,
                request=request,
                started_at=datetime.now(UTC),
            )
        except asyncio.CancelledError:
            trace.events.append(
                _event(
                    KATraceState.CANCELLED,
                    "structured_concurrency_cancelled",
                )
            )
            raise

        output_bytes = len(
            json.dumps(result.output, default=str).encode("utf-8")
        )
        if result.success and output_bytes > request.context.budget.max_output_bytes:
            result = self._invalid_output_result(
                result=result,
                output_bytes=output_bytes,
                max_output_bytes=request.context.budget.max_output_bytes,
            )
        results[canonical_id] = result
        terminal = (
            KATraceState.EXECUTED
            if result.success
            else {
                KAExecutionState.BLOCKED: KATraceState.BLOCKED,
                KAExecutionState.UNAVAILABLE: KATraceState.UNAVAILABLE,
                KAExecutionState.CANCELLED: KATraceState.CANCELLED,
                KAExecutionState.TIMED_OUT: KATraceState.TIMED_OUT,
            }.get(result.state, KATraceState.FAILED)
        )
        trace.events.append(
            KATraceEvent(
                state=terminal,
                reason=(
                    "canonical_result_committed"
                    if result.success
                    else (
                        result.error.code.value
                        if result.error
                        else "execution_failed"
                    )
                ),
                result_trace_id=result.trace_id,
            )
        )
        if (
            result.success
            and entry.effect_class == "effect_oriented_review_required"
        ):
            trace.events.append(
                KATraceEvent(
                    state=KATraceState.EFFECT_PROPOSED,
                    reason="proposal_only_requires_cp19_i_authoritative_port",
                    result_trace_id=result.trace_id,
                )
            )
        return result

    def _implementation_accepts_field(
        self,
        canonical_id: str,
        field_name: str,
    ) -> bool:
        """Inject dependency payloads only into schemas that declare the field."""
        manifest = getattr(self.controller, "manifest", None)
        definition = (
            manifest.entries.get(canonical_id)
            if manifest is not None
            else None
        )
        entrypoint = (
            definition.implementation.entrypoint
            if definition is not None
            else None
        )
        if entrypoint is None:
            return False
        try:
            module = importlib.import_module(entrypoint.module)
        except Exception:
            return False
        for value in vars(module).values():
            fields = getattr(value, "model_fields", None)
            if isinstance(fields, dict) and field_name in fields:
                return True
        try:
            callable_owner = (
                getattr(module, entrypoint.class_name)
                if entrypoint.class_name
                else module
            )
            return field_name in inspect.getsource(
                getattr(callable_owner, entrypoint.callable)
            )
        except (OSError, TypeError):
            return False

    @staticmethod
    def _dependencies_succeeded(
        entry: KAPlanEntry,
        results: dict[str, KAExecutionResult],
    ) -> bool:
        return all(
            dependency in results and results[dependency].success
            for dependency in entry.dependencies
        )

    @staticmethod
    def _timeout_result(
        *,
        canonical_id: str,
        plan: KASelectionPlan,
        request: KASelectionRequest,
        started_at: datetime,
    ) -> KAExecutionResult:
        return KAExecutionResult(
            canonical_id=canonical_id,
            ka_version="unknown",
            manifest_version=plan.manifest_version,
            state=KAExecutionState.TIMED_OUT,
            outcome_type=KAOutcomeType.TIMEOUT,
            success=False,
            error=KAExecutionError(
                code=KAFailureCode.DEADLINE_EXCEEDED,
                message="Knowledge Algorithm node deadline was exceeded.",
            ),
            request_id=request.context.request_id,
            run_id=request.context.run_id,
            trace_id=str(uuid4()),
            started_at=started_at,
            completed_at=datetime.now(UTC),
            duration_ms=0.0,
        )

    @staticmethod
    def _invalid_output_result(
        *,
        result: KAExecutionResult,
        output_bytes: int,
        max_output_bytes: int,
    ) -> KAExecutionResult:
        return result.model_copy(
            update={
                "state": KAExecutionState.FAILED,
                "outcome_type": KAOutcomeType.INTERNAL_FAILURE,
                "success": False,
                "output": {},
                "error": KAExecutionError(
                    code=KAFailureCode.INVALID_IMPLEMENTATION_RESULT,
                    message="Knowledge Algorithm output exceeded its budget.",
                    internal_details={
                        "output_bytes": output_bytes,
                        "max_output_bytes": max_output_bytes,
                    },
                ),
            }
        )

    @staticmethod
    def _report(
        *,
        plan: KASelectionPlan,
        status: KAPlanExecutionStatus,
        started_at: datetime,
        started: float,
        results: dict[str, KAExecutionResult],
        traces: dict[str, KANodeTrace],
        required_failure: str | None = None,
    ) -> KAPlanExecutionReport:
        return KAPlanExecutionReport(
            plan_id=plan.plan_id,
            manifest_version=plan.manifest_version,
            request_id=plan.request_id,
            run_id=plan.run_id,
            status=status,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            duration_ms=(time.perf_counter() - started) * 1000,
            results=results,
            traces=traces,
            required_failure=required_failure,
        )

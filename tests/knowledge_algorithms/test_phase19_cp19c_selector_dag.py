from __future__ import annotations

import asyncio
import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from backend.knowledge_algorithms.contracts import (
    KAExecutionResult,
    KAExecutionState,
    KAOutcomeType,
)
from backend.knowledge_algorithms.controller import CanonicalKAController
from backend.knowledge_algorithms.ka_master_controller import (
    KAMasterController,
)
from backend.knowledge_algorithms.manifest import load_manifest
from backend.knowledge_algorithms.selection import (
    KAPlanDisposition,
    KAPlanExecutionStatus,
    KAPlanExecutor,
    KAPlanValidationError,
    KASelectionRequest,
    KATraceState,
    ManifestKASelector,
)
from scripts.build_ka_selector_fixtures import OUTPUT_DIR, build_fixture
from scripts.verify_ka_selector_dag import verify

ROOT = Path(__file__).resolve().parents[2]


def _result(
    canonical_id: str,
    *,
    success: bool = True,
    request_id: str = "test-request",
    run_id: str = "test-run",
    output: dict | None = None,
) -> KAExecutionResult:
    now = datetime.now(UTC)
    return KAExecutionResult(
        canonical_id=canonical_id,
        ka_version="test",
        manifest_version="test",
        state=(KAExecutionState.SUCCEEDED if success else KAExecutionState.FAILED),
        outcome_type=(
            KAOutcomeType.VALUE if success else KAOutcomeType.INTERNAL_FAILURE
        ),
        success=success,
        output=output or ({"canonical_id": canonical_id} if success else {}),
        request_id=request_id,
        run_id=run_id,
        trace_id=str(uuid4()),
        started_at=now,
        completed_at=now,
    )


class RecordingController:
    def __init__(
        self,
        *,
        failures: set[str] | None = None,
        delay_seconds: float = 0.0,
    ):
        self.failures = failures or set()
        self.delay_seconds = delay_seconds
        self.calls: list[tuple[str, dict]] = []
        self._lock = threading.Lock()
        self.in_flight = 0
        self.max_in_flight = 0

    def execute(self, request, *, allow_scoped_alias: bool = False):
        del allow_scoped_alias
        with self._lock:
            self.calls.append((request.ka_id, request.input))
            self.in_flight += 1
            self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            if self.delay_seconds:
                time.sleep(self.delay_seconds)
            return _result(
                request.ka_id,
                success=request.ka_id not in self.failures,
                request_id=request.context.request_id,
                run_id=request.context.run_id,
            )
        finally:
            with self._lock:
                self.in_flight -= 1


def _wide_budget_context() -> dict:
    return {
        "request_id": "cp19c-test-request",
        "run_id": "cp19c-test-run",
        "budget": {
            "deadline_ms": 3_600_000,
            "max_dependency_executions": 512,
            "max_recursion_depth": 32,
            "max_selected_algorithms": 512,
            "max_fan_out": 128,
            "max_parallelism": 8,
            "max_input_bytes": 1_000_000,
            "max_output_bytes": 5_000_000,
            "max_provider_calls": 0,
            "max_effects": 0,
        },
    }


def test_cp19c_manifest_dependency_graph_is_acyclic_and_namespaced():
    manifest = load_manifest()

    assert manifest.status == "cp19_j_product_workflow_authority"
    assert manifest.capability_count == 213
    assert (
        sum(
            len(definition.contract.dependencies)
            for definition in manifest.entries.values()
        )
        == 135
    )
    for definition in manifest.entries.values():
        assert (
            definition.contract.dependency_result_contract
            == "dle.ka-execution-result.v1#output"
        )
        assert definition.contract.dependency_input_field == "dependency_results"


def test_cp19c_reciprocal_design_dependencies_have_prerequisite_order():
    manifest = load_manifest()

    for canonical_id, override in manifest.authority[
        "dependency_overrides"
    ].items():
        assert (
            manifest.entries[canonical_id].contract.dependencies
            == override["dependencies"]
        )
        assert override["rationale"]


def test_cp19c_all_213_positive_and_negative_fixtures_are_current():
    selector = ManifestKASelector()
    fixture_paths = sorted(OUTPUT_DIR.glob("*.json"))

    assert len(fixture_paths) == 213
    for path in fixture_paths:
        fixture = json.loads(path.read_text(encoding="utf-8"))
        canonical_id = fixture["canonical_id"]
        assert fixture == build_fixture(canonical_id)
        for fixture_name in ("positive_selector", "negative_selector"):
            case = fixture[fixture_name]
            plan = selector.plan(case["request"])
            entry = plan.entries[canonical_id]
            expected = case["expected"]
            assert entry.disposition.value == expected["disposition"]
            assert (entry.disposition == KAPlanDisposition.SELECTED) is expected[
                "selected"
            ]
            assert entry.reason == expected["reason"]
        if canonical_id == "KA-033":
            assert selector.plan(fixture["positive_selector"]["request"]).valid is False
        else:
            assert selector.plan(fixture["positive_selector"]["request"]).valid


def test_cp19c_machine_verification_evidence_passes():
    evidence = verify()

    assert evidence["status"] == "pass", evidence["errors"]
    assert evidence["canonical_capabilities"] == 213
    assert evidence["positive_fixtures_verified"] == 213
    assert evidence["positive_selected"] == 212
    assert evidence["positive_reserved_denial"] == 1
    assert evidence["negative_fixtures_verified"] == 213
    assert evidence["dependency_cycles"] == 0


def test_cp19c_plan_has_all_truthful_dispositions_and_deterministic_order():
    selector = ManifestKASelector()
    request = {
        "mode": "evaluation",
        "requested_ids": ["KA-117"],
        "context": _wide_budget_context(),
    }

    first = selector.plan(request)
    second = selector.plan(request)

    assert first.valid and second.valid
    assert len(first.entries) == 213
    assert first.execution_order == second.execution_order
    assert first.selected_ids == second.selected_ids
    assert first.entries["KA-117"].required
    assert first.entries["KA-117"].disposition == KAPlanDisposition.SELECTED
    assert first.entries["KA-065"].role.value == "dependency"
    assert first.entries["KA-033"].disposition == KAPlanDisposition.SKIPPED
    assert all(
        set(first.execution_order[index]).isdisjoint(
            set().union(*first.execution_order[:index])
        )
        for index in range(1, len(first.execution_order))
    )


def test_cp19c_policy_denial_and_unavailable_service_fail_closed():
    selector = ManifestKASelector()
    denied = selector.plan(
        {
            "mode": "evaluation",
            "requested_ids": ["KA-004"],
            "context": {
                **_wide_budget_context(),
                "policy_decisions": {"denied_ka_ids": ["KA-004"]},
            },
        }
    )
    assert not denied.valid
    assert denied.entries["KA-004"].disposition == KAPlanDisposition.DENIED

    manifest = load_manifest().model_copy(deep=True)
    effect_id = next(
        canonical_id
        for canonical_id, definition in manifest.entries.items()
        if definition.contract.effect_class == "effect_oriented_review_required"
        and not definition.contract.dependencies
    )
    manifest.entries[effect_id].admission.production_enabled = True
    unavailable = ManifestKASelector(manifest).plan(
        {
            "mode": "production",
            "requested_ids": [effect_id],
            "context": _wide_budget_context(),
        }
    )
    assert not unavailable.valid
    assert unavailable.entries[effect_id].disposition == KAPlanDisposition.UNAVAILABLE
    assert (
        unavailable.entries[effect_id].reason
        == "authoritative_effect_service_unavailable"
    )


def test_cp19c_cycle_and_budget_overflow_invalidate_the_whole_plan():
    manifest = load_manifest().model_copy(deep=True)
    manifest.entries["KA-004"].contract.dependencies = ["KA-005"]
    manifest.entries["KA-005"].contract.dependencies = ["KA-004"]
    cyclic = ManifestKASelector(manifest).plan(
        {
            "mode": "evaluation",
            "requested_ids": ["KA-004"],
            "context": _wide_budget_context(),
        }
    )
    assert not cyclic.valid
    assert any(
        "dependency cycle detected" in error for error in cyclic.validation_errors
    )
    assert cyclic.execution_order == []

    constrained_context = _wide_budget_context()
    constrained_context["budget"]["max_dependency_executions"] = 1
    constrained = ManifestKASelector().plan(
        {
            "mode": "evaluation",
            "requested_ids": ["KA-1079"],
            "context": constrained_context,
        }
    )
    assert not constrained.valid
    assert any(
        "dependency execution budget exceeded" in error
        for error in constrained.validation_errors
    )


@pytest.mark.asyncio
async def test_cp19c_executor_injects_dependencies_and_records_real_trace():
    context = _wide_budget_context()
    request = KASelectionRequest.model_validate(
        {
            "mode": "evaluation",
            "requested_ids": ["KA-004"],
            "shared_input": {"query": "  verify the selector  "},
            "context": context,
        }
    )
    plan = ManifestKASelector().plan(request)

    report = await KAPlanExecutor(CanonicalKAController()).execute(plan, request)

    assert report.status == KAPlanExecutionStatus.SUCCEEDED
    assert report.results["KA-004"].success
    assert report.results["KA-004"].output["is_valid"] is True
    states = [event.state for event in report.traces["KA-004"].events]
    assert states == [
        KATraceState.PLANNED,
        KATraceState.CANDIDATE,
        KATraceState.SELECTED,
        KATraceState.ADMITTED,
        KATraceState.EXECUTING,
        KATraceState.EXECUTED,
    ]


@pytest.mark.asyncio
async def test_cp19c_required_failure_cancels_siblings_and_blocks_dependents():
    request = KASelectionRequest.model_validate(
        {
            "mode": "evaluation",
            "requested_ids": ["KA-004", "KA-005"],
            "context": _wide_budget_context(),
        }
    )
    plan = ManifestKASelector().plan(request)
    controller = RecordingController(
        failures={"KA-004"},
        delay_seconds=0.01,
    )

    report = await KAPlanExecutor(controller).execute(plan, request)

    assert report.status == KAPlanExecutionStatus.BLOCKED
    assert report.required_failure == "KA-004"
    assert report.results["KA-004"].success is False
    assert all(
        event.state != KATraceState.EXECUTED for event in report.traces["KA-004"].events
    )


@pytest.mark.asyncio
async def test_cp19c_effect_proposals_execute_serially_and_are_not_applied():
    manifest = load_manifest()
    effect_ids = [
        canonical_id
        for canonical_id, definition in manifest.entries.items()
        if definition.contract.effect_class == "effect_oriented_review_required"
        and not definition.contract.dependencies
    ][:2]
    context = _wide_budget_context()
    context["budget"]["max_effects"] = len(effect_ids)
    request = KASelectionRequest.model_validate(
        {
            "mode": "evaluation",
            "requested_ids": effect_ids,
            "context": context,
        }
    )
    plan = ManifestKASelector().plan(request)
    controller = RecordingController(delay_seconds=0.01)

    report = await KAPlanExecutor(controller).execute(plan, request)

    assert report.status == KAPlanExecutionStatus.SUCCEEDED
    assert controller.max_in_flight == 1
    for canonical_id in effect_ids:
        states = {event.state for event in report.traces[canonical_id].events}
        assert KATraceState.EFFECT_PROPOSED in states
        assert KATraceState.EFFECT_APPLIED not in states


@pytest.mark.asyncio
async def test_cp19c_master_facade_plans_and_executes_canonical_path():
    master = KAMasterController()
    request = KASelectionRequest.model_validate(
        {
            "mode": "evaluation",
            "requested_ids": ["KA-004"],
            "shared_input": {"query": "facade"},
            "context": _wide_budget_context(),
        }
    )

    plan = master.plan_algorithms(request)
    report = await master.execute_algorithm_plan(plan, request)

    assert plan.valid
    assert report.status == KAPlanExecutionStatus.SUCCEEDED
    assert report.results["KA-004"].canonical_id == "KA-004"


@pytest.mark.asyncio
async def test_cp19c_invalid_plan_cannot_execute():
    request = KASelectionRequest.model_validate(
        {
            "mode": "evaluation",
            "requested_ids": ["KA-004"],
            "context": {
                **_wide_budget_context(),
                "policy_decisions": {"denied_ka_ids": ["KA-004"]},
            },
        }
    )
    plan = ManifestKASelector().plan(request)

    with pytest.raises(KAPlanValidationError):
        await KAPlanExecutor(RecordingController()).execute(plan, request)


@pytest.mark.asyncio
async def test_cp19c_parent_cancellation_is_re_raised():
    request = KASelectionRequest.model_validate(
        {
            "mode": "evaluation",
            "requested_ids": ["KA-004", "KA-005"],
            "context": _wide_budget_context(),
        }
    )
    plan = ManifestKASelector().plan(request)
    task = asyncio.create_task(
        KAPlanExecutor(RecordingController(delay_seconds=0.2)).execute(plan, request)
    )
    await asyncio.sleep(0.01)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

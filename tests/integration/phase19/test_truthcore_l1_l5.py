"""CP19-K owning-path proof for TruthCore L1-L5 algorithms."""

from __future__ import annotations

import pytest

from backend.dmrf.truth_integration.core_adapter import TruthCoreDMRFAdapter
from backend.governed_execution.contracts import (
    GovernedContext,
    GovernedMode,
    GovernedRequest,
)
from backend.governed_execution.ten_layers import GovernedTenLayerStages
from backend.truth_engine.truth_core.context_dependencies import (
    BATCH_13_IDS,
    TruthCoreContextDependencyError,
    TruthCoreContextDependencyService,
)


def _context(query: str, *, mode: GovernedMode) -> GovernedContext:
    request = GovernedRequest(
        messages=[{"role": "user", "content": query}],
        mode=mode,
        source="cp19_k_qualification",
        principal_kind="desktop",
        principal_id="cp19-k-reviewer",
    )
    context = GovernedContext(request=request, query=query)
    context.routing = {"axis_vector": {"axes": {"15": {"value": "standard"}}}}
    return context


def _trace_states(context: GovernedContext, canonical_id: str) -> list[str]:
    traces = context.truthcore["execution_report"]["traces"]
    return [event["state"] for event in traces[canonical_id]["events"]]


@pytest.mark.asyncio
async def test_ka_001_owning_path():
    query = "Research production release readiness evidence"
    enhanced_context = _context(query, mode=GovernedMode.ENHANCED)
    stages = GovernedTenLayerStages(TruthCoreDMRFAdapter())

    enhanced = await stages.l1(
        enhanced_context,
        tier="moderate",
        axis17_context={"value": "default"},
    )

    assert enhanced.ok
    assert "KA-001" in enhanced.selected_ka_ids
    assert enhanced.ka_results["KA-001"]["output"]["strategy"] == "research"
    assert enhanced.ka_results["KA-001"]["output"]["tasks"]
    assert _trace_states(enhanced_context, "KA-001") == [
        "planned",
        "candidate",
        "selected",
        "admitted",
        "executing",
        "executed",
    ]
    assert enhanced.ka_results["KA-001"]["trace_id"]

    standard_context = _context(query, mode=GovernedMode.STANDARD)
    standard = await stages.l1(
        standard_context,
        tier="moderate",
        axis17_context={"value": "default"},
    )
    assert standard.ok
    assert "KA-001" not in standard.selected_ka_ids


def _batch_13_inputs() -> dict[str, dict]:
    return {
        "KA-003": {
            "current_state": {"region": "us"},
            "desired_state": {"region": "eu", "policy": "declared"},
        },
        "KA-011": {"data": [1, 2, 3], "model_type": "statistical"},
        "KA-015": {
            "facts": [
                {
                    "fact_id": "fact-1",
                    "observed_at": "2026-01-01T00:00:00Z",
                    "expires_at": "2026-06-01T00:00:00Z",
                }
            ],
            "reference_time": "2026-08-04T00:00:00Z",
        },
        "KA-017": {
            "location": "California",
            "entity_scope": "consumer",
            "candidates": [
                {
                    "jurisdiction_id": "US-CA",
                    "location_aliases": ["California", "US-CA"],
                    "entity_scopes": ["consumer"],
                    "regulation_refs": ["declared-control-ref"],
                }
            ],
        },
        "KA-025": {
            "nodes": [
                {"id": "claim-1", "deps": []},
                {"id": "claim-2", "deps": ["claim-1"]},
            ]
        },
        "KA-040": {
            "observation": "Latency increased after the cache change",
            "variables": ["cache_configuration", "request_volume"],
        },
    }


@pytest.fixture(scope="module")
def batch_13_result() -> dict:
    return TruthCoreContextDependencyService().prepare(
        ka_inputs=_batch_13_inputs(),
        request_id="batch-13-context",
        principal_id="cp19-k-reviewer",
    )


def _assert_batch_13_trace(result: dict, canonical_id: str) -> None:
    assert [event["state"] for event in result["traces"][canonical_id]["events"]] == [
        "planned",
        "candidate",
        "selected",
        "admitted",
        "executing",
        "executed",
    ]


def test_ka_003_owning_path(batch_13_result: dict):
    assert batch_13_result["outputs"]["KA-003"]["gap_count"] == 2
    _assert_batch_13_trace(batch_13_result, "KA-003")


def test_ka_011_owning_path(batch_13_result: dict):
    assert batch_13_result["outputs"]["KA-011"]["results"]["mean"] == 2
    _assert_batch_13_trace(batch_13_result, "KA-011")


def test_ka_015_owning_path(batch_13_result: dict):
    output = batch_13_result["outputs"]["KA-015"]
    assert output["expired_count"] == 1
    assert output["system_clock_used"] is False
    _assert_batch_13_trace(batch_13_result, "KA-015")


def test_ka_017_owning_path(batch_13_result: dict):
    output = batch_13_result["outputs"]["KA-017"]
    assert output["resolved_jurisdiction"] == "US-CA"
    assert output["legal_applicability_established"] is False
    _assert_batch_13_trace(batch_13_result, "KA-017")


def test_ka_025_owning_path(batch_13_result: dict):
    assert batch_13_result["outputs"]["KA-025"]["meta"]["is_dag"] is True
    _assert_batch_13_trace(batch_13_result, "KA-025")


def test_ka_040_owning_path(batch_13_result: dict):
    output = batch_13_result["outputs"]["KA-040"]
    assert output["hypotheses_validated"] is False
    assert all(row["evidence_status"] == "untested" for row in output["hypotheses"])
    _assert_batch_13_trace(batch_13_result, "KA-040")


def test_batch_13_owner_rejects_partial_input_set():
    with pytest.raises(TruthCoreContextDependencyError, match="exact Batch 13"):
        TruthCoreContextDependencyService().prepare(
            ka_inputs={"KA-003": _batch_13_inputs()["KA-003"]},
            request_id="batch-13-partial",
            principal_id="cp19-k-reviewer",
        )


def test_batch_13_owner_applies_no_effect(batch_13_result: dict):
    assert batch_13_result["executed_ids"] == sorted(BATCH_13_IDS)
    assert batch_13_result["external_effects_applied"] == 0
    assert batch_13_result["persistence_applied"] is False
    assert batch_13_result["provider_calls"] == 0

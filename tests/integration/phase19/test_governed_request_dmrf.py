"""CP19-K owning-path proof for governed request and DMRF algorithms."""

from __future__ import annotations

import pytest

from backend.dmrf.truth_integration.core_adapter import TruthCoreDMRFAdapter
from backend.governed_execution.contracts import GovernedContext, GovernedRequest
from backend.governed_execution.ten_layers import GovernedTenLayerStages


def _context(query: str) -> GovernedContext:
    request = GovernedRequest(
        messages=[{"role": "user", "content": query}],
        source="cp19_k_qualification",
        principal_kind="desktop",
        principal_id="cp19-k-reviewer",
    )
    context = GovernedContext(request=request, query=query)
    context.routing = {
        "axis_vector": {"axes": {"15": {"value": "standard"}}}
    }
    return context


def _trace_states(context: GovernedContext, canonical_id: str) -> list[str]:
    traces = context.truthcore["execution_report"]["traces"]
    return [event["state"] for event in traces[canonical_id]["events"]]


def _assert_complete_trace(context: GovernedContext, canonical_id: str) -> None:
    assert _trace_states(context, canonical_id) == [
        "planned",
        "candidate",
        "selected",
        "admitted",
        "executing",
        "executed",
    ]
    traces = context.truthcore["execution_report"]["traces"]
    assert traces[canonical_id]["events"][-1]["result_trace_id"]


@pytest.mark.asyncio
async def test_ka_004_owning_path():
    context = _context("  <b>Assess the control boundary</b>  ")
    stages = GovernedTenLayerStages(TruthCoreDMRFAdapter())

    layer = await stages.l1(
        context,
        tier="moderate",
        axis17_context={"value": "default"},
    )

    assert layer.ok
    assert layer.outputs["query"] == "Assess the control boundary"
    assert context.query == "Assess the control boundary"
    assert layer.ka_results["KA-004"]["output"]["is_valid"] is True
    assert layer.decisions == [
        {"decision": "allow", "reason": "normalized_and_routed"}
    ]
    _assert_complete_trace(context, "KA-004")


@pytest.mark.asyncio
async def test_ka_061_owning_path():
    context = _context("DROP DATABASE production")
    stages = GovernedTenLayerStages(TruthCoreDMRFAdapter())

    layer = await stages.l1(
        context,
        tier="moderate",
        axis17_context={"value": "default"},
    )

    assert layer.ka_results["KA-004"]["output"]["is_valid"] is True
    assert layer.ka_results["KA-061"]["output"]["blocked"] is True
    assert layer.ka_results["KA-061"]["output"]["veto"] is True
    assert layer.ok is False
    assert layer.error_code == "L1_INPUT_BLOCKED"
    assert layer.outputs["query"] == "[FILTERED]"
    assert layer.decisions[0]["decision"] == "block"
    _assert_complete_trace(context, "KA-061")

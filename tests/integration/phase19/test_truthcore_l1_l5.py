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


def _context(query: str, *, mode: GovernedMode) -> GovernedContext:
    request = GovernedRequest(
        messages=[{"role": "user", "content": query}],
        mode=mode,
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

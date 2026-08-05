from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.governed_execution.contracts import (
    EvidenceRecord,
    GovernedContext,
    SourceRecord,
)
from backend.memory.unified_memory_service import UnifiedMemoryService
from backend.governed_execution.knowledge_lifecycle import KnowledgeLifecycleCoordinator
from tests.governed_execution.test_orchestrator import (
    _Gateway,
    _orchestrator,
    _request,
)


async def _run_batch_14_owner() -> tuple[GovernedContext, dict]:
    request = _request()
    context = GovernedContext(request=request, query=request.query_text())
    context.reasoning.tier = "moderate"
    context.evidence = [
        EvidenceRecord(
            source_id="source-beta",
            citation_label="S1",
            text="beta material",
            score=0.9,
            metadata={
                "source_quality_score": 0.8,
                "freshness_max_age_days": 3650,
                "reuse_count": 2,
                "depends_on_source_ids": ["source-alpha"],
                "provenance_checks": [
                    {
                        "check_id": "hash-bound",
                        "status": "passed",
                        "authority_ref": "local-index-receipt",
                    }
                ],
            },
            source=SourceRecord(
                source_id="source-beta",
                source_type="local_document",
                captured_at="2026-08-04T00:00:00Z",
            ),
        ),
        EvidenceRecord(
            source_id="source-alpha",
            citation_label="S2",
            text="alpha evidence",
            score=0.2,
            metadata={
                "source_quality_score": 0.9,
                "freshness_max_age_days": 3650,
                "dependent_count": 1,
            },
            source=SourceRecord(
                source_id="source-alpha",
                source_type="local_document",
                captured_at="2026-08-04T00:00:00Z",
            ),
        ),
    ]
    await _orchestrator(_Gateway())._execute_retrieval_owners(context)
    return context, request.metadata["_knowledge_lifecycle"]["retrieval"]


def _assert_trace(lifecycle: dict, canonical_id: str) -> None:
    states = [event["state"] for event in lifecycle["traces"][canonical_id]["events"]]
    assert [state for state in states if state != "dependency"] == [
        "planned",
        "candidate",
        "selected",
        "admitted",
        "executing",
        "executed",
    ]


@pytest.mark.asyncio
async def test_ka_079_owning_path():
    context, lifecycle = await _run_batch_14_owner()

    assert [item.source_id for item in context.evidence] == [
        "source-alpha",
        "source-beta",
    ]
    assert [item.citation_label for item in context.evidence] == ["S1", "S2"]
    assert lifecycle["executed_ids"] == [
        "KA-018",
        "KA-025",
        "KA-079",
        "KA-1049",
        "KA-1077",
        "KA-1092",
    ]
    _assert_trace(lifecycle, "KA-079")


@pytest.mark.asyncio
async def test_ka_018_owning_path():
    _context, lifecycle = await _run_batch_14_owner()
    output = lifecycle["results"]["KA-018"]["output"]
    assert output["all_supplied_checks_passed"] is True
    assert output["source_trust_established"] is False
    _assert_trace(lifecycle, "KA-018")


@pytest.mark.asyncio
async def test_ka_1049_owning_path():
    _context, lifecycle = await _run_batch_14_owner()
    output = lifecycle["results"]["KA-1049"]["output"]
    assert output["evaluated_pair_count"] == 1
    assert output["mutation_applied"] is False
    _assert_trace(lifecycle, "KA-1049")


@pytest.mark.asyncio
async def test_ka_1077_owning_path():
    _context, lifecycle = await _run_batch_14_owner()
    output = lifecycle["results"]["KA-1077"]["output"]
    assert len(output["ranked_knowledge"]) == 2
    assert output["deterministic"] is True
    _assert_trace(lifecycle, "KA-1077")


@pytest.mark.asyncio
async def test_ka_1092_owning_path():
    _context, lifecycle = await _run_batch_14_owner()
    output = lifecycle["results"]["KA-1092"]["output"]
    assert output["dependency_consumed"] == "KA-025"
    assert output["mapping_consistent"] is True
    assert output["mutation_applied"] is False
    _assert_trace(lifecycle, "KA-1092")


def test_cp19h_truthmemory_recall_is_authorized_retention_valid_and_not_quarantined(
    tmp_path,
):
    service = UnifiedMemoryService(
        storage_path=tmp_path / "memory.json",
        auto_load=False,
        strict=True,
    )
    allowed = service.consolidate(
        "authorized alpha memory",
        metadata={
            "session_id": "session-a",
            "owner_user_id": 1,
            "tenant_id": "tenant-a",
            "quarantined": False,
        },
        trusted=True,
        source_run_id="run-allowed",
        policy_result="release_authorized",
    )
    service.consolidate(
        "authorized alpha memory quarantined",
        metadata={
            "session_id": "session-a",
            "owner_user_id": 1,
            "tenant_id": "tenant-a",
            "quarantined": True,
        },
        trusted=True,
        source_run_id="run-quarantined",
        policy_result="release_authorized",
    )
    service.consolidate(
        "authorized alpha memory expired",
        metadata={
            "session_id": "session-a",
            "owner_user_id": 1,
            "tenant_id": "tenant-a",
            "expires_at": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
        },
        trusted=True,
        source_run_id="run-expired",
        policy_result="release_authorized",
    )

    authorized = service.recall(
        "authorized alpha memory",
        context={
            "session_id": "session-a",
            "owner_user_id": 1,
            "tenant_id": "tenant-a",
        },
        limit=10,
    )
    denied = service.recall(
        "authorized alpha memory",
        context={
            "session_id": "session-b",
            "owner_user_id": 2,
            "tenant_id": "tenant-b",
        },
        limit=10,
    )

    assert [item.vertex_id for item in authorized] == [allowed.vertex_id]
    assert denied == []


def _batch_18_inputs():
    from tests.integration.phase19.test_truthmemory_truthlink_frost import (
        _batch_17_inputs,
    )

    inputs = _batch_17_inputs()
    inputs.update(
        {
            "KA-029": {
                "seed_entities": ["a"],
                "adjacency": [
                    {"node_id": "a", "neighbor_ids": ["b"]},
                    {"node_id": "b", "neighbor_ids": ["c"]},
                ],
                "depth": 1,
            },
            "KA-1079": {
                "knowledge_id": "knowledge-1",
                "validation_status": "validated",
                "confidence": 0.95,
                "evidence_count": 2,
                "citation_count": 1,
                "contradiction_count": 0,
                "provenance_complete": True,
                "risk_class": "low",
            },
        }
    )
    return inputs


def _run_batch_18_owner(canonical_id: str):
    execution = KnowledgeLifecycleCoordinator().execute_operation_sync(
        owner="retrieval_graph_memory",
        operation="promotion",
        requested_ids=[canonical_id],
        ka_inputs=_batch_18_inputs(),
        request_id=f"batch-18-{canonical_id}",
        run_id=f"batch-18-run-{canonical_id}",
        max_effects=4,
        principal_id="owner-1",
        service_capabilities={"knowledge_lifecycle_service"},
    )
    states = [
        event.state.value
        for event in execution.report.traces[canonical_id].events
        if event.state.value != "effect_proposed"
    ]
    assert states == [
        "planned",
        "candidate",
        "selected",
        "admitted",
        "executing",
        "executed",
    ]
    return execution.results[canonical_id]["output"]


def test_ka_029_owning_path():
    output = _run_batch_18_owner("KA-029")
    assert [row["node_id"] for row in output["expanded_nodes"]] == ["a", "b"]
    assert output["graph_store_read"] is False
    assert output["graph_mutation_applied"] is False


def test_ka_1079_owning_path():
    output = _run_batch_18_owner("KA-1079")
    assert output["decision"] == "approve"
    assert output["promotion_applied"] is False

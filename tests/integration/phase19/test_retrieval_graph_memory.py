from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.governed_execution.contracts import (
    EvidenceRecord,
    GovernedContext,
    SourceRecord,
)
from backend.governed_execution.knowledge_lifecycle import KnowledgeLifecycleCoordinator
from backend.memory.unified_memory_service import UnifiedMemoryService
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


def _batch_22_inputs():
    inputs = _batch_18_inputs()
    inputs.update(
        {
            "KA-080": {
                "key": "cache-a",
                "operation": "set",
                "cache_state": {"entries": {"cache-a": {"hits": 2}}},
                "value": "replacement",
                "ttl_seconds": 60,
            },
            "KA-1039": {
                "baseline_version": "v1",
                "current_version": "v2",
                "baseline_concepts": [
                    {
                        "concept_id": "control",
                        "label": "Control",
                        "definition": "A documented measure.",
                    }
                ],
                "current_concepts": [
                    {
                        "concept_id": "control",
                        "label": "Control",
                        "definition": "A verified measure.",
                    }
                ],
            },
            "KA-1040": {
                "concepts": [
                    {
                        "concept_id": "customer",
                        "label": "Customer",
                        "synonyms": ["client"],
                    },
                    {
                        "concept_id": "client",
                        "label": "Client",
                        "synonyms": ["customer"],
                    },
                ]
            },
            "KA-1043": {
                "knowledge_id": "knowledge-1",
                "events": [
                    {
                        "event_id": "e1",
                        "version_id": "v1",
                        "event_type": "created",
                        "source_ref": "receipt:1",
                    },
                    {
                        "event_id": "e2",
                        "version_id": "v2",
                        "parent_version_ids": ["v1"],
                        "event_type": "validated",
                        "source_ref": "receipt:2",
                    },
                ],
            },
            "KA-1046": {
                "updates": [
                    {
                        "update_id": "u1",
                        "knowledge_id": "knowledge-1",
                        "current_version": "v1",
                        "proposed_version": "v2",
                        "lifecycle_state": "validated",
                        "confidence": 0.95,
                        "evidence_count": 3,
                        "sensitivity": "internal",
                    }
                ]
            },
            "KA-1048": {
                "assertions": [
                    {
                        "assertion_id": "a",
                        "concept_id": "control",
                        "definition": "A verified measure.",
                        "source_ontology": "approved",
                        "authority_priority": 10,
                        "confidence": 0.9,
                        "evidence_refs": ["policy-1"],
                    },
                    {
                        "assertion_id": "b",
                        "concept_id": "control",
                        "definition": "Any process.",
                        "source_ontology": "legacy",
                        "authority_priority": 5,
                        "confidence": 0.8,
                    },
                ]
            },
            "KA-1049": {
                "knowledge_nodes": [
                    {"node_id": "a", "content": "bounded release evidence"},
                    {"node_id": "b", "content": "bounded release control"},
                ]
            },
            "KA-1077": {
                "candidates": [
                    {
                        "knowledge_id": "knowledge-1",
                        "relevance": 0.9,
                        "confidence": 0.8,
                        "freshness": 0.7,
                        "reuse_count": 2,
                        "dependent_count": 1,
                    }
                ]
            },
            "KA-1076": {
                "nodes": [
                    {
                        "node_id": "old",
                        "importance": 0.1,
                        "confidence": 0.2,
                        "age_days": 500,
                        "reuse_count": 0,
                    },
                    {
                        "node_id": "active",
                        "importance": 0.9,
                        "confidence": 0.9,
                        "age_days": 2,
                        "reuse_count": 10,
                    },
                ],
                "edges": [],
            },
            "KA-1078": {
                "candidates": [
                    {
                        "knowledge_id": "knowledge-1",
                        "validation_status": "validated",
                        "importance": 0.9,
                        "confidence": 0.95,
                        "age_days": 5,
                        "reuse_count": 10,
                    }
                ]
            },
        }
    )
    return inputs


def _run_batch_22_owner(canonical_id: str):
    from backend.governed_execution.knowledge_store_maintenance import (
        KnowledgeStoreService,
    )

    review = KnowledgeStoreService().review_maintenance_sync(
        requested_ids=[canonical_id],
        ka_inputs=_batch_22_inputs(),
        request_id=f"batch-22-{canonical_id}",
        run_id=f"batch-22-run-{canonical_id}",
        principal_id="owner-1",
    )
    assert review.ok
    receipt = review.receipts[canonical_id]
    assert receipt["service"] == "KnowledgeStoreService"
    assert receipt["status"] == "reviewed_no_mutation"
    assert receipt["applied"] is False
    assert receipt["rollback_status"] == "not_required_no_mutation"
    states = [
        event.state.value
        for event in review.execution.report.traces[canonical_id].events
        if event.state.value not in {"dependency", "effect_proposed"}
    ]
    assert states == [
        "planned",
        "candidate",
        "selected",
        "admitted",
        "executing",
        "executed",
    ]
    return review.execution.results[canonical_id]["output"]


def test_ka_080_owning_path():
    assert _run_batch_22_owner("KA-080")["cache_mutation_applied"] is False


def test_ka_1039_owning_path():
    assert _run_batch_22_owner("KA-1039")["mutation_applied"] is False


def test_ka_1040_owning_path():
    assert _run_batch_22_owner("KA-1040")["alignment_count"] == 1


def test_ka_1043_owning_path():
    assert _run_batch_22_owner("KA-1043")["lineage_complete"] is True


def test_ka_1046_owning_path():
    output = _run_batch_22_owner("KA-1046")
    assert output["patch_applied"] is False
    assert output["dependencies_consumed"] == ["KA-1079", "KA-1109"]


def test_ka_1048_owning_path():
    assert _run_batch_22_owner("KA-1048")["mutation_applied"] is False


def test_ka_1076_owning_path():
    output = _run_batch_22_owner("KA-1076")
    assert output["mutation_applied"] is False
    assert output["dependencies_consumed"] == ["KA-1077", "KA-1094"]


def test_ka_1078_owning_path():
    output = _run_batch_22_owner("KA-1078")
    assert output["tier_changes_applied"] is False
    assert output["dependencies_consumed"] == ["KA-1109"]

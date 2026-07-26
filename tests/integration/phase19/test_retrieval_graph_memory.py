from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.governed_execution.contracts import EvidenceRecord
from backend.memory.unified_memory_service import UnifiedMemoryService
from tests.governed_execution.test_orchestrator import (
    _Gateway,
    _orchestrator,
    _request,
)


@pytest.mark.asyncio
async def test_cp19h_ka079_causally_changes_selected_evidence_order(
    monkeypatch: pytest.MonkeyPatch,
):
    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(
        module,
        "retrieve_evidence",
        lambda *args, **kwargs: (
            [
                EvidenceRecord(
                    source_id="source-beta",
                    citation_label="S1",
                    text="beta material",
                    score=0.9,
                ),
                EvidenceRecord(
                    source_id="source-alpha",
                    citation_label="S2",
                    text="alpha evidence",
                    score=0.2,
                ),
            ],
            [],
        ),
    )
    result = await _orchestrator(_Gateway()).execute(_request())

    assert result.ok is True
    assert [item.source_id for item in result.evidence] == [
        "source-alpha",
        "source-beta",
    ]
    assert [item.citation_label for item in result.evidence] == ["S1", "S2"]
    lifecycle = result.metadata["knowledge_lifecycle"]["retrieval"]
    assert lifecycle["executed_ids"] == ["KA-018", "KA-079"]


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
            "expires_at": (
                datetime.now(UTC) - timedelta(minutes=1)
            ).isoformat(),
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

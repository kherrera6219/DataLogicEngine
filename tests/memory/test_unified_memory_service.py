import json
import os
import socket
from urllib.parse import urlparse

import pytest

import app as app_module
from backend.memory.unified_memory_service import UnifiedMemoryService
from backend.truth_engine.truth_core.engine import TruthCoreEngine
from core.system.frost_service import FROSTService


def _neo4j_available() -> bool:
    """Return True if the app's local Neo4j is reachable at the configured URI.

    Neo4j is a **local internal** data store for DataLogicEngine (app-owned,
    started locally via ``scripts/windows/start_local_stack.ps1`` /
    ``setup_local_databases.py``), not an external service. The end-to-end
    TruthCore workflow writes graph-backed memory through it; when the local
    Neo4j has not been started the workflow records only the in-memory write and
    ``memory_writes`` is incomplete (1 instead of 3). A bare ``pytest`` run that
    has not brought up the local data stack should skip this end-to-end test
    rather than fail it. The URI is resolved the same way
    ``backend.storage.graph_store.GraphStore`` does. (A18.)
    """
    uri = os.getenv("NEO4J_URI")
    if not uri:
        try:
            from backend.config_manager import get_config
            uri = getattr(get_config(), "NEO4J_URI", "bolt://localhost:7687")
        except Exception:
            uri = "bolt://localhost:7687"
    parsed = urlparse(uri)
    host = parsed.hostname or "localhost"
    port = parsed.port or 7687
    try:
        with socket.create_connection((host, port), timeout=0.75):
            return True
    except OSError:
        return False


def test_unified_memory_persists_and_namespaces_recall(tmp_path):
    path = tmp_path / "memory_graph.json"
    service = UnifiedMemoryService(storage_path=path, auto_load=False)

    service.consolidate(
        "L3 acquisition evidence memo",
        layer="L3",
        persona="knowledge",
        metadata={"source": "test"},
    )
    service.consolidate(
        "L8 compliance trust gate memo",
        layer="L8",
        persona="compliance",
        metadata={"source": "test"},
    )

    l3 = service.recall("acquisition evidence", layer="L3", persona="knowledge")
    l8 = service.recall("compliance trust", layer="L8", persona="compliance")

    assert [item.metadata["layer"] for item in l3] == ["L3"]
    assert [item.metadata["persona"] for item in l8] == ["compliance"]
    assert service.stats()["memory_vertices"] == 2

    reloaded = UnifiedMemoryService(storage_path=path, auto_load=True)
    assert reloaded.stats()["memory_vertices"] == 2
    assert json.loads(path.read_text(encoding="utf-8"))["vertices"]


@pytest.mark.skipif(
    not _neo4j_available(),
    reason="Local Neo4j not started (run scripts/windows/start_local_stack.ps1); "
    "graph-backed memory writes require the app's local Neo4j",
)
@pytest.mark.asyncio
async def test_truthcore_reads_and_writes_memory_each_layer(tmp_path, monkeypatch):
    service = UnifiedMemoryService(storage_path=tmp_path / "memory_graph.json", auto_load=False)
    monkeypatch.setattr("backend.memory.get_unified_memory_service", lambda: service)

    engine = TruthCoreEngine()
    result = await engine._execute_workflow(
        "Assess compliance risk",
        {"session_id": "session-1"},
        ["intent_parsing", "hybrid_retrieval", "final_safety_gate"],
        "moderate",
    )

    context = result["context"]
    assert {"L1", "L2", "L10"}.issubset(context["memory_context"].keys())
    assert len(context["memory_writes"]) == 3
    assert service.stats()["memory_vertices"] >= 4


def test_frost_branch_checkpoint_restores_memory(tmp_path, monkeypatch):
    service = UnifiedMemoryService(storage_path=tmp_path / "memory_graph.json", auto_load=False)
    monkeypatch.setattr("backend.memory.get_unified_memory_service", lambda: service)

    service.consolidate("before branch", layer="L3", persona="knowledge")
    frost = FROSTService()
    snapshot_id = frost.snapshot({"state": "before"})
    frost.branch(snapshot_id, "candidate")
    before_count = service.stats()["memory_vertices"]

    service.consolidate("after branch", layer="L3", persona="knowledge")
    assert service.stats()["memory_vertices"] == before_count + 1

    assert frost.rollback_memory_branch("candidate") is True
    assert service.stats()["memory_vertices"] == before_count


def test_health_memory_stats_uses_unified_memory_service(tmp_path, monkeypatch):
    service = UnifiedMemoryService(storage_path=tmp_path / "memory_graph.json", auto_load=False)
    service.consolidate("health memory", layer="L1", persona="global")
    monkeypatch.setattr("backend.memory.get_unified_memory_service", lambda: service)

    stats = app_module._structured_memory_stats()

    assert stats["status"] == "ok"
    assert stats["memory_vertices"] == 1
    assert stats["memory_edges"] == 0

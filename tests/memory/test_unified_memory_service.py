import json
import os

import pytest
from flask import Flask

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
    rather than fail it. The URI/credentials are resolved the same way
    ``backend.storage.graph_store.GraphStore`` does. (A18; hardened post-A12.)

    Probes with a real ``RETURN 1`` Cypher, NOT just a TCP connect: a port being
    open is not enough — an up-but-unauthenticated/uninitialized Neo4j accepts the
    socket yet fails the graph-backed memory writes (``memory_writes`` 1 != 3),
    which would make this e2e test FAIL instead of SKIP. Only run when a real
    query succeeds.
    """
    uri = os.getenv("NEO4J_URI")
    if not uri:
        try:
            from backend.config_manager import get_config
            uri = getattr(get_config(), "NEO4J_URI", "bolt://localhost:7687")
        except Exception:
            uri = "bolt://localhost:7687"
    user = os.getenv("NEO4J_USER") or "neo4j"
    password = os.getenv("NEO4J_PASSWORD") or "password"
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(uri, auth=(user, password), connection_timeout=1.0)
        try:
            with driver.session() as session:
                session.run("RETURN 1").single()
            return True
        except Exception:
            return False
        finally:
            driver.close()
    except Exception:
        return False


def test_unified_memory_persists_and_namespaces_recall(tmp_path):
    path = tmp_path / "memory_graph.json"
    service = UnifiedMemoryService(storage_path=path, auto_load=False)

    service.consolidate(
        "L3 acquisition evidence memo",
        layer="L3",
        persona="knowledge",
        metadata={"source": "test"},
        trusted=True,
        source_run_id="run-l3",
        policy_result="release_authorized",
    )
    service.consolidate(
        "L8 compliance trust gate memo",
        layer="L8",
        persona="compliance",
        metadata={"source": "test"},
        trusted=True,
        source_run_id="run-l8",
        policy_result="release_authorized",
    )

    l3 = service.recall("acquisition evidence", layer="L3", persona="knowledge")
    l8 = service.recall("compliance trust", layer="L8", persona="compliance")

    assert [item.metadata["layer"] for item in l3] == ["L3"]
    assert [item.metadata["persona"] for item in l8] == ["compliance"]
    assert service.stats()["memory_vertices"] == 2

    reloaded = UnifiedMemoryService(storage_path=path, auto_load=True)
    assert reloaded.stats()["memory_vertices"] == 2
    assert json.loads(path.read_text(encoding="utf-8"))["vertices"]


def test_unified_memory_rejects_missing_or_newer_schema_in_strict_mode(tmp_path):
    path = tmp_path / "memory_graph.json"
    path.write_text(json.dumps({"vertices": [], "edges": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="unified_memory_schema_version_incompatible"):
        UnifiedMemoryService(storage_path=path, auto_load=True, strict=True)

    path.write_text(
        json.dumps({"version": 99, "vertices": [], "edges": []}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unified_memory_schema_version_incompatible"):
        UnifiedMemoryService(storage_path=path, auto_load=True, strict=True)


def test_unified_memory_save_is_atomic_and_versioned(tmp_path):
    path = tmp_path / "memory_graph.json"
    service = UnifiedMemoryService(storage_path=path, auto_load=False)

    service.save()

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["version"] == UnifiedMemoryService.SCHEMA_VERSION
    assert not list(tmp_path.glob("*.tmp"))


def test_working_memory_cannot_poison_cross_session_trusted_recall(tmp_path):
    service = UnifiedMemoryService(
        storage_path=tmp_path / "memory_graph.json", auto_load=False
    )
    service.consolidate(
        "unvalidated provider instruction",
        layer="L3",
        metadata={"session_id": "session-a", "source": "working_result"},
    )

    assert service.recall("provider instruction", layer="L3") == []
    assert service.recall(
        "provider instruction", layer="L3", context={"session_id": "session-b"}
    ) == []
    assert len(
        service.recall(
            "provider instruction", layer="L3", context={"session_id": "session-a"}
        )
    ) == 1


def test_trusted_memory_requires_release_authority(tmp_path):
    service = UnifiedMemoryService(
        storage_path=tmp_path / "memory_graph.json", auto_load=False
    )
    with pytest.raises(ValueError, match="trusted_memory_requires_release_authority"):
        service.consolidate("unsafe promotion", trusted=True)

    vertex = service.record_release_commit(
        content="validated release memory",
        simulation_id="run-validated",
    )
    assert vertex.metadata["validation_state"] == "validated"
    assert vertex.metadata["source_run_id"] == "run-validated"
    assert service.recall("validated release memory")


def test_memory_review_delete_compaction_and_verified_backup_recovery(tmp_path):
    path = tmp_path / "memory_graph.json"
    service = UnifiedMemoryService(storage_path=path, auto_load=False, strict=True)
    trusted = service.record_release_commit(
        content="keep validated memory", simulation_id="validated-run"
    )
    service.consolidate(
        "old working one", metadata={"session_id": "working-a"}
    )
    service.consolidate(
        "old working two", metadata={"session_id": "working-b"}
    )

    assert [item["vertex_id"] for item in service.review()] == [trusted.vertex_id]
    assert len(service.review(include_working=True)) == 3
    outcome = service.compact(max_working_vertices=1)
    assert outcome == {"working_before": 2, "removed": 1, "working_after": 1}
    assert service.delete(trusted.vertex_id) is True
    assert service.review() == []

    # A subsequent valid save creates the verified last-known-good backup.
    service.save()
    backup = path.with_suffix(path.suffix + ".bak")
    assert backup.is_file()
    expected_vertices = service.stats()["memory_vertices"]
    path.write_text("{corrupt", encoding="utf-8")

    recovered = UnifiedMemoryService(storage_path=path, auto_load=True, strict=True)
    assert recovered.stats()["memory_vertices"] == expected_vertices
    assert json.loads(path.read_text(encoding="utf-8"))["integrity_sha256"]


@pytest.mark.skipif(
    not _neo4j_available(),
    reason="Local Neo4j not started (run scripts/windows/start_local_stack.ps1); "
    "graph-backed memory writes require the app's local Neo4j",
)
@pytest.mark.asyncio
async def test_truthcore_reads_and_writes_memory_each_layer(tmp_path, monkeypatch):
    service = UnifiedMemoryService(storage_path=tmp_path / "memory_graph.json", auto_load=False)
    monkeypatch.setattr("backend.memory.get_unified_memory_service", lambda: service)

    from backend.knowledge_algorithms.ka_master_controller import (
        KAMasterController,
    )

    engine = TruthCoreEngine(ka_controller=KAMasterController({}))
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


def test_health_memory_stats_uses_unified_memory_service(tmp_path):
    service = UnifiedMemoryService(storage_path=tmp_path / "memory_graph.json", auto_load=False)
    service.consolidate(
        "health memory",
        layer="L1",
        persona="global",
        trusted=True,
        source_run_id="health-run",
        policy_result="release_authorized",
    )
    test_app = Flask("memory-health-test")
    test_app.extensions["dle_unified_memory_service"] = service

    with test_app.app_context():
        stats = app_module._structured_memory_stats()

    assert stats["status"] == "ok"
    assert stats["memory_vertices"] == 1
    assert stats["memory_edges"] == 0

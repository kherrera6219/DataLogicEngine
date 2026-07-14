from backend.memory.unified_memory_service import UnifiedMemoryService


def test_owner_memory_review_compact_export_delete_and_recovery_routes(
    authenticated_client, app, tmp_path
):
    service = UnifiedMemoryService(
        storage_path=tmp_path / "memory_graph.json", auto_load=False, strict=True
    )
    trusted = service.record_release_commit(
        content="validated owner memory", simulation_id="validated-run"
    )
    service.consolidate(
        "working memory", metadata={"session_id": "working-session"}
    )
    service.save()
    app.extensions["dle_unified_memory_service"] = service

    reviewed = authenticated_client.get("/api/v1/memory/review")
    assert reviewed.status_code == 200
    assert [item["vertex_id"] for item in reviewed.get_json()["data"]["items"]] == [
        trusted.vertex_id
    ]

    exported = authenticated_client.get("/api/v1/memory/export")
    assert exported.status_code == 200
    assert exported.get_json()["data"]["integrity_sha256"]

    compacted = authenticated_client.post(
        "/api/v1/memory/compact", json={"max_working_vertices": 0}
    )
    assert compacted.status_code == 200
    assert compacted.get_json()["data"]["removed"] == 1

    deleted = authenticated_client.delete(f"/api/v1/memory/{trusted.vertex_id}")
    assert deleted.status_code == 200

    service.storage_path.write_text("{corrupt", encoding="utf-8")
    recovered = authenticated_client.post("/api/v1/memory/recover")
    assert recovered.status_code == 200

from __future__ import annotations

import pytest

from backend.governed_execution.knowledge_lifecycle import (
    KnowledgeLifecycleCoordinator,
    KnowledgeLifecycleError,
)
from backend.ingestion import LocalKnowledgeIngestionService
from models import CrossStoreOutboxEvent, IngestionJob, KnowledgeGraphNode


def _ingestion_inputs(records):
    return {
        "KA-071": {"source_type": "local_file", "payload": records},
        "KA-072": {"records": records},
        "KA-073": {"records": records},
        "KA-074": {"records": records},
        "KA-075": {
            "records": records,
            "target_schema": "knowledge_source",
        },
        "KA-076": {"records": records},
        "KA-077": {"records": records},
        "KA-078": {"record_ids": [row["record_id"] for row in records]},
    }


def test_cp19h_ingestion_executes_ka071_through_ka078_in_order():
    records = [{"record_id": "policy.md", "content": "policy"}]
    coordinator = KnowledgeLifecycleCoordinator()

    execution = coordinator.execute_operation_sync(
        owner="ingestion",
        operation="secure_pipeline",
        requested_ids=["KA-078"],
        ka_inputs=_ingestion_inputs(records),
        request_id="ingestion-test",
        run_id="ingestion-test",
        max_effects=8,
        principal_id="desktop",
        service_capabilities={"ingestion_service"},
    )

    assert execution.ok is True
    assert execution.executed_ids == [
        f"KA-{number:03d}" for number in range(71, 79)
    ]
    assert execution.results["KA-071"]["output"]["applied"] is False
    assert execution.results["KA-071"]["output"]["records_ingested"] == 0
    assert execution.results["KA-078"]["output"]["applied"] is False
    assert execution.results["KA-078"]["output"]["records_archived"] == 0


def test_cp19h_ingestion_ka_failure_stops_all_materialization(
    app,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
):
    source = tmp_path / "corpus"
    source.mkdir()
    (source / "policy.md").write_text("governed policy", encoding="utf-8")
    monkeypatch.setenv(
        "DATALOGIC_INGESTION_MANIFEST_DIR",
        str(tmp_path / "manifests"),
    )

    class FailingLifecycle:
        @staticmethod
        def execute_operation_sync(**kwargs):
            raise KnowledgeLifecycleError("injected_ingestion_ka_failure")

    with app.app_context():
        service = LocalKnowledgeIngestionService(
            knowledge_lifecycle=FailingLifecycle()
        )
        with pytest.raises(
            KnowledgeLifecycleError,
            match="injected_ingestion_ka_failure",
        ):
            service.ingest_path(source)

        assert KnowledgeGraphNode.query.count() == 0
        assert CrossStoreOutboxEvent.query.count() == 0
        job = IngestionJob.query.one()
        assert job.status == "failed"
        assert job.current_checkpoint == "failed"

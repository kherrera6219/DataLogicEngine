from __future__ import annotations

from uuid import UUID

import pytest

from backend.governed_execution.knowledge_lifecycle import (
    KnowledgeLifecycleCoordinator,
    KnowledgeLifecycleError,
)
from backend.ingestion import LocalKnowledgeIngestionService
from models import CrossStoreOutboxEvent, IngestionJob, KnowledgeGraphNode


def _secure_record(record_id: str = "policy.md"):
    return {
        "record_id": record_id,
        "relative_path": record_id,
        "source_sha256": "a" * 64,
        "size_bytes": 15,
        "detected_type": ".md",
    }


def _ingestion_inputs(records):
    return {
        "KA-071": {"source_type": "local_file", "payload": records},
        "KA-075": {
            "target_schema": "knowledge_source",
        },
        "KA-078": {"archive_requested": False},
    }


def test_cp19h_ingestion_executes_ka071_through_ka078_in_order():
    records = [_secure_record()]
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
    assert execution.executed_ids == [f"KA-{number:03d}" for number in range(71, 79)]
    assert execution.results["KA-071"]["output"]["applied"] is False
    assert execution.results["KA-071"]["output"]["records_ingested"] == 0
    assert execution.results["KA-078"]["output"]["applied"] is False
    assert execution.results["KA-078"]["output"]["records_archived"] == 0


class _SingleChunkRag:
    @staticmethod
    def chunk_text(text, chunk_size=1200):
        return [text]


def _run_ingestion_owner(app, tmp_path, monkeypatch: pytest.MonkeyPatch):
    source = tmp_path / "corpus"
    source.mkdir()
    (source / "policy.md").write_text("governed local policy", encoding="utf-8")
    monkeypatch.setenv(
        "DATALOGIC_INGESTION_MANIFEST_DIR",
        str(tmp_path / "manifests"),
    )
    with app.app_context():
        result = LocalKnowledgeIngestionService(
            rag_service=_SingleChunkRag(),
            staging_root=tmp_path / "staging",
        ).ingest_path(source)
        job = IngestionJob.query.filter_by(id=UUID(result.ingestion_id)).one()
        node = KnowledgeGraphNode.query.one()
        return {
            "result": result.to_dict(),
            "job_status": job.status,
            "lifecycle": dict(job.result_summary["_ka_lifecycle"]),
            "node_metadata": dict(node.node_metadata),
        }


def _assert_owner_trace(lifecycle: dict, canonical_id: str) -> None:
    states = lifecycle["trace_states"][canonical_id]
    required = [
        "planned",
        "candidate",
        "selected",
        "admitted",
        "executing",
        "executed",
    ]
    assert [state for state in states if state in required] == required


def test_ka_071_owning_path(app, tmp_path, monkeypatch: pytest.MonkeyPatch):
    evidence = _run_ingestion_owner(app, tmp_path, monkeypatch)
    lifecycle = evidence["lifecycle"]
    receipt = lifecycle["authoritative_effect_receipt"]

    assert lifecycle["stage_evidence"]["KA-071"] == {
        "admitted_record_count": 1,
        "applied": False,
    }
    assert receipt["status"] == "applied"
    assert receipt["service"] == "LocalKnowledgeIngestionService"
    assert receipt["ka_proposal_ids"] == [lifecycle["admission_proposal_id"]]
    assert receipt["idempotency_key"] == evidence["result"]["ingestion_id"]
    _assert_owner_trace(lifecycle, "KA-071")


def test_ka_072_owning_path(app, tmp_path, monkeypatch: pytest.MonkeyPatch):
    lifecycle = _run_ingestion_owner(app, tmp_path, monkeypatch)["lifecycle"]

    assert lifecycle["stage_evidence"]["KA-072"] == {
        "cleaned_count": 1,
        "dropped_count": 0,
    }
    assert lifecycle["executed_ids"].index("KA-072") == 1
    _assert_owner_trace(lifecycle, "KA-072")


def test_ka_073_owning_path(app, tmp_path, monkeypatch: pytest.MonkeyPatch):
    lifecycle = _run_ingestion_owner(app, tmp_path, monkeypatch)["lifecycle"]

    assert lifecycle["stage_evidence"]["KA-073"] == {
        "records_transformed": 1,
        "conversion_failure_count": 0,
    }
    assert len(lifecycle["record_chain_sha256"]) == 64
    _assert_owner_trace(lifecycle, "KA-073")


def test_ka_074_owning_path(app, tmp_path, monkeypatch: pytest.MonkeyPatch):
    evidence = _run_ingestion_owner(app, tmp_path, monkeypatch)

    assert evidence["lifecycle"]["stage_evidence"]["KA-074"] == {
        "admission_allowed": True,
        "validation_summary": {"total": 1, "valid": 1, "invalid": 0},
    }
    assert evidence["job_status"] == "materialization_pending"
    _assert_owner_trace(evidence["lifecycle"], "KA-074")


def test_ka_075_owning_path(app, tmp_path, monkeypatch: pytest.MonkeyPatch):
    evidence = _run_ingestion_owner(app, tmp_path, monkeypatch)
    lifecycle = evidence["lifecycle"]

    assert lifecycle["stage_evidence"]["KA-075"] == {
        "records_mapped": 1,
        "target_schema": "knowledge_source",
    }
    assert evidence["node_metadata"]["ingestion_ka"]["plan_id"] == lifecycle["plan_id"]
    _assert_owner_trace(lifecycle, "KA-075")


def test_ka_076_owning_path(app, tmp_path, monkeypatch: pytest.MonkeyPatch):
    lifecycle = _run_ingestion_owner(app, tmp_path, monkeypatch)["lifecycle"]

    assert lifecycle["stage_evidence"]["KA-076"] == {
        "resolution_allowed": True,
        "unique_entities_count": 1,
        "conflict_count": 0,
    }
    _assert_owner_trace(lifecycle, "KA-076")


def test_ka_077_owning_path(app, tmp_path, monkeypatch: pytest.MonkeyPatch):
    lifecycle = _run_ingestion_owner(app, tmp_path, monkeypatch)["lifecycle"]

    assert lifecycle["stage_evidence"]["KA-077"] == {
        "records_enriched": 1,
        "providers_used": [],
        "external_calls": 0,
    }
    _assert_owner_trace(lifecycle, "KA-077")


def test_ka_078_owning_path(app, tmp_path, monkeypatch: pytest.MonkeyPatch):
    lifecycle = _run_ingestion_owner(app, tmp_path, monkeypatch)["lifecycle"]

    assert lifecycle["stage_evidence"]["KA-078"] == {
        "eligible_record_count": 0,
        "records_archived": 0,
        "applied": False,
    }
    assert (
        lifecycle["archive_proposal_id"]
        not in lifecycle["authoritative_effect_receipt"]["ka_proposal_ids"]
    )
    _assert_owner_trace(lifecycle, "KA-078")


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
        service = LocalKnowledgeIngestionService(knowledge_lifecycle=FailingLifecycle())
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


def test_ingestion_owner_rejects_tampered_dependency_output_before_effects(
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

    class TamperedLifecycle:
        @staticmethod
        def execute_operation_sync(**kwargs):
            execution = KnowledgeLifecycleCoordinator().execute_operation_sync(
                **kwargs
            )
            enriched = execution.results["KA-077"]["output"]["enriched_records"]
            enriched.append(dict(enriched[0]))
            return execution

    with app.app_context():
        service = LocalKnowledgeIngestionService(
            rag_service=_SingleChunkRag(),
            staging_root=tmp_path / "staging",
            knowledge_lifecycle=TamperedLifecycle(),
        )
        with pytest.raises(
            KnowledgeLifecycleError,
            match="KA-077 changed the admitted record identity set",
        ):
            service.ingest_path(source)

        assert KnowledgeGraphNode.query.count() == 0
        assert CrossStoreOutboxEvent.query.count() == 0
        job = IngestionJob.query.one()
        assert job.status == "failed"
        assert job.current_checkpoint == "failed"

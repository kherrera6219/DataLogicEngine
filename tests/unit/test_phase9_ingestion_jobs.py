import time
from pathlib import Path
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from backend.ingestion import LocalKnowledgeIngestionService
from backend.ingestion.acquisition import AcquisitionLimitError
from backend.ingestion.job_coordination import RedisIngestionJobCoordinator
from backend.ingestion.jobs import IngestionJobRunner
from backend.ingestion.reconciliation import IngestionCorpusReconciler
from backend.memory.unified_memory_service import UnifiedMemoryService
from extensions import db
from models import (
    CrossStoreOutboxEvent,
    CrossStoreMaterializationState,
    IngestionAttempt,
    IngestionChunk,
    IngestionFile,
    IngestionJob,
    KnowledgeGraphNode,
)


class SingleChunkRag:
    def chunk_text(self, text, chunk_size=1200):
        return [text]


def _queued_job(source, *, status="queued"):
    return IngestionJob(
        status=status,
        source_path=str(source),
        source_digest="a" * 64,
        recursive=True,
        chunk_size=1200,
        max_file_bytes=1024,
        max_total_bytes=4096,
        max_files=10,
        current_checkpoint=status,
    )


def test_sync_ingestion_persists_job_file_chunk_and_attempt(app, tmp_path, monkeypatch):
    monkeypatch.setenv("DATALOGIC_INGESTION_MANIFEST_DIR", str(tmp_path / "manifests"))
    source = tmp_path / "corpus"
    source.mkdir()
    (source / "policy.txt").write_text("durable policy source", encoding="utf-8")

    with app.app_context():
        result = LocalKnowledgeIngestionService(
            rag_service=SingleChunkRag(),
            staging_root=tmp_path / "staging",
        ).ingest_path(source)

        job = IngestionJob.query.filter_by(id=UUID(result.ingestion_id)).one()
        assert job.status == "materialization_pending"
        assert job.current_checkpoint == "materialization_pending"
        assert job.files_ingested == 1
        assert job.chunks_created == 1
        assert IngestionFile.query.filter_by(job_id=job.id).count() == 1
        assert IngestionChunk.query.filter_by(job_id=job.id).count() == 1
        attempt = IngestionAttempt.query.filter_by(job_id=job.id).one()
        assert attempt.status == "completed"
        assert attempt.completed_at is not None


def test_failed_acquisition_is_durable_and_safe(app, tmp_path, monkeypatch):
    monkeypatch.setenv("DATALOGIC_INGESTION_MANIFEST_DIR", str(tmp_path / "manifests"))
    source = tmp_path / "corpus"
    source.mkdir()
    (source / "large.txt").write_text("larger than the job", encoding="utf-8")

    with app.app_context():
        service = LocalKnowledgeIngestionService(
            rag_service=SingleChunkRag(),
            staging_root=tmp_path / "staging",
            max_total_bytes=4,
        )
        with pytest.raises(AcquisitionLimitError):
            service.ingest_path(source)

        job = IngestionJob.query.one()
        assert job.status == "failed"
        assert job.last_error_code == "ingestion_total_bytes_exceeded"
        assert job.last_error_message == "Ingestion failed safely"
        attempt = IngestionAttempt.query.filter_by(job_id=job.id).one()
        assert attempt.status == "failed"


def test_original_source_is_hash_anchored_to_required_object_materialization(
    app, tmp_path, monkeypatch
):
    monkeypatch.setenv("DATALOGIC_INGESTION_MANIFEST_DIR", str(tmp_path / "manifests"))
    monkeypatch.setattr(
        "backend.storage.artifact_materialization.object_store_is_required",
        lambda: True,
    )
    source = tmp_path / "source.txt"
    source.write_text("retained source evidence", encoding="utf-8")

    with app.app_context():
        result = LocalKnowledgeIngestionService(
            rag_service=SingleChunkRag(),
            staging_root=tmp_path / "staging",
        ).ingest_path(source)
        file_record = IngestionFile.query.one()
        event = CrossStoreOutboxEvent.query.filter_by(
            entity_type="ingestion_file_source",
            destination="minio",
        ).one()

        assert file_record.object_bucket == "knowledge-sources"
        assert file_record.object_status == "pending"
        assert file_record.object_sha256 == event.payload["body_sha256"]
        assert event.payload["metadata"]["source_sha256"] == file_record.source_sha256
        assert event.payload.get("body_path")
        assert "body_base64" not in event.payload
        assert CrossStoreOutboxEvent.query.filter_by(
            entity_type="ingestion_file_normalized",
            destination="minio",
        ).count() == 1
        assert result.materializations_pending == 4


def test_async_status_is_read_from_postgresql_authority(app, tmp_path, monkeypatch):
    monkeypatch.setenv("DATALOGIC_INGESTION_MANIFEST_DIR", str(tmp_path / "manifests"))
    source = tmp_path / "corpus"
    source.mkdir()
    (source / "async.txt").write_text("durable async source", encoding="utf-8")

    with app.app_context():
        service = LocalKnowledgeIngestionService(
            rag_service=SingleChunkRag(),
            staging_root=tmp_path / "staging",
        )
        ingestion_id = service.ingest_path_async(source, flask_app=app)
        for _ in range(30):
            status = LocalKnowledgeIngestionService.get_async_status(ingestion_id)
            if status and status["status"] not in {"queued", "running"}:
                break
            time.sleep(0.1)

        assert status is not None
        assert status["status"] == "materialization_pending"
        assert status["result"]["ingestion_id"] == ingestion_id

        # A new service instance reads the same durable authority; no process-local
        # status dictionary is required.
        assert LocalKnowledgeIngestionService.get_async_status(ingestion_id) == status


def test_async_job_survives_original_source_removal_from_app_owned_staging(
    app, tmp_path, monkeypatch
):
    source = tmp_path / "selected"
    source.mkdir()
    original = source / "restart.txt"
    original.write_text("restart durable evidence", encoding="utf-8")
    staging_root = tmp_path / "runtime-staging"

    class DeferredRunner:
        def submit(self, *_args, **_kwargs):
            return None

    import backend.ingestion.jobs as jobs_module

    real_get_runner = jobs_module.get_ingestion_job_runner
    monkeypatch.setattr(jobs_module, "get_ingestion_job_runner", lambda _app: DeferredRunner())
    with app.app_context():
        ingestion_id = LocalKnowledgeIngestionService(
            rag_service=SingleChunkRag(),
            staging_root=staging_root,
        ).ingest_path_async(source, flask_app=app)
        job = db.session.get(IngestionJob, UUID(ingestion_id))
        assert Path(job.source_path).is_relative_to(staging_root / "pending")
        assert str(source.resolve()) not in job.source_path

    original.unlink()
    source.rmdir()
    monkeypatch.setattr(jobs_module, "get_ingestion_job_runner", real_get_runner)

    runner = IngestionJobRunner(app)
    runner._run_acquired(ingestion_id)
    runner.stop()

    with app.app_context():
        job = db.session.get(IngestionJob, UUID(ingestion_id))
        assert job.status == "materialization_pending"
        assert job.files_ingested == 1
        assert not Path(job.source_path).parent.exists()


def test_runner_requeues_interrupted_attempt_from_postgresql(app, tmp_path, monkeypatch):
    submitted = []
    with app.app_context():
        job = _queued_job(tmp_path / "source", status="running")
        db.session.add(job)
        db.session.flush()
        attempt = IngestionAttempt(
            job_id=job.id,
            attempt_number=1,
            status="running",
            checkpoint="parsing",
        )
        db.session.add(attempt)
        db.session.commit()
        job_id = job.id

    runner = IngestionJobRunner(app)
    monkeypatch.setattr(runner, "submit", lambda value: submitted.append(value))
    runner.start()
    runner.stop()

    with app.app_context():
        job = db.session.get(IngestionJob, job_id)
        attempt = IngestionAttempt.query.filter_by(job_id=job_id).one()
        assert job.status == "queued"
        assert job.current_checkpoint == "restart_reconciled"
        assert attempt.status == "interrupted"
        assert attempt.error_code == "ingestion_worker_interrupted"
        assert submitted == [str(job_id)]


def test_redis_coordination_is_content_free_and_idempotent():
    redis = MagicMock()
    redis.set.return_value = True
    redis.exists.return_value = 0
    pipeline = MagicMock()
    redis.pipeline.return_value = pipeline
    coordinator = RedisIngestionJobCoordinator(redis)
    job_id = "00000000-0000-0000-0000-000000000909"

    coordinator.enqueue(job_id)
    assert coordinator.acquire(job_id, worker_id="worker-1", lease_seconds=60) is True
    coordinator.request_control(job_id, "pause")

    redis.zadd.assert_called_once_with(
        "ingestion:jobs:queue", {job_id: pytest.approx(time.time(), abs=2)}, nx=True
    )
    redis.zrem.assert_called_once_with("ingestion:jobs:queue", job_id)
    assert all("source" not in str(call).lower() for call in pipeline.method_calls)
    redis.set.assert_any_call(
        f"ingestion:jobs:{job_id}:pause", "1", ex=86400
    )


def test_corpus_scanner_completes_only_after_every_required_revision(app, tmp_path, monkeypatch):
    monkeypatch.setenv("DATALOGIC_INGESTION_MANIFEST_DIR", str(tmp_path / "manifests"))
    monkeypatch.setattr(
        "backend.storage.artifact_materialization.object_store_is_required",
        lambda: True,
    )
    source = tmp_path / "source.txt"
    source.write_text("reconciled evidence", encoding="utf-8")

    with app.app_context():
        result = LocalKnowledgeIngestionService(
            rag_service=SingleChunkRag(), staging_root=tmp_path / "staging"
        ).ingest_path(source)
        file_record = IngestionFile.query.one()
        file_record.object_status = "ready"
        file_record.normalized_object_status = "ready"
        chunk = IngestionChunk.query.one()
        for state in CrossStoreMaterializationState.query.filter_by(
            entity_type="knowledge_graph_node", entity_id=chunk.node_uid
        ).all():
            state.state = "succeeded"
            state.observed_revision = chunk.source_revision
        db.session.commit()

        report = IngestionCorpusReconciler().scan(job_id=result.ingestion_id)
        job = IngestionJob.query.one()
        assert report["divergence_count"] == 0
        assert report["consistent_jobs"] == 1
        assert job.status == "completed"
        assert job.chunks_indexed == 1
        assert job.materializations_pending == 0


def test_corpus_repair_requeues_retained_failed_outbox(app, tmp_path, monkeypatch):
    monkeypatch.setenv("DATALOGIC_INGESTION_MANIFEST_DIR", str(tmp_path / "manifests"))
    source = tmp_path / "source.txt"
    source.write_text("repairable evidence", encoding="utf-8")

    with app.app_context():
        result = LocalKnowledgeIngestionService(
            rag_service=SingleChunkRag(), staging_root=tmp_path / "staging"
        ).ingest_path(source)
        event = CrossStoreOutboxEvent.query.filter_by(destination="chroma").one()
        state = CrossStoreMaterializationState.query.filter_by(
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            destination=event.destination,
        ).one()
        event.status = "failed"
        event.safe_reason = "test_failure"
        state.state = "failed"
        db.session.commit()

        report = IngestionCorpusReconciler().scan(
            job_id=result.ingestion_id, repair=True
        )
        db.session.refresh(event)
        assert report["divergence_count"] >= 1
        assert report["jobs"][0]["requeued"] == 1
        assert event.status == "pending"


def test_modified_source_queues_old_revision_deletion_and_reconciles(app, tmp_path, monkeypatch):
    monkeypatch.setenv("DATALOGIC_INGESTION_MANIFEST_DIR", str(tmp_path / "manifests"))
    source = tmp_path / "policy.txt"
    source.write_text("policy revision one", encoding="utf-8")

    with app.app_context():
        service = LocalKnowledgeIngestionService(
            rag_service=SingleChunkRag(), staging_root=tmp_path / "staging"
        )
        first = service.ingest_path(source)
        first_file = IngestionFile.query.filter_by(job_id=UUID(first.ingestion_id)).one()
        first_chunk = IngestionChunk.query.filter_by(job_id=UUID(first.ingestion_id)).one()
        first_document_uid = first_file.document_uid
        first_node_uid = first_chunk.node_uid

        source.write_text("policy revision two", encoding="utf-8")
        second = service.ingest_path(source)
        second_file = IngestionFile.query.filter_by(job_id=UUID(second.ingestion_id)).one()
        second_chunk = IngestionChunk.query.filter_by(job_id=UUID(second.ingestion_id)).one()

        assert second_file.document_uid == first_document_uid
        assert second_chunk.node_uid != first_node_uid
        assert first_file.status == "deletion_pending"
        assert CrossStoreOutboxEvent.query.filter(
            CrossStoreOutboxEvent.operation.in_(
                ("delete_knowledge_node", "delete_object")
            )
        ).count() == 4

        first_file.object_status = "deleted"
        first_file.normalized_object_status = "deleted"
        for state in CrossStoreMaterializationState.query.all():
            state.state = "succeeded"
            state.observed_revision = state.source_revision
        db.session.commit()

        report = IngestionCorpusReconciler().scan()
        first_job = db.session.get(IngestionJob, UUID(first.ingestion_id))
        second_job = db.session.get(IngestionJob, UUID(second.ingestion_id))
        assert report["divergence_count"] == 0
        assert first_job.status == "superseded"
        assert second_job.status == "completed"
        assert first_chunk.materialization_state == "deleted"
        assert KnowledgeGraphNode.query.filter_by(uid=first_node_uid).one_or_none() is None
        assert KnowledgeGraphNode.query.filter_by(uid=second_chunk.node_uid).one_or_none() is not None


def test_delete_request_covers_object_vector_and_graph(app, tmp_path, monkeypatch):
    monkeypatch.setenv("DATALOGIC_INGESTION_MANIFEST_DIR", str(tmp_path / "manifests"))
    source = tmp_path / "delete.txt"
    source.write_text("delete me everywhere", encoding="utf-8")

    with app.app_context():
        result = LocalKnowledgeIngestionService(
            rag_service=SingleChunkRag(), staging_root=tmp_path / "staging"
        ).ingest_path(source)
        job = db.session.get(IngestionJob, UUID(result.ingestion_id))
        response = IngestionCorpusReconciler().request_delete(job)

        assert response["status"] == "deletion_pending"
        assert IngestionFile.query.one().status == "deletion_pending"
        operations = {
            event.operation for event in CrossStoreOutboxEvent.query.all()
        }
        assert {"delete_object", "delete_knowledge_node"} <= operations


def test_delete_retains_shared_chunks_and_removes_source_linked_memory(
    app, tmp_path, monkeypatch
):
    monkeypatch.setenv("DATALOGIC_INGESTION_MANIFEST_DIR", str(tmp_path / "manifests"))
    source = tmp_path / "shared.txt"
    source.write_text("shared revision evidence", encoding="utf-8")

    with app.app_context():
        service = LocalKnowledgeIngestionService(
            rag_service=SingleChunkRag(), staging_root=tmp_path / "staging"
        )
        first = service.ingest_path(source)
        second = service.ingest_path(source)
        second_job = db.session.get(IngestionJob, UUID(second.ingestion_id))
        second_chunk = IngestionChunk.query.filter_by(job_id=second_job.id).one()

        memory = UnifiedMemoryService(
            storage_path=tmp_path / "memory.json", auto_load=False, strict=True
        )
        retained = memory.record_release_commit(
            content="answer derived from the shared source",
            simulation_id="trace-shared",
            metadata={"source_ids": [second_chunk.node_uid]},
        )
        app.extensions["dle_unified_memory_service"] = memory

        outcome = IngestionCorpusReconciler().request_delete(second_job)

        assert outcome["memory_records_deleted"] == 1
        assert retained.vertex_id not in memory.graph.vertices
        assert second_chunk.materialization_state == "shared_reference_retained"
        assert CrossStoreOutboxEvent.query.filter_by(
            operation="delete_knowledge_node"
        ).count() == 0
        assert KnowledgeGraphNode.query.filter_by(uid=second_chunk.node_uid).one_or_none()
        assert db.session.get(IngestionJob, UUID(first.ingestion_id)) is not None

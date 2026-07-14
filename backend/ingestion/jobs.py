"""Bounded durable execution and restart reconciliation for ingestion jobs."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime
import logging
import os
from pathlib import Path
import shutil
from threading import Event, Lock
import uuid

from backend.ingestion.job_coordination import (
    IngestionJobCoordinatorUnavailable,
    RedisIngestionJobCoordinator,
)


logger = logging.getLogger(__name__)


class IngestionJobRunner:
    """Own bounded ingestion workers with PostgreSQL authority and Redis coordination."""

    def __init__(self, app, *, max_workers: int = 2) -> None:
        self.app = app
        self._executor = ThreadPoolExecutor(
            max_workers=max(1, min(8, int(max_workers))),
            thread_name_prefix="dle-ingestion-job",
        )
        self._futures: dict[str, Future] = {}
        self._service_overrides: dict[str, object] = {}
        self._lock = Lock()
        self._stopping = Event()
        self._lease_seconds = max(
            60,
            min(3600, int(app.config.get("DLE_INGESTION_JOB_LEASE_SECONDS", 300))),
        )
        self._coordinator = None
        if app.config.get("DLE_USE_REDIS") or app.config.get("DLE_PRODUCTION_MODE"):
            redis_url = app.config.get("DLE_REDIS_URL") or os.environ.get(
                "REDIS_URL", "redis://127.0.0.1:6379/0"
            )
            self._coordinator = RedisIngestionJobCoordinator.from_url(redis_url)

    def start(self) -> None:
        """Requeue idempotent interrupted attempts from PostgreSQL authority."""
        from extensions import db
        from models import IngestionAttempt, IngestionJob

        with self.app.app_context():
            interrupted = IngestionJob.query.filter_by(status="running").all()
            interrupted_ids = {job.id for job in interrupted}
            for job in interrupted:
                job.status = "queued"
                job.current_checkpoint = "restart_reconciled"
                job.last_error_code = None
                job.last_error_message = None
            if interrupted_ids:
                attempts = IngestionAttempt.query.filter(
                    IngestionAttempt.job_id.in_(interrupted_ids),
                    IngestionAttempt.status == "running",
                ).all()
                for attempt in attempts:
                    attempt.status = "interrupted"
                    attempt.checkpoint = "restart_reconciled"
                    attempt.error_code = "ingestion_worker_interrupted"
                    attempt.error_message = "The prior worker stopped before commit"
                    attempt.completed_at = datetime.now(UTC)
            queued_ids = [
                str(job.id)
                for job in IngestionJob.query.filter_by(status="queued").all()
            ]
            db.session.commit()
        for job_id in queued_ids:
            self.submit(job_id)

    def submit(self, job_id: str, *, service=None) -> None:
        normalized = str(uuid.UUID(str(job_id)))
        with self._lock:
            if self._stopping.is_set():
                raise RuntimeError("Ingestion job runner is stopping")
            existing = self._futures.get(normalized)
            if existing is not None and not existing.done():
                if service is not None:
                    self._service_overrides[normalized] = service
                return
            if service is not None:
                self._service_overrides[normalized] = service
            if self._coordinator is not None:
                self._coordinator.enqueue(normalized)
            future = self._executor.submit(self._run, normalized)
            self._futures[normalized] = future
            future.add_done_callback(lambda _future: self._forget(normalized))

    def _forget(self, job_id: str) -> None:
        with self._lock:
            self._futures.pop(job_id, None)
            self._service_overrides.pop(job_id, None)

    def _run(self, job_id: str) -> None:
        worker_id = str(uuid.uuid4())
        if self._coordinator is not None and not self._coordinator.acquire(
            job_id,
            worker_id=worker_id,
            lease_seconds=self._lease_seconds,
        ):
            return
        try:
            self._run_acquired(job_id)
        finally:
            if self._coordinator is not None:
                try:
                    self._coordinator.release(job_id, worker_id=worker_id)
                except IngestionJobCoordinatorUnavailable:
                    logger.error("Ingestion coordination lease release failed")

    def _requested_control(self, job_id: str) -> str | None:
        if self._stopping.is_set():
            return "pause"
        from extensions import db
        from models import IngestionJob

        job = db.session.get(IngestionJob, uuid.UUID(job_id))
        if job is None:
            return "cancel"
        db.session.refresh(job)
        if job.cancellation_requested:
            return "cancel"
        if job.pause_requested:
            return "pause"
        if self._coordinator is not None:
            return self._coordinator.requested_control(job_id)
        return None

    def _run_acquired(self, job_id: str) -> None:
        from extensions import db
        from models import IngestionJob

        with self.app.app_context():
            job = db.session.get(IngestionJob, uuid.UUID(job_id))
            if job is None or job.status != "queued":
                return
            control = self._requested_control(job_id)
            if control:
                self._finalize_control(job, control)
                return
            request_options = dict(job.result_summary or {})
            source_path = job.source_path
            recursive = bool(job.recursive)
            user_id = job.user_id
            tenant_id = job.tenant_id
            source_label = job.source_label
            service_options = {
                "chunk_size": job.chunk_size,
                "max_file_bytes": job.max_file_bytes,
                "max_total_bytes": job.max_total_bytes,
                "max_files": job.max_files,
                "max_pages": job.max_pages,
                "max_archive_entries": job.max_archive_entries,
                "max_decompressed_bytes": job.max_decompressed_bytes,
                "max_archive_depth": job.max_archive_depth,
                "parser_timeout_seconds": job.parser_timeout_seconds,
            }
            if request_options.get("_staging_root"):
                service_options["staging_root"] = request_options["_staging_root"]

            from backend.ingestion.local_ingestion import (
                IngestionControlRequested,
                LocalKnowledgeIngestionService,
            )

            with self._lock:
                service = self._service_overrides.get(job_id)
            if service is None:
                service = LocalKnowledgeIngestionService(**service_options)
            try:
                result = service.ingest_path(
                    source_path,
                    recursive=recursive,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    source_label=source_label,
                    metadata=(
                        request_options.get("_request_metadata")
                        if isinstance(request_options.get("_request_metadata"), dict)
                        else None
                    ),
                    ingestion_id=job_id,
                    control_check=lambda: self._requested_control(job_id),
                    progress_callback=lambda checkpoint, counts: self._record_progress(
                        job_id, checkpoint, counts
                    ),
                )
                durable_job = db.session.get(IngestionJob, uuid.UUID(job_id))
                if durable_job is not None:
                    summary = dict(durable_job.result_summary or result.to_dict())
                    summary["neo4j_sync"] = (
                        {"status": "pending_outbox"}
                        if request_options.get("_sync_neo4j") and result.chunks_created > 0
                        else None
                    )
                    durable_job.result_summary = summary
                    db.session.commit()
                    self._cleanup_completed_staging(
                        job_id,
                        request_options.get("_durable_staging_session"),
                        request_options.get("_staging_root"),
                    )
                    self._record_state(job_id, durable_job.status)
            except IngestionControlRequested:
                controlled = db.session.get(IngestionJob, uuid.UUID(job_id))
                if controlled is not None:
                    self._record_state(job_id, controlled.status)
            except Exception:
                logger.exception("Durable ingestion job %s failed", job_id)
                failed = db.session.get(IngestionJob, uuid.UUID(job_id))
                if failed is not None:
                    self._record_state(job_id, failed.status)

    def _record_state(self, job_id: str, state: str) -> None:
        if self._coordinator is not None:
            self._coordinator.record_state(job_id, state)

    @staticmethod
    def _cleanup_completed_staging(
        job_id: str, session_value: object, processing_root_value: object
    ) -> None:
        if not session_value or not processing_root_value:
            return
        session = Path(str(session_value)).expanduser().resolve()
        pending_root = (
            Path(str(processing_root_value)).expanduser().resolve().parent / "pending"
        ).resolve()
        if session.parent != pending_root or session.name != str(uuid.UUID(job_id)):
            raise RuntimeError("unsafe_durable_ingestion_staging_cleanup")
        shutil.rmtree(session, ignore_errors=True)

    def _record_progress(
        self, job_id: str, checkpoint: str, counts: dict[str, int]
    ) -> None:
        if self._coordinator is not None:
            self._coordinator.record_progress(
                job_id,
                state="running",
                checkpoint=checkpoint,
                counts=counts,
            )

    def coordination_state(self, job_id: str) -> dict[str, str] | None:
        if self._coordinator is None:
            return None
        return self._coordinator.get_state(job_id)

    def _finalize_control(self, job, action: str) -> None:
        from extensions import db

        now = datetime.now(UTC)
        job.status = "cancelled" if action == "cancel" else "paused"
        job.current_checkpoint = job.status
        job.completed_at = now if action == "cancel" else None
        db.session.commit()
        self._record_state(str(job.id), job.status)

    def cancel(self, job) -> None:
        job.cancellation_requested = True
        if self._coordinator is not None:
            self._coordinator.request_control(str(job.id), "cancel")

    def pause(self, job) -> None:
        job.pause_requested = True
        if self._coordinator is not None:
            self._coordinator.request_control(str(job.id), "pause")

    def resume(self, job) -> None:
        from extensions import db

        job.cancellation_requested = False
        job.pause_requested = False
        job.status = "queued"
        job.current_checkpoint = "queued"
        job.completed_at = None
        job.last_error_code = None
        job.last_error_message = None
        db.session.commit()
        if self._coordinator is not None:
            self._coordinator.clear_controls(str(job.id))
        self.submit(str(job.id))

    def stop(self) -> None:
        """Cooperatively pause active jobs and drain bounded workers."""
        self._stopping.set()
        self._executor.shutdown(wait=True, cancel_futures=False)


def get_ingestion_job_runner(app) -> IngestionJobRunner:
    runner = app.extensions.get("dle_ingestion_job_runner")
    if runner is None:
        runner = IngestionJobRunner(
            app,
            max_workers=int(app.config.get("DLE_INGESTION_JOB_WORKERS", 2)),
        )
        app.extensions["dle_ingestion_job_runner"] = runner
        runner.start()
    return runner

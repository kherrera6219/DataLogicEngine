"""Bounded durable execution for Phase 8 gateway jobs."""

from __future__ import annotations

import asyncio
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime
import hashlib
import logging
import os
from threading import Lock
import uuid

from backend.governed_execution.cancellation import CANCELLATION_REGISTRY
from backend.llm_gateway.payload_cipher import decrypt_payload, encrypt_payload
from backend.llm_gateway.job_coordination import (
    GatewayJobCoordinatorUnavailable,
    RedisGatewayJobCoordinator,
)


logger = logging.getLogger(__name__)


class GatewayJobRunner:
    """Own a bounded worker pool and reconcile durable jobs on application start."""

    def __init__(self, app, *, max_workers: int = 4) -> None:
        self.app = app
        self._executor = ThreadPoolExecutor(
            max_workers=max(1, min(16, int(max_workers))),
            thread_name_prefix="dle-gateway-job",
        )
        self._futures: dict[str, Future] = {}
        self._lock = Lock()
        self._stopping = False
        self._coordination_retention = max(
            3600,
            int(app.config.get("DLE_GATEWAY_JOB_RETENTION_HOURS", 24)) * 3600,
        )
        self._coordination_lease_seconds = max(
            60,
            min(3600, int(app.config.get("DLE_GATEWAY_JOB_LEASE_SECONDS", 300))),
        )
        self._coordinator = None
        if app.config.get("DLE_USE_REDIS") or app.config.get("DLE_PRODUCTION_MODE"):
            redis_url = app.config.get("DLE_REDIS_URL") or os.environ.get(
                "REDIS_URL", "redis://127.0.0.1:6379/0"
            )
            self._coordinator = RedisGatewayJobCoordinator.from_url(redis_url)

    def _record_coordination_state(self, job_id: str, state: str) -> None:
        if self._coordinator is None:
            return
        self._coordinator.record_state(
            job_id,
            state,
            retention_seconds=self._coordination_retention,
        )

    def start(self) -> None:
        """Reconcile interrupted work without risking duplicate provider spend."""
        from extensions import db
        from models import GatewayAsyncRun

        with self.app.app_context():
            now = datetime.now(UTC)
            interrupted = GatewayAsyncRun.query.filter_by(status="running").all()
            for job in interrupted:
                job.status = "failed"
                job.error_code = "JOB_INTERRUPTED_RETRY_UNSAFE"
                job.error_message = (
                    "The application stopped while this job was running. "
                    "It was not replayed because provider spend may already have occurred."
                )
                job.completed_at = now
            interrupted_ids = [str(job.id) for job in interrupted]
            queued_ids = [str(job.id) for job in GatewayAsyncRun.query.filter_by(status="queued").all()]
            db.session.commit()
        for job_id in interrupted_ids:
            self._record_coordination_state(job_id, "failed")
        for job_id in queued_ids:
            self.submit(job_id)

    def submit(self, job_id: str) -> None:
        normalized = str(uuid.UUID(str(job_id)))
        with self._lock:
            if self._stopping:
                raise RuntimeError("Gateway job runner is stopping")
            existing = self._futures.get(normalized)
            if existing is not None and not existing.done():
                return
            self._record_coordination_state(normalized, "queued")
            future = self._executor.submit(self._run, normalized)
            self._futures[normalized] = future
            future.add_done_callback(lambda _future: self._forget(normalized))

    def _forget(self, job_id: str) -> None:
        with self._lock:
            self._futures.pop(job_id, None)

    def _run(self, job_id: str) -> None:
        worker_id = str(uuid.uuid4())
        if self._coordinator is not None:
            if not self._coordinator.acquire(
                job_id,
                worker_id=worker_id,
                lease_seconds=self._coordination_lease_seconds,
            ):
                return
        try:
            self._run_acquired(job_id)
        finally:
            if self._coordinator is not None:
                try:
                    self._coordinator.release(job_id, worker_id=worker_id)
                except GatewayJobCoordinatorUnavailable:
                    logger.error("Gateway job coordination lease release failed")

    def _run_acquired(self, job_id: str) -> None:
        from extensions import db
        from models import GatewayAsyncRun

        with self.app.app_context():
            job = db.session.get(GatewayAsyncRun, uuid.UUID(job_id))
            if job is None or job.status != "queued":
                return
            now = datetime.now(UTC)
            redis_cancelled = (
                self._coordinator.is_cancel_requested(job_id)
                if self._coordinator is not None
                else False
            )
            if job.cancellation_requested or redis_cancelled:
                job.status = "cancelled"
                job.completed_at = now
                db.session.commit()
                self._record_coordination_state(job_id, "cancelled")
                return
            expiry_now = now.replace(tzinfo=None) if job.expires_at.tzinfo is None else now
            if job.expires_at <= expiry_now:
                job.status = "expired"
                job.error_code = "JOB_EXPIRED"
                job.error_message = "The gateway job expired before execution."
                job.completed_at = now
                db.session.commit()
                self._record_coordination_state(job_id, "expired")
                return
            job.status = "running"
            job.started_at = now
            job.attempt_count = int(job.attempt_count or 0) + 1
            payload = decrypt_payload(job.request_encryption, job.request_ciphertext)
            user_id = job.user_id
            api_key_id = str(job.api_key_id) if job.api_key_id else None
            request_id = job.request_id
            db.session.commit()
            self._record_coordination_state(job_id, "running")

            try:
                from backend.llm_gateway.api import execute_gateway_job_payload

                result_payload, response_status = asyncio.run(
                    execute_gateway_job_payload(
                        payload,
                        user_id=user_id,
                        api_key_id=api_key_id,
                    )
                )
            except Exception:
                logger.exception("Durable gateway job execution failed")
                result_payload = {
                    "error": "Gateway job execution failed",
                    "code": "GATEWAY_JOB_INTERNAL_ERROR",
                    "request_id": request_id,
                }
                response_status = 500

            job = db.session.get(GatewayAsyncRun, uuid.UUID(job_id))
            if job is None:
                return
            try:
                encryption, ciphertext = encrypt_payload(result_payload)
                encoded_result = ciphertext.encode("utf-8")
                result_hash = hashlib.sha256(encoded_result).hexdigest()
                threshold = max(
                    65_536,
                    min(
                        16_777_216,
                        int(self.app.config.get("DLE_GATEWAY_OBJECT_RESULT_THRESHOLD", 262_144)),
                    ),
                )
                job.response_encryption = encryption
                job.response_sha256 = result_hash
                job.response_size_bytes = len(encoded_result)
                if len(encoded_result) >= threshold:
                    from backend.storage.artifact_materialization import persist_object_artifact

                    object_key = f"jobs/{job.id}/result.enc"
                    reference = persist_object_artifact(
                        entity_type="gateway_async_run_result",
                        entity_id=str(job.id),
                        bucket="gateway-results",
                        key=object_key,
                        body=encoded_result,
                        schema_version="gateway-job-result.v1",
                        content_type="application/octet-stream",
                        metadata={
                            "encryption": encryption,
                            "request_id": job.request_id,
                        },
                    )
                    job.response_storage = "minio_ciphertext"
                    job.response_ciphertext = None
                    job.response_object_bucket = reference["bucket"]
                    job.response_object_key = reference["key"]
                else:
                    job.response_storage = "postgresql_ciphertext"
                    job.response_ciphertext = ciphertext
                    job.response_object_bucket = None
                    job.response_object_key = None
            except Exception:
                logger.exception("Durable gateway job result persistence failed")
                job.status = "failed"
                job.error_code = "GATEWAY_JOB_RESULT_PERSISTENCE_FAILED"
                job.error_message = "Gateway job result could not be persisted safely."
                job.completed_at = datetime.now(UTC)
                db.session.commit()
                self._record_coordination_state(job_id, "failed")
                return
            job.response_status = int(response_status)
            job.run_id = str(result_payload.get("run_id") or "") or None
            job.error_code = str(result_payload.get("code") or "")[:100] or None
            job.error_message = str(result_payload.get("error") or "")[:500] or None
            job.completed_at = datetime.now(UTC)
            cancelled = job.cancellation_requested or job.error_code == "REQUEST_CANCELLED"
            job.status = "cancelled" if cancelled else (
                "completed" if 200 <= int(response_status) < 300 else "failed"
            )
            db.session.commit()
            self._record_coordination_state(job_id, job.status)

    def cancel(self, job) -> bool:
        job.cancellation_requested = True
        if self._coordinator is not None:
            self._coordinator.request_cancel(
                str(job.id),
                retention_seconds=self._coordination_retention,
            )
            self._record_coordination_state(str(job.id), "cancellation_requested")
        signalled = CANCELLATION_REGISTRY.cancel(job.request_id)
        if job.run_id:
            signalled = CANCELLATION_REGISTRY.cancel(job.run_id) or signalled
        return signalled

    def stop(self) -> None:
        """Cancel admitted work and wait for cooperative governed cancellation."""
        from extensions import db
        from models import GatewayAsyncRun

        with self._lock:
            self._stopping = True
            futures = list(self._futures.values())
        with self.app.app_context():
            running = GatewayAsyncRun.query.filter(
                GatewayAsyncRun.status.in_(("queued", "running"))
            ).all()
            for job in running:
                job.cancellation_requested = True
                if self._coordinator is not None:
                    self._coordinator.request_cancel(
                        str(job.id),
                        retention_seconds=self._coordination_retention,
                    )
                CANCELLATION_REGISTRY.cancel(job.request_id)
            db.session.commit()
        for future in futures:
            future.cancel()
        self._executor.shutdown(wait=True, cancel_futures=True)


def get_gateway_job_runner(app) -> GatewayJobRunner:
    runner = app.extensions.get("dle_gateway_job_runner")
    if runner is None:
        runner = GatewayJobRunner(
            app,
            max_workers=int(app.config.get("DLE_GATEWAY_JOB_WORKERS", 4)),
        )
        app.extensions["dle_gateway_job_runner"] = runner
        runner.start()
    return runner

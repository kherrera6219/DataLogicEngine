"""PostgreSQL-authoritative ingestion corpus consistency scanning and repair."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from extensions import db
from models import (
    CrossStoreMaterializationState,
    CrossStoreOutboxEvent,
    IngestionChunk,
    IngestionFile,
    IngestionJob,
    KnowledgeGraphNode,
)


class IngestionCorpusReconciler:
    """Compare expected ingestion revisions with every required materialization."""

    REQUIRED_CHUNK_DESTINATIONS = ("chroma", "neo4j")

    def request_delete(self, job: IngestionJob) -> dict[str, Any]:
        """Queue idempotent deletion for every retained store in one SQL transaction."""
        from backend.storage.outbox import CrossStoreOutbox

        outbox = CrossStoreOutbox(db.session)
        queued = 0
        files = IngestionFile.query.filter_by(job_id=job.id).all()
        source_ids: set[str] = set()
        document_uids = {
            str(source_file.document_uid)
            for source_file in files
            if source_file.document_uid
        }
        for source_file in files:
            if source_file.status in {"rejected", "deleted"}:
                continue
            delete_revision = f"delete:{job.id}"
            for chunk in IngestionChunk.query.filter_by(
                job_id=job.id, file_id=source_file.id
            ):
                source_ids.add(chunk.node_uid)
                if self._has_active_chunk_reference(chunk, excluding_file_id=source_file.id):
                    chunk.materialization_state = "shared_reference_retained"
                    continue
                for destination in self.REQUIRED_CHUNK_DESTINATIONS:
                    event = outbox.enqueue(
                        entity_type="knowledge_graph_node",
                        entity_id=chunk.node_uid,
                        destination=destination,
                        operation="delete_knowledge_node",
                        schema_version="knowledge-node.v1",
                        source_revision=delete_revision,
                        payload={"node_uid": chunk.node_uid},
                        correlation_id=str(job.id),
                    )
                    queued += event.status != "succeeded"
                chunk.materialization_state = "deletion_pending"
            if source_file.object_bucket and source_file.object_key:
                event = outbox.enqueue(
                    entity_type="ingestion_file_source",
                    entity_id=str(source_file.id),
                    destination="minio",
                    operation="delete_object",
                    schema_version="ingestion-source.v1",
                    source_revision=delete_revision,
                    payload={
                        "bucket": source_file.object_bucket,
                        "key": source_file.object_key,
                    },
                    correlation_id=str(job.id),
                )
                queued += event.status != "succeeded"
                source_file.object_status = "deletion_pending"
            if source_file.normalized_object_bucket and source_file.normalized_object_key:
                event = outbox.enqueue(
                    entity_type="ingestion_file_normalized",
                    entity_id=str(source_file.id),
                    destination="minio",
                    operation="delete_object",
                    schema_version="ingestion-normalized.v1",
                    source_revision=delete_revision,
                    payload={
                        "bucket": source_file.normalized_object_bucket,
                        "key": source_file.normalized_object_key,
                    },
                    correlation_id=str(job.id),
                )
                queued += event.status != "succeeded"
                source_file.normalized_object_status = "deletion_pending"
            source_file.status = "deletion_pending"
        from backend.memory import get_unified_memory_service

        memory_records_deleted = get_unified_memory_service().delete_by_sources(
            source_ids=source_ids,
            ingestion_id=str(job.id),
            document_uids=document_uids,
        )
        job.status = "deletion_pending"
        job.current_checkpoint = "deletion_pending"
        job.materializations_pending = int(queued)
        job.completed_at = None
        summary = dict(job.result_summary or {})
        summary["memory_records_deleted"] = memory_records_deleted
        job.result_summary = summary
        db.session.commit()
        return {
            "ingestion_id": str(job.id),
            "status": job.status,
            "materializations_pending": int(queued),
            "memory_records_deleted": memory_records_deleted,
        }

    def scan(
        self,
        *,
        job_id: str | UUID | None = None,
        user_id: int | None = None,
        repair: bool = False,
    ) -> dict[str, Any]:
        query = IngestionJob.query.filter(
            IngestionJob.status.in_(
                (
                    "materialization_pending",
                    "deletion_pending",
                    "completed",
                    "failed",
                )
            )
        )
        if job_id is not None:
            query = query.filter(IngestionJob.id == UUID(str(job_id)))
        if user_id is not None:
            query = query.filter(IngestionJob.user_id == user_id)
        jobs = query.order_by(IngestionJob.created_at).all()
        reports = [self._scan_job(job, repair=repair) for job in jobs]
        db.session.commit()
        divergence_count = sum(len(item["divergences"]) for item in reports)
        return {
            "scanned_jobs": len(reports),
            "consistent_jobs": sum(1 for item in reports if item["consistent"]),
            "divergence_count": divergence_count,
            "repair_requested": bool(repair),
            "jobs": reports,
        }

    def _scan_job(self, job: IngestionJob, *, repair: bool) -> dict[str, Any]:
        divergences: list[dict[str, str]] = []
        repaired = 0
        files = IngestionFile.query.filter_by(job_id=job.id).all()
        chunks = IngestionChunk.query.filter_by(job_id=job.id).all()
        chunks_by_file: dict[UUID, list[IngestionChunk]] = {}
        for chunk in chunks:
            chunks_by_file.setdefault(chunk.file_id, []).append(chunk)
        deletion_chunk_ids: set[UUID] = set()

        for source_file in files:
            if source_file.status == "rejected":
                continue
            if source_file.status in {"deletion_pending", "deleted"}:
                deletion_chunk_ids.update(
                    chunk.id for chunk in chunks_by_file.get(source_file.id, [])
                )
                if source_file.status == "deleted":
                    continue
                deletion_ready = (
                    source_file.object_status in {None, "deleted"}
                    and source_file.normalized_object_status in {None, "deleted"}
                )
                if not deletion_ready:
                    divergences.append(
                        self._divergence(
                            "minio", str(source_file.id), "deletion_pending"
                        )
                    )
                    if repair:
                        repaired += self._requeue_failed(
                            "ingestion_file_source", str(source_file.id), "minio"
                        )
                    if source_file.normalized_object_status not in {None, "deleted"}:
                        if repair:
                            repaired += self._requeue_failed(
                                "ingestion_file_normalized", str(source_file.id), "minio"
                            )
                for chunk in chunks_by_file.get(source_file.id, []):
                    if chunk.materialization_state == "shared_reference_retained":
                        continue
                    chunk_deleted = True
                    for destination in self.REQUIRED_CHUNK_DESTINATIONS:
                        state = CrossStoreMaterializationState.query.filter_by(
                            entity_type="knowledge_graph_node",
                            entity_id=chunk.node_uid,
                            destination=destination,
                        ).one_or_none()
                        if (
                            state is None
                            or state.state != "succeeded"
                            or not str(state.source_revision).startswith("delete:")
                            or state.observed_revision != state.source_revision
                        ):
                            chunk_deleted = False
                            divergences.append(
                                self._divergence(
                                    destination,
                                    chunk.node_uid,
                                    "deletion_pending",
                                )
                            )
                            if repair:
                                repaired += self._requeue_failed(
                                    "knowledge_graph_node",
                                    chunk.node_uid,
                                    destination,
                                )
                    if chunk_deleted:
                        chunk.materialization_state = "deleted"
                        node = KnowledgeGraphNode.query.filter_by(uid=chunk.node_uid).one_or_none()
                        if node is not None:
                            db.session.delete(node)
                    else:
                        deletion_ready = False
                if deletion_ready:
                    source_file.status = "deleted"
                continue
            if not source_file.object_bucket or not source_file.object_key:
                divergences.append(
                    self._divergence("minio", str(source_file.id), "object_reference_missing")
                )
            elif source_file.object_status != "ready":
                reason = f"object_{source_file.object_status or 'state_missing'}"
                divergences.append(self._divergence("minio", str(source_file.id), reason))
                if repair:
                    repaired += self._requeue_failed(
                        "ingestion_file_source", str(source_file.id), "minio"
                    )
            if not source_file.normalized_object_bucket or not source_file.normalized_object_key:
                divergences.append(
                    self._divergence("minio", str(source_file.id), "normalized_object_reference_missing")
                )
            elif source_file.normalized_object_status != "ready":
                reason = (
                    f"normalized_object_{source_file.normalized_object_status or 'state_missing'}"
                )
                divergences.append(self._divergence("minio", str(source_file.id), reason))
                if repair:
                    repaired += self._requeue_failed(
                        "ingestion_file_normalized", str(source_file.id), "minio"
                    )

        indexed = 0
        for chunk in chunks:
            if chunk.id in deletion_chunk_ids:
                continue
            chunk_consistent = True
            for destination in self.REQUIRED_CHUNK_DESTINATIONS:
                state = CrossStoreMaterializationState.query.filter_by(
                    entity_type="knowledge_graph_node",
                    entity_id=chunk.node_uid,
                    destination=destination,
                ).one_or_none()
                if state is None:
                    chunk_consistent = False
                    divergences.append(
                        self._divergence(destination, chunk.node_uid, "state_missing")
                    )
                    continue
                if state.source_revision != chunk.source_revision:
                    chunk_consistent = False
                    divergences.append(
                        self._divergence(
                            destination, chunk.node_uid, "source_revision_mismatch"
                        )
                    )
                    continue
                if state.state != "succeeded" or state.observed_revision != chunk.source_revision:
                    chunk_consistent = False
                    divergences.append(
                        self._divergence(
                            destination,
                            chunk.node_uid,
                            f"materialization_{state.state}",
                        )
                    )
                    if repair:
                        repaired += self._requeue_failed(
                            "knowledge_graph_node", chunk.node_uid, destination
                        )
            chunk.materialization_state = "ready" if chunk_consistent else "pending"
            if chunk_consistent:
                indexed += 1

        job.chunks_indexed = indexed
        job.materializations_pending = len(divergences)
        active_files = [
            source_file
            for source_file in files
            if source_file.status not in {"rejected", "deleted"}
        ]
        if (
            not divergences
            and files
            and not active_files
            and any(source_file.status == "deleted" for source_file in files)
        ):
            job.status = "superseded"
            job.current_checkpoint = "superseded"
            job.completed_at = datetime.now(UTC)
        elif not divergences and job.status == "materialization_pending":
            job.status = "completed"
            job.current_checkpoint = "completed"
            job.completed_at = datetime.now(UTC)
            summary = dict(job.result_summary or {})
            summary["chunks_indexed"] = indexed
            summary["materializations_pending"] = 0
            job.result_summary = summary
            for source_file in files:
                if source_file.status == "materialization_pending":
                    source_file.status = "ready"
        elif divergences and job.status == "completed":
            job.status = "materialization_pending"
            job.current_checkpoint = "reconciliation_required"
            job.completed_at = None

        return {
            "ingestion_id": str(job.id),
            "status": job.status,
            "consistent": not divergences,
            "files": len(files),
            "chunks": len(chunks),
            "chunks_indexed": indexed,
            "requeued": repaired,
            "divergences": divergences,
        }

    @staticmethod
    def _divergence(destination: str, entity_id: str, reason: str) -> dict[str, str]:
        return {
            "destination": str(destination),
            "entity_id": str(entity_id),
            "reason": str(reason),
        }

    @staticmethod
    def _requeue_failed(entity_type: str, entity_id: str, destination: str) -> int:
        event = (
            CrossStoreOutboxEvent.query.filter_by(
                entity_type=entity_type,
                entity_id=entity_id,
                destination=destination,
            )
            .order_by(CrossStoreOutboxEvent.created_at.desc())
            .first()
        )
        if event is None or event.status not in {"failed", "processing"}:
            return 0
        event.status = "pending"
        event.available_at = None
        event.locked_at = None
        event.safe_reason = None
        return 1

    @staticmethod
    def _has_active_chunk_reference(
        chunk: IngestionChunk, *, excluding_file_id: UUID
    ) -> bool:
        return (
            IngestionChunk.query.join(
                IngestionFile, IngestionFile.id == IngestionChunk.file_id
            )
            .filter(
                IngestionChunk.node_uid == chunk.node_uid,
                IngestionChunk.file_id != excluding_file_id,
                IngestionFile.status.in_(("ready", "materialization_pending", "duplicate")),
            )
            .first()
            is not None
        )

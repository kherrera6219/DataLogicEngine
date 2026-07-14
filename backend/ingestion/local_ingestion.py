"""Local-first raw document ingestion into SQL knowledge nodes and Chroma."""

from __future__ import annotations

import logging
import multiprocessing
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import shutil
from typing import Any, Callable, Iterable
from uuid import UUID, uuid4
import zipfile

from flask import current_app, has_app_context

from backend.ingestion.acquisition import SecureAcquisitionSession
from extensions import db
from models import (
    IngestionAttempt,
    IngestionChunk,
    IngestionFile,
    IngestionJob,
    KnowledgeGraphNode,
)


logger = logging.getLogger(__name__)


def _bounded_binary_document_worker(
    path: str,
    mime_type: str,
    max_pages: int,
    max_archive_entries: int,
    max_decompressed_bytes: int,
    max_archive_depth: int,
    output,
) -> None:
    """Validate and parse one binary document in a terminable child process."""
    try:
        file_path = Path(path)
        if mime_type == "application/pdf":
            try:
                from pypdf import PdfReader
            except ImportError:
                import PyPDF2  # type: ignore

                PdfReader = PyPDF2.PdfReader
            reader = PdfReader(str(file_path))
            if reader.is_encrypted:
                output.put(("error", "encrypted_document_not_allowed"))
                return
            if len(reader.pages) > max_pages:
                output.put(("error", "document_page_limit_exceeded"))
                return
        elif mime_type.endswith("wordprocessingml.document"):
            if max_archive_depth < 1:
                output.put(("error", "archive_depth_exceeded"))
                return
            with zipfile.ZipFile(file_path) as archive:
                members = archive.infolist()
                if len(members) > max_archive_entries:
                    output.put(("error", "archive_entry_limit_exceeded"))
                    return
                expanded = 0
                for member in members:
                    normalized = member.filename.replace("\\", "/")
                    parts = Path(normalized).parts
                    if normalized.startswith("/") or ".." in parts:
                        output.put(("error", "archive_path_traversal"))
                        return
                    if member.flag_bits & 0x1:
                        output.put(("error", "encrypted_archive_not_allowed"))
                        return
                    expanded += int(member.file_size or 0)
                    if expanded > max_decompressed_bytes:
                        output.put(("error", "archive_decompression_limit_exceeded"))
                        return
                    if max_archive_depth <= 1 and Path(normalized).suffix.lower() in {
                        ".zip",
                        ".docx",
                        ".jar",
                    }:
                        output.put(("error", "archive_depth_exceeded"))
                        return

        from backend.services.document_processor import DocumentProcessor

        body = file_path.read_bytes()
        result = DocumentProcessor().process_file(body, file_path.name, mime_type)
        text = str(result.get("text") or "").strip()
        output.put(("ok", text))
    except Exception:
        output.put(("error", "document_parser_failed"))


class IngestionControlRequested(RuntimeError):
    """Cooperative pause/cancel signal raised at a durable checkpoint."""

    def __init__(self, action: str) -> None:
        self.action = str(action)
        super().__init__(f"ingestion_{self.action}_requested")

SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".json", ".yaml", ".yml", ".log"}
SUPPORTED_BINARY_EXTENSIONS = {".pdf", ".docx"}
SUPPORTED_EXTENSIONS = SUPPORTED_TEXT_EXTENSIONS | SUPPORTED_BINARY_EXTENSIONS


@dataclass
class RejectedFile:
    path: str
    reason: str


@dataclass
class IngestedChunk:
    node_uid: str
    node_id: str
    source_path: str
    chunk_index: int
    chunk_count: int
    content_hash: str
    chunk_hash: str
    indexed: bool
    materialization_state: str = "pending"


@dataclass
class IngestionResult:
    ingestion_id: str
    source: str
    files_scanned: int = 0
    files_ingested: int = 0
    files_rejected: int = 0
    chunks_created: int = 0
    chunks_indexed: int = 0
    materializations_pending: int = 0
    rejected_files: list[RejectedFile] = field(default_factory=list)
    chunks: list[IngestedChunk] = field(default_factory=list)
    manifest_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["rejected_files"] = [asdict(item) for item in self.rejected_files]
        payload["chunks"] = [asdict(item) for item in self.chunks]
        return payload


class LocalKnowledgeIngestionService:
    """Ingest local files into the app-owned knowledge corpus."""

    def __init__(
        self,
        *,
        rag_service: Any | None = None,
        document_processor: Any | None = None,
        chunk_size: int = 1200,
        max_file_bytes: int = 10 * 1024 * 1024,
        max_total_bytes: int = 100 * 1024 * 1024,
        max_files: int = 1000,
        max_pages: int = 500,
        max_archive_entries: int = 10_000,
        max_decompressed_bytes: int = 100 * 1024 * 1024,
        max_archive_depth: int = 1,
        parser_timeout_seconds: int = 60,
        supported_extensions: Iterable[str] | None = None,
        staging_root: str | os.PathLike[str] | None = None,
    ) -> None:
        self.rag_service = rag_service
        self.document_processor = document_processor
        self.chunk_size = int(chunk_size)
        self.max_file_bytes = int(max_file_bytes)
        self.max_total_bytes = int(max_total_bytes)
        self.max_files = int(max_files)
        self.max_pages = int(max_pages)
        self.max_archive_entries = int(max_archive_entries)
        self.max_decompressed_bytes = int(max_decompressed_bytes)
        self.max_archive_depth = int(max_archive_depth)
        self.parser_timeout_seconds = int(parser_timeout_seconds)
        if self.chunk_size <= 0:
            raise ValueError("invalid_chunk_size")
        if self.max_file_bytes <= 0:
            raise ValueError("invalid_max_file_bytes")
        if self.max_total_bytes <= 0:
            raise ValueError("invalid_max_total_bytes")
        if self.max_files <= 0:
            raise ValueError("invalid_max_files")
        if self.max_pages <= 0:
            raise ValueError("invalid_max_pages")
        if self.max_archive_entries <= 0:
            raise ValueError("invalid_max_archive_entries")
        if self.max_decompressed_bytes <= 0:
            raise ValueError("invalid_max_decompressed_bytes")
        if self.max_archive_depth < 0:
            raise ValueError("invalid_max_archive_depth")
        if self.parser_timeout_seconds <= 0:
            raise ValueError("invalid_parser_timeout_seconds")
        self.supported_extensions = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in (supported_extensions or SUPPORTED_EXTENSIONS)
        }
        self.staging_root = (
            Path(staging_root).expanduser().resolve()
            if staging_root is not None
            else None
        )

    def ingest_path(
        self,
        source_path: str | os.PathLike[str],
        *,
        recursive: bool = True,
        user_id: int | None = None,
        tenant_id: str | None = None,
        source_label: str | None = None,
        metadata: dict[str, Any] | None = None,
        ingestion_id: str | None = None,
        control_check: Callable[[], str | None] | None = None,
        progress_callback: Callable[[str, dict[str, int]], None] | None = None,
    ) -> IngestionResult:
        """Ingest one local file or directory into SQL and vector search."""
        source = Path(os.path.abspath(Path(source_path).expanduser()))
        result = IngestionResult(
            ingestion_id=str(ingestion_id or uuid4()),
            source=str(source_label or source.name),
        )
        acquisition = SecureAcquisitionSession(
            ingestion_id=result.ingestion_id,
            source=source,
            staging_root=self._acquisition_staging_root(),
            supported_extensions=self.supported_extensions,
            max_file_bytes=self.max_file_bytes,
            max_total_bytes=self.max_total_bytes,
            max_files=self.max_files,
            recursive=recursive,
        )
        job, attempt = self._start_job(
            result.ingestion_id,
            source=acquisition.source_root,
            source_digest=self._sha256(str(source).casefold()),
            recursive=recursive,
            user_id=user_id,
            tenant_id=tenant_id,
            source_label=source_label or source.name,
        )
        try:
            self._raise_if_controlled(control_check)
            acquired = acquisition.acquire()
            self._raise_if_controlled(control_check)
            job.current_checkpoint = "acquired"
            attempt.checkpoint = "acquired"
            request_options = dict(job.result_summary or {})
            preacquisition_rejected = request_options.get("_preacquisition_rejected")
            if not isinstance(preacquisition_rejected, list):
                preacquisition_rejected = []
            result.files_scanned = (
                len(acquired.files)
                + len(acquired.rejected)
                + len(preacquisition_rejected)
            )
            self._publish_progress(progress_callback, "acquired", result)
            for rejected in preacquisition_rejected:
                if not isinstance(rejected, dict):
                    continue
                relative_path = str(rejected.get("relative_path") or "unknown")
                reason = str(rejected.get("reason") or "acquisition_rejected")
                result.files_rejected += 1
                result.rejected_files.append(
                    RejectedFile(path=relative_path, reason=reason)
                )
                db.session.add(
                    IngestionFile(
                        job_id=job.id,
                        relative_path=relative_path,
                        source_path=relative_path,
                        document_uid=self._document_uid(
                            tenant_id, job.source_digest, relative_path
                        ),
                        status="rejected",
                        error_code=reason,
                    )
                )
            for rejected in acquired.rejected:
                result.files_rejected += 1
                result.rejected_files.append(
                    RejectedFile(path=rejected.relative_path, reason=rejected.reason)
                )
                db.session.add(
                    IngestionFile(
                        job_id=job.id,
                        relative_path=rejected.relative_path,
                        source_path=rejected.relative_path,
                        document_uid=self._document_uid(
                            tenant_id, job.source_digest, rejected.relative_path
                        ),
                        status="rejected",
                        error_code=rejected.reason,
                    )
                )
            if not acquired.files and not acquired.rejected:
                result.rejected_files.append(
                    RejectedFile(path=str(source_label or source.name), reason="No supported files found")
                )
                result.files_rejected = 1

            rag = self._get_rag_service()
            for acquired_file in acquired.files:
                self._raise_if_controlled(control_check)
                self._publish_progress(progress_callback, "parsing", result)
                staged_path = acquired_file.staged_path
                original_path = acquired_file.source_path
                file_record = IngestionFile(
                    job_id=job.id,
                    relative_path=acquired_file.relative_path,
                    source_path=acquired_file.relative_path,
                    document_uid=self._document_uid(
                        tenant_id, job.source_digest, acquired_file.relative_path
                    ),
                    source_revision=f"sha256:{acquired_file.sha256}",
                    source_sha256=acquired_file.sha256,
                    size_bytes=acquired_file.size_bytes,
                    detected_type=acquired_file.detected_type,
                    status="processing",
                )
                db.session.add(file_record)
                db.session.flush()
                result.materializations_pending += self._supersede_prior_revisions(
                    file_record,
                    replacement_revision=f"sha256:{acquired_file.sha256}",
                    correlation_id=result.ingestion_id,
                )
                text, rejection = self._extract_text(staged_path)
                if rejection:
                    result.files_rejected += 1
                    result.rejected_files.append(
                        RejectedFile(path=acquired_file.relative_path, reason=rejection)
                    )
                    file_record.status = "rejected"
                    file_record.error_code = rejection
                    continue

                from backend.security.content_defense import evaluate_untrusted_content

                cleaned_text, defense_result = evaluate_untrusted_content(text)
                injection_hits = list(defense_result.categories)
                file_record.defense_result = defense_result.to_dict()
                file_record.parser_result = {
                    "status": "passed",
                    "detected_type": acquired_file.detected_type,
                }
                if not defense_result.safe_for_retrieval:
                    result.files_rejected += 1
                    result.rejected_files.append(
                        RejectedFile(
                            path=acquired_file.relative_path,
                            reason="content_defense_rejected",
                        )
                    )
                    file_record.status = "rejected"
                    file_record.error_code = "content_defense_rejected"
                    continue
                chunks = (
                    rag.chunk_text(cleaned_text, chunk_size=self.chunk_size)
                    if rag
                    else [cleaned_text]
                )
                chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
                if not chunks:
                    result.files_rejected += 1
                    result.rejected_files.append(
                        RejectedFile(path=str(original_path), reason="No text after normalization")
                    )
                    file_record.status = "rejected"
                    file_record.error_code = "no_text_after_normalization"
                    continue

                from backend.storage.artifact_materialization import (
                    persist_object_artifact,
                )

                spool_dir = (
                    self._artifact_spool_root()
                    / result.ingestion_id
                    / str(file_record.id)
                ).resolve()
                expected_spool_parent = (
                    self._artifact_spool_root() / result.ingestion_id
                ).resolve()
                if spool_dir.parent != expected_spool_parent:
                    raise RuntimeError("unsafe_ingestion_artifact_spool_path")
                spool_dir.mkdir(parents=True, exist_ok=False)
                original_spool = spool_dir / f"original{staged_path.suffix.lower()}"
                normalized_spool = spool_dir / "normalized.txt"
                shutil.copy2(staged_path, original_spool)
                normalized_spool.write_text(cleaned_text, encoding="utf-8", newline="\n")

                object_reference = persist_object_artifact(
                    entity_type="ingestion_file_source",
                    entity_id=str(file_record.id),
                    bucket="knowledge-sources",
                    key=f"sources/{file_record.id}/original{staged_path.suffix.lower()}",
                    body_path=original_spool,
                    schema_version="ingestion-source.v1",
                    content_type=(
                        mimetypes.guess_type(original_path.name)[0]
                        or "application/octet-stream"
                    ),
                    metadata={
                        "ingestion_id": result.ingestion_id,
                        "source_sha256": acquired_file.sha256,
                        "relative_path": acquired_file.relative_path,
                        "retention_class": "ingested_content",
                    },
                    commit=False,
                )
                file_record.object_bucket = object_reference["bucket"]
                file_record.object_key = object_reference["key"]
                file_record.object_sha256 = object_reference["body_sha256"]
                file_record.object_status = object_reference["status"]
                if object_reference["status"] == "pending":
                    result.materializations_pending += 1

                normalized_reference = persist_object_artifact(
                    entity_type="ingestion_file_normalized",
                    entity_id=str(file_record.id),
                    bucket="knowledge-sources",
                    key=f"sources/{file_record.id}/normalized.txt",
                    body_path=normalized_spool,
                    schema_version="ingestion-normalized.v1",
                    content_type="text/plain; charset=utf-8",
                    metadata={
                        "ingestion_id": result.ingestion_id,
                        "source_sha256": acquired_file.sha256,
                        "content_sha256": self._sha256(cleaned_text),
                        "relative_path": acquired_file.relative_path,
                        "retention_class": "ingested_content",
                        "content_defense_policy": defense_result.policy_version,
                        "content_defense_disposition": defense_result.disposition,
                    },
                    commit=False,
                )
                file_record.normalized_object_bucket = normalized_reference["bucket"]
                file_record.normalized_object_key = normalized_reference["key"]
                file_record.normalized_object_sha256 = normalized_reference["body_sha256"]
                file_record.normalized_object_status = normalized_reference["status"]
                if normalized_reference["status"] == "pending":
                    result.materializations_pending += 1
                if (
                    object_reference["status"] == "ready"
                    and normalized_reference["status"] == "ready"
                ):
                    shutil.rmtree(spool_dir, ignore_errors=True)

                content_hash = self._sha256(cleaned_text)
                file_record.content_sha256 = content_hash
                embedding_revision = str(
                    getattr(rag, "embedding_revision", "unavailable") or "unavailable"
                )
                embedding_dimensions = int(
                    getattr(rag, "embedding_dimensions", 0) or 0
                )
                file_record.embedding_revision = (
                    f"{embedding_revision}:{embedding_dimensions}"
                    if embedding_dimensions
                    else embedding_revision
                )
                file_record.chunk_count = len(chunks)
                created_for_file = 0
                for index, chunk in enumerate(chunks):
                    self._raise_if_controlled(control_check)
                    chunk_hash = self._sha256(chunk)
                    document_chunk_hash = self._sha256(
                        ":".join(
                            (
                                tenant_id or "owner",
                                acquired_file.relative_path,
                                acquired_file.sha256,
                                str(index),
                                chunk_hash,
                            )
                        )
                    )
                    uid = f"ki_{document_chunk_hash[:24]}"
                    existing = KnowledgeGraphNode.query.filter_by(uid=uid).first()
                    node_id = f"KI-{document_chunk_hash[:16]}"
                    title = f"{source_label or original_path.name} [{index + 1}/{len(chunks)}]"
                    source_revision = (
                        f"sha256:{acquired_file.sha256}:{content_hash}:{chunk_hash}"
                    )
                    node_metadata = {
                        **(metadata or {}),
                        "ingestion_id": result.ingestion_id,
                        "source": "local_file_ingestion",
                        "source_path": acquired_file.relative_path,
                        "acquisition_relative_path": acquired_file.relative_path,
                        "source_file_sha256": acquired_file.sha256,
                        "source_file_size_bytes": acquired_file.size_bytes,
                        "document_uid": file_record.document_uid,
                        "source_revision": source_revision,
                        "detected_type": acquired_file.detected_type,
                        "file_name": original_path.name,
                        "mime_type": mimetypes.guess_type(original_path.name)[0] or "text/plain",
                        "content_hash": content_hash,
                        "chunk_hash": chunk_hash,
                        "chunk_index": index,
                        "chunk_count": len(chunks),
                        "prompt_injection_markers_removed": injection_hits,
                        "content_defense": defense_result.to_dict(),
                        "embedding_revision": file_record.embedding_revision,
                        "retention_class": "ingested_content",
                        "permissions": {
                            "owner_user_id": user_id,
                            "tenant_id": tenant_id,
                        },
                        "ingested_at": datetime.now(UTC).isoformat(),
                    }
                    if not existing:
                        node = KnowledgeGraphNode(
                            uid=uid,
                            node_id=node_id,
                            node_type="ingested_document_chunk",
                            label=title,
                            title=title,
                            description=chunk[:500],
                            content=chunk,
                            content_type="text/plain",
                            node_metadata=node_metadata,
                            tenant_id=tenant_id,
                        )
                        db.session.add(node)
                        created_for_file += 1
                        result.chunks_created += 1

                    from backend.storage.outbox import CrossStoreOutbox

                    material_node_metadata = (
                        dict(existing.node_metadata or {}) if existing else node_metadata
                    )
                    material_title = str(existing.title or existing.label) if existing else title
                    material_content = str(existing.content or "") if existing else chunk
                    materialization_metadata = {
                        **material_node_metadata,
                        "node_id": node_id,
                        "title": material_title,
                        "tenant_id": tenant_id or "",
                    }
                    outbox = CrossStoreOutbox(db.session)
                    chroma_event = outbox.enqueue(
                        entity_type="knowledge_graph_node",
                        entity_id=uid,
                        destination="chroma",
                        operation="upsert_knowledge_node",
                        schema_version="knowledge-node.v1",
                        source_revision=source_revision,
                        payload={
                            "node_uid": uid,
                            "content": material_content,
                            "node_type": "ingested_document_chunk",
                            "metadata": materialization_metadata,
                        },
                        correlation_id=result.ingestion_id,
                    )
                    neo4j_event = outbox.enqueue(
                        entity_type="knowledge_graph_node",
                        entity_id=uid,
                        destination="neo4j",
                        operation="merge_knowledge_node",
                        schema_version="knowledge-node.v1",
                        source_revision=source_revision,
                        payload={
                            "node_uid": uid,
                            "properties": {
                                "node_id": node_id,
                                "node_type": "ingested_document_chunk",
                                "label": material_title,
                                "title": material_title,
                                "description": material_content[:500],
                                "content": material_content,
                                "content_type": "text/plain",
                                "tenant_id": tenant_id,
                            },
                        },
                        correlation_id=result.ingestion_id,
                    )
                    events = (chroma_event, neo4j_event)
                    pending_count = sum(
                        1 for event in events if event.status != "succeeded"
                    )
                    result.materializations_pending += pending_count
                    indexed = pending_count == 0
                    if indexed:
                        result.chunks_indexed += 1
                    db.session.add(
                        IngestionChunk(
                            job_id=job.id,
                            file_id=file_record.id,
                            node_uid=uid,
                            chunk_index=index,
                            chunk_count=len(chunks),
                            content_sha256=content_hash,
                            chunk_sha256=chunk_hash,
                            source_revision=source_revision,
                            materialization_state=("ready" if indexed else "pending"),
                        )
                    )
                    result.chunks.append(
                        IngestedChunk(
                            node_uid=uid,
                            node_id=node_id,
                            source_path=acquired_file.relative_path,
                            chunk_index=index,
                            chunk_count=len(chunks),
                            content_hash=content_hash,
                            chunk_hash=chunk_hash,
                            indexed=indexed,
                            materialization_state=("ready" if indexed else "pending"),
                        )
                    )

                if created_for_file:
                    result.files_ingested += 1
                    file_record.status = "materialization_pending"
                else:
                    file_record.status = "duplicate"
                self._publish_progress(progress_callback, "materialization_queued", result)

            self._write_manifest(result)
            job.files_scanned = result.files_scanned
            job.files_ingested = result.files_ingested
            job.files_rejected = result.files_rejected
            job.chunks_created = result.chunks_created
            job.chunks_indexed = result.chunks_indexed
            job.materializations_pending = result.materializations_pending
            job.status = (
                "materialization_pending"
                if result.materializations_pending
                else "completed"
            )
            job.current_checkpoint = job.status
            job.completed_at = (
                datetime.now(UTC) if job.status == "completed" else None
            )
            job.result_summary = result.to_dict()
            attempt.status = "completed"
            attempt.checkpoint = job.current_checkpoint
            attempt.completed_at = datetime.now(UTC)
            db.session.commit()
            self._publish_progress(progress_callback, job.status, result)
            return result
        except IngestionControlRequested as exc:
            db.session.rollback()
            self._cleanup_uncommitted_artifact_spool(result.ingestion_id)
            self._mark_job_controlled(result.ingestion_id, exc.action)
            raise
        except Exception as exc:
            db.session.rollback()
            self._cleanup_uncommitted_artifact_spool(result.ingestion_id)
            self._mark_job_failed(result.ingestion_id, exc)
            raise
        finally:
            acquisition.cleanup()

    @staticmethod
    def _raise_if_controlled(
        control_check: Callable[[], str | None] | None,
    ) -> None:
        if control_check is None:
            return
        action = control_check()
        if action in {"cancel", "pause"}:
            raise IngestionControlRequested(action)

    @staticmethod
    def _publish_progress(
        callback: Callable[[str, dict[str, int]], None] | None,
        checkpoint: str,
        result: IngestionResult,
    ) -> None:
        if callback is None:
            return
        callback(
            checkpoint,
            {
                "files_scanned": result.files_scanned,
                "files_ingested": result.files_ingested,
                "files_rejected": result.files_rejected,
                "chunks_created": result.chunks_created,
                "chunks_indexed": result.chunks_indexed,
                "materializations_pending": result.materializations_pending,
            },
        )

    def _start_job(
        self,
        ingestion_id: str,
        *,
        source: Path,
        source_digest: str | None = None,
        recursive: bool,
        user_id: int | None,
        tenant_id: str | None,
        source_label: str | None,
    ) -> tuple[IngestionJob, IngestionAttempt]:
        job_uuid = UUID(str(ingestion_id))
        job = db.session.get(IngestionJob, job_uuid)
        if job is None:
            job = IngestionJob(
                id=job_uuid,
                user_id=user_id,
                tenant_id=tenant_id,
                status="queued",
                source_path=str(source),
                source_label=source_label,
                source_digest=str(source_digest or self._sha256(str(source).casefold())),
                recursive=bool(recursive),
                chunk_size=self.chunk_size,
                max_file_bytes=self.max_file_bytes,
                max_total_bytes=self.max_total_bytes,
                max_files=self.max_files,
                max_pages=self.max_pages,
                max_archive_entries=self.max_archive_entries,
                max_decompressed_bytes=self.max_decompressed_bytes,
                max_archive_depth=self.max_archive_depth,
                parser_timeout_seconds=self.parser_timeout_seconds,
                current_checkpoint="queued",
            )
            db.session.add(job)
            db.session.flush()
        job.status = "running"
        job.current_checkpoint = "acquisition"
        job.started_at = job.started_at or datetime.now(UTC)
        runtime = current_app.extensions.get("dle_runtime") if has_app_context() else None
        attempt_number = (
            IngestionAttempt.query.filter_by(job_id=job.id).count() + 1
        )
        attempt = IngestionAttempt(
            job_id=job.id,
            attempt_number=attempt_number,
            status="running",
            worker_instance_id=str(getattr(runtime, "instance_id", "") or "") or None,
            checkpoint="acquisition",
        )
        db.session.add(attempt)
        db.session.commit()
        return job, attempt

    @staticmethod
    def _mark_job_failed(ingestion_id: str, exc: Exception) -> None:
        try:
            job = db.session.get(IngestionJob, UUID(str(ingestion_id)))
            if job is None:
                return
            raw_code = str(exc).strip()
            error_code = (
                raw_code
                if re.fullmatch(r"[a-z0-9_:-]{1,120}", raw_code)
                else "ingestion_internal_failure"
            )
            job.status = "failed"
            job.current_checkpoint = "failed"
            job.last_error_code = error_code
            job.last_error_message = "Ingestion failed safely"
            job.completed_at = datetime.now(UTC)
            attempt = (
                IngestionAttempt.query.filter_by(job_id=job.id)
                .order_by(IngestionAttempt.attempt_number.desc())
                .first()
            )
            if attempt is not None:
                attempt.status = "failed"
                attempt.checkpoint = "failed"
                attempt.error_code = error_code
                attempt.error_message = "Ingestion failed safely"
                attempt.completed_at = datetime.now(UTC)
            db.session.commit()
        except Exception:
            db.session.rollback()

    @staticmethod
    def _mark_job_controlled(ingestion_id: str, action: str) -> None:
        try:
            job = db.session.get(IngestionJob, UUID(str(ingestion_id)))
            if job is None:
                return
            now = datetime.now(UTC)
            job.status = "cancelled" if action == "cancel" else "paused"
            job.current_checkpoint = job.status
            job.completed_at = now if action == "cancel" else None
            attempt = (
                IngestionAttempt.query.filter_by(job_id=job.id)
                .order_by(IngestionAttempt.attempt_number.desc())
                .first()
            )
            if attempt is not None:
                attempt.status = job.status
                attempt.checkpoint = job.status
                attempt.completed_at = now
            db.session.commit()
        except Exception:
            db.session.rollback()

    def _acquisition_staging_root(self) -> Path:
        if self.staging_root is not None:
            return self.staging_root
        explicit = os.environ.get("DATALOGIC_INGESTION_STAGING_ROOT")
        if explicit:
            return Path(explicit).expanduser().resolve()
        if has_app_context():
            runtime = current_app.extensions.get("dle_runtime")
            runtime_root = getattr(runtime, "runtime_root", None)
            if runtime_root is not None:
                return Path(runtime_root).resolve() / "staging" / "ingestion"
        raise RuntimeError("ingestion_staging_root_unavailable")

    def _artifact_spool_root(self) -> Path:
        explicit = os.environ.get("DATALOGIC_INGESTION_ARTIFACT_SPOOL_ROOT")
        root = (
            Path(explicit).expanduser().resolve()
            if explicit
            else self._acquisition_staging_root() / "artifact-spool"
        )
        return root.resolve()

    def _cleanup_uncommitted_artifact_spool(self, ingestion_id: str) -> None:
        root = self._artifact_spool_root()
        target = (root / str(UUID(str(ingestion_id)))).resolve()
        if target.parent != root:
            raise RuntimeError("unsafe_ingestion_artifact_spool_cleanup")
        shutil.rmtree(target, ignore_errors=True)

    def _get_rag_service(self) -> Any | None:
        if self.rag_service is not None:
            return self.rag_service
        try:
            from backend.services.rag_service import get_rag_service

            self.rag_service = get_rag_service()
            return self.rag_service
        except Exception:
            return None

    @classmethod
    def _document_uid(
        cls, tenant_id: str | None, source_digest: str, relative_path: str
    ) -> str:
        digest = cls._sha256(
            ":".join(
                (
                    tenant_id or "owner",
                    str(source_digest),
                    str(relative_path).casefold(),
                )
            )
        )
        return f"kidoc_{digest[:32]}"

    @staticmethod
    def _supersede_prior_revisions(
        current_file: IngestionFile,
        *,
        replacement_revision: str,
        correlation_id: str,
    ) -> int:
        """Queue deletion of every older revision for the same stable document."""
        if not current_file.document_uid:
            return 0
        prior_files = IngestionFile.query.filter(
            IngestionFile.document_uid == current_file.document_uid,
            IngestionFile.id != current_file.id,
            IngestionFile.status.in_(
                ("ready", "materialization_pending", "duplicate")
            ),
        ).all()
        pending = 0
        from backend.storage.outbox import CrossStoreOutbox

        outbox = CrossStoreOutbox(db.session)
        for prior in prior_files:
            if prior.source_sha256 == current_file.source_sha256:
                continue
            delete_revision = f"delete:{replacement_revision}"
            for chunk in IngestionChunk.query.filter_by(job_id=prior.job_id, file_id=prior.id):
                chroma_event = outbox.enqueue(
                    entity_type="knowledge_graph_node",
                    entity_id=chunk.node_uid,
                    destination="chroma",
                    operation="delete_knowledge_node",
                    schema_version="knowledge-node.v1",
                    source_revision=delete_revision,
                    payload={"node_uid": chunk.node_uid},
                    correlation_id=correlation_id,
                )
                neo4j_event = outbox.enqueue(
                    entity_type="knowledge_graph_node",
                    entity_id=chunk.node_uid,
                    destination="neo4j",
                    operation="delete_knowledge_node",
                    schema_version="knowledge-node.v1",
                    source_revision=delete_revision,
                    payload={"node_uid": chunk.node_uid},
                    correlation_id=correlation_id,
                )
                pending += sum(
                    event.status != "succeeded"
                    for event in (chroma_event, neo4j_event)
                )
                chunk.materialization_state = "deletion_pending"
            if prior.object_bucket and prior.object_key:
                object_event = outbox.enqueue(
                    entity_type="ingestion_file_source",
                    entity_id=str(prior.id),
                    destination="minio",
                    operation="delete_object",
                    schema_version="ingestion-source.v1",
                    source_revision=delete_revision,
                    payload={
                        "bucket": prior.object_bucket,
                        "key": prior.object_key,
                    },
                    correlation_id=correlation_id,
                )
                pending += object_event.status != "succeeded"
                prior.object_status = "deletion_pending"
            if prior.normalized_object_bucket and prior.normalized_object_key:
                normalized_event = outbox.enqueue(
                    entity_type="ingestion_file_normalized",
                    entity_id=str(prior.id),
                    destination="minio",
                    operation="delete_object",
                    schema_version="ingestion-normalized.v1",
                    source_revision=delete_revision,
                    payload={
                        "bucket": prior.normalized_object_bucket,
                        "key": prior.normalized_object_key,
                    },
                    correlation_id=correlation_id,
                )
                pending += normalized_event.status != "succeeded"
                prior.normalized_object_status = "deletion_pending"
            prior.status = "deletion_pending"
        return int(pending)

    def _iter_files(self, source: Path, *, recursive: bool) -> Iterable[Path]:
        if source.is_file():
            if source.suffix.lower() in self.supported_extensions:
                yield source
            return
        if not source.is_dir():
            return
        iterator = source.rglob("*") if recursive else source.glob("*")
        for file_path in iterator:
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                yield file_path

    def _extract_text(self, file_path: Path) -> tuple[str, str | None]:
        try:
            size = file_path.stat().st_size
        except OSError as exc:
            return "", f"Cannot stat file: {exc}"
        if size <= 0:
            return "", "Empty file"
        if size > self.max_file_bytes:
            return "", f"File exceeds max size of {self.max_file_bytes} bytes"

        suffix = file_path.suffix.lower()

        # Delegate binary formats to DocumentProcessor.
        if suffix in SUPPORTED_BINARY_EXTENSIONS:
            return self._extract_via_document_processor(file_path, suffix)

        # Text files: read with encoding fallback.
        try:
            return file_path.read_text(encoding="utf-8"), None
        except UnicodeDecodeError:
            try:
                return file_path.read_text(encoding="utf-8-sig"), None
            except UnicodeDecodeError:
                return file_path.read_text(encoding="latin-1"), None
        except OSError as exc:
            return "", f"Cannot read file: {exc}"

    def _extract_via_document_processor(
        self, file_path: Path, suffix: str,
    ) -> tuple[str, str | None]:
        """Extract text from binary documents using DocumentProcessor."""
        mime_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        mime_type = mime_map.get(suffix)
        if not mime_type:
            return "", f"Unsupported binary extension: {suffix}"

        if self.document_processor is None:
            context = multiprocessing.get_context("spawn")
            output = context.Queue(maxsize=1)
            process = context.Process(
                target=_bounded_binary_document_worker,
                args=(
                    str(file_path),
                    mime_type,
                    self.max_pages,
                    self.max_archive_entries,
                    self.max_decompressed_bytes,
                    self.max_archive_depth,
                    output,
                ),
                name="dle-bounded-document-parser",
                daemon=True,
            )
            process.start()
            process.join(timeout=self.parser_timeout_seconds)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                output.close()
                return "", "document_parser_timeout"
            try:
                status, value = output.get(timeout=1)
            except Exception:
                return "", "document_parser_failed"
            finally:
                output.close()
            if status != "ok":
                return "", str(value)
            return (str(value), None) if str(value).strip() else (
                "",
                "document_processor_returned_no_text",
            )

        processor = self._get_document_processor()
        if processor is None:
            return "", f"No document processor available for {suffix} files"
        try:
            file_bytes = file_path.read_bytes()
            result = processor.process_file(file_bytes, file_path.name, mime_type)
            text = result.get("text", "").strip()
            if not text:
                return "", "Document processor returned no text"
            # Check for library-missing fallback messages.
            if text.startswith("[") and "requires" in text and "library" in text:
                return "", text
            return text, None
        except ValueError as exc:
            return "", f"Document processing failed: {exc}"
        except OSError as exc:
            return "", f"Cannot read file: {exc}"

    def _get_document_processor(self) -> Any | None:
        """Lazy-load the global DocumentProcessor instance."""
        if self.document_processor is not None:
            return self.document_processor
        try:
            from backend.services.document_processor import document_processor

            self.document_processor = document_processor
            return self.document_processor
        except Exception:
            return None

    @staticmethod
    def _sha256(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _manifest_dir() -> Path:
        explicit = os.environ.get("DATALOGIC_INGESTION_MANIFEST_DIR")
        if explicit:
            return Path(explicit).expanduser().resolve()
        settings_path = os.environ.get("DATALOGIC_STORAGE_SETTINGS_PATH")
        if settings_path:
            return Path(settings_path).expanduser().resolve().parent / "ingestion" / "manifests"
        return Path.cwd() / "reports" / "ingestion"

    def _write_manifest(self, result: IngestionResult) -> None:
        manifest_dir = self._manifest_dir()
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / f"{result.ingestion_id}.json"
        result.manifest_path = str(manifest_path)
        manifest_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # KI-7: Async ingestion with background threading + Neo4j sync
    # ------------------------------------------------------------------

    def ingest_path_async(
        self,
        source_path: str | os.PathLike[str],
        *,
        recursive: bool = True,
        user_id: int | None = None,
        tenant_id: str | None = None,
        source_label: str | None = None,
        metadata: dict[str, Any] | None = None,
        sync_neo4j: bool = False,
        flask_app: Any | None = None,
    ) -> str:
        """Acquire into durable app staging, then queue without path authority."""
        ingestion_id = str(uuid4())
        source = Path(os.path.abspath(Path(source_path).expanduser()))
        app = flask_app or (
            current_app._get_current_object() if has_app_context() else None
        )
        if app is None:
            raise RuntimeError("ingestion_application_context_required")
        from backend.ingestion.jobs import get_ingestion_job_runner

        runner = get_ingestion_job_runner(app)
        staging_root = self._acquisition_staging_root()
        pending_root = staging_root / "pending"
        processing_root = staging_root / "processing"
        durable_acquisition = SecureAcquisitionSession(
            ingestion_id=ingestion_id,
            source=source,
            staging_root=pending_root,
            supported_extensions=self.supported_extensions,
            max_file_bytes=self.max_file_bytes,
            max_total_bytes=self.max_total_bytes,
            max_files=self.max_files,
            recursive=recursive,
        )
        acquired = durable_acquisition.acquire()
        request_options: dict[str, Any] = {
            "_request_metadata": dict(metadata or {}),
            "_sync_neo4j": bool(sync_neo4j),
            "_preacquired": True,
            "_staging_root": str(processing_root),
            "_durable_staging_session": str(durable_acquisition.session_root),
            "_preacquisition_rejected": [
                {
                    "relative_path": item.relative_path,
                    "reason": item.reason,
                }
                for item in acquired.rejected
            ],
        }
        job = IngestionJob(
            id=UUID(ingestion_id),
            user_id=user_id,
            tenant_id=tenant_id,
            status="queued",
            source_path=str(durable_acquisition.source_root),
            source_label=source_label or source.name,
            source_digest=self._sha256(str(source).casefold()),
            recursive=bool(recursive),
            chunk_size=self.chunk_size,
            max_file_bytes=self.max_file_bytes,
            max_total_bytes=self.max_total_bytes,
            max_files=self.max_files,
            max_pages=self.max_pages,
            max_archive_entries=self.max_archive_entries,
            max_decompressed_bytes=self.max_decompressed_bytes,
            max_archive_depth=self.max_archive_depth,
            parser_timeout_seconds=self.parser_timeout_seconds,
            current_checkpoint="queued",
            result_summary=request_options,
        )
        try:
            db.session.add(job)
            db.session.commit()
        except Exception:
            db.session.rollback()
            durable_acquisition.cleanup()
            raise
        worker_service = LocalKnowledgeIngestionService(
            rag_service=self.rag_service,
            document_processor=self.document_processor,
            chunk_size=self.chunk_size,
            max_file_bytes=self.max_file_bytes,
            max_total_bytes=self.max_total_bytes,
            max_files=self.max_files,
            max_pages=self.max_pages,
            max_archive_entries=self.max_archive_entries,
            max_decompressed_bytes=self.max_decompressed_bytes,
            max_archive_depth=self.max_archive_depth,
            parser_timeout_seconds=self.parser_timeout_seconds,
            supported_extensions=self.supported_extensions,
            staging_root=processing_root,
        )
        runner.submit(ingestion_id, service=worker_service)
        return ingestion_id

    @staticmethod
    def get_async_status(ingestion_id: str) -> dict[str, Any] | None:
        """Return status from the PostgreSQL job authority."""
        try:
            job_id = UUID(str(ingestion_id))
        except (TypeError, ValueError):
            return None
        job = db.session.get(IngestionJob, job_id)
        return job.to_status_dict() if job is not None else None

    @staticmethod
    def _sync_to_neo4j() -> dict[str, Any] | None:
        """Run idempotent SQL→Neo4j sync after ingestion."""
        try:
            from scripts.sync_nodes_to_neo4j import sync

            return sync()
        except Exception as exc:
            logger.warning("Post-ingestion Neo4j sync failed: %s", exc)
            return {"error": str(exc)}

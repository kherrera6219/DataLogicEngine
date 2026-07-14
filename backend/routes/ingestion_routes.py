"""Local-first knowledge ingestion API routes."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
from uuid import UUID

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user

from backend.auth.api_decorators import api_session_login_required
from backend.ingestion import LocalKnowledgeIngestionService
from backend.security.desktop_ipc import require_desktop_ipc_capability
from backend.utils.error_normalization import normalize_public_error_message
from extensions import db
from models import (
    CrossStoreMaterializationState,
    IngestionChunk,
    IngestionFile,
    IngestionJob,
)


ingestion_api = Blueprint("ingestion_api", __name__, url_prefix="/api/v1/ingestion")

DEFAULT_CHUNK_SIZE = 1200
DEFAULT_MAX_FILE_BYTES = 10 * 1024 * 1024
DEFAULT_MAX_TOTAL_BYTES = 100 * 1024 * 1024
DEFAULT_MAX_FILES = 1000
DEFAULT_MAX_PAGES = 500
DEFAULT_MAX_ARCHIVE_ENTRIES = 10_000
DEFAULT_MAX_DECOMPRESSED_BYTES = 100 * 1024 * 1024
DEFAULT_MAX_ARCHIVE_DEPTH = 1
DEFAULT_PARSER_TIMEOUT_SECONDS = 60


def _is_desktop_mode() -> bool:
    return os.environ.get("IS_DESKTOP_APP", "false").lower() in {"1", "true", "yes", "on"}


def _resolve_allowed_source(raw_path: str) -> Path:
    # Preserve the lexical source for acquisition-time link/reparse checks.
    source = Path(os.path.abspath(Path(raw_path).expanduser()))
    if _is_desktop_mode():
        return source

    root = Path(os.environ.get("DATALOGIC_INGESTION_ROOT", Path.cwd())).expanduser().resolve()
    resolved_source = source.resolve()
    if resolved_source != root and root not in resolved_source.parents:
        raise ValueError(f"Source path must stay under {root}")
    return source


def _read_manifest(path: Path) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    payload.setdefault("manifest_path", str(path))
    return payload


def _bounded_int(
    payload: dict,
    name: str,
    default: int,
    *,
    minimum: int,
    maximum: int,
) -> int:
    if name not in payload:
        return default
    try:
        value = int(payload[name])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{name}") from exc
    if value < minimum or value > maximum:
        raise ValueError(f"invalid_{name}")
    return value


def _job_file_states(job: IngestionJob, *, limit: int = 100) -> list[dict]:
    """Return bounded, content-free per-file and per-store progress."""
    files = (
        IngestionFile.query.filter_by(job_id=job.id)
        .order_by(IngestionFile.created_at, IngestionFile.relative_path)
        .limit(max(1, min(int(limit), 100)))
        .all()
    )
    file_ids = [item.id for item in files]
    chunks = (
        IngestionChunk.query.filter(IngestionChunk.file_id.in_(file_ids)).all()
        if file_ids
        else []
    )
    chunk_ids_by_file: dict[UUID, list[str]] = {}
    for chunk in chunks:
        chunk_ids_by_file.setdefault(chunk.file_id, []).append(chunk.node_uid)
    node_uids = [chunk.node_uid for chunk in chunks]
    states = (
        CrossStoreMaterializationState.query.filter(
            CrossStoreMaterializationState.entity_type == "knowledge_graph_node",
            CrossStoreMaterializationState.entity_id.in_(node_uids),
        ).all()
        if node_uids
        else []
    )
    state_by_node_destination = {
        (state.entity_id, state.destination): state.state for state in states
    }

    payload: list[dict] = []
    for source_file in files:
        file_nodes = chunk_ids_by_file.get(source_file.id, [])

        def destination_status(destination: str) -> str:
            if not file_nodes:
                return "not_applicable" if source_file.status == "rejected" else "pending"
            observed = {
                state_by_node_destination.get((node_uid, destination), "pending")
                for node_uid in file_nodes
            }
            return observed.pop() if len(observed) == 1 else "partial"

        payload.append(
            {
                "relative_path": source_file.relative_path,
                "status": source_file.status,
                "source_revision": source_file.source_revision,
                "detected_type": source_file.detected_type,
                "parser_result": source_file.parser_result,
                "defense_result": source_file.defense_result,
                "object_status": source_file.object_status,
                "normalized_object_status": source_file.normalized_object_status,
                "embedding_revision": source_file.embedding_revision,
                "vector_status": destination_status("chroma"),
                "graph_status": destination_status("neo4j"),
                "last_retrieved_at": (
                    source_file.last_retrieved_at.isoformat()
                    if source_file.last_retrieved_at
                    else None
                ),
                "last_retrieval_trace_id": source_file.last_retrieval_trace_id,
                "error_code": source_file.error_code,
            }
        )
    return payload


def _job_history_payload(job: IngestionJob) -> dict:
    payload = job.to_history_dict()
    payload["files"] = _job_file_states(job)
    return payload


@ingestion_api.route("/supported", methods=["GET"])
@api_session_login_required
def get_supported_ingestion_types():
    """Return supported local ingestion file types and defaults."""
    from backend.ingestion.local_ingestion import SUPPORTED_EXTENSIONS

    return jsonify(
        {
            "success": True,
            "data": {
                "extensions": sorted(SUPPORTED_EXTENSIONS),
                "default_chunk_size": DEFAULT_CHUNK_SIZE,
                "default_max_file_bytes": DEFAULT_MAX_FILE_BYTES,
                "default_max_total_bytes": DEFAULT_MAX_TOTAL_BYTES,
                "default_max_files": DEFAULT_MAX_FILES,
                "default_max_pages": DEFAULT_MAX_PAGES,
                "default_max_archive_entries": DEFAULT_MAX_ARCHIVE_ENTRIES,
                "default_max_decompressed_bytes": DEFAULT_MAX_DECOMPRESSED_BYTES,
                "default_max_archive_depth": DEFAULT_MAX_ARCHIVE_DEPTH,
                "default_parser_timeout_seconds": DEFAULT_PARSER_TIMEOUT_SECONDS,
            },
        }
    )


@ingestion_api.route("/history", methods=["GET"])
@api_session_login_required
def list_ingestion_history():
    """Return PostgreSQL-authoritative jobs plus retained legacy manifests."""
    try:
        requested_limit = int(request.args.get("limit", 20))
    except (TypeError, ValueError):
        requested_limit = 20
    limit = max(1, min(requested_limit, 100))
    jobs = (
        IngestionJob.query.order_by(IngestionJob.created_at.desc())
        .limit(limit)
        .all()
    )
    items = [_job_history_payload(job) for job in jobs]
    if len(items) >= limit:
        return jsonify({"success": True, "data": {"items": items}})

    manifest_dir = LocalKnowledgeIngestionService._manifest_dir()
    if not manifest_dir.exists():
        return jsonify({"success": True, "data": {"items": items}})
    known_ids = {str(item.get("ingestion_id") or "") for item in items}
    manifests = sorted(
        manifest_dir.glob("*.json"),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    )
    for path in manifests:
        item = _read_manifest(path)
        if not item or str(item.get("ingestion_id") or "") in known_ids:
            continue
        items.append(item)
        if len(items) >= limit:
            break
    return jsonify({"success": True, "data": {"items": items}})


@ingestion_api.route("/local", methods=["POST"])
@api_session_login_required
def ingest_local_path():
    """Ingest a local file or folder into the knowledge corpus."""
    capability_error = require_desktop_ipc_capability("ingestion")
    if capability_error:
        return capability_error
    data = request.get_json(silent=True) or {}
    raw_path = str(data.get("path") or "").strip()
    if not raw_path:
        return jsonify({"success": False, "error": "path is required"}), 400

    try:
        source = _resolve_allowed_source(raw_path)
        service = LocalKnowledgeIngestionService(
            chunk_size=_bounded_int(
                data, "chunk_size", DEFAULT_CHUNK_SIZE, minimum=1, maximum=100_000
            ),
            max_file_bytes=_bounded_int(
                data,
                "max_file_bytes",
                DEFAULT_MAX_FILE_BYTES,
                minimum=1,
                maximum=100 * 1024 * 1024,
            ),
            max_total_bytes=_bounded_int(
                data,
                "max_total_bytes",
                DEFAULT_MAX_TOTAL_BYTES,
                minimum=1,
                maximum=1024 * 1024 * 1024,
            ),
            max_files=_bounded_int(
                data, "max_files", DEFAULT_MAX_FILES, minimum=1, maximum=10_000
            ),
            max_pages=_bounded_int(
                data, "max_pages", DEFAULT_MAX_PAGES, minimum=1, maximum=10_000
            ),
            max_archive_entries=_bounded_int(
                data,
                "max_archive_entries",
                DEFAULT_MAX_ARCHIVE_ENTRIES,
                minimum=1,
                maximum=100_000,
            ),
            max_decompressed_bytes=_bounded_int(
                data,
                "max_decompressed_bytes",
                DEFAULT_MAX_DECOMPRESSED_BYTES,
                minimum=1,
                maximum=2 * 1024 * 1024 * 1024,
            ),
            max_archive_depth=_bounded_int(
                data,
                "max_archive_depth",
                DEFAULT_MAX_ARCHIVE_DEPTH,
                minimum=0,
                maximum=3,
            ),
            parser_timeout_seconds=_bounded_int(
                data,
                "parser_timeout_seconds",
                DEFAULT_PARSER_TIMEOUT_SECONDS,
                minimum=1,
                maximum=300,
            ),
        )
        result = service.ingest_path(
            source,
            recursive=bool(data.get("recursive", True)),
            user_id=getattr(current_user, "id", None),
            tenant_id=getattr(current_user, "tenant_id", None),
            source_label=data.get("source_label"),
            metadata=data.get("metadata") if isinstance(data.get("metadata"), dict) else None,
        )
        return jsonify({"success": True, "data": result.to_dict()}), 201
    except ValueError as exc:
        return jsonify({
            "success": False,
            "error": normalize_public_error_message(str(exc), "Invalid ingestion path"),
        }), 400
    except Exception:
        return jsonify({"success": False, "error": "Local ingestion failed"}), 500


@ingestion_api.route("/local/async", methods=["POST"])
@api_session_login_required
def ingest_local_path_async():
    """Start ingestion in the background and return the ingestion_id immediately."""
    capability_error = require_desktop_ipc_capability("ingestion")
    if capability_error:
        return capability_error
    data = request.get_json(silent=True) or {}
    raw_path = str(data.get("path") or "").strip()
    if not raw_path:
        return jsonify({"success": False, "error": "path is required"}), 400

    try:
        source = _resolve_allowed_source(raw_path)
        service = LocalKnowledgeIngestionService(
            chunk_size=_bounded_int(
                data, "chunk_size", DEFAULT_CHUNK_SIZE, minimum=1, maximum=100_000
            ),
            max_file_bytes=_bounded_int(
                data,
                "max_file_bytes",
                DEFAULT_MAX_FILE_BYTES,
                minimum=1,
                maximum=100 * 1024 * 1024,
            ),
            max_total_bytes=_bounded_int(
                data,
                "max_total_bytes",
                DEFAULT_MAX_TOTAL_BYTES,
                minimum=1,
                maximum=1024 * 1024 * 1024,
            ),
            max_files=_bounded_int(
                data, "max_files", DEFAULT_MAX_FILES, minimum=1, maximum=10_000
            ),
            max_pages=_bounded_int(
                data, "max_pages", DEFAULT_MAX_PAGES, minimum=1, maximum=10_000
            ),
            max_archive_entries=_bounded_int(
                data,
                "max_archive_entries",
                DEFAULT_MAX_ARCHIVE_ENTRIES,
                minimum=1,
                maximum=100_000,
            ),
            max_decompressed_bytes=_bounded_int(
                data,
                "max_decompressed_bytes",
                DEFAULT_MAX_DECOMPRESSED_BYTES,
                minimum=1,
                maximum=2 * 1024 * 1024 * 1024,
            ),
            max_archive_depth=_bounded_int(
                data,
                "max_archive_depth",
                DEFAULT_MAX_ARCHIVE_DEPTH,
                minimum=0,
                maximum=3,
            ),
            parser_timeout_seconds=_bounded_int(
                data,
                "parser_timeout_seconds",
                DEFAULT_PARSER_TIMEOUT_SECONDS,
                minimum=1,
                maximum=300,
            ),
        )
        ingestion_id = service.ingest_path_async(
            source,
            recursive=bool(data.get("recursive", True)),
            user_id=getattr(current_user, "id", None),
            tenant_id=getattr(current_user, "tenant_id", None),
            source_label=data.get("source_label"),
            metadata=data.get("metadata") if isinstance(data.get("metadata"), dict) else None,
            sync_neo4j=bool(data.get("sync_neo4j", False)),
            flask_app=current_app._get_current_object(),
        )
        return jsonify({"success": True, "data": {"ingestion_id": ingestion_id, "status": "queued"}}), 202
    except ValueError as exc:
        return jsonify({
            "success": False,
            "error": normalize_public_error_message(str(exc), "Invalid ingestion path"),
        }), 400
    except Exception:
        return jsonify({"success": False, "error": "Failed to start async ingestion"}), 500


@ingestion_api.route("/status/<ingestion_id>", methods=["GET"])
@api_session_login_required
def get_ingestion_status(ingestion_id: str):
    """Return the status of an async ingestion run."""
    status = LocalKnowledgeIngestionService.get_async_status(ingestion_id)
    if status is None:
        return jsonify({"success": False, "error": "Ingestion run not found"}), 404
    job = _load_ingestion_job(ingestion_id)
    if job is not None:
        status["files"] = _job_file_states(job)
        try:
            from backend.ingestion.jobs import get_ingestion_job_runner

            live_state = get_ingestion_job_runner(
                current_app._get_current_object()
            ).coordination_state(ingestion_id)
        except Exception:
            live_state = None
        if live_state:
            status["checkpoint"] = live_state.get("checkpoint") or status.get("checkpoint")
            for name in (
                "files_scanned",
                "files_ingested",
                "files_rejected",
                "chunks_created",
                "chunks_indexed",
                "materializations_pending",
            ):
                if name in live_state:
                    status[name] = int(live_state[name])
    return jsonify({"success": True, "data": status})


def _load_ingestion_job(ingestion_id: str) -> IngestionJob | None:
    try:
        job_id = UUID(str(ingestion_id))
    except (TypeError, ValueError):
        return None
    return db.session.get(IngestionJob, job_id)


@ingestion_api.route("/jobs/<ingestion_id>/cancel", methods=["POST"])
@api_session_login_required
def cancel_ingestion_job(ingestion_id: str):
    """Request durable cooperative cancellation."""
    job = _load_ingestion_job(ingestion_id)
    if job is None:
        return jsonify({"success": False, "error": "Ingestion run not found"}), 404
    if job.status not in {"queued", "running", "paused"}:
        return jsonify({"success": False, "error": "Ingestion run is not cancellable"}), 409
    from backend.ingestion.jobs import get_ingestion_job_runner

    runner = get_ingestion_job_runner(current_app._get_current_object())
    runner.cancel(job)
    if job.status in {"queued", "paused"}:
        job.status = "cancelled"
        job.current_checkpoint = "cancelled"
        job.completed_at = datetime.now(UTC)
    db.session.commit()
    return jsonify({"success": True, "data": job.to_status_dict()}), 202


@ingestion_api.route("/jobs/<ingestion_id>/pause", methods=["POST"])
@api_session_login_required
def pause_ingestion_job(ingestion_id: str):
    """Request a durable pause at the next safe checkpoint."""
    job = _load_ingestion_job(ingestion_id)
    if job is None:
        return jsonify({"success": False, "error": "Ingestion run not found"}), 404
    if job.status not in {"queued", "running"}:
        return jsonify({"success": False, "error": "Ingestion run is not pausable"}), 409
    from backend.ingestion.jobs import get_ingestion_job_runner

    runner = get_ingestion_job_runner(current_app._get_current_object())
    runner.pause(job)
    if job.status == "queued":
        job.status = "paused"
        job.current_checkpoint = "paused"
    db.session.commit()
    return jsonify({"success": True, "data": job.to_status_dict()}), 202


def _resume_or_retry_ingestion(ingestion_id: str, allowed: set[str]):
    job = _load_ingestion_job(ingestion_id)
    if job is None:
        return jsonify({"success": False, "error": "Ingestion run not found"}), 404
    if job.status not in allowed:
        return jsonify({"success": False, "error": "Ingestion run cannot be restarted"}), 409
    from backend.ingestion.jobs import get_ingestion_job_runner

    get_ingestion_job_runner(current_app._get_current_object()).resume(job)
    return jsonify({"success": True, "data": job.to_status_dict()}), 202


@ingestion_api.route("/jobs/<ingestion_id>/resume", methods=["POST"])
@api_session_login_required
def resume_ingestion_job(ingestion_id: str):
    """Resume an owner-paused ingestion job idempotently."""
    return _resume_or_retry_ingestion(ingestion_id, {"paused"})


@ingestion_api.route("/jobs/<ingestion_id>/retry", methods=["POST"])
@api_session_login_required
def retry_ingestion_job(ingestion_id: str):
    """Retry a safely failed or cancelled ingestion job."""
    return _resume_or_retry_ingestion(ingestion_id, {"failed", "cancelled"})


@ingestion_api.route("/corpus/consistency", methods=["GET"])
@api_session_login_required
def scan_ingestion_corpus():
    """Return real PostgreSQL-to-store revision consistency."""
    from backend.ingestion.reconciliation import IngestionCorpusReconciler

    report = IngestionCorpusReconciler().scan()
    return jsonify({"success": True, "data": report})


@ingestion_api.route("/jobs/<ingestion_id>/repair", methods=["POST"])
@api_session_login_required
def repair_ingestion_job(ingestion_id: str):
    """Requeue retained failed materializations for one ingestion job."""
    job = _load_ingestion_job(ingestion_id)
    if job is None:
        return jsonify({"success": False, "error": "Ingestion run not found"}), 404
    from backend.ingestion.reconciliation import IngestionCorpusReconciler

    report = IngestionCorpusReconciler().scan(job_id=job.id, repair=True)
    return jsonify({"success": True, "data": report}), 202


@ingestion_api.route("/jobs/<ingestion_id>/delete", methods=["POST"])
@api_session_login_required
def delete_ingestion_job(ingestion_id: str):
    """Delete one ingested source revision from every retained store."""
    job = _load_ingestion_job(ingestion_id)
    if job is None:
        return jsonify({"success": False, "error": "Ingestion run not found"}), 404
    if job.status not in {"completed", "materialization_pending", "failed"}:
        return jsonify({"success": False, "error": "Ingestion run is not deletable"}), 409
    from backend.ingestion.reconciliation import IngestionCorpusReconciler

    result = IngestionCorpusReconciler().request_delete(job)
    return jsonify({"success": True, "data": result}), 202

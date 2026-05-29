"""Local-first knowledge ingestion API routes."""

from __future__ import annotations

import json
import os
from pathlib import Path

from flask import Blueprint, jsonify, request
from flask_login import current_user

from backend.auth.api_decorators import api_session_login_required
from backend.ingestion import LocalKnowledgeIngestionService


ingestion_api = Blueprint("ingestion_api", __name__, url_prefix="/api/v1/ingestion")


def _is_desktop_mode() -> bool:
    return os.environ.get("IS_DESKTOP_APP", "false").lower() in {"1", "true", "yes", "on"}


def _resolve_allowed_source(raw_path: str) -> Path:
    source = Path(raw_path).expanduser().resolve()
    if _is_desktop_mode():
        return source

    root = Path(os.environ.get("DATALOGIC_INGESTION_ROOT", Path.cwd())).expanduser().resolve()
    if source != root and not str(source).startswith(str(root) + os.sep):
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


@ingestion_api.route("/supported", methods=["GET"])
@api_session_login_required
def get_supported_ingestion_types():
    """Return supported local ingestion file types and defaults."""
    from backend.ingestion.local_ingestion import SUPPORTED_TEXT_EXTENSIONS

    return jsonify(
        {
            "success": True,
            "data": {
                "extensions": sorted(SUPPORTED_TEXT_EXTENSIONS),
                "default_chunk_size": 1200,
                "default_max_file_bytes": 10 * 1024 * 1024,
            },
        }
    )


@ingestion_api.route("/history", methods=["GET"])
@api_session_login_required
def list_ingestion_history():
    """Return recent local ingestion manifests."""
    try:
        requested_limit = int(request.args.get("limit", 20))
    except (TypeError, ValueError):
        requested_limit = 20
    limit = max(1, min(requested_limit, 100))
    manifest_dir = LocalKnowledgeIngestionService._manifest_dir()
    if not manifest_dir.exists():
        return jsonify({"success": True, "data": {"items": []}})

    manifests = sorted(
        manifest_dir.glob("*.json"),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    )
    items = [item for path in manifests[:limit] if (item := _read_manifest(path))]
    return jsonify({"success": True, "data": {"items": items}})


@ingestion_api.route("/local", methods=["POST"])
@api_session_login_required
def ingest_local_path():
    """Ingest a local file or folder into the knowledge corpus."""
    data = request.get_json(silent=True) or {}
    raw_path = str(data.get("path") or "").strip()
    if not raw_path:
        return jsonify({"success": False, "error": "path is required"}), 400

    try:
        source = _resolve_allowed_source(raw_path)
        service = LocalKnowledgeIngestionService(
            chunk_size=int(data.get("chunk_size") or 1200),
            max_file_bytes=int(data.get("max_file_bytes") or 10 * 1024 * 1024),
        )
        result = service.ingest_path(
            source,
            recursive=bool(data.get("recursive", True)),
            tenant_id=getattr(current_user, "tenant_id", None),
            source_label=data.get("source_label"),
            metadata=data.get("metadata") if isinstance(data.get("metadata"), dict) else None,
        )
        return jsonify({"success": True, "data": result.to_dict()}), 201
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception:
        return jsonify({"success": False, "error": "Local ingestion failed"}), 500

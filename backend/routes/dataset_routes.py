"""REST API endpoints for Training Dataset Exporter."""

from __future__ import annotations

import logging
import math
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, jsonify, request

from backend.auth.api_decorators import api_admin_required
from backend.dataset_exporter import DatasetExporter, ParquetWriter
from backend.runtime.application import get_application_runtime
from extensions import db

logger = logging.getLogger(__name__)

dataset_bp = Blueprint("dataset_api", __name__, url_prefix="/api/v1/dataset")


@dataset_bp.route("/export", methods=["POST"])
@api_admin_required
def export_dataset_endpoint():
    """Create a bounded export in the app-owned runtime dataset directory."""
    try:
        body = request.get_json(silent=True)
        if body is None:
            body = {}
        if not isinstance(body, dict):
            raise TypeError("Request body must be a JSON object.")
        if "output_path" in body:
            raise ValueError("output_path is managed by the application and cannot be overridden.")

        export_type = str(body.get("export_type", "sft")).lower()
        format_type = str(body.get("format_type", "parquet")).lower()
        min_confidence = float(body.get("min_confidence", 0.98))
        limit = int(body.get("limit", 1000))
        if export_type not in {"sft", "prm"}:
            raise ValueError("export_type must be 'sft' or 'prm'; DPO requires stored preference evidence.")
        if format_type not in {"parquet", "jsonl"}:
            raise ValueError("format_type must be 'parquet' or 'jsonl'.")
        if not math.isfinite(min_confidence) or not 0.0 <= min_confidence <= 1.0:
            raise ValueError("min_confidence must be a finite number from 0.0 through 1.0.")
        if isinstance(body.get("limit", 1000), bool) or not 1 <= limit <= 10_000:
            raise ValueError("limit must be an integer from 1 through 10000.")

        dataset_root = get_application_runtime().runtime_root / "datasets"
        artifact_name = f"{export_type}-{uuid4().hex}.{format_type}"

        result = DatasetExporter.export_from_db(
            db_session=db.session,
            export_type=export_type,
            output_path=artifact_name,
            min_confidence=min_confidence,
            format_type=format_type,
            limit=limit,
            base_dir=dataset_root,
        )
        written_name = Path(result.pop("output_path")).name
        result["artifact_name"] = written_name

        return jsonify(result), 200

    except (TypeError, ValueError) as exc:
        return jsonify({"status": "error", "error": "invalid_parameter", "message": str(exc)}), 400
    except Exception:
        logger.exception("Dataset export API endpoint failed")
        return jsonify({"status": "error", "error": "export_failed", "message": "Dataset export failed."}), 500


@dataset_bp.route("/stats", methods=["GET"])
@api_admin_required
def dataset_stats_endpoint():
    """Return dataset export status and high-confidence candidate counts."""
    try:
        from models import TraceRun

        total_runs = db.session.query(TraceRun).count()
        qualified_runs = (
            db.session.query(TraceRun)
            .filter(
                TraceRun.confidence >= 0.98,
                TraceRun.status.in_(("completed", "succeeded", "success")),
                TraceRun.truthgate_decision.in_(("allow", "release")),
                TraceRun.input_message.isnot(None),
                TraceRun.final_answer.isnot(None),
            )
            .count()
        )

        return jsonify(
            {
                "status": "active",
                "total_trace_runs": total_runs,
                "release_candidate_runs": qualified_runs,
                "supported_types": ["sft", "prm"],
                "supported_formats": ["parquet", "jsonl"],
                "pyarrow_available": ParquetWriter.is_pyarrow_available(),
                "redaction_enforced": True,
            }
        ), 200
    except Exception:
        logger.exception("Dataset stats endpoint failed")
        return jsonify({"status": "error", "message": "Dataset statistics are unavailable."}), 500

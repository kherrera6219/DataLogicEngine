"""REST API endpoints for Training Dataset Exporter."""

from __future__ import annotations

import logging
import math
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, jsonify, request

from backend.auth.api_decorators import (
    api_admin_required,
    get_authenticated_principal,
)
from backend.dataset_exporter import DatasetExporter, ParquetWriter
from backend.llm_gateway.model_lifecycle import (
    ProviderModelLifecycleError,
    ProviderModelLifecycleService,
)
from backend.runtime.application import get_application_runtime
from extensions import db

logger = logging.getLogger(__name__)

dataset_bp = Blueprint("dataset_api", __name__, url_prefix="/api/v1/dataset")


def _model_lifecycle_service() -> ProviderModelLifecycleService:
    runtime_root = get_application_runtime().runtime_root
    return ProviderModelLifecycleService(
        dataset_root=runtime_root / "datasets",
        admission_root=runtime_root / "model-training-admissions",
    )


def _principal_id() -> str:
    principal = get_authenticated_principal()
    value = str(getattr(principal, "id", "") or "").strip()
    if not value:
        raise ProviderModelLifecycleError(
            "Authenticated principal is required"
        )
    return value


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

    except (TypeError, ValueError):
        return jsonify({"status": "error", "error": "invalid_parameter", "message": "Invalid export parameters."}), 400
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


@dataset_bp.route("/training-admissions", methods=["POST"])
@api_admin_required
def create_training_admission_endpoint():
    """Record an idempotent model-training admission without claiming execution."""
    try:
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise ProviderModelLifecycleError(
                "Request body must be a JSON object"
            )
        idempotency_key = str(
            request.headers.get("Idempotency-Key") or ""
        ).strip()
        request_id = str(
            request.headers.get("X-Request-ID") or uuid4()
        ).strip()
        admission = _model_lifecycle_service().submit_training_admission(
            artifact_name=str(body.get("artifact_name") or ""),
            export_type=str(body.get("export_type") or ""),
            model_name=str(body.get("model_name") or ""),
            epochs=body.get("epochs"),
            hyperparameters=body.get("hyperparameters") or {},
            parameter_space=body.get("parameter_space") or {},
            tuning_observations=body.get("tuning_observations") or [],
            idempotency_key=idempotency_key,
            request_id=request_id,
            principal_id=_principal_id(),
        )
        return jsonify(admission), 201
    except ProviderModelLifecycleError as exc:
        return jsonify(
            {
                "status": "error",
                "error": "training_admission_rejected",
                "message": str(exc),
            }
        ), 400
    except (TypeError, ValueError):
        return jsonify(
            {
                "status": "error",
                "error": "training_admission_rejected",
                "message": "Invalid request parameter or payload format.",
            }
        ), 400
    except Exception:
        logger.exception("Model training admission failed")
        return jsonify(
            {
                "status": "error",
                "error": "training_admission_failed",
                "message": "Model training admission failed.",
            }
        ), 500


@dataset_bp.route("/evaluations", methods=["POST"])
@api_admin_required
def evaluate_model_endpoint():
    """Evaluate caller-supplied predictions and labels without inference."""
    try:
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise ProviderModelLifecycleError(
                "Request body must be a JSON object"
            )
        request_id = str(
            request.headers.get("X-Request-ID") or uuid4()
        ).strip()
        evaluation = _model_lifecycle_service().evaluate_model(
            model_id=str(body.get("model_id") or ""),
            test_set=str(body.get("test_set") or ""),
            predictions=body.get("predictions") or [],
            labels=body.get("labels") or [],
            acceptance_accuracy=body.get("acceptance_accuracy", 0.8),
            request_id=request_id,
            principal_id=_principal_id(),
        )
        return jsonify(evaluation), 200
    except ProviderModelLifecycleError as exc:
        return jsonify(
            {
                "status": "error",
                "error": "evaluation_rejected",
                "message": str(exc),
            }
        ), 400
    except (TypeError, ValueError):
        return jsonify(
            {
                "status": "error",
                "error": "evaluation_rejected",
                "message": "Invalid request parameter or payload format.",
            }
        ), 400
    except Exception:
        logger.exception("Measured model evaluation failed")
        return jsonify(
            {
                "status": "error",
                "error": "evaluation_failed",
                "message": "Measured model evaluation failed.",
            }
        ), 500


@dataset_bp.route("/release-preparations", methods=["POST"])
@api_admin_required
def create_release_preparation_endpoint():
    """Record bounded model release preparation without claiming deployment."""
    try:
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise ProviderModelLifecycleError(
                "Request body must be a JSON object"
            )
        idempotency_key = str(
            request.headers.get("Idempotency-Key") or ""
        ).strip()
        request_id = str(
            request.headers.get("X-Request-ID") or uuid4()
        ).strip()
        preparation = _model_lifecycle_service().submit_release_preparation(
            artifact_name=str(body.get("artifact_name") or ""),
            current_version=str(body.get("current_version") or ""),
            increment=str(body.get("increment") or "patch"),
            source_commit=(
                str(body["source_commit"])
                if body.get("source_commit") is not None
                else None
            ),
            release_channel=str(body.get("release_channel") or "candidate"),
            target_environment=str(body.get("target_environment") or ""),
            parameter_count=body.get("parameter_count"),
            target_sparsity=body.get("target_sparsity"),
            pruning_method=str(
                body.get("pruning_method") or "magnitude_unstructured"
            ),
            importance_profile_sha256=body.get("importance_profile_sha256"),
            source_bit_depth=body.get("source_bit_depth", 32),
            target_bit_depth=body.get("target_bit_depth", 8),
            target_format=str(body.get("target_format") or "onnx"),
            calibration_profile_sha256=body.get(
                "calibration_profile_sha256"
            ),
            experiment_id=str(body.get("experiment_id") or ""),
            traffic_split_percent=body.get("traffic_split_percent") or {},
            experiment_observations=(
                body.get("experiment_observations") or {}
            ),
            min_sample_size=body.get("min_sample_size", 1_000),
            health_observation=body.get("health_observation") or {},
            idempotency_key=idempotency_key,
            request_id=request_id,
            principal_id=_principal_id(),
        )
        return jsonify(preparation), 201
    except ProviderModelLifecycleError as exc:
        return jsonify(
            {
                "status": "error",
                "error": "release_preparation_rejected",
                "message": str(exc),
            }
        ), 400
    except (TypeError, ValueError):
        return jsonify(
            {
                "status": "error",
                "error": "release_preparation_rejected",
                "message": "Invalid request parameter or payload format.",
            }
        ), 400
    except Exception:
        logger.exception("Model release preparation failed")
        return jsonify(
            {
                "status": "error",
                "error": "release_preparation_failed",
                "message": "Model release preparation failed.",
            }
        ), 500

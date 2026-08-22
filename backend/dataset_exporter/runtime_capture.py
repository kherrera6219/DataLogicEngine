"""Post-release staging writer for optional usage-data capture.

Capture is export-only. It never trains a model, never stores credentials,
and never writes pre-release or quarantined content.
"""

from __future__ import annotations

import json
import logging
import math
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .capture_policy import (
    ALLOWED_CAPTURE_FIELDS,
    CAPTURE_SCHEMA_VERSION,
    CAPTURE_SUBDIR,
    is_training_data_capture_enabled,
)
from .privacy_redactor import PrivacyRedactor, SecurityError

logger = logging.getLogger(__name__)


def _capture_root(base_dir: str | Path | None = None) -> Path:
    if base_dir is not None:
        root = Path(base_dir)
        if root.name == CAPTURE_SUBDIR:
            return root
        return root / CAPTURE_SUBDIR
    from backend.runtime.application import get_application_runtime

    return get_application_runtime().runtime_root / "datasets" / CAPTURE_SUBDIR


def is_release_authorized_for_capture(trace: dict[str, Any]) -> bool:
    """Fail-closed eligibility used by both staging and later export."""

    if not isinstance(trace, dict):
        return False
    if bool(trace.get("quarantine") or trace.get("quarantined")):
        return False
    if trace.get("containment_class") == "never_persist":
        return False
    if trace.get("release_authorized") is not True:
        return False
    if trace.get("regulatory_pass") is False:
        return False
    if trace.get("security_pass") is False:
        return False
    status = str(trace.get("status") or "").strip().lower()
    if status and status not in {"completed", "succeeded", "success"}:
        return False
    decision = str(trace.get("truthgate_decision") or "").strip().lower()
    if decision and decision not in {"allow", "release"}:
        return False
    if not str(trace.get("query") or "").strip():
        return False
    if not str(trace.get("released_answer") or "").strip():
        return False
    try:
        confidence = float(trace.get("confidence", 0.0))
    except (TypeError, ValueError):
        return False
    return math.isfinite(confidence)


def compute_release_authorized(record: Any) -> bool:
    """Same completed/released predicate used by DatasetExporter.export_from_db."""

    status = str(getattr(record, "status", "") or "").strip().lower()
    truthgate_decision = str(getattr(record, "truthgate_decision", "") or "").strip().lower()
    return (
        status in {"completed", "succeeded", "success"}
        and truthgate_decision in {"allow", "release"}
        and getattr(record, "regulatory_pass", None) is not False
        and getattr(record, "security_pass", None) is not False
        and bool(str(getattr(record, "input_message", "") or "").strip())
        and bool(str(getattr(record, "final_answer", "") or "").strip())
    )


def capture_payload_from_run(record: Any, stages: list[Any] | None = None) -> dict[str, Any]:
    """Allowlisted capture dict from a committed TraceRun."""

    snapshot = record.data_snapshot if isinstance(getattr(record, "data_snapshot", None), dict) else {}
    stage_list = []
    for item in stages or []:
        if isinstance(item, dict):
            stage_list.append(
                {
                    "stage": str(item.get("stage") or item.get("name") or ""),
                    "status": str(item.get("status") or ""),
                }
            )
        else:
            stage_list.append(
                {
                    "stage": str(getattr(item, "name", "") or ""),
                    "status": str(getattr(item, "status", "") or ""),
                }
            )
    return {
        "schema_version": CAPTURE_SCHEMA_VERSION,
        "run_id": str(getattr(record, "run_id", "") or ""),
        "query": str(getattr(record, "input_message", "") or ""),
        "released_answer": str(getattr(record, "final_answer", "") or ""),
        "confidence": float(getattr(record, "confidence", 0.0) or 0.0),
        "tier": getattr(record, "tier", None),
        "status": str(getattr(record, "status", "") or ""),
        "truthgate_decision": str(getattr(record, "truthgate_decision", "") or ""),
        "stages": stage_list,
        "release_authorized": compute_release_authorized(record),
        "quarantine": bool(snapshot.get("quarantine") or snapshot.get("quarantined")),
        "containment_class": snapshot.get("containment_class"),
        "regulatory_pass": getattr(record, "regulatory_pass", None),
        "security_pass": getattr(record, "security_pass", None),
        "source": "runtime_capture",
    }


def build_capture_row(trace: dict[str, Any]) -> dict[str, Any] | None:
    if not is_release_authorized_for_capture(trace):
        return None
    row: dict[str, Any] = {
        "schema_version": CAPTURE_SCHEMA_VERSION,
        "source": "runtime_capture",
        "captured_at": datetime.now(UTC).isoformat(),
        "run_id": str(trace.get("run_id") or ""),
        "query": str(trace.get("query") or ""),
        "released_answer": str(trace.get("released_answer") or ""),
        "release_authorized": True,
        "quarantine": False,
    }
    try:
        row["confidence"] = float(trace.get("confidence") or 0.0)
    except (TypeError, ValueError):
        return None
    stages = trace.get("stages") if isinstance(trace.get("stages"), list) else []
    row["stages"] = [
        {
            "stage": str(item.get("stage") or item.get("name") or ""),
            "status": str(item.get("status") or ""),
        }
        for item in stages
        if isinstance(item, dict)
    ]
    if trace.get("containment_class"):
        row["containment_class"] = str(trace.get("containment_class"))
    if trace.get("tier") is not None:
        row["tier"] = trace.get("tier")
    if trace.get("status"):
        row["status"] = str(trace.get("status"))
    if trace.get("truthgate_decision"):
        row["truthgate_decision"] = str(trace.get("truthgate_decision"))
    allowed = {key: row[key] for key in ALLOWED_CAPTURE_FIELDS if key in row}
    return PrivacyRedactor.redact_data(allowed)


def capture_stats(base_dir: str | Path | None = None) -> dict[str, Any]:
    try:
        root = _capture_root(base_dir)
        if not root.exists():
            return {"staged_capture_rows": 0, "last_capture_at": None}
        files = [path for path in root.glob("*.jsonl") if path.is_file()]
        last_capture_at = None
        if files:
            latest = max(files, key=lambda item: item.stat().st_mtime)
            last_capture_at = datetime.fromtimestamp(latest.stat().st_mtime, UTC).isoformat()
        return {"staged_capture_rows": len(files), "last_capture_at": last_capture_at}
    except Exception:
        logger.debug("Capture stats failed closed", exc_info=True)
        return {"staged_capture_rows": 0, "last_capture_at": None}


def count_staged_capture_rows(base_dir: str | Path | None = None) -> int:
    return int(capture_stats(base_dir)["staged_capture_rows"])


def load_staged_capture_traces(
    *,
    base_dir: str | Path | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    traces: list[dict[str, Any]] = []
    try:
        root = _capture_root(base_dir)
        if not root.exists():
            return traces
        paths = sorted(root.glob("*.jsonl"), key=lambda item: item.stat().st_mtime, reverse=True)
        for path in paths:
            if len(traces) >= limit:
                break
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                traces.append(payload)
    except Exception:
        logger.debug("Capture load failed closed", exc_info=True)
    return traces[:limit]


def maybe_stage_released_trace(
    trace: dict[str, Any],
    *,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Stage one released trace when the owner flag is on.

    Failures are logged and swallowed so the governed run is never blocked.
    """

    result: dict[str, Any] = {"status": "skipped", "reason": "flag_off", "path": None}
    try:
        if not is_training_data_capture_enabled():
            return result
        row = build_capture_row(trace)
        if row is None:
            result["reason"] = "not_release_authorized"
            return result
        run_id = str(row.get("run_id") or "").strip()
        if not run_id:
            result["reason"] = "missing_run_id"
            return result
        root = _capture_root(base_dir)
        root.mkdir(parents=True, exist_ok=True)
        destination = PrivacyRedactor.validate_safe_path(f"{run_id}.jsonl", base_dir=root)
        if destination.exists():
            result["reason"] = "already_staged"
            result["path"] = str(destination)
            result["status"] = "idempotent"
            return result
        temporary = destination.with_name(destination.name + ".tmp")
        temporary.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(temporary, destination)
        result.update({"status": "staged", "reason": "ok", "path": str(destination)})
        return result
    except (SecurityError, OSError, ValueError) as exc:
        logger.warning("Runtime training-data capture skipped: %s", exc)
        result["reason"] = "capture_failed"
        return result
    except Exception:
        logger.warning("Runtime training-data capture failed closed", exc_info=True)
        result["reason"] = "capture_failed"
        return result


def maybe_stage_training_capture(
    run_id: str,
    *,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Load a committed TraceRun and stage it when the owner flag is on."""

    result: dict[str, Any] = {"status": "skipped", "reason": "flag_off", "path": None}
    try:
        if not is_training_data_capture_enabled():
            return result
        from extensions import db
        from models import TraceRun, TraceStage

        try:
            parsed = uuid.UUID(str(run_id))
        except (TypeError, ValueError):
            result["reason"] = "missing_run_id"
            return result
        record = db.session.get(TraceRun, parsed)
        if record is None:
            result["reason"] = "missing_run"
            return result
        stages = (
            db.session.query(TraceStage)
            .filter(TraceStage.run_id == record.run_id)
            .order_by(TraceStage.step_index.asc())
            .all()
        )
        return maybe_stage_released_trace(capture_payload_from_run(record, stages), base_dir=base_dir)
    except Exception:
        logger.warning("Runtime training-data capture failed closed", exc_info=True)
        result["reason"] = "capture_failed"
        return result

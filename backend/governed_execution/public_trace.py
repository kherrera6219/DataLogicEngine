"""Safe, bounded presentation records for desktop trace surfaces.

The governed trace database keeps operational inputs and outputs needed for
audit and replay.  Those records are not a UI contract.  This module exposes a
small allowlisted receipt that explains observable stage work without leaking
prompts, retrieved text, provider output, secrets, or private reasoning.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any

PUBLIC_TRACE_SCHEMA_VERSION = "dle.public-trace-event.v1"
TRACE_UNAVAILABLE_SCHEMA_VERSION = "dle.trace-unavailable.v1"
MAX_PUBLIC_TRACE_NARRATIVE_CHARS = 320
_SAFE_TEXT = re.compile(r"[^A-Za-z0-9 _.:/()-]+")
_LAYER_NAME = re.compile(r"^layer_(\d+)_([a-z0-9_]+?)(?:_\d+)?$")


def _value(source: Any, key: str, default: Any = None) -> Any:
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _mapping(source: Any, *keys: str) -> dict[str, Any]:
    for key in keys:
        candidate = _value(source, key)
        if isinstance(candidate, dict):
            return candidate
    return {}


def _iso(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str) and value:
        return value[:64]
    return None


def _safe_text(value: Any, *, limit: int = 120) -> str:
    normalized = " ".join(str(value or "").split())
    return _SAFE_TEXT.sub("", normalized)[:limit]


def _public_name(raw_name: Any) -> str:
    normalized = str(raw_name or "Stage").strip()
    layer_match = _LAYER_NAME.match(normalized)
    if layer_match:
        normalized = layer_match.group(2)
    elif normalized.startswith("refinement_"):
        normalized = "refinement"
    elif "_" not in normalized:
        return _safe_text(normalized, limit=100) or "Stage"
    normalized = normalized.replace("_", " ").strip()
    return _safe_text(normalized.capitalize() or "Stage", limit=100)


def _layer_index(stage: Any, inputs: dict[str, Any]) -> int | None:
    recorded = _value(stage, "layer_index")
    if isinstance(recorded, int):
        return recorded
    layer_id = inputs.get("layer_id")
    if isinstance(layer_id, str) and layer_id.startswith("L"):
        try:
            return int(layer_id[1:])
        except ValueError:
            return None
    match = _LAYER_NAME.match(str(_value(stage, "name", "")))
    return int(match.group(1)) if match else None


def _step_index(stage: Any, inputs: dict[str, Any]) -> int | None:
    recorded = _value(stage, "step_index")
    if isinstance(recorded, int):
        return recorded
    for key in ("step", "step_index"):
        candidate = inputs.get(key)
        if isinstance(candidate, int):
            return candidate
    return None


def _safe_refinement_receipt(outputs: dict[str, Any]) -> dict[str, Any] | None:
    receipt = outputs.get("refinement")
    if not isinstance(receipt, dict):
        return None
    steps: list[dict[str, Any]] = []
    for raw_step in list(receipt.get("steps") or [])[:12]:
        if not isinstance(raw_step, dict):
            continue
        steps.append(
            {
                "step": raw_step.get("step") if isinstance(raw_step.get("step"), int) else None,
                "step_id": _safe_text(raw_step.get("step_id"), limit=80),
                "name": _safe_text(raw_step.get("name"), limit=100),
                "status": _safe_text(raw_step.get("status"), limit=40),
                "reason": (
                    _safe_text(raw_step.get("reason"), limit=160)
                    if raw_step.get("reason")
                    else None
                ),
            }
        )
    return {
        "schema_version": _safe_text(receipt.get("schema_version"), limit=80),
        "registry_version": _safe_text(receipt.get("registry_version"), limit=80),
        "status": _safe_text(receipt.get("status"), limit=40),
        "step_count": receipt.get("step_count")
        if isinstance(receipt.get("step_count"), int)
        else len(steps),
        "rewrite_authorized": receipt.get("rewrite_authorized") is True,
        "blocked_by_step": (
            _safe_text(receipt.get("blocked_by_step"), limit=80)
            if receipt.get("blocked_by_step")
            else None
        ),
        "steps": steps,
    }


def _narrative(
    *,
    name: str,
    status: str,
    layer_index: int | None,
    outputs: dict[str, Any],
    error_code: str | None,
    refinement: dict[str, Any] | None,
) -> str:
    if status == "running":
        text = f"Started {name}."
    elif status in {"failed", "fail", "blocked", "cancelled"}:
        suffix = f" Error code: {_safe_text(error_code, limit=80)}." if error_code else ""
        text = f"{name} did not complete successfully.{suffix}"
    elif refinement:
        count = refinement.get("step_count", len(refinement.get("steps") or []))
        text = f"Accounted for {count} ordered refinement steps."
    elif layer_index == 2:
        evidence_ids = outputs.get("evidence_ids")
        count = len(evidence_ids) if isinstance(evidence_ids, list) else 0
        text = f"Retrieved and recorded {count} evidence records."
    elif layer_index == 4:
        profiles = outputs.get("profiles") or outputs.get("persona_profiles")
        count = len(profiles) if isinstance(profiles, dict) else 0
        text = f"Constructed {count} governed persona profiles."
    elif layer_index == 5:
        text = "Recorded the candidate construction plan and analyst inputs."
    elif layer_index == 6:
        text = "Validated the candidate against recorded claims and evidence."
    elif layer_index == 9:
        text = "Recorded whether refinement was required before release."
    elif layer_index == 10:
        text = "Applied the governed release decision."
    else:
        text = f"Completed {name}."
    return text[:MAX_PUBLIC_TRACE_NARRATIVE_CHARS]


def present_stage_event(run_id: str, stage: Any, *, sequence: int) -> dict[str, Any]:
    """Return one stable public receipt for a live or persisted stage state."""

    stage_id = str(_value(stage, "stage_id", ""))
    status_value = _value(stage, "status", "unknown")
    status = _safe_text(getattr(status_value, "value", status_value), limit=40).lower()
    inputs = _mapping(stage, "inputs", "input")
    outputs = _mapping(stage, "outputs", "output")
    metrics = _mapping(stage, "metrics")
    name = _public_name(_value(stage, "name", _value(stage, "stage_name", "Stage")))
    layer_index = _layer_index(stage, inputs)
    step_index = _step_index(stage, inputs)
    error_code = _safe_text(_value(stage, "error_code"), limit=80) or None
    refinement = _safe_refinement_receipt(outputs)
    start_time = _iso(_value(stage, "started_at", _value(stage, "start_time")))
    end_time = _iso(_value(stage, "completed_at", _value(stage, "end_time")))
    duration = _value(stage, "duration_ms")
    if not isinstance(duration, int):
        duration = None
    stable_event_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"dle-public-trace:{run_id}:{stage_id}:{status}",
        )
    )
    event = {
        "schema_version": PUBLIC_TRACE_SCHEMA_VERSION,
        "event_id": stable_event_id,
        "sequence": max(1, int(sequence)),
        "run_id": str(run_id),
        "stage_id": stage_id,
        "name": name,
        "stage_type": _safe_text(_value(stage, "stage_type", "stage"), limit=40),
        "layer_index": layer_index,
        "step_index": step_index,
        "status": status,
        "narrative": _narrative(
            name=name,
            status=status,
            layer_index=layer_index,
            outputs=outputs,
            error_code=error_code,
            refinement=refinement,
        ),
        "occurred_at": end_time or start_time,
        "start_time": start_time,
        "end_time": end_time,
        "duration_ms": duration,
        "timing": {
            "start_time": start_time,
            "end_time": end_time,
            "duration_ms": duration,
        },
        "error_code": error_code,
    }
    if refinement:
        event["refinement"] = refinement
        event["outputs"] = {"refinement": refinement}
    if isinstance(metrics.get("trace_sequence"), int):
        event["sequence"] = max(1, int(metrics["trace_sequence"]))
    return event


def trace_unavailable_payload(
    run_id: str | None,
    *,
    code: str,
    message: str,
    retryable: bool,
) -> dict[str, Any]:
    """Return a typed failure envelope that cannot be mistaken for empty data."""

    return {
        "schema_version": TRACE_UNAVAILABLE_SCHEMA_VERSION,
        "run_id": str(run_id) if run_id is not None else None,
        "status": "unavailable",
        "error": {
            "code": _safe_text(code, limit=80),
            "message": _safe_text(message, limit=240),
            "retryable": bool(retryable),
        },
    }

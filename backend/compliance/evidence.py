"""Truthful evidence records for compliance control mappings."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

CLAIM_TYPES = {
    "control_mapping",
    "automated_control_check",
    "self_assessment_evidence",
    "policy_status",
}
RESULTS = {"passed", "failed", "not_measured", "not_applicable"}
REQUIRED_FIELDS = {
    "control_id",
    "claim_type",
    "check_version",
    "executed_at",
    "scope",
    "result",
    "evidence_ref",
    "source_record",
}


class ComplianceEvidenceError(ValueError):
    """Raised when a displayed compliance result lacks required evidence."""


def normalize_evidence_record(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if not isinstance(value, Mapping):
        raise ComplianceEvidenceError("compliance_evidence_record_must_be_an_object")
    missing = sorted(REQUIRED_FIELDS - set(value))
    if missing:
        raise ComplianceEvidenceError(
            f"compliance_evidence_missing_fields:{','.join(missing)}"
        )

    normalized = {
        key: _bounded_string(value.get(key), key, 512)
        for key in REQUIRED_FIELDS - {"executed_at"}
    }
    if normalized["claim_type"] not in CLAIM_TYPES:
        raise ComplianceEvidenceError("compliance_claim_type_invalid")
    if normalized["result"] not in RESULTS:
        raise ComplianceEvidenceError("compliance_result_invalid")

    executed_at = value.get("executed_at")
    if isinstance(executed_at, datetime):
        parsed = executed_at
    else:
        try:
            parsed = datetime.fromisoformat(str(executed_at).replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise ComplianceEvidenceError("compliance_execution_time_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ComplianceEvidenceError("compliance_execution_time_timezone_required")
    normalized["executed_at"] = parsed.isoformat()
    normalized["evidence_sha256"] = evidence_record_fingerprint(normalized)
    return normalized


def summarize_evidence(records: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {result: 0 for result in sorted(RESULTS)}
    for record in records:
        counts[record["result"]] += 1
    if not records or counts["not_measured"]:
        overall_result = "not_measured"
    elif counts["failed"]:
        overall_result = "checks_failed"
    elif counts["passed"]:
        overall_result = "checks_passed"
    else:
        overall_result = "not_applicable"
    measured = counts["passed"] + counts["failed"]
    return {
        "overall_result": overall_result,
        "record_count": len(records),
        "result_counts": counts,
        "measured_check_count": measured,
        "passed_check_count": counts["passed"],
        "pass_rate": round(counts["passed"] / measured, 4) if measured else None,
        "certification_claim": False,
        "independent_assessment": False,
    }


def evidence_record_fingerprint(record: Mapping[str, Any]) -> str:
    payload = {
        key: value
        for key, value in record.items()
        if key != "evidence_sha256"
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _bounded_string(value: Any, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ComplianceEvidenceError(f"compliance_{field}_must_be_text")
    normalized = value.strip()
    if not normalized or len(normalized) > maximum:
        raise ComplianceEvidenceError(f"compliance_{field}_invalid_length")
    return normalized

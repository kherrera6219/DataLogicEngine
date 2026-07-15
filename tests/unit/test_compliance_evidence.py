from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from backend.compliance.evidence import (
    ComplianceEvidenceError,
    evidence_record_fingerprint,
    normalize_evidence_record,
    summarize_evidence,
)
from backend.reports.compliance import ComplianceFramework, ComplianceReportGenerator


def _record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "control_id": "CC6.1",
        "claim_type": "automated_control_check",
        "check_version": "access-control.v1",
        "executed_at": datetime(2026, 7, 14, 12, 0, tzinfo=UTC),
        "scope": "local_application_runtime",
        "result": "passed",
        "evidence_ref": "diagnostics://access-control/2026-07-14",
        "source_record": "access-control-check:42",
    }
    record.update(overrides)
    return record


def test_normalize_evidence_record_adds_stable_fingerprint():
    normalized = normalize_evidence_record(_record())

    assert normalized["executed_at"] == "2026-07-14T12:00:00+00:00"
    assert normalized["evidence_sha256"] == evidence_record_fingerprint(normalized)
    assert len(normalized["evidence_sha256"]) == 64


def test_normalize_evidence_record_rejects_missing_required_fields():
    record = _record()
    del record["evidence_ref"]

    with pytest.raises(
        ComplianceEvidenceError,
        match="compliance_evidence_missing_fields:evidence_ref",
    ):
        normalize_evidence_record(record)


def test_normalize_evidence_record_requires_timezone():
    with pytest.raises(
        ComplianceEvidenceError,
        match="compliance_execution_time_timezone_required",
    ):
        normalize_evidence_record(_record(executed_at=datetime(2026, 7, 14, 12, 0)))


def test_summarize_evidence_uses_not_measured_without_records():
    summary = summarize_evidence([])

    assert summary["overall_result"] == "not_measured"
    assert summary["pass_rate"] is None
    assert summary["certification_claim"] is False


def test_summarize_evidence_reports_failed_checks_without_certification_claim():
    records = [
        normalize_evidence_record(_record(result="passed")),
        normalize_evidence_record(
            _record(
                control_id="CC7.2",
                result="failed",
                source_record="monitoring-check:7",
            )
        ),
    ]

    summary = summarize_evidence(records)

    assert summary["overall_result"] == "checks_failed"
    assert summary["pass_rate"] == 0.5
    assert summary["independent_assessment"] is False


def test_report_without_evidence_is_explicitly_not_measured(tmp_path: Path):
    reporter = ComplianceReportGenerator(output_dir=str(tmp_path))
    end = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)

    report = reporter.generate_report(
        ComplianceFramework.SOC2,
        end - timedelta(days=30),
        end,
        [],
    )

    assert report["schema_version"] == "dle.compliance-evidence-report.v1"
    assert report["report_classification"] == "self_assessment_evidence"
    assert report["framework_map_is_certification"] is False
    assert report["summary"]["overall_result"] == "not_measured"
    assert Path(report["pdf_export_path"]).is_file()


def test_report_rejects_invalid_input_instead_of_fabricating_results(tmp_path: Path):
    reporter = ComplianceReportGenerator(output_dir=str(tmp_path))
    end = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)

    with pytest.raises(ComplianceEvidenceError):
        reporter.generate_report(
            ComplianceFramework.SOC2,
            end - timedelta(days=1),
            end,
            [{"control_id": "CC6.1"}],
        )

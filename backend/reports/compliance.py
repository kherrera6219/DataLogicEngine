"""Compliance control-map self-assessment evidence reports."""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.compliance.evidence import normalize_evidence_record, summarize_evidence

logger = logging.getLogger(__name__)


class ComplianceFramework(Enum):
    """Framework maps supported for self-assessment evidence organization."""

    SOC2 = "SOC2"
    GDPR = "GDPR"
    HIPAA = "HIPAA"
    ISO27001 = "ISO27001"
    CCPA = "CCPA"


class ComplianceReportGenerator:
    """Generate non-certifying reports from supplied, versioned evidence records."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        framework: ComplianceFramework,
        start_date: datetime,
        end_date: datetime,
        data_points: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if end_date < start_date:
            raise ValueError("compliance_report_period_invalid")
        records = [normalize_evidence_record(item) for item in data_points]
        report = {
            "schema_version": "dle.compliance-evidence-report.v1",
            "report_id": f"RPT-{uuid.uuid4()}",
            "report_classification": "self_assessment_evidence",
            "framework_map": framework.value,
            "framework_map_is_certification": False,
            "generated_at": datetime.now().astimezone().isoformat(),
            "period": {
                "start": start_date.astimezone().isoformat(),
                "end": end_date.astimezone().isoformat(),
            },
            "summary": summarize_evidence(records),
            "evidence_records": records,
            "limitations": [
                "This report is application-generated self-assessment evidence.",
                "It is not an independent audit, attestation, or certification.",
                "Organizational and process controls outside recorded checks are not assessed.",
            ],
        }
        report["pdf_export_path"] = self.export_to_pdf(report)
        return report

    def export_to_pdf(self, report: dict[str, Any]) -> str:
        framework = str(report["framework_map"])
        filename = f"{report['report_id']}_{framework}_SELF_ASSESSMENT.pdf"
        filepath = self.output_dir / filename
        document = SimpleDocTemplate(str(filepath), pagesize=LETTER)
        styles = getSampleStyleSheet()
        elements = [
            Paragraph(
                f"DataLogicEngine - {framework} Control-Map Self-Assessment Evidence",
                styles["Title"],
            ),
            Paragraph(f"Report ID: {report['report_id']}", styles["Normal"]),
            Paragraph(f"Generated: {report['generated_at']}", styles["Normal"]),
            Paragraph(
                "This application-generated report is not an independent audit, attestation, or certification.",
                styles["Normal"],
            ),
            Spacer(1, 12),
        ]

        summary = report["summary"]
        summary_table = Table(
            [
                ["Evidence metric", "Value"],
                ["Framework map", framework],
                ["Overall check result", summary["overall_result"]],
                ["Evidence records", str(summary["record_count"])],
                ["Measured checks", str(summary["measured_check_count"])],
                ["Passed checks", str(summary["passed_check_count"])],
                [
                    "Pass rate",
                    "Not measured"
                    if summary["pass_rate"] is None
                    else f"{summary['pass_rate'] * 100:.1f}%",
                ],
            ]
        )
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        elements.extend([summary_table, Spacer(1, 12)])

        elements.append(Paragraph("Versioned evidence records", styles["Heading2"]))
        rows = [["Control", "Claim type", "Result", "Evidence reference"]]
        for record in report["evidence_records"]:
            rows.append(
                [
                    record["control_id"],
                    record["claim_type"],
                    record["result"],
                    record["evidence_ref"],
                ]
            )
        if len(rows) == 1:
            rows.append(["No evidence supplied", "-", "not_measured", "-"])
        evidence_table = Table(rows, repeatRows=1)
        evidence_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        elements.append(evidence_table)

        try:
            document.build(elements)
        except Exception as exc:
            filepath.unlink(missing_ok=True)
            raise RuntimeError("compliance_evidence_pdf_export_failed") from exc
        logger.info(
            "Compliance self-assessment evidence report exported",
            extra={
                "event": "compliance_evidence_report.exported",
                "report_id": report["report_id"],
                "framework_map": framework,
                "record_count": summary["record_count"],
            },
        )
        return os.fspath(filepath)


compliance_reporter = ComplianceReportGenerator()

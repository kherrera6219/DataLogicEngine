#!/usr/bin/env python3
"""
Validate SQLAlchemy model portability between SQLite and PostgreSQL.

This script performs a static parity check against the model metadata:
1. Ensures every table can compile to both SQLite and PostgreSQL DDL.
2. Flags PostgreSQL-specific column types that do not declare SQLite variants.
3. Emits a machine-readable report for CI and release gates.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

from flask import Flask
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.schema import CreateTable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from extensions import db  # noqa: E402
import models  # noqa: F401, E402


@dataclass
class ParityIssue:
    severity: str
    table: str
    column: str | None
    check: str
    detail: str


def _load_metadata():
    app = Flask("schema_parity_check")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        return db.Model.metadata


def _dialect_specific_without_variant(column_type) -> bool:
    type_module = type(column_type).__module__
    if not type_module.startswith("sqlalchemy.dialects.postgresql"):
        return False

    variant_mapping = getattr(column_type, "_variant_mapping", {}) or {}
    if not variant_mapping:
        return True

    for dialect_name in variant_mapping:
        if str(dialect_name).strip().lower() == "sqlite":
            return False
    return True


def validate_parity() -> List[ParityIssue]:
    metadata = _load_metadata()
    sqlite_dialect = sqlite.dialect()
    postgres_dialect = postgresql.dialect()
    issues: List[ParityIssue] = []

    for table_name, table in sorted(metadata.tables.items()):
        # Table-level DDL compilation parity
        try:
            str(CreateTable(table).compile(dialect=sqlite_dialect))
        except Exception as exc:
            issues.append(
                ParityIssue(
                    severity="error",
                    table=table_name,
                    column=None,
                    check="sqlite_ddl_compile",
                    detail=str(exc),
                )
            )
        try:
            str(CreateTable(table).compile(dialect=postgres_dialect))
        except Exception as exc:
            issues.append(
                ParityIssue(
                    severity="error",
                    table=table_name,
                    column=None,
                    check="postgres_ddl_compile",
                    detail=str(exc),
                )
            )

        for column in table.columns:
            try:
                column.type.compile(dialect=sqlite_dialect)
            except Exception as exc:
                issues.append(
                    ParityIssue(
                        severity="error",
                        table=table_name,
                        column=column.name,
                        check="sqlite_type_compile",
                        detail=str(exc),
                    )
                )

            try:
                column.type.compile(dialect=postgres_dialect)
            except Exception as exc:
                issues.append(
                    ParityIssue(
                        severity="error",
                        table=table_name,
                        column=column.name,
                        check="postgres_type_compile",
                        detail=str(exc),
                    )
                )

            if _dialect_specific_without_variant(column.type):
                issues.append(
                    ParityIssue(
                        severity="warning",
                        table=table_name,
                        column=column.name,
                        check="postgres_specific_type",
                        detail=(
                            f"{type(column.type).__name__} is PostgreSQL-specific and does not declare "
                            "an explicit SQLite variant."
                        ),
                    )
                )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SQLite/Postgres model parity.")
    parser.add_argument(
        "--report",
        default="reports/schema_parity_report.json",
        help="Path to JSON report output.",
    )
    args = parser.parse_args()

    issues = validate_parity()
    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]

    report_payload = {
        "status": "pass" if not errors else "fail",
        "summary": {
            "errors": len(errors),
            "warnings": len(warnings),
            "total_issues": len(issues),
        },
        "issues": [asdict(issue) for issue in issues],
    }

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

    print(
        f"[schema-parity] status={report_payload['status']} "
        f"errors={len(errors)} warnings={len(warnings)} report={report_path}"
    )

    if errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify controlled headers and authority binding for existing canonical documents."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import re
from typing import Any

try:
    from generate_documentation_authority import (
        CONTROLLED_HEADER_FIELDS,
        DEFAULT_CONFIG,
        ROOT,
        STATUS_VOCABULARY,
        load_authority,
    )
except ModuleNotFoundError:  # Imported as scripts.verify_doc_authority in tests.
    from scripts.generate_documentation_authority import (
        CONTROLLED_HEADER_FIELDS,
        DEFAULT_CONFIG,
        ROOT,
        STATUS_VOCABULARY,
        load_authority,
    )


DEFAULT_REPORT = (
    ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-16"
    / "document-authority-verification.json"
)
PRODUCT_VERSIONS = ROOT / "config" / "product-versions.json"
TABLE_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$")


def _clean(value: str) -> str:
    return value.strip().strip("`").strip()


def parse_controlled_header(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines()[:160]:
        match = TABLE_ROW.match(line)
        if not match:
            continue
        key = _clean(match.group(1))
        value = _clean(match.group(2))
        if key in {"Field", "---"} or set(key) == {"-"}:
            continue
        rows.setdefault(key, value)
    return rows


def verify(
    authority: dict[str, Any],
    *,
    root: Path = ROOT,
    product_versions_path: Path = PRODUCT_VERSIONS,
) -> dict[str, Any]:
    errors: list[str] = []
    documents: list[dict[str, Any]] = []
    product_version = json.loads(product_versions_path.read_text(encoding="utf-8"))[
        "product"
    ]["version"]
    approval = authority.get("approval", {})
    if approval.get("status") != "approved":
        errors.append("information_architecture_not_approved")
    if approval.get("archive_delete_authorized") is not False:
        errors.append("archive_delete_boundary_not_fail_closed")

    for item in authority["canonical_documents"]:
        path = root / item["path"]
        if not path.is_file():
            documents.append(
                {
                    "id": item["id"],
                    "path": item["path"],
                    "state": "planned",
                    "header_status": "not_applicable_until_created",
                }
            )
            continue
        header = parse_controlled_header(path)
        missing = [field for field in CONTROLLED_HEADER_FIELDS if not header.get(field)]
        document_errors: list[str] = []
        if missing:
            document_errors.extend(f"missing_field:{field}" for field in missing)
        if header.get("Document ID") != item["id"]:
            document_errors.append("document_id_mismatch")
        if header.get("Title") != item["title"]:
            document_errors.append("title_mismatch")
        if header.get("Product version") != product_version:
            document_errors.append("product_version_mismatch")
        if header.get("Status") not in STATUS_VOCABULARY:
            document_errors.append("status_vocabulary_mismatch")
        if header.get("Owner") != item["owner"]:
            document_errors.append("owner_mismatch")
        if header.get("Approver") != "Kevin Herrera, Product Owner":
            document_errors.append("approver_mismatch")
        if document_errors:
            errors.extend(f"{item['path']}:{error}" for error in document_errors)
        documents.append(
            {
                "id": item["id"],
                "path": item["path"],
                "state": "existing",
                "header_status": "pass" if not document_errors else "fail",
                "missing_fields": missing,
                "errors": document_errors,
            }
        )

    existing = [row for row in documents if row["state"] == "existing"]
    planned = [row for row in documents if row["state"] == "planned"]
    return {
        "schema_version": "dle.document-authority-verification.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "authority_version": authority["program_version"],
        "product_version": product_version,
        "status": "pass" if not errors else "fail",
        "existing_canonical_count": len(existing),
        "planned_canonical_count": len(planned),
        "controlled_header_pass_count": sum(
            row["header_status"] == "pass" for row in existing
        ),
        "archive_delete_authorized": approval.get("archive_delete_authorized"),
        "errors": sorted(errors),
        "documents": documents,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    result = verify(load_authority(args.config))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        f"Document authority: {result['status']} "
        f"headers={result['controlled_header_pass_count']}/{result['existing_canonical_count']} "
        f"planned={result['planned_canonical_count']} errors={len(result['errors'])}"
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

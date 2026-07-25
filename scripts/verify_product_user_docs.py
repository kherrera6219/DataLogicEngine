#!/usr/bin/env python3
"""Verify the Phase 16 CP16-B canonical product/user documentation checkpoint."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from generate_documentation_authority import DEFAULT_CONFIG, ROOT, load_authority
    from verify_doc_authority import parse_controlled_header
except ModuleNotFoundError:  # Imported as scripts.verify_product_user_docs in tests.
    from scripts.generate_documentation_authority import (
        DEFAULT_CONFIG,
        ROOT,
        load_authority,
    )
    from scripts.verify_doc_authority import parse_controlled_header


DEFAULT_REPORT = (
    ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-16"
    / "product-user-document-verification.json"
)
TARGETS = {
    "docs/PRODUCT_REQUIREMENTS.md": {
        "sources": {
            "docs/PRODUCT_DESIGN.md",
            "docs/PRODUCT_OVERVIEW.md",
            "docs/COMPONENT_MAP.md",
            "docs/diagrams/11_frontend_product_surface_and_trace_review_map.md",
        },
        "markers": {
            "DLE-FR-001",
            "Supported product boundary",
            "Explicit exclusions",
            "Production/public release is **NO-GO**",
            "ADR-0010 selects SeaweedFS 4.40-dle.1",
        },
    },
    "docs/INSTALLATION_GUIDE.md": {
        "sources": {"docs/WINDOWS_11_LOCAL_RUNBOOK.md"},
        "markers": {
            "at_rest_protection_not_ready",
            "Automatic update is disabled",
            "Clean installation",
            "Repair",
            "Upgrade",
            "Rollback",
            "Uninstall and data choice",
        },
    },
    "docs/ADMINISTRATOR_OPERATIONS_GUIDE.md": {
        "sources": {
            "docs/DEPLOYMENT.md",
            "docs/OPERATIONAL_RUNBOOKS.md",
            "docs/PRIVATE_GATEWAY_RUNBOOK.md",
        },
        "markers": {
            "PostgreSQL",
            "Redis",
            "Neo4j",
            "ChromaDB",
            "app-owned S3-compatible object store",
            "Backup",
            "Restore and disaster recovery",
            "Client Gateway",
            "MCP connector operations",
        },
    },
    "docs/TROUBLESHOOTING_SUPPORT_GUIDE.md": {
        "sources": {"SUPPORT.md"},
        "markers": {
            "preserve the safety gate",
            "Preview bundle",
            "Common problems",
            "Reporting channels",
            "SECURITY.md",
        },
    },
    "docs/PRIVACY_AI_NOTICE.md": {
        "sources": {"docs/PRIVACY_POLICY.md"},
        "markers": {
            "Local-first does not mean air-gapped",
            "OpenAI and Google processing",
            "## Retention",
            "External telemetry",
            "AI purpose and limitations",
            "not measured",
        },
    },
}
ALLOWED_STATUSES = {"active", "qualification_only", "release_blocked"}
PROHIBITED_CLAIMS = {
    "production release is approved",
    "certified by microsoft",
    "fully compliant",
    "seaweedfs is the approved production object store",
}


def _source_routes(authority: dict[str, Any], target: str) -> set[str]:
    return set(authority.get("merge_routes", {}).get(target, []))


def verify(authority: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    documents: list[dict[str, Any]] = []
    portal = (root / "docs" / "README.md").read_text(encoding="utf-8")

    for target, requirements in TARGETS.items():
        path = root / target
        document_errors: list[str] = []
        if not path.is_file():
            document_errors.append("missing_target")
            text = ""
            header: dict[str, str] = {}
        else:
            text = path.read_text(encoding="utf-8")
            header = parse_controlled_header(path)
        missing_markers = sorted(
            marker for marker in requirements["markers"] if marker not in text
        )
        if missing_markers:
            document_errors.extend(
                f"missing_marker:{marker}" for marker in missing_markers
            )
        expected_sources = requirements["sources"]
        actual_sources = _source_routes(authority, target)
        if actual_sources != expected_sources:
            document_errors.append("source_route_mismatch")
        if header.get("Status") not in ALLOWED_STATUSES:
            document_errors.append("unapproved_product_user_status")
        if target not in portal:
            document_errors.append("documentation_portal_link_missing")
        lowered = text.casefold()
        document_errors.extend(
            f"prohibited_claim:{claim}"
            for claim in sorted(PROHIBITED_CLAIMS)
            if claim in lowered
        )
        errors.extend(f"{target}:{error}" for error in document_errors)
        documents.append(
            {
                "path": target,
                "status": header.get("Status"),
                "sources": sorted(actual_sources),
                "missing_markers": missing_markers,
                "errors": document_errors,
            }
        )

    return {
        "schema_version": "dle.product-user-document-verification.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "authority_version": authority["program_version"],
        "status": "pass" if not errors else "fail",
        "target_count": len(TARGETS),
        "verified_count": sum(not item["errors"] for item in documents),
        "archive_delete_authorized": authority.get("approval", {}).get(
            "archive_delete_authorized"
        ),
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
        f"Product/user documentation: {result['status']} "
        f"verified={result['verified_count']}/{result['target_count']} "
        f"errors={len(result['errors'])}"
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

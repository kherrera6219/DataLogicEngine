#!/usr/bin/env python3
"""Verify Phase 16 CP16-D/CP16-E external review and submission records."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

try:
    from generate_documentation_authority import DEFAULT_CONFIG, ROOT, load_authority
    from verify_doc_authority import parse_controlled_header
except ModuleNotFoundError:  # Imported through the scripts namespace in tests.
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
    / "submission-external-review-verification.json"
)
TARGETS = {
    "docs/PROFESSIONAL_REVIEW_INDEX.md": {
        "markers": {
            "not evidence that a professional",
            "Exact review subject",
            "Review paths",
            "Reviewer assignment register",
            "Required final package",
        }
    },
    "docs/MICROSOFT_SUBMISSION_DOSSIER.md": {
        "markers": {
            "DataLogicEngine has not been submitted",
            "Selected qualification route",
            "MSI/EXE submission",
            "Microsoft Store Policies",
            "MSI/EXE package requirements matrix",
            "Partner Center submission inventory",
            "WACK and certification evidence",
        }
    },
    "docs/INDEPENDENT_REVIEW_RECORD.md": {
        "markers": {
            "No independent reviewer is assigned",
            "Independence and competence register",
            "Required scope and methods",
            "Finding register",
            "Reviewer disposition template",
            "Production/public release remains **NO-GO**",
        }
    },
}
ALLOWED_STATUSES = {"not_evaluated", "release_blocked"}
PROHIBITED_CLAIMS = {
    "microsoft approved datalogicengine",
    "microsoft certified datalogicengine",
    "independent review passed",
    "production release is approved",
    "fully compliant",
}


def verify(authority: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    documents: list[dict[str, Any]] = []
    portal = (root / "docs" / "README.md").read_text(encoding="utf-8")
    routes = authority.get("merge_routes", {})

    for target, requirements in TARGETS.items():
        path = root / target
        item_errors: list[str] = []
        if not path.is_file():
            item_errors.append("missing_target")
            text = ""
            header: dict[str, str] = {}
        else:
            text = path.read_text(encoding="utf-8")
            header = parse_controlled_header(path)
        missing_markers = sorted(
            marker for marker in requirements["markers"] if marker not in text
        )
        item_errors.extend(f"missing_marker:{marker}" for marker in missing_markers)
        if routes.get(target, []) != []:
            item_errors.append("unexpected_source_route")
        if header.get("Status") not in ALLOWED_STATUSES:
            item_errors.append("external_record_status_not_fail_closed")
        if target not in portal:
            item_errors.append("documentation_portal_link_missing")
        lowered = text.casefold()
        item_errors.extend(
            f"prohibited_claim:{claim}"
            for claim in sorted(PROHIBITED_CLAIMS)
            if claim in lowered
        )
        errors.extend(f"{target}:{error}" for error in item_errors)
        documents.append(
            {
                "path": target,
                "status": header.get("Status"),
                "missing_markers": missing_markers,
                "errors": item_errors,
            }
        )

    return {
        "schema_version": "dle.submission-external-review-verification.v1",
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
        f"Submission/external review documentation: {result['status']} "
        f"verified={result['verified_count']}/{result['target_count']} "
        f"errors={len(result['errors'])}"
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

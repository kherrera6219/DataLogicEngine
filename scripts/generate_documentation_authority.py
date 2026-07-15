#!/usr/bin/env python3
"""Generate the Phase 16 documentation BOM and old-to-new disposition crosswalk."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "documentation-authority.json"
DEFAULT_REPORT = (
    ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-16"
    / "document-disposition-inventory.json"
)
DEFAULT_BOM = ROOT / "docs" / "DOCUMENTATION_BOM.md"
DEFAULT_CROSSWALK = ROOT / "docs" / "DOCUMENTATION_CROSSWALK.md"
GENERATED_OUTPUTS = {
    "docs/DOCUMENTATION_BOM.md",
    "docs/DOCUMENTATION_CROSSWALK.md",
}

CONTROLLED_HEADER_FIELDS = (
    "Document ID",
    "Title",
    "Document version",
    "Product version",
    "Status",
    "Audience",
    "Owner",
    "Approver",
    "Source of authority",
    "Confidentiality",
    "Last reviewed",
    "Next-review trigger",
    "Requirements and evidence",
)

STATUS_VOCABULARY = {
    "active": "Approved current behavior or procedure within its stated scope.",
    "draft": "Work in progress; not an approved production authority.",
    "generated": "Mechanically produced from a named authority; do not hand-edit.",
    "not_evaluated": "Required evidence has not yet been collected.",
    "qualification_only": "May be used for engineering qualification, not production.",
    "release_blocked": "A named release gate remains open.",
    "historical": "Retained for audit or research and not current authority.",
    "unsupported": "Outside the approved product contract.",
}


def load_authority(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def markdown_paths(root: Path = ROOT) -> list[str]:
    paths = {path.relative_to(root).as_posix() for path in root.glob("*.md")}
    docs_root = root / "docs"
    if docs_root.exists():
        paths.update(path.relative_to(root).as_posix() for path in docs_root.rglob("*.md"))
    paths.update(GENERATED_OUTPUTS)
    return sorted(paths, key=str.casefold)


def _route_lookup(authority: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    lookup: dict[str, str] = {}
    duplicates: list[str] = []
    for target, sources in authority.get("merge_routes", {}).items():
        for source in sources:
            if source in lookup:
                duplicates.append(source)
            lookup[source] = target
    return lookup, sorted(set(duplicates))


def _archive_target(path: str) -> str:
    if path.startswith("docs/archive/"):
        return path
    if path.startswith("docs/"):
        return f"docs/archive/phase-16/{path.removeprefix('docs/')}"
    return f"docs/archive/phase-16/root/{path}"


def build_inventory(authority: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    canonical = {item["path"]: item for item in authority["canonical_documents"]}
    generated = set(authority.get("generated_companions", [])) | GENERATED_OUTPUTS
    exempt = set(authority.get("cap_exempt_authoritative_inputs", []))
    historical = set(authority.get("historical_documents", []))
    historical_prefixes = tuple(authority.get("historical_prefixes", []))
    routes, duplicate_routes = _route_lookup(authority)
    rows: list[dict[str, Any]] = []

    for path in markdown_paths(root):
        if path in canonical:
            item = canonical[path]
            rows.append(
                {
                    "path": path,
                    "document_class": item["class"],
                    "disposition": "authoritative input",
                    "target": path,
                    "cap_counted": True,
                    "basis": "selected canonical document",
                }
            )
        elif path in generated:
            rows.append(
                {
                    "path": path,
                    "document_class": "engineering_maintenance",
                    "disposition": "generated replacement",
                    "target": path,
                    "cap_counted": False,
                    "basis": "generated companion artifact",
                }
            )
        elif path in exempt:
            rows.append(
                {
                    "path": path,
                    "document_class": (
                        "product_public"
                        if path in {"CODE_OF_CONDUCT.md", "COMMERCIAL_LICENSE.md"}
                        else "engineering_maintenance"
                    ),
                    "disposition": "authoritative input",
                    "target": path,
                    "cap_counted": False,
                    "basis": "normative legal or temporary program authority outside the final canonical cap",
                }
            )
        elif path in historical or path.startswith(historical_prefixes):
            rows.append(
                {
                    "path": path,
                    "document_class": "historical_research",
                    "disposition": "historical archive",
                    "target": _archive_target(path),
                    "cap_counted": False,
                    "basis": "historical audit, research, wireframe, whitepaper, or session material",
                }
            )
        elif path in routes:
            target = routes[path]
            target_item = canonical.get(target)
            rows.append(
                {
                    "path": path,
                    "document_class": (
                        target_item["class"] if target_item else "engineering_maintenance"
                    ),
                    "disposition": f"merge into {target}",
                    "target": target,
                    "cap_counted": False,
                    "basis": "approved Phase 16 consolidation route",
                }
            )
        else:
            rows.append(
                {
                    "path": path,
                    "document_class": None,
                    "disposition": "unclassified",
                    "target": None,
                    "cap_counted": False,
                    "basis": "no authority rule",
                }
            )

    dispositions = Counter(row["disposition"].split(" ")[0] for row in rows)
    unclassified = [row["path"] for row in rows if row["disposition"] == "unclassified"]
    authority_approved = authority.get("approval", {}).get("status") == "approved"
    inventory_status = (
        "approved_map_pass" if authority_approved else "draft_pass"
    ) if not unclassified and not duplicate_routes else "fail"
    return {
        "schema_version": "dle.documentation-disposition-inventory.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "authority_version": authority["program_version"],
        "authority_status": authority["status"],
        "manual_review_required": True,
        "status": inventory_status,
        "summary": {
            "markdown_file_count": len(rows),
            "canonical_document_count": len(canonical),
            "canonical_limit": authority["max_hand_maintained_canonical_documents"],
            "existing_canonical_count": sum(
                1 for path in canonical if (root / path).is_file()
            ),
            "planned_canonical_count": sum(
                1 for path in canonical if not (root / path).is_file()
            ),
            "unclassified_count": len(unclassified),
            "duplicate_route_count": len(duplicate_routes),
            "disposition_prefix_counts": dict(sorted(dispositions.items())),
        },
        "unclassified": unclassified,
        "duplicate_routes": duplicate_routes,
        "documents": rows,
    }


def render_bom(authority: dict[str, Any], root: Path = ROOT) -> str:
    lines = [
        "# Generated Documentation Bill of Materials",
        "",
        "> Generated by `scripts/generate_documentation_authority.py` from",
        "> `config/documentation-authority.json`. Do not hand-edit.",
        "",
        "## Control status",
        "",
        f"- Authority version: `{authority['program_version']}`",
        f"- Status: `{authority['status']}`",
        f"- Canonical limit: `{authority['max_hand_maintained_canonical_documents']}`",
        f"- Selected canonical documents: `{len(authority['canonical_documents'])}`",
        (
            f"- Approval: `{authority.get('approval', {}).get('status', 'pending')}` by "
            f"`{authority.get('approval', {}).get('owner', 'unassigned')}` on "
            f"`{authority.get('approval', {}).get('approved_at', 'not recorded')}`."
        ),
        (
            "- Archive/delete authorized: `"
            f"{str(authority.get('approval', {}).get('archive_delete_authorized', False)).lower()}`."
        ),
        "",
        "## Canonical hand-maintained set",
        "",
        "| ID | Path | Class | Owner | State |",
        "|---|---|---|---|---|",
    ]
    for item in authority["canonical_documents"]:
        state = "existing" if (root / item["path"]).is_file() else "planned"
        lines.append(
            f"| `{item['id']}` | `{item['path']}` | `{item['class']}` | "
            f"{item['owner']} | {state} |"
        )
    lines.extend(
        [
            "",
            "## Required controlled header",
            "",
            "Every canonical document must carry these fields:",
            "",
            *[f"- {field}" for field in CONTROLLED_HEADER_FIELDS],
            "",
            "## Controlled status vocabulary",
            "",
            "| Term | Meaning |",
            "|---|---|",
            *[f"| `{term}` | {meaning} |" for term, meaning in STATUS_VOCABULARY.items()],
            "",
            "`compliant`, `certified`, `validated`, or equivalent language requires an explicitly stated scope and evidence authority.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_crosswalk(inventory: dict[str, Any]) -> str:
    lines = [
        "# Generated Documentation Disposition Crosswalk",
        "",
        "> Generated by `scripts/generate_documentation_authority.py`. Do not hand-edit.",
        "",
        f"Status: `{inventory['status']}`. Manual review required: `{str(inventory['manual_review_required']).lower()}`.",
        "",
        "No archive, merge, or deletion action is authorized by this draft alone.",
        "",
        "| Existing path | Class | Disposition | Target | Basis |",
        "|---|---|---|---|---|",
    ]
    for row in inventory["documents"]:
        lines.append(
            f"| `{row['path']}` | `{row['document_class'] or 'unclassified'}` | "
            f"{row['disposition']} | `{row['target'] or '-'}` | {row['basis']} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--bom", type=Path, default=DEFAULT_BOM)
    parser.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    args = parser.parse_args(argv)
    authority = load_authority(args.config)
    inventory = build_inventory(authority)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    args.bom.write_text(render_bom(authority), encoding="utf-8")
    args.crosswalk.write_text(render_crosswalk(inventory), encoding="utf-8")
    print(
        "Documentation authority: "
        f"status={inventory['status']} files={inventory['summary']['markdown_file_count']} "
        f"canonical={inventory['summary']['canonical_document_count']} "
        f"unclassified={inventory['summary']['unclassified_count']}"
    )
    return 0 if inventory["status"].endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())

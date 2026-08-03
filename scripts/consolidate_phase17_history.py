#!/usr/bin/env python3
"""Plan, apply, and verify Phase 17 historical-document consolidation."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any

try:
    from generate_documentation_authority import DEFAULT_CONFIG, ROOT, load_authority
    from verify_docs_references import collect_active_markdown_files
except ModuleNotFoundError:
    from scripts.generate_documentation_authority import (
        DEFAULT_CONFIG,
        ROOT,
        load_authority,
    )
    from scripts.verify_docs_references import collect_active_markdown_files


DEFAULT_REPORT = (
    ROOT / "reports" / "production-readiness" / "2026" / "phase-17"
    / "history-consolidation.json"
)
LINK_RE = re.compile(r"(\[[^\]]+\]\()([^)]+)(\))")
AUDIT_DESTINATIONS = {
    "REPO_AUDIT_LOG.md": "docs/archive/audits/REPO_AUDIT_LOG_through_2026-07-15.md",
    "docs/REPO_AUDIT_LOG.md": None,
    "docs/ROOT_CLEANUP_REVIEW_2026-07-06.md": "docs/archive/audits/ROOT_CLEANUP_REVIEW_2026-07-06.md",
    "docs/SUBFOLDER_MARKDOWN_REVIEW_2026-07-06.md": "docs/archive/audits/SUBFOLDER_MARKDOWN_REVIEW_2026-07-06.md",
    "docs/TOP_LEVEL_MARKDOWN_REVIEW_2026-07-06.md": "docs/archive/audits/TOP_LEVEL_MARKDOWN_REVIEW_2026-07-06.md",
    "docs/audits/AUDITS_MARKDOWN_REVIEW_2026-07-06.md": "docs/archive/audits/AUDITS_MARKDOWN_REVIEW_2026-07-06.md",
    "docs/audits/DataLogicEngine_Audit_Slice_Findings_Report_2026-07-06.md": "docs/archive/audits/DataLogicEngine_Audit_Slice_Findings_Report_2026-07-06.md",
    "docs/audits/DataLogicEngine_Chat_Data_Path_QC_2026-07-10.md": "docs/archive/audits/DataLogicEngine_Chat_Data_Path_QC_2026-07-10.md",
    "docs/audits/DataLogicEngine_Cross_System_Data_Path_QC_2026-07-10.md": "docs/archive/audits/DataLogicEngine_Cross_System_Data_Path_QC_2026-07-10.md",
    "docs/audits/DataLogicEngine_Routes_Audit.md": "docs/archive/audits/DataLogicEngine_Routes_Audit.md",
}


def _sha256(path: Path, expected_hash: str | None = None) -> str:
    try:
        content = path.read_bytes()
    except Exception:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    h1 = hashlib.sha256(content).hexdigest()
    if expected_hash and h1 == expected_hash:
        return h1
    if expected_hash:
        clean_lf = content.replace(b"\r\n", b"\n")
        h_lf = hashlib.sha256(clean_lf).hexdigest()
        if h_lf == expected_hash:
            return expected_hash
        clean_crlf = clean_lf.replace(b"\n", b"\r\n")
        h_crlf = hashlib.sha256(clean_crlf).hexdigest()
        if h_crlf == expected_hash:
            return expected_hash
    return h1




def _git_blob(path: str, root: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", f"HEAD:{path}"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _versioned_destination(destination: Path) -> Path:
    return destination.with_name(
        f"{destination.stem}__active-through-2026-07-15{destination.suffix}"
    )


def _assert_inside_root(path: Path, root: Path) -> None:
    path.resolve().relative_to(root.resolve())


def build_plan(*, root: Path = ROOT) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for source, destination in AUDIT_DESTINATIONS.items():
        source_path = root / source
        if not source_path.is_file():
            raise FileNotFoundError(source)
        if destination is None:
            action = "delete_duplicate_pointer"
            retained_at = AUDIT_DESTINATIONS["REPO_AUDIT_LOG.md"]
        else:
            action = "move"
            retained_at = destination
        records.append(
            {
                "source": source,
                "action": action,
                "destination": destination,
                "retained_at": retained_at,
                "sha256": _sha256(source_path),
                "git_blob": _git_blob(source, root),
                "byte_count": source_path.stat().st_size,
            }
        )

    for folder in ("whitepapers", "wireframes"):
        active_root = root / "docs" / folder
        archive_root = root / "docs" / "archive" / folder
        for source_path in sorted(active_root.rglob("*")):
            if not source_path.is_file():
                continue
            source = source_path.relative_to(root).as_posix()
            relative = source_path.relative_to(active_root)
            destination_path = archive_root / relative
            source_hash = _sha256(source_path)
            if destination_path.is_file() and _sha256(destination_path) == source_hash:
                action = "remove_byte_identical_duplicate"
                retained_at = destination_path.relative_to(root).as_posix()
                destination = None
            else:
                if destination_path.exists():
                    destination_path = _versioned_destination(destination_path)
                if destination_path.exists():
                    raise FileExistsError(destination_path)
                action = "move"
                destination = destination_path.relative_to(root).as_posix()
                retained_at = destination
            records.append(
                {
                    "source": source,
                    "action": action,
                    "destination": destination,
                    "retained_at": retained_at,
                    "sha256": source_hash,
                    "git_blob": _git_blob(source, root),
                    "byte_count": source_path.stat().st_size,
                }
            )

    return {
        "schema_version": "dle.phase17-history-consolidation.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "ready_to_apply",
        "source_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip(),
        "summary": {
            "record_count": len(records),
            "move_count": sum(row["action"] == "move" for row in records),
            "identical_duplicate_count": sum(
                row["action"] == "remove_byte_identical_duplicate" for row in records
            ),
            "pointer_delete_count": sum(
                row["action"] == "delete_duplicate_pointer" for row in records
            ),
        },
        "records": records,
        "errors": [],
    }


def _source_map(plan: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    audit_log_destination = str(AUDIT_DESTINATIONS["REPO_AUDIT_LOG.md"])
    for row in plan["records"]:
        target = row.get("destination") or row.get("retained_at")
        if row["action"] == "delete_duplicate_pointer":
            target = audit_log_destination
        mapping[row["source"]] = str(target)
    return mapping


def _resolve_link(source_file: Path, target: str, root: Path) -> tuple[str | None, str]:
    raw = target.strip()
    if raw.startswith(("#", "http://", "https://", "mailto:", "ftp:")):
        return None, ""
    path_part, separator, anchor = raw.partition("#")
    candidate = (source_file.parent / path_part).resolve()
    try:
        relative = candidate.relative_to(root.resolve()).as_posix()
    except ValueError:
        return None, anchor
    if not (root / relative).exists():
        fallback = (root / path_part).resolve()
        try:
            fallback_relative = fallback.relative_to(root.resolve()).as_posix()
        except ValueError:
            return relative, anchor
        if (root / fallback_relative).exists():
            relative = fallback_relative
    return relative, anchor if separator else ""


def migrate_links(plan: dict[str, Any], *, root: Path = ROOT) -> int:
    mapping = _source_map(plan)
    excluded = set(mapping)
    changed = 0
    for path in collect_active_markdown_files(root):
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        original = path.read_text(encoding="utf-8")

        def replace(match: re.Match[str]) -> str:
            nonlocal changed
            resolved, anchor = _resolve_link(path, match.group(2), root)
            if resolved not in mapping:
                return match.group(0)
            destination = root / mapping[resolved]
            replacement = os.path.relpath(destination, path.parent).replace("\\", "/")
            changed += 1
            return f"{match.group(1)}{replacement}{'#' + anchor if anchor else ''}{match.group(3)}"

        updated = LINK_RE.sub(replace, original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
    return changed


def apply_plan(plan: dict[str, Any], *, root: Path = ROOT) -> None:
    migrate_links(plan, root=root)
    for row in plan["records"]:
        source = root / row["source"]
        _assert_inside_root(source, root)
        if row["action"] in {
            "remove_byte_identical_duplicate",
            "delete_duplicate_pointer",
        }:
            source.unlink()
            continue
        destination = root / row["destination"]
        _assert_inside_root(destination, root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.replace(destination)


def verify(plan: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    verified = 0
    for row in plan["records"]:
        source = root / row["source"]
        if source.exists():
            errors.append(f"historical_source_still_active:{row['source']}")
            continue
        retained = root / row["retained_at"]
        if row["action"] == "delete_duplicate_pointer":
            if not row.get("git_blob"):
                errors.append("deleted_pointer_missing_git_identity")
            else:
                verified += 1
            continue
        if not retained.is_file():
            errors.append(f"retained_destination_missing:{row['retained_at']}")
        elif _sha256(retained, row["sha256"]) != row["sha256"]:
            errors.append(f"retained_hash_mismatch:{row['source']}")
        else:
            verified += 1
    active_historical = [
        path.relative_to(root).as_posix()
        for folder in (root / "docs" / "whitepapers", root / "docs" / "wireframes")
        if folder.exists()
        for path in folder.rglob("*")
        if path.is_file()
    ]
    errors.extend(f"historical_prefix_still_active:{path}" for path in active_historical)
    result = dict(plan)
    result["verified_at"] = datetime.now(UTC).isoformat()
    result["status"] = "pass" if not errors else "fail"
    result["summary"] = dict(result["summary"])
    result["summary"]["verified_count"] = verified
    result["summary"]["active_historical_count"] = len(active_historical)
    result["errors"] = sorted(errors)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    load_authority(args.config)
    if args.report.is_file():
        plan = json.loads(args.report.read_text(encoding="utf-8"))
        if plan.get("status") == "pass":
            result = verify(plan)
        elif args.apply:
            apply_plan(plan)
            result = verify(plan)
        else:
            result = plan
    else:
        plan = build_plan()
        result = plan
        if args.apply:
            apply_plan(plan)
            result = verify(plan)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    summary = result["summary"]
    print(
        f"Phase 17 history consolidation: {result['status']} "
        f"records={summary['record_count']} moves={summary['move_count']} "
        f"duplicates={summary['identical_duplicate_count']} "
        f"verified={summary.get('verified_count', 0)} errors={len(result['errors'])}"
    )
    return 0 if result["status"] in {"ready_to_apply", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

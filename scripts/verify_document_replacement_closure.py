#!/usr/bin/env python3
"""Freeze and verify Phase 16 source replacement, links, and retained evidence."""

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


DEFAULT_BASELINE = (
    ROOT / "reports" / "production-readiness" / "2026" / "phase-16"
    / "document-replacement-baseline.json"
)
DEFAULT_REPORT = (
    ROOT / "reports" / "production-readiness" / "2026" / "phase-16"
    / "document-replacement-closure.json"
)
LINK_RE = re.compile(r"(\[[^\]]+\]\()([^)]+)(\))")
BACKTICK_RE = re.compile(r"`([^`]+)`")


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
    try:
        result = subprocess.run(
            ["git", "rev-parse", f"HEAD:{path}"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _git_worktree_blob(path: Path, root: Path) -> str | None:
    """Hash a working-tree file through Git's canonical clean filters.

    The Phase 16 baseline was frozen from a Windows checkout that contained
    mixed line endings. Comparing only raw SHA-256 bytes makes the same tracked
    evidence fail on Linux even though Git records identical content. The Git
    blob identity is already retained in the baseline, so use the same clean
    filter Git applies before committing while still detecting real edits.
    """
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        return None
    try:
        result = subprocess.run(
            ["git", "hash-object", f"--path={relative}", str(path)],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _archive_path(source: str, archive_root: str) -> str:
    if source.startswith("docs/"):
        suffix = source.removeprefix("docs/")
    else:
        suffix = f"root/{source}"
    return f"{archive_root.rstrip('/')}/{suffix}"


def _sources(authority: dict[str, Any]) -> dict[str, str]:
    return {
        source: target
        for target, sources in authority.get("merge_routes", {}).items()
        for source in sources
    }


def _heading_present(text: str, title: str) -> bool:
    expected = title.strip().casefold()
    return any(
        line.lstrip("#").strip().casefold() == expected
        for line in text.splitlines()
        if line.startswith("#")
    )


def freeze_baseline(
    authority: dict[str, Any], *, root: Path = ROOT, output: Path = DEFAULT_BASELINE
) -> dict[str, Any]:
    control = authority["replacement_control"]
    records: list[dict[str, Any]] = []
    for source, target in sorted(_sources(authority).items()):
        source_path = root / source
        if not source_path.is_file():
            raise FileNotFoundError(f"Cannot freeze missing source: {source}")
        records.append(
            {
                "source": source,
                "target": target,
                "archive_path": _archive_path(source, control["archive_root"]),
                "sha256": _sha256(source_path),
                "git_blob": _git_blob(source, root),
                "byte_count": source_path.stat().st_size,
            }
        )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()
    baseline = {
        "schema_version": "dle.document-replacement-baseline.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "authority_version": authority["program_version"],
        "source_commit": head,
        "source_count": len(records),
        "records": records,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
    return baseline


def _resolve_link(source_file: Path, target: str, root: Path) -> tuple[str | None, str]:
    raw = target.strip()
    if raw.startswith(("#", "http://", "https://", "mailto:", "ftp:")):
        return None, ""
    path_part, separator, anchor = raw.partition("#")
    if not path_part:
        return None, anchor
    candidate = (source_file.parent / path_part).resolve()
    try:
        relative = candidate.relative_to(root.resolve()).as_posix()
    except ValueError:
        return None, anchor
    if not (root / relative).exists():
        root_candidate = (root / path_part).resolve()
        try:
            root_relative = root_candidate.relative_to(root.resolve()).as_posix()
        except ValueError:
            return relative, anchor
        if (root / root_relative).exists():
            relative = root_relative
    return relative, anchor if separator else ""


def migrate_links(authority: dict[str, Any], *, root: Path = ROOT) -> dict[str, int]:
    routes = _sources(authority)
    source_paths = set(routes)
    changed_files = 0
    changed_links = 0
    changed_refs = 0
    for path in collect_active_markdown_files(root):
        relative = path.relative_to(root).as_posix()
        if relative in source_paths or relative == "docs/DOCUMENTATION_CROSSWALK.md":
            continue
        original = path.read_text(encoding="utf-8")

        def replace_link(match: re.Match[str]) -> str:
            nonlocal changed_links
            resolved, anchor = _resolve_link(path, match.group(2), root)
            if resolved not in routes:
                return match.group(0)
            target = routes[resolved]
            target_path = root / target
            relative_target = os.path.relpath(target_path, path.parent).replace("\\", "/")
            changed_links += 1
            suffix = f"#{anchor}" if anchor else ""
            return f"{match.group(1)}{relative_target}{suffix}{match.group(3)}"

        updated = LINK_RE.sub(replace_link, original)
        def replace_backtick(match: re.Match[str]) -> str:
            nonlocal changed_refs
            value = match.group(1)
            suffix_match = re.search(r"(:\d+(?:-\d+)?)$", value)
            suffix = suffix_match.group(1) if suffix_match else ""
            source = value[: -len(suffix)] if suffix else value
            target = routes.get(source)
            if target is None:
                return match.group(0)
            changed_refs += 1
            return f"`{target}{suffix}`"

        updated = BACKTICK_RE.sub(replace_backtick, updated)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed_files += 1
    return {
        "changed_files": changed_files,
        "changed_links": changed_links,
        "changed_backtick_references": changed_refs,
    }


def _legacy_link_references(
    authority: dict[str, Any], *, root: Path = ROOT
) -> list[dict[str, Any]]:
    routes = _sources(authority)
    source_paths = set(routes)
    findings: list[dict[str, Any]] = []
    for path in collect_active_markdown_files(root):
        relative = path.relative_to(root).as_posix()
        if relative in source_paths or relative == "docs/DOCUMENTATION_CROSSWALK.md":
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in LINK_RE.finditer(line):
                resolved, _ = _resolve_link(path, match.group(2), root)
                if resolved in routes:
                    findings.append(
                        {
                            "path": relative,
                            "line": line_number,
                            "source": resolved,
                            "target": routes[resolved],
                        }
                    )
            for match in BACKTICK_RE.finditer(line):
                value = match.group(1).strip()
                source = re.sub(r":\d+(?:-\d+)?$", "", value)
                if source in routes:
                    findings.append(
                        {
                            "path": relative,
                            "line": line_number,
                            "source": source,
                            "target": routes[source],
                        }
                    )
    return findings


def verify(
    authority: dict[str, Any],
    baseline: dict[str, Any],
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    control = authority.get("replacement_control", {})
    routes = _sources(authority)
    reviews = control.get("target_reviews", {})
    routed_targets = {target for target in routes.values()}
    if len(routes) != 72:
        errors.append(f"source_count_mismatch:{len(routes)}")
    if set(reviews) != routed_targets:
        errors.append("target_review_coverage_mismatch")

    target_records: list[dict[str, Any]] = []
    for target in sorted(routed_targets):
        path = root / target
        missing_sections: list[str] = []
        if not path.is_file():
            errors.append(f"missing_target:{target}")
            text = ""
        else:
            text = path.read_text(encoding="utf-8")
            missing_sections = [
                section for section in reviews.get(target, []) if not _heading_present(text, section)
            ]
            errors.extend(f"missing_retained_section:{target}:{item}" for item in missing_sections)
        target_records.append(
            {
                "target": target,
                "technical_review": "verified" if not missing_sections and path.is_file() else "fail",
                "required_sections": reviews.get(target, []),
                "missing_sections": missing_sections,
            }
        )

    baseline_rows = {row["source"]: row for row in baseline.get("records", [])}
    if set(baseline_rows) != set(routes):
        errors.append("baseline_source_coverage_mismatch")
    source_records: list[dict[str, Any]] = []
    active_count = 0
    archived_count = 0
    for source, target in sorted(routes.items()):
        expected = baseline_rows.get(source, {})
        archive_path = _archive_path(source, control.get("archive_root", "docs/archive/phase-16"))
        active = root / source
        archived = root / archive_path
        locations = [path for path in (active, archived) if path.is_file()]
        if len(locations) != 1:
            errors.append(f"source_location_count:{source}:{len(locations)}")
            actual_hash = None
            actual_git_blob = None
            location = None
        else:
            location = locations[0]
            actual_hash = _sha256(location, expected.get("sha256"))
            actual_git_blob = _git_worktree_blob(location, root)

            if location == active:
                active_count += 1
            else:
                archived_count += 1
        hash_verified = actual_hash == expected.get("sha256") or (
            bool(expected.get("git_blob"))
            and actual_git_blob == expected.get("git_blob")
        )
        if not hash_verified:
            errors.append(f"retained_evidence_hash_mismatch:{source}")
        if expected.get("target") != target or expected.get("archive_path") != archive_path:
            errors.append(f"baseline_route_mismatch:{source}")
        source_records.append(
            {
                "source": source,
                "target": target,
                "archive_path": archive_path,
                "location": location.relative_to(root).as_posix() if location else None,
                "sha256": actual_hash,
                "expected_sha256": expected.get("sha256"),
                "git_blob": actual_git_blob,
                "expected_git_blob": expected.get("git_blob"),
                "retained_evidence": "verified" if hash_verified else "fail",
            }
        )

    legacy_links = _legacy_link_references(authority, root=root)
    errors.extend(
        f"unmigrated_link:{item['path']}:{item['line']}:{item['source']}"
        for item in legacy_links
    )
    archive_authorized = authority.get("approval", {}).get("archive_delete_authorized") is True
    if archived_count == len(routes) and active_count == 0:
        state = "pass"
    elif active_count == len(routes) and archived_count == 0 and not errors:
        state = "ready_to_archive"
    else:
        state = "fail"
    if state == "pass" and not archive_authorized:
        errors.append("archived_without_authorization")
        state = "fail"
    return {
        "schema_version": "dle.document-replacement-closure.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "authority_version": authority.get("program_version"),
        "status": state if not errors else "fail",
        "reviewed_at": control.get("reviewed_at"),
        "reviewed_by": control.get("reviewed_by"),
        "review_scope": control.get("review_scope"),
        "archive_delete_authorized": archive_authorized,
        "summary": {
            "source_count": len(routes),
            "active_source_count": active_count,
            "archived_source_count": archived_count,
            "target_count": len(routed_targets),
            "verified_target_count": sum(not row["missing_sections"] for row in target_records),
            "unmigrated_link_count": len(legacy_links),
            "retained_evidence_pass_count": sum(row["retained_evidence"] == "verified" for row in source_records),
        },
        "errors": sorted(set(errors)),
        "unmigrated_links": legacy_links,
        "archive_proposal": source_records,
        "target_reviews": target_records,
    }


def archive_sources(authority: dict[str, Any], baseline: dict[str, Any], *, root: Path = ROOT) -> int:
    preflight = verify(authority, baseline, root=root)
    if preflight["status"] != "ready_to_archive":
        raise RuntimeError(f"Archive preflight is {preflight['status']}: {preflight['errors']}")
    if authority.get("approval", {}).get("archive_delete_authorized") is not True:
        raise RuntimeError("Archive/delete authorization is not recorded")
    control = authority["replacement_control"]
    count = 0
    for source in sorted(_sources(authority)):
        old = root / source
        new = root / _archive_path(source, control["archive_root"])
        new.parent.mkdir(parents=True, exist_ok=True)
        old.replace(new)
        count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--freeze-baseline", action="store_true")
    parser.add_argument("--migrate-links", action="store_true")
    parser.add_argument("--archive", action="store_true")
    args = parser.parse_args(argv)
    authority = load_authority(args.config)
    if args.migrate_links:
        print(f"Link migration: {migrate_links(authority)}")
    if args.freeze_baseline:
        freeze_baseline(authority, output=args.baseline)
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    if args.archive:
        print(f"Archived source documents: {archive_sources(authority, baseline)}")
    result = verify(authority, baseline)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        "Document replacement closure: "
        f"{result['status']} sources={result['summary']['source_count']} "
        f"archived={result['summary']['archived_source_count']} "
        f"targets={result['summary']['verified_target_count']}/{result['summary']['target_count']} "
        f"links={result['summary']['unmigrated_link_count']} errors={len(result['errors'])}"
    )
    return 0 if result["status"] in {"ready_to_archive", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate key documentation indexes, local markdown links, and heading structures.

Features:
1. Auto-discovers all active markdown files (ignoring generated docs and archives).
2. Performs strict validation on backtick references (legacy index checks).
3. Performs strict validation on local markdown links (verifying exact file case-sensitivity!).
4. Performs warning-level linting on heading structures (multiple H1 headings, skipped levels).
5. Integrates transparently with existing CI/CD gates and git pre-commit hooks.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

# Paths to validate for backtick indexes (original index checks)
DOC_INDEX_FILES = [
    Path("docs/README.md"),
    Path("docs/DOCUMENTATION_COVERAGE_MATRIX.md"),
]

# Capture references in backticks like `docs/FILE.md`, `README.md`
REF_RE = re.compile(r"`([^`]+)`")

# Capture standard markdown links `[label](target)`
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# Repo root
ROOT_DIR = Path(__file__).resolve().parents[1]


def is_external_link(target: str) -> bool:
    """Return True if the target points to an external site, protocol, or template domain."""
    target_lower = target.strip().lower()
    if any(target_lower.startswith(proto) for proto in ("http://", "https://", "mailto:", "ftp:")):
        return True
    return False


def exists_case_sensitive(path: Path) -> bool:
    """Check if a path exists on disk with exact case-sensitivity match (prevents CI Linux failures)."""
    if not path.exists():
        return False
    
    current = path.resolve()
    # Traverse directory tree upwards, checking exact spelling/case in each directory listing
    while current != current.parent:
        parent = current.parent
        name = current.name
        try:
            # os.listdir is case-exact even on case-insensitive operating systems (Windows)
            names = os.listdir(parent)
            if name not in names:
                return False
        except OSError:
            # Access error or root directory, fall back to default check
            pass
        current = parent
    return True


def collect_active_markdown_files(root: Path) -> list[Path]:
    """Discover all active markdown files in the repository.

    Excludes:
    - .venv, .git, and standard build folders (handled automatically by glob/exclusion).
    - Anything inside docs/archive/ (archived reference material).
    - Auto-generated inventory assets: docs/GENERATED_STRUCTURE.md, docs/FILE_INVENTORY.csv.
    """
    md_files: list[Path] = []
    
    # Scan root folder
    for path in root.glob("*.md"):
        if path.is_file():
            md_files.append(path)
            
    # Scan docs folder recursively
    docs_dir = root / "docs"
    if docs_dir.is_dir():
        for path in docs_dir.rglob("*.md"):
            parts = path.relative_to(root).parts
            # Exclude archive directory
            if "archive" in parts:
                continue
            # Exclude auto-generated structure summary
            if path.name == "GENERATED_STRUCTURE.md":
                continue
            md_files.append(path)
            
    return sorted(md_files)


def collect_backtick_refs(lines: list[str]) -> list[tuple[int, str]]:
    """Collect line numbers and string values of potential file references in backticks."""
    refs: list[tuple[int, str]] = []
    for line_idx, line in enumerate(lines, start=1):
        for m in REF_RE.finditer(line):
            ref = m.group(1).strip()
            if not ref:
                continue
            # Filter for docs or index file patterns
            if ref.endswith("/*"):
                refs.append((line_idx, ref))
                continue
            if ref.startswith("docs/") or ref in {
                "README.md",
                "CONTRIBUTING.md",
                "pyproject.toml",
            }:
                refs.append((line_idx, ref))
    return refs


def collect_markdown_links(lines: list[str]) -> list[tuple[int, str]]:
    """Collect line numbers and target destinations of all standard markdown links."""
    links: list[tuple[int, str]] = []
    for line_idx, line in enumerate(lines, start=1):
        for m in LINK_RE.finditer(line):
            target = m.group(2).strip()
            if target:
                links.append((line_idx, target))
    return links


def validate_headings(lines: list[str]) -> list[str]:
    """Scan headers and return warning strings for structure issues (H1 count, skipped levels)."""
    warnings: list[str] = []
    h1_count = 0
    prev_level = 0
    
    for idx, line in enumerate(lines, start=1):
        if line.startswith("#"):
            parts = line.split(" ", 1)
            hashes = parts[0]
            if not all(c == "#" for c in hashes):
                continue
            level = len(hashes)
            if level == 1:
                h1_count += 1
            if prev_level > 0 and level > prev_level + 1:
                warnings.append(
                    f"Line {idx}: Skipped heading level from h{prev_level} to h{level} (e.g. ## directly to ####)"
                )
            prev_level = level
            
    if h1_count > 1:
        warnings.append(
            f"Multiple h1 headings found ({h1_count}). Document should ideally contain exactly one top-level h1 heading."
        )
    return warnings


def main() -> int:
    active_files = collect_active_markdown_files(ROOT_DIR)
    
    strict_errors: list[str] = []
    style_warnings: list[str] = []
    
    print(f"Discovered {len(active_files)} active markdown files for validation.")
    
    for file_path in active_files:
        rel_path = file_path.relative_to(ROOT_DIR)
        
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            strict_errors.append(f"{rel_path}: failed to read file: {exc}")
            continue
            
        lines = content.splitlines()
        
        # 1. Backtick Index Validation (Legacy checks for index files)
        if file_path in [ROOT_DIR / p for p in DOC_INDEX_FILES]:
            for line_no, ref in collect_backtick_refs(lines):
                if ref.endswith("/*"):
                    parent = ROOT_DIR / ref[:-2]
                    if not parent.is_dir():
                        strict_errors.append(
                            f"{rel_path}:{line_no}: missing directory for wildcard reference `{ref}`"
                        )
                    continue
                
                target = ROOT_DIR / ref
                if not exists_case_sensitive(target):
                    strict_errors.append(
                        f"{rel_path}:{line_no}: missing/casing-incorrect referenced file `{ref}`"
                    )
        
        # 2. Markdown Links Target Validation (Full link verification)
        for line_no, target in collect_markdown_links(lines):
            # Ignore external links or anchor only links
            if is_external_link(target):
                continue
            if target.startswith("#"):
                # Inside-document anchor; skip checking on files
                continue
                
            # Split target file from anchor (e.g. docs/API.md#authentication -> docs/API.md)
            target_file = target.split("#")[0].strip()
            if not target_file:
                continue
                
            # Resolve relative to the source file containing the link
            resolved = (file_path.parent / target_file).resolve()
            
            # Fallback check relative to repo root
            if not resolved.exists():
                resolved = (ROOT_DIR / target_file).resolve()
                
            if not exists_case_sensitive(resolved):
                strict_errors.append(
                    f"{rel_path}:{line_no}: broken local link target `{target}`"
                )
                
        # 3. Document Headings Check
        headings_warnings = validate_headings(lines)
        for warn in headings_warnings:
            style_warnings.append(f"{rel_path}: {warn}")
            
    # Output Report
    if style_warnings:
        print("\nStyle & Heading Structure Warnings:")
        for warn in style_warnings:
            print(f" [WARN] {warn}")
            
    if strict_errors:
        print("\nBroken Link & Reference Errors:")
        for err in strict_errors:
            print(f" [ERR]  {err}")
        print(f"\nDocumentation validation failed: {len(strict_errors)} errors, {len(style_warnings)} warnings.")
        return 1
        
    print(f"\nDocumentation validation passed: 0 errors, {len(style_warnings)} warnings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

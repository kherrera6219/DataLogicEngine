#!/usr/bin/env python3
"""Validate key documentation indexes reference existing local files.

Current scope:
- docs/README.md
- docs/DOCUMENTATION_COVERAGE_MATRIX.md
"""

from __future__ import annotations

import re
from pathlib import Path

DOC_INDEX_FILES = [
    Path("docs/README.md"),
    Path("docs/DOCUMENTATION_COVERAGE_MATRIX.md"),
]

# Capture references like `docs/FILE.md`, `README.md`, `docs/archive/*`
REF_RE = re.compile(r"`([^`]+)`")


def collect_refs(index_file: Path) -> list[tuple[Path, int, str]]:
    refs: list[tuple[Path, int, str]] = []
    lines = index_file.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines, start=1):
        for m in REF_RE.finditer(line):
            ref = m.group(1).strip()
            if not ref:
                continue
            if ref.endswith("/*"):
                ref_path = Path(ref[:-2])
                refs.append((index_file, i, str(ref_path) + "/*"))
                continue
            if ref.startswith("docs/") or ref in {
                "README.md",
                "CONTRIBUTING.md",
                "pyproject.toml",
            }:
                refs.append((index_file, i, ref))
    return refs


def main() -> int:
    missing: list[str] = []

    for index_file in DOC_INDEX_FILES:
        if not index_file.exists():
            missing.append(f"{index_file}: index file not found")
            continue

        for src_file, line, ref in collect_refs(index_file):
            if ref.endswith("/*"):
                parent = Path(ref[:-2])
                if not parent.exists() or not parent.is_dir():
                    missing.append(f"{src_file}:{line}: missing directory for wildcard reference `{ref}`")
                continue

            target = Path(ref)
            if not target.exists():
                missing.append(f"{src_file}:{line}: missing referenced file `{ref}`")

    if missing:
        print("Documentation reference validation failed:")
        for err in missing:
            print(f" - {err}")
        return 1

    print("Documentation reference validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate documentation inventory artifacts.

Outputs:
1. docs/FILE_INVENTORY.csv
2. docs/GENERATED_STRUCTURE.md
"""

from __future__ import annotations

import csv
import os
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_CSV = ROOT_DIR / "docs" / "FILE_INVENTORY.csv"
OUTPUT_STRUCTURE = ROOT_DIR / "docs" / "GENERATED_STRUCTURE.md"

IGNORE_DIRS = {
    ".git",
    ".venv",
    ".idea",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".next",
    "coverage",
    ".pytest_cache",
    "htmlcov",
    "logs",
    "tmp",
    ".gemini",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
}

IGNORE_FILES = {
    ".DS_Store",
    "Thumbs.db",
}

IGNORE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".tmp",
    ".swp",
}

TARGET_DIRS = [
    "backend",
    "core",
    "frontend",
    "routes",
    "scripts",
    "tests",
    "docs",
]

MAX_DEPTH = 3
MAX_ENTRIES_PER_DIR = 40


def _is_ignored_file(path: Path) -> bool:
    if path.name in IGNORE_FILES:
        return True
    return path.suffix.lower() in IGNORE_SUFFIXES


def _file_info(path: Path) -> dict[str, str | int]:
    stats = path.stat()
    return {
        "Path": str(path.relative_to(ROOT_DIR)),
        "Size_Bytes": stats.st_size,
        "Extension": path.suffix,
        "Last_Modified": datetime.fromtimestamp(
            stats.st_mtime,
            tz=timezone.utc,
        ).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def _iter_files() -> list[Path]:
    tracked = _git_tracked_files()
    if tracked:
        return tracked

    files: list[Path] = []
    for root, dirs, names in os.walk(ROOT_DIR):
        dirs[:] = sorted(d for d in dirs if d not in IGNORE_DIRS)
        for name in sorted(names):
            path = Path(root) / name
            if _is_ignored_file(path):
                continue
            files.append(path)
    return files


def _git_tracked_files() -> list[Path]:
    """Return git-tracked files for deterministic, production-focused inventory."""
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT_DIR), "ls-files", "-z"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []

    raw = result.stdout.decode("utf-8", errors="ignore")
    entries = [item for item in raw.split("\0") if item]
    paths: list[Path] = []
    for item in sorted(entries):
        path = ROOT_DIR / item
        if not path.exists():
            continue
        if any(part in IGNORE_DIRS for part in path.relative_to(ROOT_DIR).parts):
            continue
        if _is_ignored_file(path):
            continue
        paths.append(path)
    return paths


def generate_inventory() -> list[dict[str, str | int]]:
    print(f"Scanning {ROOT_DIR}...")
    file_paths = _iter_files()
    inventory: list[dict[str, str | int]] = []
    for path in file_paths:
        try:
            inventory.append(_file_info(path))
        except OSError as exc:
            print(f"Skipping {path}: {exc}")

    inventory.sort(key=lambda row: str(row["Path"]).lower())

    print(f"Writing inventory to {OUTPUT_CSV}...")
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["Path", "Size_Bytes", "Extension", "Last_Modified"],
        )
        writer.writeheader()
        writer.writerows(inventory)

    print(f"Inventory complete. {len(inventory)} files indexed.")
    return inventory


def _format_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024**2:
        return f"{num_bytes / 1024:.1f} KB"
    if num_bytes < 1024**3:
        return f"{num_bytes / (1024**2):.1f} MB"
    return f"{num_bytes / (1024**3):.1f} GB"


def _list_entries(base: Path, depth: int) -> list[Path]:
    entries = [
        item
        for item in base.iterdir()
        if item.name not in IGNORE_DIRS and not _is_ignored_file(item)
    ]
    entries.sort(key=lambda item: (item.is_file(), item.name.lower()))
    return entries[:MAX_ENTRIES_PER_DIR]


def _render_tree(base: Path, prefix: str = "", depth: int = 0) -> list[str]:
    lines: list[str] = []
    if depth > MAX_DEPTH:
        return lines

    entries = _list_entries(base, depth)
    total_entries = len(
        [
            item
            for item in base.iterdir()
            if item.name not in IGNORE_DIRS and not _is_ignored_file(item)
        ]
    )

    for idx, entry in enumerate(entries):
        is_last = idx == len(entries) - 1
        connector = "└──" if is_last else "├──"
        suffix = "/" if entry.is_dir() else ""
        lines.append(f"{prefix}{connector} {entry.name}{suffix}")
        if entry.is_dir() and depth < MAX_DEPTH:
            next_prefix = prefix + ("    " if is_last else "│   ")
            lines.extend(_render_tree(entry, next_prefix, depth + 1))

    if total_entries > len(entries):
        hidden = total_entries - len(entries)
        lines.append(f"{prefix}└── ... ({hidden} additional entries omitted)")
    return lines


def _top_level_count(inventory: list[dict[str, str | int]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in inventory:
        path = Path(str(row["Path"]))
        root = path.parts[0] if len(path.parts) > 1 else "(root)"
        counter[root] += 1
    return counter


def _extension_count(inventory: list[dict[str, str | int]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in inventory:
        ext = str(row["Extension"]) or "(no extension)"
        counter[ext] += 1
    return counter


def generate_structure(inventory: list[dict[str, str | int]]) -> None:
    print(f"Writing structure summary to {OUTPUT_STRUCTURE}...")

    generated_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    total_files = len(inventory)
    total_size = sum(int(row["Size_Bytes"]) for row in inventory)

    top_counts = _top_level_count(inventory)
    ext_counts = _extension_count(inventory)

    lines: list[str] = []
    lines.append("# Generated Repository Structure")
    lines.append("")
    lines.append("This file is generated by `scripts/generate_docs.py`.")
    lines.append("")
    lines.append("## Inventory summary")
    lines.append("")
    lines.append(f"- Generated at: `{generated_at}`")
    lines.append(f"- Root: `{ROOT_DIR}`")
    lines.append(f"- Total files indexed: `{total_files}`")
    lines.append(f"- Total indexed size: `{_format_size(total_size)}`")
    lines.append("")
    lines.append("## Top-level directory distribution")
    lines.append("")
    lines.append("| Directory | File count |")
    lines.append("|---|---:|")
    for directory, count in top_counts.most_common(20):
        lines.append(f"| `{directory}` | {count} |")
    lines.append("")
    lines.append("## Extension distribution")
    lines.append("")
    lines.append("| Extension | File count |")
    lines.append("|---|---:|")
    for ext, count in ext_counts.most_common(25):
        lines.append(f"| `{ext}` | {count} |")
    lines.append("")

    for target in TARGET_DIRS:
        target_path = ROOT_DIR / target
        if not target_path.exists():
            continue
        lines.append(f"## `{target}/`")
        lines.append("")
        lines.append("```text")
        lines.append(f"{target}/")
        lines.extend(_render_tree(target_path, "", 0))
        lines.append("```")
        lines.append("")

    with OUTPUT_STRUCTURE.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(lines).rstrip() + "\n")

    print("Structure summary generated.")


if __name__ == "__main__":
    rows = generate_inventory()
    generate_structure(rows)

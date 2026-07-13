#!/usr/bin/env python3
"""Inventory required-service consumers and fallback references."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports/production-readiness/2026/phase-00/runtime/service-consumers.json"
TOKENS = {
    "postgresql": ("postgresql", "postgres", "psycopg"),
    "redis": ("redis",),
    "neo4j": ("neo4j", "bolt://"),
    "chromadb": ("chromadb", "chroma"),
    "minio": ("minio", "object_store", "object storage", "s3"),
}
FALLBACKS = ("sqlite", "in-memory", "in_memory", "memory fallback", "filesystem", "local file", "mock")
SUFFIXES = {".py", ".ts", ".tsx", ".js", ".yml", ".yaml", ".toml"}
SKIP = {
    ".git", ".venv", "node_modules", ".next", "dist", "dist-electron",
    "dist-smoke", "build", "docs", "reports", "tests", "test-results",
    "out", "storybook-static", "htmlcov", "logs", "__pycache__",
}
SOURCE_ROOTS = [ROOT / "backend", ROOT / "core", ROOT / "frontend", ROOT / "sdk", ROOT / "config", ROOT / "deploy"]
ROOT_FILES = [ROOT / "app.py", ROOT / "main.py", ROOT / "wsgi.py", ROOT / "docker-compose.yml", ROOT / "pyproject.toml"]


def aggregate_by_file(items: list[dict[str, object]], classification: str, target_phase: int) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}
    for item in items:
        file_name = str(item["file"])
        record = grouped.setdefault(
            file_name,
            {
                "file": file_name,
                "matches": 0,
                "samples": [],
                "classification": classification,
                "disposition": "finish",
                "target_phase": target_phase,
            },
        )
        record["matches"] = int(record["matches"]) + 1
        samples = record["samples"]
        if isinstance(samples, list) and len(samples) < 5:
            samples.append({"line": item["line"], "text": item["text"]})
    return sorted(grouped.values(), key=lambda item: str(item["file"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    consumers = {service: [] for service in TOKENS}
    fallbacks: list[dict[str, object]] = []
    candidates = [path for path in ROOT_FILES if path.exists()]
    for source_root in SOURCE_ROOTS:
        for current, directories, files in os.walk(source_root):
            directories[:] = [name for name in directories if name not in SKIP]
            base = Path(current)
            candidates.extend(base / name for name in files)
    for path in candidates:
        if path.suffix not in SUFFIXES:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        relative = str(path.relative_to(ROOT))
        for number, line in enumerate(lines, 1):
            lowered = line.lower()
            for service, tokens in TOKENS.items():
                if any(token in lowered for token in tokens):
                    consumers[service].append({"file": relative, "line": number, "text": line.strip()[:240]})
            if any(token in lowered for token in FALLBACKS):
                fallbacks.append({"file": relative, "line": number, "text": line.strip()[:240], "disposition": "review-required"})
    payload = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "review_status": "text inventory; caller and fallback classification required",
        "summary": {
            **{f"{service}_matching_files": len(aggregate_by_file(items, "required-service-consumer", 3)) for service, items in consumers.items()},
            "fallback_matching_files": len(aggregate_by_file(fallbacks, "fallback-reference", 3)),
        },
        "service_consumers": {
            service: aggregate_by_file(items, "required-service-consumer", 3)
            for service, items in consumers.items()
        },
        "fallback_references": aggregate_by_file(fallbacks, "fallback-reference", 3),
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    print(f"Wrote {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

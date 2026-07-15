#!/usr/bin/env python3
"""Compare normalized release payload inventories from two isolated builds."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def compare_inventories(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    first_rows = {item["label"]: item for item in first.get("inventories", [])}
    second_rows = {item["label"]: item for item in second.get("inventories", [])}
    labels = sorted(set(first_rows) | set(second_rows))
    comparisons = []
    for label in labels:
        left = first_rows.get(label, {})
        right = second_rows.get(label, {})
        comparisons.append(
            {
                "label": label,
                "first_normalized_sha256": left.get("normalized_sha256"),
                "second_normalized_sha256": right.get("normalized_sha256"),
                "first_file_count": left.get("file_count"),
                "second_file_count": right.get("file_count"),
                "matched": bool(left)
                and bool(right)
                and left.get("normalized_sha256") == right.get("normalized_sha256")
                and left.get("file_count") == right.get("file_count"),
            }
        )
    return {
        "schema_version": "dle.release-reproducibility-comparison.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "pass" if comparisons and all(row["matched"] for row in comparisons) else "fail",
        "comparisons": comparisons,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    first = json.loads(args.first.read_text(encoding="utf-8"))
    second = json.loads(args.second.read_text(encoding="utf-8"))
    result = compare_inventories(first, second)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for row in result["comparisons"]:
        print(f"[{'PASS' if row['matched'] else 'FAIL'}] {row['label']}")
    print(f"Report: {args.output}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Enforce the repository's per-scope Python coverage floor.

Coverage reports may be supplied more than once. Executed lines are unioned,
which supports local baseline-plus-targeted qualification without changing the
measured source denominator. CI normally supplies one combined backend/core
report from the complete test suite.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SCOPES = {
    "backend": lambda path: path == "backend" or path.startswith("backend/"),
    "backend/security": lambda path: path.startswith("backend/security/"),
    "core": lambda path: path == "core" or path.startswith("core/"),
}


def _normalized(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def measure_reports(report_paths: list[Path]) -> dict[str, tuple[int, int, float]]:
    statements_by_file: dict[str, set[int]] = {}
    executed_by_file: dict[str, set[int]] = {}

    for report_path in report_paths:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        for raw_path, details in payload.get("files", {}).items():
            path = _normalized(raw_path)
            executed = {int(line) for line in details.get("executed_lines", [])}
            missing = {int(line) for line in details.get("missing_lines", [])}
            statements_by_file.setdefault(path, set()).update(executed | missing)
            executed_by_file.setdefault(path, set()).update(executed)

    measurements: dict[str, tuple[int, int, float]] = {}
    for scope, matches in SCOPES.items():
        paths = [path for path in statements_by_file if matches(path)]
        if not paths:
            raise ValueError(f"Coverage reports contain no files for required scope: {scope}")
        statements = sum(len(statements_by_file[path]) for path in paths)
        covered = sum(
            len(executed_by_file.get(path, set()) & statements_by_file[path])
            for path in paths
        )
        percent = 100.0 * covered / statements if statements else 100.0
        measurements[scope] = (covered, statements, percent)
    return measurements


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        action="append",
        required=True,
        type=Path,
        help="Coverage.py JSON report; repeat to union compatible reports.",
    )
    parser.add_argument("--minimum", type=float, default=80.0)
    args = parser.parse_args()

    missing_reports = [str(path) for path in args.report if not path.is_file()]
    if missing_reports:
        parser.error(f"coverage report not found: {', '.join(missing_reports)}")

    try:
        measurements = measure_reports(args.report)
    except (ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    failures = []
    for scope, (covered, statements, percent) in measurements.items():
        state = "PASS" if percent >= args.minimum else "FAIL"
        print(f"[{state}] {scope}: {percent:.2f}% ({covered:,}/{statements:,}); minimum {args.minimum:.2f}%")
        if percent < args.minimum:
            failures.append(scope)

    if failures:
        print("Coverage gate failed for: " + ", ".join(failures))
        return 1
    print("Coverage gate passed for every required Python scope.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

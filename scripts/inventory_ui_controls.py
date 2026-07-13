#!/usr/bin/env python3
"""Create a review-first inventory of visible React controls and pages."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
DEFAULT_OUTPUT = ROOT / "reports/production-readiness/2026/phase-00/runtime/ui-controls.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    controls: list[dict[str, object]] = []
    pages: list[str] = []
    pattern = re.compile(r"<(button|Button|a|Link|input|select|textarea)\b([^>]*)>")
    for current, directories, files in os.walk(FRONTEND):
        directories[:] = [name for name in directories if name not in {"node_modules", ".next", "dist", "out", "build", "dist-electron", "dist-smoke", "storybook-static", "tests", "test-results", "logs"}]
        base = Path(current)
        for name in files:
            if not name.endswith(".tsx") or name.endswith((".test.tsx", ".spec.tsx")):
                continue
            path = base / name
            relative = str(path.relative_to(ROOT))
            if path.name == "page.tsx":
                pages.append(relative)
            lines = path.read_text(encoding="utf-8").splitlines()
            for number, line in enumerate(lines, 1):
                for match in pattern.finditer(line):
                    attrs = match.group(2)
                    wired = any(token in attrs for token in ("onClick=", "onChange=", "href=", "type=\"submit\"", "type='submit'"))
                    disabled = bool(re.search(r"\bdisabled(?:\s|=|$)", attrs))
                    classification = "disabled" if disabled else ("partial" if wired else "no-op")
                    controls.append({
                        "file": relative,
                        "line": number,
                        "element": match.group(1),
                        "has_obvious_handler_or_target": wired,
                        "disabled_literal": disabled,
                        "classification": classification,
                        "classification_basis": "static JSX heuristic; installed workflow verification required",
                    })
    payload = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "review_status": "initial allowed-state classification; installed behavior verification assigned by feature ledger",
        "summary": {
            "pages": len(pages),
            "controls": len(controls),
            "without_obvious_handler_or_target": sum(not item["has_obvious_handler_or_target"] for item in controls),
        },
        "pages": sorted(pages),
        "controls": controls,
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    print(f"Wrote {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

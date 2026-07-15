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
    pattern = re.compile(
        r"<(button|Button|a|Link|input|select|textarea)\b([^>]*)>",
        re.DOTALL,
    )
    for current, directories, files in os.walk(FRONTEND):
        directories[:] = [name for name in directories if name not in {"node_modules", ".next", "dist", "out", "build", "dist-electron", "dist-smoke", "storybook-static", "stories", "tests", "test-results", "logs"}]
        base = Path(current)
        for name in files:
            if not name.endswith(".tsx") or name.endswith((".test.tsx", ".spec.tsx")):
                continue
            path = base / name
            relative = path.relative_to(ROOT).as_posix()
            if relative.startswith("frontend/components/ui/"):
                continue
            if path.name == "page.tsx":
                pages.append(relative)
            source = path.read_text(encoding="utf-8")
            for match in pattern.finditer(source):
                attrs = match.group(2)
                prefix = source[:match.start()]
                wrapped_by_link = prefix.rfind("<Link") > prefix.rfind("</Link")
                wrapped_by_trigger = bool(
                    re.search(
                        r"<[A-Za-z][A-Za-z0-9.]*Trigger\b[^>]*\basChild\b[^>]*>\s*$",
                        prefix[-500:],
                        re.DOTALL,
                    )
                )
                wired = (
                    any(token in attrs for token in ("onClick=", "onChange=", "href=", "type=\"submit\"", "type='submit'"))
                    or (match.group(1) == "Button" and "asChild" in attrs)
                    or wrapped_by_link
                    or wrapped_by_trigger
                )
                attrs_without_strings = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\'', "", attrs, flags=re.DOTALL)
                disabled_match = re.search(
                    r"\bdisabled\b(?:\s*=\s*(\{[^}]*\}))?",
                    attrs_without_strings,
                )
                disabled_declared = disabled_match is not None
                disabled_value = disabled_match.group(1).strip() if disabled_match and disabled_match.group(1) else None
                disabled = disabled_declared and disabled_value in {None, "{true}", '"true"', "'true'"}
                classification = "disabled" if disabled else ("partial" if wired else "no-op")
                controls.append({
                    "file": relative,
                    "line": source.count("\n", 0, match.start()) + 1,
                    "element": match.group(1),
                    "has_obvious_handler_or_target": wired,
                    "has_disabled_state": disabled_declared,
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
            "enabled_without_obvious_action": sum(item["classification"] == "no-op" for item in controls),
            "disabled_controls": sum(item["classification"] == "disabled" for item in controls),
            "controls_with_disabled_state": sum(item["has_disabled_state"] for item in controls),
            "wired_or_targeted_controls": sum(item["classification"] == "partial" for item in controls),
        },
        "pages": sorted(pages),
        "controls": controls,
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    try:
        display_output = output.relative_to(ROOT)
    except ValueError:
        display_output = output
    print(f"Wrote {display_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

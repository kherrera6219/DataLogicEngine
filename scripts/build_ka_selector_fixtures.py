#!/usr/bin/env python3
"""Generate the canonical CP19-C positive/negative selector fixtures."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.knowledge_algorithms.manifest import load_manifest

OUTPUT_DIR = ROOT / "tests" / "knowledge_algorithms" / "phase19"


def _slug(canonical_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", canonical_id.lower()).strip("_")


def _context(canonical_id: str) -> dict[str, Any]:
    slug = _slug(canonical_id)
    return {
        "request_id": f"cp19c-fixture-{slug}",
        "run_id": f"cp19c-fixture-run-{slug}",
        "workflow": "cp19_c_selector_qualification",
        "budget": {
            "deadline_ms": 3_600_000,
            "max_dependency_executions": 512,
            "max_recursion_depth": 32,
            "max_selected_algorithms": 512,
            "max_fan_out": 128,
            "max_parallelism": 8,
            "max_input_bytes": 1_000_000,
            "max_output_bytes": 5_000_000,
            "max_provider_calls": 0,
            "max_effects": 512,
        },
    }


def build_fixture(canonical_id: str) -> dict[str, Any]:
    reserved = canonical_id == "KA-033"
    positive_disposition = "denied" if reserved else "selected"
    positive_reason = (
        "reserved_disabled" if reserved else "explicit_capability_request"
    )
    negative_request: dict[str, Any]
    negative_expected: dict[str, Any]
    if reserved:
        negative_request = {
            "mode": "evaluation",
            "stages": ["not_applicable_fixture_stage"],
            "context": _context(canonical_id),
        }
        negative_expected = {
            "disposition": "skipped",
            "selected": False,
            "reason": "selector_predicates_not_matched",
        }
    else:
        denied_context = _context(canonical_id)
        denied_context["policy_decisions"] = {
            "denied_ka_ids": [canonical_id]
        }
        negative_request = {
            "mode": "evaluation",
            "requested_ids": [canonical_id],
            "context": denied_context,
        }
        negative_expected = {
            "disposition": "denied",
            "selected": False,
            "reason": "policy_denied",
        }
    return {
        "schema_version": "dle.ka-selector-fixture.v1",
        "canonical_id": canonical_id,
        "positive_selector": {
            "request": {
                "mode": "evaluation",
                "requested_ids": [canonical_id],
                "context": _context(canonical_id),
            },
            "expected": {
                "disposition": positive_disposition,
                "selected": not reserved,
                "reason": positive_reason,
            },
        },
        "negative_selector": {
            "request": negative_request,
            "expected": negative_expected,
        },
    }


def _text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def write_or_check(*, check: bool) -> int:
    manifest = load_manifest()
    expected = {
        OUTPUT_DIR / f"{_slug(canonical_id)}.json": _text(
            build_fixture(canonical_id)
        )
        for canonical_id in manifest.entries
    }
    stale: list[Path] = []
    for path, content in expected.items():
        existing = path.read_text(encoding="utf-8") if path.exists() else None
        if existing != content:
            stale.append(path)
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
    extras = (
        sorted(set(OUTPUT_DIR.glob("*.json")) - set(expected))
        if OUTPUT_DIR.exists()
        else []
    )
    if check and (stale or extras):
        for path in stale:
            print(f"stale: {path.relative_to(ROOT).as_posix()}")
        for path in extras:
            print(f"extra: {path.relative_to(ROOT).as_posix()}")
        return 1
    if not check:
        for path in extras:
            path.unlink()
        print(f"generated {len(expected)} CP19-C selector fixtures")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return write_or_check(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())

"""Run a real Phase 13 resource soak or an explicitly non-qualifying short observation."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.observability.soak import (  # noqa: E402
    SOAK_PROFILES,
    collect_resource_sample,
    evaluate_soak,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=sorted(SOAK_PROFILES), required=True)
    parser.add_argument("--runtime-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--installed-application", action="store_true")
    parser.add_argument(
        "--engineering-duration-seconds",
        type=float,
        help="Shortens the run and forces a non-qualifying engineering result.",
    )
    parser.add_argument("--engineering-interval-seconds", type=float)
    args = parser.parse_args()

    profile = SOAK_PROFILES[args.profile]
    duration = float(profile.required_duration_seconds)
    interval = float(profile.sample_interval_seconds)
    engineering_override = args.engineering_duration_seconds is not None
    if engineering_override:
        if args.engineering_duration_seconds <= 0:
            parser.error("--engineering-duration-seconds must be positive")
        duration = args.engineering_duration_seconds
        interval = args.engineering_interval_seconds or min(1.0, duration / 2)
        if interval <= 0:
            parser.error("--engineering-interval-seconds must be positive")

    started = time.monotonic()
    samples = [collect_resource_sample(args.runtime_root)]
    while time.monotonic() - started < duration:
        remaining = duration - (time.monotonic() - started)
        time.sleep(min(interval, max(0.0, remaining)))
        samples.append(collect_resource_sample(args.runtime_root))
    observed_duration = time.monotonic() - started
    report = evaluate_soak(
        profile,
        samples,
        observed_duration_seconds=observed_duration,
        installed_application=args.installed_application and not engineering_override,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "schema_version",
        "profile",
        "status",
        "resource_checks_passed",
        "qualifies_cp13_e",
    )}, indent=2, sort_keys=True))
    return 0 if report["resource_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

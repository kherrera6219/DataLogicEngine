#!/usr/bin/env python3
"""Developer onboarding and local readiness checks for DataLogicEngine."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

try:
    from scripts import runtime_precheck, verify_environment_parity, verify_lockfiles
except ImportError:  # pragma: no cover - direct script execution fallback
    import runtime_precheck  # type: ignore[no-redef]
    import verify_environment_parity  # type: ignore[no-redef]
    import verify_lockfiles  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Finding:
    area: str
    level: str
    message: str


def _collect_runtime_findings(
    *,
    strict: bool,
    fail_on_warn: bool,
    skip_ports: bool,
    allow_env_from_process: bool,
) -> list[Finding]:
    results: list[runtime_precheck.CheckResult] = []
    with contextlib.redirect_stdout(io.StringIO()):
        for check in (
            runtime_precheck.check_python,
            runtime_precheck.check_node,
            runtime_precheck.check_backend_dependencies,
            runtime_precheck.check_templates_and_static,
        ):
            results.extend(check())
        results.extend(
            runtime_precheck.check_env_files(
                allow_env_from_process=allow_env_from_process,
            )
        )
        if skip_ports:
            results.append(runtime_precheck.CheckResult("INFO", "Port checks skipped"))
        else:
            results.extend(runtime_precheck.check_ports())

    return [
        Finding(area="runtime", level=item.level, message=item.message)
        for item in results
    ]


def _collect_parity_findings(*, strict: bool) -> list[Finding]:
    findings: list[verify_environment_parity.Finding] = []
    findings.extend(verify_environment_parity._check_python(strict=strict))
    findings.extend(verify_environment_parity._check_node(strict=strict))
    findings.extend(verify_environment_parity._check_required_files())
    findings.extend(verify_environment_parity._check_ci_version_pins())
    return [
        Finding(area="parity", level=item.level, message=item.message)
        for item in findings
    ]


def _collect_lockfile_findings() -> list[Finding]:
    findings: list[verify_lockfiles.Finding] = []
    findings.extend(verify_lockfiles._check_uv_lock())
    findings.extend(verify_lockfiles._check_npm_lock())
    return [
        Finding(area="lockfiles", level=item.level, message=item.message)
        for item in findings
    ]


def _check_git_hooks(*, root: Path = ROOT) -> list[Finding]:
    findings: list[Finding] = []
    git_bin = shutil.which("git") or shutil.which("git.exe")
    if not git_bin:
        return [Finding("git", "ERROR", "Git not found in PATH.")]

    findings.append(Finding("git", "OK", f"git found at {git_bin}"))

    hooks_dir = root / ".githooks"
    if hooks_dir.exists():
        findings.append(Finding("git", "OK", f"Found repo hooks directory at {hooks_dir}"))
    else:
        findings.append(
            Finding(
                "git",
                "WARN",
                "Repo hooks directory .githooks is missing; local hook bootstrap cannot be verified.",
            )
        )

    try:
        completed = subprocess.run(
            ["git", "config", "--get", "core.hooksPath"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception as exc:  # noqa: BLE001
        findings.append(Finding("git", "WARN", f"Unable to inspect git hooksPath: {exc}"))
        return findings

    hooks_path = (completed.stdout or "").strip()
    if not hooks_path:
        findings.append(
            Finding(
                "git",
                "ACTION",
                "Git hooks path is not configured. Run `git config core.hooksPath .githooks`.",
            )
        )
        return findings

    normalized = hooks_path.replace("\\", "/").rstrip("/")
    if normalized.endswith(".githooks"):
        findings.append(
            Finding(
                "git",
                "OK",
                f"Git hooks path configured as {hooks_path}.",
            )
        )
    else:
        findings.append(
            Finding(
                "git",
                "WARN",
                f"Git hooks path points to '{hooks_path}' instead of '.githooks'.",
            )
        )
    return findings


def _failure_levels(*, strict: bool, fail_on_warn: bool) -> set[str]:
    levels = {"BLOCKER", "ERROR"}
    if strict:
        levels.add("ACTION")
    if fail_on_warn:
        levels.add("WARN")
    return levels


def _print_section(title: str, findings: list[Finding]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    for finding in findings:
        print(f"[{finding.level}] {finding.message}")


def _write_report(
    path: Path,
    findings: list[Finding],
    *,
    strict: bool,
    fail_on_warn: bool,
    skip_ports: bool,
    allow_env_from_process: bool,
) -> None:
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "strict": strict,
        "fail_on_warn": fail_on_warn,
        "skip_ports": skip_ports,
        "allow_env_from_process": allow_env_from_process,
        "findings": [asdict(item) for item in findings],
        "summary": {
            "ok": sum(1 for item in findings if item.level == "OK"),
            "info": sum(1 for item in findings if item.level == "INFO"),
            "action": sum(1 for item in findings if item.level == "ACTION"),
            "warn": sum(1 for item in findings if item.level == "WARN"),
            "error": sum(1 for item in findings if item.level in {"BLOCKER", "ERROR"}),
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat ACTION findings as failures and require exact CI version parity.",
    )
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Treat WARN findings as failures.",
    )
    parser.add_argument(
        "--skip-ports",
        action="store_true",
        help="Skip local port checks.",
    )
    parser.add_argument(
        "--allow-env-from-process",
        action="store_true",
        help="Allow process-injected env vars when .env/config.env is absent.",
    )
    parser.add_argument(
        "--json-report",
        type=Path,
        default=Path("reports/dev_doctor_report.json"),
        help="Output report path (JSON).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    print("DataLogicEngine developer doctor")
    print("================================")

    findings: list[Finding] = []

    runtime_findings = _collect_runtime_findings(
        strict=args.strict,
        fail_on_warn=args.fail_on_warn,
        skip_ports=args.skip_ports,
        allow_env_from_process=args.allow_env_from_process,
    )
    parity_findings = _collect_parity_findings(strict=args.strict)
    lockfile_findings = _collect_lockfile_findings()
    git_findings = _check_git_hooks()

    findings.extend(runtime_findings)
    findings.extend(parity_findings)
    findings.extend(lockfile_findings)
    findings.extend(git_findings)

    _print_section("Runtime readiness", runtime_findings)
    _print_section("CI parity", parity_findings)
    _print_section("Dependency lockfiles", lockfile_findings)
    _print_section("Git hooks", git_findings)

    failing_levels = _failure_levels(
        strict=args.strict,
        fail_on_warn=args.fail_on_warn,
    )
    failing_findings = [item for item in findings if item.level in failing_levels]

    print("\nSummary")
    print("-------")
    print(f"Findings: {len(findings)}")
    print(f"Fail levels: {', '.join(sorted(failing_levels))}")
    print(f"Blocking findings: {len(failing_findings)}")
    print(f"Action items: {sum(1 for item in findings if item.level == 'ACTION')}")
    print(f"Warnings: {sum(1 for item in findings if item.level == 'WARN')}")

    _write_report(
        args.json_report,
        findings,
        strict=args.strict,
        fail_on_warn=args.fail_on_warn,
        skip_ports=args.skip_ports,
        allow_env_from_process=args.allow_env_from_process,
    )
    print(f"Report: {args.json_report}")

    if failing_findings:
        print("\nDeveloper doctor failed: fix the blocking findings before relying on this environment.")
        return 1

    print("\nDeveloper doctor passed: the local environment meets the required baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

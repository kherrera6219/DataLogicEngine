#!/usr/bin/env python3
"""Verify the authoritative Python and Node release dependency locks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "config" / "dependency-authority.json"
REQUIREMENTS_SOURCE = ROOT / "requirements.txt"
PYTHON_LOCK = ROOT / "requirements.lock"
UV_LOCK = ROOT / "uv.lock"
PYPROJECT = ROOT / "pyproject.toml"
NPM_MANIFEST = ROOT / "frontend" / "package.json"
NPM_LOCK = ROOT / "frontend" / "package-lock.json"
EXPECTED_AUTHORITY_SCHEMA = "dle.dependency-authority.v1"


@dataclass
class Finding:
    level: str
    message: str


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_authority() -> tuple[dict[str, Any] | None, list[Finding]]:
    if not AUTHORITY.is_file():
        return None, [Finding("ERROR", "Missing dependency authority: config/dependency-authority.json")]
    try:
        payload = _load_json(AUTHORITY)
    except (OSError, json.JSONDecodeError) as exc:
        return None, [Finding("ERROR", f"Dependency authority is invalid: {exc}")]
    if payload.get("schema_version") != EXPECTED_AUTHORITY_SCHEMA:
        return payload, [Finding("ERROR", "Unsupported dependency-authority schema version.")]
    return payload, [Finding("OK", "Dependency authority schema is valid.")]


def _direct_requirements(path: Path) -> tuple[dict[str, str], list[Finding]]:
    requirements: dict[str, str] = {}
    findings: list[Finding] = []
    if not path.is_file():
        return requirements, [Finding("ERROR", f"Missing reviewed dependency source: {path.name}")]
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.split(" #", 1)[0].strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(
            r"([A-Za-z0-9_.-]+)(?:\[[^]]+\])?==([^;\s]+)(?:\s*;\s*.+)?",
            line,
        )
        if not match:
            findings.append(
                Finding(
                    "ERROR",
                    f"{path.name}:{line_number} must use one exact == direct dependency pin.",
                )
            )
            continue
        name = _canonical_name(match.group(1))
        version = match.group(2)
        if name in requirements:
            findings.append(Finding("ERROR", f"Duplicate direct dependency pin: {name}."))
        requirements[name] = version
    if requirements:
        findings.append(Finding("OK", f"{path.name} contains {len(requirements)} exact direct pins."))
    return requirements, findings


def _locked_packages(text: str) -> dict[str, tuple[str, bool]]:
    matches = list(re.finditer(r"(?m)^([A-Za-z0-9_.-]+)==([^\\\s;]+)(?:\s*;[^\\\n]+)?\s*\\?\s*$", text))
    packages: dict[str, tuple[str, bool]] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.start():end]
        packages[_canonical_name(match.group(1))] = (match.group(2), "--hash=sha256:" in block)
    return packages


def _check_python_lock() -> list[Finding]:
    direct, findings = _direct_requirements(REQUIREMENTS_SOURCE)
    if not PYTHON_LOCK.is_file():
        findings.append(Finding("ERROR", "Missing generated Python release lock: requirements.lock"))
        return findings
    text = PYTHON_LOCK.read_text(encoding="utf-8")
    source_hash_match = re.search(r"(?m)^# source-sha256: ([0-9a-f]{64})$", text)
    actual_source_hash = _sha256(REQUIREMENTS_SOURCE)
    if source_hash_match and source_hash_match.group(1) == actual_source_hash:
        findings.append(Finding("OK", "requirements.lock matches the reviewed requirements.txt hash."))
    else:
        findings.append(Finding("ERROR", "requirements.lock is stale for the current requirements.txt."))
    if "http://" in text:
        findings.append(Finding("ERROR", "requirements.lock contains an insecure http:// source."))
    else:
        findings.append(Finding("OK", "requirements.lock contains no insecure http:// sources."))

    locked = _locked_packages(text)
    missing_or_drifted = [
        f"{name}=={version}"
        for name, version in direct.items()
        if name not in locked or locked[name][0] != version
    ]
    unhashed = sorted(name for name, (_version, hashed) in locked.items() if not hashed)
    if missing_or_drifted:
        findings.append(
            Finding("ERROR", f"Direct pins missing or drifted in requirements.lock: {missing_or_drifted}")
        )
    else:
        findings.append(Finding("OK", "Every reviewed Python direct pin is present in requirements.lock."))
    if unhashed:
        findings.append(Finding("ERROR", f"Locked Python packages without SHA-256 hashes: {unhashed}"))
    else:
        findings.append(Finding("OK", f"All {len(locked)} locked Python packages carry SHA-256 hashes."))
    return findings


def _check_uv_lock() -> list[Finding]:
    """Enforce the decision to remove the contradictory root uv project lock."""

    findings: list[Finding] = []
    if UV_LOCK.exists():
        findings.append(Finding("ERROR", "uv.lock must be absent; requirements.lock is the Python release lock."))
    else:
        findings.append(Finding("OK", "No contradictory root uv.lock is present."))
    try:
        payload = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
        dependencies = payload.get("project", {}).get("dependencies", [])
    except (OSError, tomllib.TOMLDecodeError) as exc:
        findings.append(Finding("ERROR", f"Unable to parse pyproject.toml: {exc}"))
        return findings
    if dependencies:
        findings.append(
            Finding("ERROR", "pyproject.toml must not carry a second root runtime dependency declaration.")
        )
    else:
        findings.append(Finding("OK", "pyproject.toml correctly delegates runtime dependencies to the release lock."))
    return findings


def _check_npm_lock(authority: dict[str, Any] | None) -> list[Finding]:
    findings: list[Finding] = []
    if not NPM_MANIFEST.is_file() or not NPM_LOCK.is_file():
        return [Finding("ERROR", "Missing frontend/package.json or frontend/package-lock.json.")]
    try:
        manifest = _load_json(NPM_MANIFEST)
        lock = _load_json(NPM_LOCK)
    except (OSError, json.JSONDecodeError) as exc:
        return [Finding("ERROR", f"Unable to parse Node dependency metadata: {exc}")]
    lock_version = int(lock.get("lockfileVersion", 0))
    if lock_version != 3:
        findings.append(Finding("ERROR", f"package-lock.json lockfileVersion must be 3 (found {lock_version})."))
    else:
        findings.append(Finding("OK", "package-lock.json lockfileVersion is 3."))
    root = lock.get("packages", {}).get("", {})
    for field in ("name", "version"):
        if root.get(field) != manifest.get(field) or lock.get(field) != manifest.get(field):
            findings.append(Finding("ERROR", f"Node {field} differs between package.json and package-lock.json."))
        else:
            findings.append(Finding("OK", f"Node {field} matches package.json and package-lock.json."))
    for field in ("dependencies", "devDependencies"):
        if root.get(field, {}) != manifest.get(field, {}):
            findings.append(Finding("ERROR", f"Node {field} drifted between package.json and lock root."))
        else:
            findings.append(Finding("OK", f"Node {field} matches the lock root."))
    expected_electron = (
        authority.get("node", {}).get("electron", {}).get("package_version")
        if authority
        else None
    )
    locked_electron = lock.get("packages", {}).get("node_modules/electron", {}).get("version")
    if expected_electron and locked_electron == expected_electron:
        findings.append(
            Finding("OK", f"Electron release runtime is locked to reviewed version {expected_electron}.")
        )
    else:
        findings.append(
            Finding(
                "ERROR",
                f"Electron lock {locked_electron!r} differs from reviewed authority {expected_electron!r}.",
            )
        )
    serialized = json.dumps(lock)
    if re.search(r"http://[^\"']+", serialized):
        findings.append(Finding("ERROR", "package-lock.json contains an insecure http:// dependency URL."))
    else:
        findings.append(Finding("OK", "package-lock.json contains no insecure http:// dependency URLs."))
    return findings


def _write_report(path: Path, findings: list[Finding], authority: dict[str, Any] | None) -> None:
    payload = {
        "schema_version": "dle.dependency-lock-verification.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "authority": authority,
        "findings": [asdict(item) for item in findings],
        "summary": {
            "ok": sum(1 for item in findings if item.level == "OK"),
            "error": sum(1 for item in findings if item.level == "ERROR"),
            "warn": sum(1 for item in findings if item.level == "WARN"),
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json-report",
        type=Path,
        default=Path("reports/lockfile_governance_report.json"),
        help="Output report path (JSON).",
    )
    args = parser.parse_args(argv)
    authority, findings = _load_authority()
    findings.extend(_check_python_lock())
    findings.extend(_check_uv_lock())
    findings.extend(_check_npm_lock(authority))
    for finding in findings:
        print(f"[{finding.level}] {finding.message}")
    _write_report(args.json_report, findings=findings, authority=authority)
    print(f"Report: {args.json_report}")
    return 1 if any(finding.level == "ERROR" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())

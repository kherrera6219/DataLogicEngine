#!/usr/bin/env python3
"""Verify every release-facing version against config/product-versions.json."""

from __future__ import annotations

import argparse
import ast
import json
import re
import tomllib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "config" / "product-versions.json"


@dataclass(frozen=True, slots=True)
class VersionCheck:
    surface: str
    expected: str
    actual: str
    passed: bool


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def _migration_heads(root: Path) -> set[str]:
    revisions: set[str] = set()
    parents: set[str] = set()
    for path in (root / "migrations" / "versions").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        values: dict[str, Any] = {}
        for node in tree.body:
            if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                continue
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in {"revision", "down_revision"}:
                values[target.id] = ast.literal_eval(node.value)
        revision = values.get("revision")
        down_revision = values.get("down_revision")
        if isinstance(revision, str):
            revisions.add(revision)
        if isinstance(down_revision, str):
            parents.add(down_revision)
        elif isinstance(down_revision, (tuple, list)):
            parents.update(str(item) for item in down_revision)
    return revisions - parents


def _semver_core(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[-+].*)?", value)
    if not match:
        raise ValueError(f"Invalid semantic version: {value}")
    return tuple(int(part) for part in match.groups())


def collect_checks(root: Path = ROOT) -> list[VersionCheck]:
    authority = _json(root / "config" / "product-versions.json")
    product_version = str(authority["product"]["version"])
    contracts = authority["contracts"]
    sdks = authority["sdks"]
    frontend = _json(root / "frontend" / "package.json")
    frontend_lock = _json(root / "frontend" / "package-lock.json")
    pyproject = _toml(root / "pyproject.toml")
    python_sdk = _toml(root / "sdk" / "UKG_Python_SDK" / "pyproject.toml")
    typescript_sdk = _json(root / "sdk" / "DataLogicEngine_TypeScript_SDK" / "package.json")
    provider_manifest = _json(root / "config" / "provider_manifest.v1.json")
    builder = (root / "frontend" / "electron-builder.yml").read_text(encoding="utf-8")
    next_config = (root / "frontend" / "next.config.ts").read_text(encoding="utf-8")
    about_page = (root / "frontend" / "app" / "about" / "page.tsx").read_text(encoding="utf-8")
    spec = (root / "backend.spec").read_text(encoding="utf-8")
    app_text = (root / "app.py").read_text(encoding="utf-8")
    external_contract = (root / "backend" / "llm_gateway" / "external_contract.py").read_text(
        encoding="utf-8"
    )
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    released_versions = re.findall(r"(?m)^## \[([0-9]+\.[0-9]+\.[0-9]+)\]", changelog)
    latest_released = max(released_versions, key=_semver_core)

    lock_root = frontend_lock.get("packages", {}).get("", {})
    heads = _migration_heads(root)
    checks = [
        VersionCheck("pyproject", product_version, str(pyproject["project"]["version"]), pyproject["project"]["version"] == product_version),
        VersionCheck("frontend-package", product_version, str(frontend.get("version")), frontend.get("version") == product_version),
        VersionCheck("frontend-lock", product_version, str(frontend_lock.get("version")), frontend_lock.get("version") == product_version),
        VersionCheck("frontend-lock-root", product_version, str(lock_root.get("version")), lock_root.get("version") == product_version),
        VersionCheck("python-sdk", str(sdks["python"]), str(python_sdk["project"]["version"]), python_sdk["project"]["version"] == sdks["python"]),
        VersionCheck("typescript-sdk", str(sdks["typescript"]), str(typescript_sdk.get("version")), typescript_sdk.get("version") == sdks["typescript"]),
        VersionCheck("provider-manifest", str(contracts["provider_manifest"]), str(provider_manifest.get("schema_version")), provider_manifest.get("schema_version") == contracts["provider_manifest"]),
        VersionCheck("data-plane-schema", str(contracts["data_plane_schema"]), ",".join(sorted(heads)), heads == {contracts["data_plane_schema"]}),
        VersionCheck("electron-artifact-name", "version macro", "present" if "${version}" in builder else "missing", "${version}" in builder),
        VersionCheck("electron-update-signature", "true", "true" if re.search(r"(?m)^\s*verifyUpdateCodeSignature:\s*true\s*$", builder) else "false", bool(re.search(r"(?m)^\s*verifyUpdateCodeSignature:\s*true\s*$", builder))),
        VersionCheck("changelog-lineage", f">={latest_released}", product_version, _semver_core(product_version) >= _semver_core(latest_released)),
        VersionCheck("next-build-injection", "authority", "present" if "product-versions.json" in next_config and "NEXT_PUBLIC_APP_VERSION" in next_config else "missing", "product-versions.json" in next_config and "NEXT_PUBLIC_APP_VERSION" in next_config),
        VersionCheck("about-ui", "NEXT_PUBLIC_APP_VERSION", "present" if "NEXT_PUBLIC_APP_VERSION" in about_page else "missing", "NEXT_PUBLIC_APP_VERSION" in about_page),
        VersionCheck("frozen-bundle", "config/product-versions.json", "present" if "product-versions.json" in spec else "missing", "product-versions.json" in spec),
        VersionCheck("backend-file-version", "build/backend-version-info.txt", "present" if "backend-version-info.txt" in spec else "missing", "backend-version-info.txt" in spec),
        VersionCheck("backend-runtime", "PRODUCT_VERSION", "present" if "PRODUCT_VERSION" in app_text else "missing", "PRODUCT_VERSION" in app_text),
        VersionCheck("gateway-contract", "authority reference", "present" if 'CONTRACT_VERSIONS["gateway"]' in external_contract else "missing", 'CONTRACT_VERSIONS["gateway"]' in external_contract),
        VersionCheck("virtual-model-manifest", "authority reference", "present" if 'CONTRACT_VERSIONS["virtual_model_manifest"]' in external_contract else "missing", 'CONTRACT_VERSIONS["virtual_model_manifest"]' in external_contract),
    ]
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/production-readiness/2026/phase-14/product-version-parity.json"),
    )
    args = parser.parse_args(argv)
    checks = collect_checks()
    payload = {
        "schema_version": "dle.product-version-parity.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "authority": str(AUTHORITY.relative_to(ROOT)).replace("\\", "/"),
        "checks": [asdict(check) for check in checks],
        "passed": all(check.passed for check in checks),
    }
    report = args.report if args.report.is_absolute() else ROOT / args.report
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for check in checks:
        print(f"[{'PASS' if check.passed else 'FAIL'}] {check.surface}: {check.actual}")
    print(f"Report: {report}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

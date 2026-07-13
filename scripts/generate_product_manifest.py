#!/usr/bin/env python3
"""Generate the Phase 0 machine-readable product and version manifest."""

from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import tomllib
from datetime import UTC, datetime
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports/production-readiness/2026/phase-00/runtime/product-manifest.json"


def read_toml(path: Path) -> dict:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def run(command: list[str]) -> str | None:
    executable = shutil.which(command[0]) or shutil.which(f"{command[0]}.cmd")
    if executable:
        command = [executable, *command[1:]]
    try:
        result = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return (result.stdout or result.stderr).strip() or None


def package_version(name: str) -> str | None:
    package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    return package.get("dependencies", {}).get(name) or package.get("devDependencies", {}).get(name)


def model_defaults() -> dict[str, str]:
    text = (ROOT / "backend/llm_gateway/model_defaults.py").read_text(encoding="utf-8")
    values: dict[str, str] = {}
    for constant in ("OPENAI_LATEST_MODEL", "GOOGLE_LATEST_MODEL"):
        match = re.search(rf'^\s*{constant}\s*=\s*["\']([^"\']+)', text, re.MULTILINE)
        if match:
            values[constant.removesuffix("_LATEST_MODEL").lower()] = match.group(1)
    return values


def compose_services() -> dict[str, dict[str, object]]:
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8")) or {}
    output: dict[str, dict[str, object]] = {}
    for name, config in (compose.get("services") or {}).items():
        output[name] = {
            "image": config.get("image"),
            "container_name": config.get("container_name"),
            "ports": config.get("ports", []),
            "depends_on": config.get("depends_on", []),
        }
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    backend = read_toml(ROOT / "pyproject.toml")["project"]
    sdk = read_toml(ROOT / "sdk/UKG_Python_SDK/pyproject.toml")["project"]
    frontend = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    services = compose_services()
    required_services = ["postgresql", "redis", "neo4j", "chromadb", "minio"]
    compose_mapping = {
        "postgresql": "db",
        "redis": "redis",
        "neo4j": "neo4j",
        "chromadb": "chroma",
        "minio": "minio",
    }
    missing = [service for service, compose_name in compose_mapping.items() if compose_name not in services]
    broad_tags = {
        name: item["image"]
        for name, item in services.items()
        if item.get("image") and (str(item["image"]).endswith(":latest") or "@sha256:" not in str(item["image"]))
    }

    payload = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "authority": "PRODUCTION_COMPLETION_PLAN_2026.md v1.2.0",
        "git": {
            "head": run(["git", "rev-parse", "HEAD"]),
            "branch": run(["git", "branch", "--show-current"]),
            "working_tree_changes": len((run(["git", "status", "--porcelain"]) or "").splitlines()),
        },
        "product": {
            "name": "DataLogicEngine Desktop",
            "target": "local-first Windows 11 x64 governed LLM middleware",
            "backend_version": backend.get("version"),
            "frontend_version": frontend.get("version"),
            "sdk_version": sdk.get("version"),
            "installer_channel": "latest-local-qc",
        },
        "runtime": {
            "python_required": backend.get("requires-python"),
            "python_detected": platform.python_version(),
            "node_required": frontend.get("engines", {}).get("node"),
            "node_detected": run(["node", "--version"]),
            "npm_required": frontend.get("engines", {}).get("npm"),
            "npm_detected": run(["npm", "--version"]),
            "electron_constraint": package_version("electron"),
            "next_constraint": package_version("next"),
        },
        "api": {
            "public_prefix": "/api/v1",
            "public_contract_version": "unified-version-pending-phase-0",
            "schema_version": "cross-store-contract-pending-phase-4",
            "gateway_profiles": ["loopback-default", "private-windows-pending-qualification"],
        },
        "providers": {
            "supported": ["openai", "google"],
            "default_models": model_defaults(),
        },
        "internal_services": {
            "required": required_services,
            "compose": services,
            "missing_from_compose": missing,
            "non_immutable_image_references": broad_tags,
        },
        "known_manifest_gaps": [
            "Product, frontend, and SDK versions are not unified.",
            "Public API and cross-store schema versions are not yet authoritative.",
            *(["Required ChromaDB service is absent from docker-compose.yml."] if "chromadb" in missing else []),
            *(["One or more service images are not pinned by immutable digest."] if broad_tags else []),
        ],
    }

    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output.relative_to(ROOT)}")
    print(f"Missing required Compose services: {', '.join(missing) or 'none'}")
    print(f"Non-immutable image references: {len(broad_tags)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

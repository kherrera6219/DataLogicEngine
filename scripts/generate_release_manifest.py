#!/usr/bin/env python3
"""Generate the authoritative source/build/release inventory for DataLogicEngine."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports/production-readiness/2026/phase-14/release-manifest.json"
BUILD_INPUTS = (
    "config/product-versions.json",
    "config/dependency-authority.json",
    "config/release-trust-policy.json",
    "config/release-channel.json",
    "config/legacy-retirement.json",
    "requirements.txt",
    "requirements.lock",
    "pyproject.toml",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/electron-builder.yml",
    "backend.spec",
    "deploy/internal-data-plane.candidate-lock.json",
)
PYTHON_COMPONENTS = (
    "pyinstaller",
    "psycopg2-binary",
    "redis",
    "neo4j",
    "chromadb",
    "boto3",
    "cryptography",
)
NODE_COMPONENTS = (
    "electron",
    "electron-builder",
    "next",
    "@cyclonedx/cyclonedx-npm",
)


def _python_runtime_matches(required: str, detected: str) -> bool:
    required_parts = required.split(".")
    detected_parts = detected.split(".")
    return len(required_parts) >= 2 and detected_parts[:2] == required_parts[:2]


def _node_runtime_matches(required_major: int, detected: str | None) -> bool:
    match = re.fullmatch(r"v(\d+)(?:\.\d+){2}", detected or "")
    return bool(match and int(match.group(1)) == required_major)




def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(root: Path, command: list[str]) -> str | None:
    executable = shutil.which(command[0]) or shutil.which(f"{command[0]}.cmd")
    if executable:
        command = [executable, *command[1:]]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return (completed.stdout or completed.stderr).strip() or None


def _python_lock_versions(path: Path) -> dict[str, str]:
    versions: dict[str, str] = {}
    for match in re.finditer(r"(?m)^([A-Za-z0-9_.-]+)==([^\\\s;]+)", path.read_text(encoding="utf-8")):
        name = re.sub(r"[-_.]+", "-", match.group(1)).lower()
        versions[name] = match.group(2)
    return versions


def _node_lock_versions(lock: dict[str, Any]) -> dict[str, str | None]:
    packages = lock.get("packages", {})
    return {
        name: packages.get(f"node_modules/{name}", {}).get("version")
        for name in NODE_COMPONENTS
    }


def _artifact_inventory(root: Path, expected_installer: str) -> dict[str, Any]:
    installer_paths = sorted(root.glob("DataLogicEngine Setup *.exe"))
    rows: list[dict[str, Any]] = []
    for artifact in installer_paths:
        rows.append(
            {
                "path": artifact.relative_to(root).as_posix(),
                "size_bytes": artifact.stat().st_size,
                "sha256": _sha256(artifact),
                "canonical_version": artifact.name == expected_installer,
                "checksum_sidecar": (root / f"{artifact.name}.sha256").is_file(),
                "blockmap": (root / f"{artifact.name}.blockmap").is_file(),
            }
        )
    backend = root / "dist" / "DataLogic_Backend" / "DataLogic_Backend.exe"
    portable = root / "frontend" / "dist" / "win-unpacked" / "DataLogicEngine Desktop.exe"
    return {
        "expected_installer": expected_installer,
        "installers": rows,
        "backend_executable": {
            "path": backend.relative_to(root).as_posix(),
            "present": backend.is_file(),
            "sha256": _sha256(backend) if backend.is_file() else None,
        },
        "portable_executable": {
            "path": portable.relative_to(root).as_posix(),
            "present": portable.is_file(),
            "sha256": _sha256(portable) if portable.is_file() else None,
        },
    }


def build_manifest(root: Path) -> dict[str, Any]:
    product = _json(root / "config" / "product-versions.json")
    dependencies = _json(root / "config" / "dependency-authority.json")
    trust = _json(root / "config" / "release-trust-policy.json")
    release_channel = _json(root / "config" / "release-channel.json")
    service_lock = _json(root / "deploy" / "internal-data-plane.candidate-lock.json")
    npm_lock = _json(root / "frontend" / "package-lock.json")
    python_versions = _python_lock_versions(root / "requirements.lock")
    product_version = str(product["product"]["version"])
    expected_installer = f"DataLogicEngine Setup {product_version}.exe"
    artifacts = _artifact_inventory(root, expected_installer)
    raw_status_lines = (_run(root, ["git", "status", "--porcelain"]) or "").splitlines()
    status_lines = [
        line
        for line in raw_status_lines
        if not (line.startswith("?? reports/") or line.startswith("?? reports\\"))
    ]
    detected_python = platform.python_version()
    detected_node = _run(root, ["node", "--version"])
    git_head = _run(root, ["git", "rev-parse", "HEAD"])

    build_inputs = []
    for relative_path in BUILD_INPUTS:
        path = root / relative_path
        build_inputs.append(
            {
                "path": relative_path,
                "present": path.is_file(),
                "sha256": _sha256(path) if path.is_file() else None,
            }
        )

    release_blockers: list[str] = []
    if status_lines:
        release_blockers.append("source_worktree_not_clean")
    if not _python_runtime_matches(dependencies["python"]["python_version"], detected_python):
        release_blockers.append("release_python_runtime_mismatch")
    if not _node_runtime_matches(dependencies["node"]["release_build_node_major"], detected_node):
        release_blockers.append("release_node_runtime_mismatch")
    if not any(row["canonical_version"] for row in artifacts["installers"]):
        release_blockers.append("canonical_versioned_installer_not_built")
    if any(not row["canonical_version"] for row in artifacts["installers"]):
        release_blockers.append("stale_or_noncanonical_installer_present")
    if trust.get("signing", {}).get("production_authorized") is not True:
        release_blockers.append("production_signing_authority_not_approved")
    if trust.get("updates", {}).get("production_qualified") is not True:
        release_blockers.append("signed_updates_not_qualified")
    if trust.get("distribution", {}).get("authority_approved") is not True:
        release_blockers.append("distribution_authority_not_approved")
    if (
        release_channel.get("channel") != "production"
        or release_channel.get("data_plane_profile") != "production"
        or release_channel.get("production_authorized") is not True
    ):
        release_blockers.append("release_channel_is_candidate_only")
    if service_lock.get("production_provisioning_authorized") is not True:
        release_blockers.append("internal_data_plane_is_candidate_only")
    if service_lock.get("architecture_change_authorized") is not True:
        release_blockers.append("object_store_replacement_control_open")
    signature_inventory_path = (
        root
        / "reports"
        / "production-readiness"
        / "2026"
        / "phase-14"
        / "binary-signature-inventory.json"
    )
    try:
        signature_inventory = _json(signature_inventory_path)
    except (OSError, json.JSONDecodeError):
        signature_inventory = None
    if not signature_inventory or signature_inventory.get("status") != "pass":
        release_blockers.append("embedded_release_binaries_not_signature_verified")
    release_blockers.append("neo4j_embedded_jre_inventory_requires_final_image_sbom")

    electron = dependencies["node"]["electron"]
    python_components = {name: python_versions.get(name) for name in PYTHON_COMPONENTS}
    manifest = {
        "schema_version": "dle.release-manifest.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "release_ready" if not release_blockers else "engineering_only_blocked_for_release",
        "authority": {
            "product_versions": "config/product-versions.json",
            "dependencies": "config/dependency-authority.json",
            "release_trust": "config/release-trust-policy.json",
            "release_channel": "config/release-channel.json",
            "legacy_retirement": "config/legacy-retirement.json",
            "internal_data_plane": "deploy/internal-data-plane.candidate-lock.json",
        },
        "source": {
            "commit": git_head,
            "branch": _run(root, ["git", "branch", "--show-current"]),
            "tag": _run(root, ["git", "describe", "--tags", "--exact-match"]),
            "clean": not status_lines,
            "change_count": len(status_lines),
        },
        "product": product,
        "runtime": {
            "release_python": dependencies["python"]["python_version"],
            "detected_python": detected_python,
            "detected_python_executable": sys.executable,
            "release_build_node_major": dependencies["node"]["release_build_node_major"],
            "detected_node": detected_node,
            "detected_npm": _run(root, ["npm", "--version"]),
            "electron": {
                "package": _node_lock_versions(npm_lock)["electron"],
                "chromium": electron["chromium_version"],
                "embedded_node": electron["embedded_node_version"],
                "metadata": electron["official_release_metadata"],
            },
            "python_components": python_components,
            "node_components": _node_lock_versions(npm_lock),
        },
        "internal_data_plane": {
            "status": service_lock.get("status"),
            "runtime": service_lock.get("runtime"),
            "services": service_lock.get("services"),
            "jre": {
                "delivery": "embedded_in_pinned_neo4j_service_image",
                "exact_version": None,
                "evidence_required": "final service-image and installer SBOM",
            },
        },
        "build_inputs": build_inputs,
        "artifacts": artifacts,
        "binary_signature_inventory": signature_inventory,
        "release_blockers": sorted(set(release_blockers)),
    }
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--require-clean", action="store_true")
    parser.add_argument("--require-artifacts", action="store_true")
    parser.add_argument("--require-release-authority", action="store_true")
    args = parser.parse_args(argv)

    root = args.repo_root.resolve()
    manifest = build_manifest(root)
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    failures: list[str] = []
    if args.require_clean and not manifest["source"]["clean"]:
        failures.append("release build source is not clean")
    if args.require_artifacts:
        installers = manifest["artifacts"]["installers"]
        if not any(row["canonical_version"] for row in installers):
            failures.append("canonical versioned installer is missing")
        if any(not row["canonical_version"] for row in installers):
            failures.append("stale/noncanonical installer is present")
    if args.require_release_authority and manifest["release_blockers"]:
        failures.extend(manifest["release_blockers"])

    print(f"Release manifest: {output}")
    print(f"Status: {manifest['status']}")
    print(f"Release blockers: {len(manifest['release_blockers'])}")
    for failure in failures:
        print(f"[FAIL] {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Compose dependency and service SBOMs around the final installer artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compose_installer_sbom(
    installer: Path,
    product_version: str,
    child_sboms: list[tuple[str, Path, dict[str, Any]]],
) -> dict[str, Any]:
    installer_ref = f"installer:datalogicengine:{product_version}"
    components: list[dict[str, Any]] = []
    dependency_refs: list[str] = []
    for source, path, sbom in child_sboms:
        ref = f"sbom:{source}:{_sha256(path)}"
        dependency_refs.append(ref)
        components.append(
            {
                "type": "data",
                "bom-ref": ref,
                "name": f"DataLogicEngine {source} component SBOM",
                "version": str(sbom.get("version", 1)),
                "hashes": [{"alg": "SHA-256", "content": _sha256(path)}],
                "properties": [
                    {"name": "dle.source", "value": path.name},
                    {
                        "name": "dle.componentCount",
                        "value": str(len(sbom.get("components", []))),
                    },
                ],
            }
        )
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(UTC).isoformat(),
            "component": {
                "type": "file",
                "bom-ref": installer_ref,
                "name": installer.name,
                "version": product_version,
                "hashes": [{"alg": "SHA-256", "content": _sha256(installer)}],
            },
            "properties": [
                {
                    "name": "dle.compositionScope",
                    "value": "backend-lock,frontend-lock,service-assets",
                },
                {
                    "name": "dle.fileInventory",
                    "value": "release-content-inventory.json",
                },
            ],
        },
        "components": components,
        "dependencies": [{"ref": installer_ref, "dependsOn": dependency_refs}],
        "compositions": [{"aggregate": "complete", "assemblies": dependency_refs}],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installer", type=Path, required=True)
    parser.add_argument("--backend-sbom", type=Path, required=True)
    parser.add_argument("--frontend-sbom", type=Path, required=True)
    parser.add_argument("--services-sbom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    product = json.loads((ROOT / "config" / "product-versions.json").read_text(encoding="utf-8"))
    child_paths = [
        ("backend", args.backend_sbom),
        ("frontend", args.frontend_sbom),
        ("services", args.services_sbom),
    ]
    child_sboms = [
        (name, path, json.loads(path.read_text(encoding="utf-8")))
        for name, path in child_paths
    ]
    payload = compose_installer_sbom(
        args.installer,
        str(product["product"]["version"]),
        child_sboms,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Installer SBOM: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

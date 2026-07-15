#!/usr/bin/env python3
"""Generate a CycloneDX SBOM for pinned internal runtime and service assets."""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _digest_hash(value: str | None) -> list[dict[str, str]]:
    if value and value.startswith("sha256:") and len(value) == 71:
        return [{"alg": "SHA-256", "content": value.removeprefix("sha256:")}]
    return []


def _license(value: str) -> dict[str, dict[str, str]]:
    aliases = {
        "AGPL-3.0-selected-from-tri-license": "AGPL-3.0-only",
        "GPL-3.0": "GPL-3.0-only",
    }
    return {"license": {"id": aliases.get(value, value)}}


def build_service_sbom(lock: dict[str, Any], product_version: str) -> dict[str, Any]:
    components: list[dict[str, Any]] = []
    runtime = lock["runtime"]
    components.append(
        {
            "type": "application",
            "bom-ref": f"runtime:podman:{runtime['version']}",
            "name": runtime["name"],
            "version": runtime["version"],
            "hashes": [
                {"alg": "SHA-256", "content": runtime["windows_x64_msi_sha256"]}
            ],
            "licenses": [_license(runtime["license"])],
            "properties": [
                {"name": "dle.productionApproved", "value": "false"},
                {"name": "dle.assetRole", "value": "container-runtime-candidate"},
            ],
        }
    )
    for name, service in lock["services"].items():
        product = service.get("product", name)
        image = str(service["image"])
        index_digest = image.rsplit("@", 1)[-1] if "@" in image else None
        component = {
            "type": "container",
            "bom-ref": f"service:{name}:{service['version']}",
            "name": product,
            "version": service["version"],
            "hashes": _digest_hash(index_digest),
            "licenses": [_license(service["license"])],
            "externalReferences": [
                {"type": "distribution", "url": image},
            ],
            "properties": [
                {
                    "name": "dle.linuxAmd64Digest",
                    "value": str(service["linux_amd64_digest"]),
                },
                {
                    "name": "dle.productionApproved",
                    "value": str(bool(service.get("production_approved"))).lower(),
                },
                {"name": "dle.assetRole", "value": name},
            ],
        }
        components.append(component)

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(UTC).isoformat(),
            "component": {
                "type": "application",
                "bom-ref": f"product:datalogicengine:{product_version}",
                "name": "DataLogicEngine Desktop internal data plane",
                "version": product_version,
            },
            "properties": [
                {"name": "dle.lockStatus", "value": str(lock["status"])},
                {
                    "name": "dle.productionProvisioningAuthorized",
                    "value": str(bool(lock["production_provisioning_authorized"])).lower(),
                },
                {
                    "name": "dle.architectureChangeAuthorized",
                    "value": str(bool(lock["architecture_change_authorized"])).lower(),
                },
            ],
        },
        "components": components,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lock",
        type=Path,
        default=ROOT / "deploy" / "internal-data-plane.candidate-lock.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/production-readiness/2026/phase-14/sbom-services.cdx.json"),
    )
    args = parser.parse_args(argv)
    lock = json.loads(args.lock.read_text(encoding="utf-8"))
    product = json.loads((ROOT / "config" / "product-versions.json").read_text(encoding="utf-8"))
    payload = build_service_sbom(lock, str(product["product"]["version"]))
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Service asset SBOM: {output} ({len(payload['components'])} components)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

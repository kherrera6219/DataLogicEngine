"""Authoritative product and compatibility versions for source and frozen builds."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


VERSION_AUTHORITY_SCHEMA = "dle.product-versions.v1"
_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")


def _authority_candidates() -> tuple[Path, ...]:
    source_root = Path(__file__).resolve().parents[1]
    candidates = [source_root / "config" / "product-versions.json"]
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        candidates.insert(0, Path(bundle_root) / "config" / "product-versions.json")
    return tuple(candidates)


def load_version_authority(path: str | Path | None = None) -> dict[str, Any]:
    """Load and minimally validate the single checked-in version authority."""

    if path is not None:
        candidates = (Path(path),)
    else:
        candidates = _authority_candidates()
    authority_path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if authority_path is None:
        raise RuntimeError("product_version_authority_missing")

    try:
        payload = json.loads(authority_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("product_version_authority_invalid") from exc
    if payload.get("schema_version") != VERSION_AUTHORITY_SCHEMA:
        raise RuntimeError("product_version_authority_schema_unsupported")

    product = payload.get("product")
    contracts = payload.get("contracts")
    sdks = payload.get("sdks")
    if not isinstance(product, dict) or not isinstance(contracts, dict) or not isinstance(sdks, dict):
        raise RuntimeError("product_version_authority_incomplete")
    product_version = str(product.get("version") or "")
    if not _SEMVER.fullmatch(product_version):
        raise RuntimeError("product_version_authority_semver_invalid")
    required_contracts = {
        "public_api",
        "governed_execution",
        "gateway",
        "virtual_model_manifest",
        "provider_manifest",
        "data_plane_schema",
    }
    if any(not str(contracts.get(key) or "").strip() for key in required_contracts):
        raise RuntimeError("product_version_contract_authority_incomplete")
    if any(not str(sdks.get(key) or "").strip() for key in ("python", "typescript")):
        raise RuntimeError("product_version_sdk_authority_incomplete")
    return payload


VERSION_AUTHORITY = load_version_authority()
PRODUCT_VERSION = str(VERSION_AUTHORITY["product"]["version"])
WINDOWS_FILE_VERSION = str(VERSION_AUTHORITY["product"]["windows_file_version"])
CONTRACT_VERSIONS: Mapping[str, str] = MappingProxyType(
    {key: str(value) for key, value in VERSION_AUTHORITY["contracts"].items()}
)
SDK_VERSIONS: Mapping[str, str] = MappingProxyType(
    {key: str(value) for key, value in VERSION_AUTHORITY["sdks"].items()}
)
SUPPORTED_UPGRADE_SOURCES = tuple(
    str(value) for value in VERSION_AUTHORITY.get("upgrade", {}).get("supported_product_sources", [])
)


def version_summary() -> Mapping[str, Any]:
    """Return a content-free immutable summary for manifests and diagnostics."""

    return MappingProxyType(
        {
            "product_version": PRODUCT_VERSION,
            "windows_file_version": WINDOWS_FILE_VERSION,
            "contracts": CONTRACT_VERSIONS,
            "sdks": SDK_VERSIONS,
        }
    )

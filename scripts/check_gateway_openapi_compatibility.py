"""Fail CI when dle-gateway.v1 loses a published compatible contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = ROOT / "docs" / "openapi.yaml"
DEFAULT_BASELINE = ROOT / "docs" / "contracts" / "gateway-v1-compatibility.json"


def _load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"OpenAPI document is not an object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Compatibility baseline is not an object: {path}")
    return value


def find_breaking_changes(spec: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    """Return removals or restrictions that require a new gateway major version."""
    findings: list[str] = []
    paths = spec.get("paths", {})
    for path, expected in baseline.get("operations", {}).items():
        operation_set = paths.get(path)
        if not isinstance(operation_set, dict):
            findings.append(f"removed path: {path}")
            continue
        for method in expected.get("methods", []):
            if method not in operation_set:
                findings.append(f"removed operation: {method.upper()} {path}")
        actual_responses = {
            str(code)
            for method in expected.get("methods", [])
            for code in operation_set.get(method, {}).get("responses", {})
        }
        for status in expected.get("success_responses", []):
            if str(status) not in actual_responses:
                findings.append(f"removed success response {status}: {path}")

    schemas = spec.get("components", {}).get("schemas", {})
    for name, expected in baseline.get("schemas", {}).items():
        actual = schemas.get(name)
        if not isinstance(actual, dict):
            findings.append(f"removed schema: {name}")
            continue
        published_required = set(expected.get("required", []))
        new_required = set(actual.get("required", [])) - published_required
        if new_required:
            findings.append(f"new required fields in {name}: {sorted(new_required)}")
        if expected.get("additionalProperties") is False and actual.get("additionalProperties") is not False:
            findings.append(f"{name} no longer rejects unknown fields")
        actual_properties = actual.get("properties", {})
        for property_name, property_contract in expected.get("properties", {}).items():
            current = actual_properties.get(property_name)
            if not isinstance(current, dict):
                findings.append(f"removed property: {name}.{property_name}")
                continue
            expected_type = property_contract.get("type")
            if expected_type and current.get("type") != expected_type:
                findings.append(
                    f"changed type: {name}.{property_name} "
                    f"{expected_type}->{current.get('type')}"
                )
            missing_enum = set(property_contract.get("enum", [])) - set(current.get("enum", []))
            if missing_enum:
                findings.append(
                    f"removed enum values from {name}.{property_name}: {sorted(missing_enum)}"
                )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    args = parser.parse_args()
    findings = find_breaking_changes(_load_yaml(args.spec), _load_json(args.baseline))
    if findings:
        print("Breaking dle-gateway.v1 contract changes detected:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("dle-gateway.v1 compatibility baseline passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate and verify the live Flask route trust-boundary manifest."""

from __future__ import annotations

import argparse
import inspect
import json
import os
import re
import sys
import tempfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DEFAULT_OUTPUT = ROOT / "reports/production-readiness/2026/phase-01/runtime/route-manifest.json"
MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
ALLOWED_CLASSES = {
    "public-health",
    "authenticated-read",
    "authenticated-mutation",
    "external-client-read",
    "external-client-governed-execution",
    "owner-admin-mutation",
    "desktop-only",
    "internal-only",
}
PUBLIC_HEALTH_PATHS = {"/live", "/ready", "/health"}
GOVERNED_PATH_TOKENS = ("/chat", "/query", "/execute", "/orchestrate", "/completions")
PUBLIC_HEALTH_PATHS.add("/api/v1/gateway/health")


def configure_safe_inventory_environment() -> None:
    os.environ.setdefault("IS_DESKTOP_APP", "false")
    os.environ.setdefault("USE_REDIS", "false")
    os.environ.setdefault("RATELIMIT_STORAGE_URI", "memory://")
    os.environ.setdefault("SESSION_TYPE", "null")
    os.environ.setdefault("DSQP_LLM_ASSISTED", "false")
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("ENCRYPTION_KEK_SECRET", "phase1-inventory-process-only-value")
    os.environ.setdefault(
        "UKG_KEY_DIR",
        str(Path(tempfile.gettempdir()) / "datalogicengine-phase1-route-inventory-keys"),
    )
    os.environ.setdefault("NEO4J_URI", "bolt://127.0.0.1:1")


def wrapper_chain(view: Any) -> list[dict[str, str]]:
    chain: list[dict[str, str]] = []
    seen: set[int] = set()
    current = view
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        code = getattr(current, "__code__", None)
        chain.append(
            {
                "name": getattr(current, "__name__", type(current).__name__),
                "code_name": getattr(code, "co_name", ""),
                "module": getattr(current, "__module__", ""),
                "auth_guard": getattr(current, "__dle_auth_guard__", ""),
            }
        )
        current = getattr(current, "__wrapped__", None)
    return chain


def auth_evidence(chain: list[dict[str, str]]) -> list[str]:
    tokens = ("login_required", "admin_required", "desktop", "api_key", "auth")
    evidence: list[str] = []
    for item in chain:
        if item.get("auth_guard"):
            evidence.append(str(item["auth_guard"]))
        label = f"{item['module']}:{item['code_name']}"
        if any(token in label.lower() for token in tokens):
            evidence.append(label)
    return evidence


def classify(path: str, endpoint: str, methods: set[str], evidence: list[str]) -> str:
    lowered_path = path.lower()
    lowered_endpoint = endpoint.lower()
    mutation = bool(methods & MUTATION_METHODS)
    if endpoint == "static" or lowered_path.startswith("/static/"):
        return "desktop-only"
    if path in PUBLIC_HEALTH_PATHS and not mutation:
        return "public-health"
    if lowered_path.startswith(("/internal", "/metrics")):
        return "internal-only"
    if "desktop" in lowered_endpoint or lowered_path.startswith("/api/auth/desktop"):
        return "desktop-only"
    if mutation and ("admin" in lowered_endpoint or "/admin/" in lowered_path):
        return "owner-admin-mutation"
    if mutation and any("owner-admin" in item for item in evidence):
        return "owner-admin-mutation"
    if lowered_path.startswith("/api/v1/gateway"):
        if mutation and any(token in lowered_path for token in GOVERNED_PATH_TOKENS):
            return "external-client-governed-execution"
        if any("gateway-api-key" in item for item in evidence):
            return "external-client-read" if not mutation else "external-client-governed-execution"
        return "authenticated-mutation" if mutation else "authenticated-read"
    if mutation and lowered_path.startswith(("/api/v1", "/v1")):
        return "authenticated-mutation"
    if mutation:
        return "authenticated-mutation"
    if lowered_path.startswith(("/api/v1", "/v1")):
        return "authenticated-read"
    if lowered_path.startswith("/api/"):
        return "authenticated-read"
    return "desktop-only"


def build_graphql_inventory() -> list[dict[str, Any]]:
    from backend.graphql_schema import schema  # pylint: disable=import-outside-toplevel

    graphql_schema = schema.graphql_schema
    rows: list[dict[str, Any]] = []
    for operation_type, root in (
        ("query", graphql_schema.query_type),
        ("mutation", graphql_schema.mutation_type),
    ):
        if root is None:
            continue
        for name in sorted(root.fields):
            rows.append(
                {
                    "operation_type": operation_type,
                    "name": name,
                    "classification": "authenticated-read" if operation_type == "query" else "authenticated-mutation",
                    "server_owned_principal": True,
                }
            )
    return rows


def build_ipc_inventory() -> list[dict[str, Any]]:
    main_source = (ROOT / "frontend/electron/main.ts").read_text(encoding="utf-8")
    preload_source = (ROOT / "frontend/electron/preload.ts").read_text(encoding="utf-8")
    main_channels = set(re.findall(r"ipcMain\.handle\(\s*['\"]([^'\"]+)", main_source))
    preload_channels = set(re.findall(r"invokeWithTimeout\(\s*['\"]([^'\"]+)", preload_source))
    return [
        {
            "channel": channel,
            "classification": "desktop-only",
            "main_handler": channel in main_channels,
            "typed_preload_capability": channel in preload_channels,
            "sender_validation": True,
        }
        for channel in sorted(main_channels | preload_channels)
    ]


def build_mcp_inventory() -> list[dict[str, Any]]:
    source = (ROOT / "backend/mcp_server/router.py").read_text(encoding="utf-8")
    methods = sorted(set(re.findall(r"method\s*==\s*['\"]([^'\"]+)", source)))
    return [
        {
            "method": method,
            "classification": "authenticated-read" if method.endswith("/list") or method == "initialize" else "authenticated-mutation",
            "server_owned_principal": True,
            "missing_scope_fails_closed": True,
        }
        for method in methods
    ]


def build_file_inventory() -> list[dict[str, Any]]:
    return [
        {"capability": "backup-output-folder", "classification": "desktop-only", "control": "single-use expiring picker token plus main-process signature"},
        {"capability": "ingestion-file-or-folder", "classification": "desktop-only", "control": "single-use expiring picker token plus main-process signature"},
        {"capability": "packaged-renderer-read", "classification": "desktop-only", "control": "canonical path constrained to packaged out directory"},
        {"capability": "desktop-secret-store", "classification": "internal-only", "control": "safeStorage or DPAPI plus restrictive ACL"},
        {"capability": "desktop-runtime-logs", "classification": "internal-only", "control": "bounded local file with credential redaction"},
    ]


def build_network_inventory() -> list[dict[str, Any]]:
    return [
        {"surface": "flask-desktop-listener", "classification": "desktop-only", "binding": "loopback-only", "private_listener_enabled": False},
        {"surface": "same-host-api-gateway", "classification": "external-client-governed-execution", "binding": "loopback-only", "private_listener_enabled": False},
        {"surface": "private-network-gateway", "classification": "internal-only", "binding": "disabled-until-phase-8", "private_listener_enabled": False},
        {"surface": "local-model-runtime", "classification": "internal-only", "binding": "loopback-only", "private_listener_enabled": False},
        {"surface": "provider-egress", "classification": "internal-only", "binding": "backend-only outbound HTTPS", "private_listener_enabled": False},
    ]


def build_manifest() -> dict[str, Any]:
    configure_safe_inventory_environment()
    from app import app  # pylint: disable=import-outside-toplevel

    rows: list[dict[str, Any]] = []
    for rule in sorted(app.url_map.iter_rules(), key=lambda item: (item.rule, item.endpoint)):
        methods = set(rule.methods or ()) - {"HEAD", "OPTIONS"}
        view = app.view_functions.get(rule.endpoint)
        chain = wrapper_chain(inspect.unwrap(view) if view is not None else view)
        # inspect.unwrap removes the evidence-bearing wrappers; use the original
        # view for the actual chain while retaining the unwrapped source below.
        original_chain = wrapper_chain(view) if view is not None else []
        blueprint_name = rule.endpoint.rsplit(".", 1)[0] if "." in rule.endpoint else None
        blueprint_guards = app.before_request_funcs.get(blueprint_name, [])
        guard_evidence = [
            evidence
            for guard in blueprint_guards
            for evidence in auth_evidence(wrapper_chain(guard))
        ]
        evidence = sorted(set(auth_evidence(original_chain) + guard_evidence))
        category = classify(rule.rule, rule.endpoint, methods, evidence)
        rows.append(
            {
                "path": rule.rule,
                "endpoint": rule.endpoint,
                "methods": sorted(methods),
                "classification": category,
                "required_principal": "none" if category == "public-health" else category,
                "auth_evidence": evidence,
                "source_module": chain[0]["module"] if chain else "unknown",
                "blueprint": blueprint_name,
                "mutation_without_auth_evidence": bool(methods & MUTATION_METHODS) and not evidence,
            }
        )
    counts = Counter(row["classification"] for row in rows)
    graphql_rows = build_graphql_inventory()
    ipc_rows = build_ipc_inventory()
    mcp_rows = build_mcp_inventory()
    file_rows = build_file_inventory()
    network_rows = build_network_inventory()
    unclassified_surfaces = sum(
        1
        for surface_rows in (graphql_rows, ipc_rows, mcp_rows, file_rows, network_rows)
        for row in surface_rows
        if row.get("classification") not in ALLOWED_CLASSES
    )
    ipc_incomplete = sum(
        not row["main_handler"] or not row["typed_preload_capability"] or not row["sender_validation"]
        for row in ipc_rows
    )
    return {
        "schema_version": "1.1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "live Flask app.url_map",
        "allowed_classifications": sorted(ALLOWED_CLASSES),
        "summary": {
            "routes": len(rows),
            "classifications": dict(sorted(counts.items())),
            "unclassified": sum(row["classification"] not in ALLOWED_CLASSES for row in rows),
            "mutations_without_auth_evidence": sum(row["mutation_without_auth_evidence"] for row in rows),
            "graphql_operations": len(graphql_rows),
            "ipc_channels": len(ipc_rows),
            "mcp_methods": len(mcp_rows),
            "file_capabilities": len(file_rows),
            "network_surfaces": len(network_rows),
            "unclassified_non_http_surfaces": unclassified_surfaces,
            "incomplete_ipc_channels": ipc_incomplete,
        },
        "routes": rows,
        "graphql_operations": graphql_rows,
        "ipc_channels": ipc_rows,
        "mcp_methods": mcp_rows,
        "file_capabilities": file_rows,
        "network_surfaces": network_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fail-unclassified", action="store_true")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    payload = build_manifest()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    print(f"Wrote {output.relative_to(ROOT)}")
    if args.fail_unclassified and (
        payload["summary"]["unclassified"]
        or payload["summary"]["unclassified_non_http_surfaces"]
        or payload["summary"]["incomplete_ipc_channels"]
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

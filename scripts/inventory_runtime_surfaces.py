#!/usr/bin/env python3
"""Inventory runtime entry points for Phase 0 classification."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports/production-readiness/2026/phase-00/runtime/runtime-surfaces.json"
SKIP_PARTS = {
    ".git", ".venv", "node_modules", ".next", "dist", "dist-electron",
    "dist-smoke", "build", "docs", "reports", "tests", "test-results",
    "out", "storybook-static", "htmlcov", "logs", "__pycache__",
}
SOURCE_ROOTS = [ROOT / "backend", ROOT / "core", ROOT / "frontend", ROOT / "sdk"]
ROOT_FILES = [ROOT / "app.py", ROOT / "main.py", ROOT / "wsgi.py"]


def source_files(suffixes: set[str]):
    for path in ROOT_FILES:
        if path.suffix in suffixes and path.exists():
            yield path
    for source_root in SOURCE_ROOTS:
        for current, directories, files in os.walk(source_root):
            directories[:] = [name for name in directories if name not in SKIP_PARTS]
            base = Path(current)
            for name in files:
                path = base / name
                if path.suffix in suffixes:
                    yield path


def route_inventory() -> list[dict[str, object]]:
    routes: list[dict[str, object]] = []
    for path in source_files({".py"}):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for index, line in enumerate(lines):
            match = re.search(r"@[^\s]+\.route\((['\"])(.*?)\1(.*)", line)
            if not match:
                continue
            decorator_block = [line.strip()]
            function_name = "unknown"
            for following in lines[index + 1 : index + 12]:
                stripped = following.strip()
                if stripped.startswith("@"):
                    decorator_block.append(stripped)
                function_match = re.match(r"(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
                if function_match:
                    function_name = function_match.group(1)
                    break
            joined = " ".join(lines[index : index + 4])
            methods_match = re.search(r"methods\s*=\s*\[([^]]+)]", joined)
            methods = re.findall(r"['\"]([A-Z]+)['\"]", methods_match.group(1)) if methods_match else ["GET"]
            auth = [item for item in decorator_block if any(token in item.lower() for token in ("auth", "login", "admin", "key", "desktop"))]
            route_path = match.group(2)
            lowered_file = str(path.relative_to(ROOT)).lower()
            if "admin" in lowered_file or route_path.startswith("/api/admin"):
                classification = "administration"
            elif route_path.startswith(("/api/v1", "/v1")):
                classification = "client-gateway"
            elif route_path.startswith(("/health", "/live", "/ready", "/metrics")):
                classification = "internal-service"
            else:
                classification = "desktop-only"
            routes.append({
                "file": str(path.relative_to(ROOT)),
                "line": index + 1,
                "function": function_name,
                "path": route_path,
                "methods": methods,
                "auth_decorators": auth,
                "classification": classification,
                "authorization_boundary": "decorator-present" if auth else "review-required",
            })
    return routes


def regex_inventory(pattern: str, suffixes: set[str], kind: str) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    compiled = re.compile(pattern)
    for path in source_files(suffixes):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, 1):
            for match in compiled.finditer(line):
                output.append({"kind": kind, "file": str(path.relative_to(ROOT)), "line": number, "value": match.group(1)})
    return output


def summarize_urls(items: list[dict[str, object]]) -> list[dict[str, object]]:
    domains: dict[str, dict[str, object]] = {}
    for item in items:
        value = str(item["value"])
        try:
            domain = urlparse(value).netloc.lower()
        except ValueError:
            continue
        if not domain:
            continue
        record = domains.setdefault(domain, {"domain": domain, "matches": 0, "samples": []})
        record["matches"] = int(record["matches"]) + 1
        samples = record["samples"]
        if isinstance(samples, list) and len(samples) < 5:
            samples.append({"value": value, "file": item["file"], "line": item["line"]})
    return sorted(domains.values(), key=lambda item: str(item["domain"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    routes = route_inventory()
    ipc = regex_inventory(r"ipcMain\.(?:handle|on)\(\s*['\"]([^'\"]+)", {".ts", ".js"}, "electron-ipc")
    for item in ipc:
        item["classification"] = "desktop-only"
        item["authorization_boundary"] = "electron-preload-ipc"
    graphql = regex_inventory(
        r"(?:@(?:query|mutation|subscription)\.(?:field|resolver)|type\s+(?:Query|Mutation|Subscription)|extend\s+type\s+(?:Query|Mutation|Subscription))[^\n]*?([A-Za-z_][A-Za-z0-9_]*)?",
        {".py", ".ts", ".tsx", ".js"},
        "graphql-operation",
    )
    realtime = regex_inventory(
        r"(?:socketio\.on|@[^\s]+\.websocket|text/event-stream|EventSource\(|new\s+WebSocket\()[^\n'\"]*['\"]?([^'\"\s,)]+)?",
        {".py", ".ts", ".tsx", ".js"},
        "websocket-sse",
    )
    preload = regex_inventory(
        r"contextBridge\.exposeInMainWorld\(\s*['\"]([^'\"]+)",
        {".ts", ".js"},
        "preload-export",
    )
    mcp = regex_inventory(
        r"(?:@(?:mcp|server)\.(?:tool|resource|prompt)|['\"](?:tools/call|tools/list|resources/read|resources/list|prompts/get|prompts/list)['\"])[^\n]*?([A-Za-z_][A-Za-z0-9_./-]*)?",
        {".py", ".ts", ".tsx", ".js"},
        "mcp-method",
    )
    local_files = regex_inventory(
        r"(?:showOpenDialog|showSaveDialog|readFile|writeFile|createReadStream|createWriteStream|Path\()[^\n'\"]*['\"]([^'\"]+)['\"]",
        {".py", ".ts", ".tsx", ".js"},
        "local-file-entry",
    )
    for item in graphql:
        item["classification"] = "client-gateway"
        item["authorization_boundary"] = "review-required"
    for item in realtime:
        item["classification"] = "client-gateway"
        item["authorization_boundary"] = "review-required"
    for item in preload:
        item["classification"] = "desktop-only"
        item["authorization_boundary"] = "electron-preload"
    for item in mcp:
        item["classification"] = "administration"
        item["authorization_boundary"] = "review-required"
    for item in local_files:
        item["classification"] = "desktop-only"
        item["authorization_boundary"] = "file-capability-review-required"
    url_matches = regex_inventory(r"(https?://[^\s'\"`)]+)", {".py", ".ts", ".tsx", ".js"}, "external-url")
    urls = summarize_urls(url_matches)
    for item in urls:
        item["classification"] = "external-network"
        item["authorization_boundary"] = "egress-allowlist-review-required"
    payload = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "review_status": "machine inventory with initial classification; manual contract verification required",
        "summary": {
            "flask_routes": len(routes),
            "graphql_operations": len(graphql),
            "electron_ipc": len(ipc),
            "websocket_sse": len(realtime),
            "preload_exports": len(preload),
            "mcp_methods": len(mcp),
            "local_file_entries": len(local_files),
            "external_domains": len(urls),
        },
        "flask_routes": routes,
        "graphql_operations": graphql,
        "electron_ipc": ipc,
        "websocket_sse": realtime,
        "preload_exports": preload,
        "mcp_methods": mcp,
        "local_file_entries": local_files,
        "external_network_domains": urls,
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    print(f"Wrote {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

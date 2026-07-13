"""Fail when application/route imports directly start mutable runtime resources."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DISALLOWED_CALLS = {
    "AuditLogger",
    "AudioService",
    "AxisSystem",
    "DocumentProcessor",
    "EncryptionManager",
    "GraphDatabase.driver",
    "GraphStore",
    "LLMGateway",
    "MCPManager",
    "MCPSubscriptionManager",
    "MCPSamplingService",
    "ObjectStore",
    "OpenAI",
    "Thread",
    "UnifiedMemoryService",
    "VectorStore",
    "VideoService",
    "asyncio.new_event_loop",
    "create_multi_agent_simulation_engine",
    "get_graph_store",
    "get_object_store",
    "get_unified_memory_service",
    "get_vector_store",
    "initialize_collections",
    "os.makedirs",
}


def _call_name(node: ast.Call) -> str:
    parts: list[str] = []
    value = node.func
    while isinstance(value, ast.Attribute):
        parts.append(value.attr)
        value = value.value
    if isinstance(value, ast.Name):
        parts.append(value.id)
    return ".".join(reversed(parts))


def _module_scope_calls(tree: ast.Module):
    for statement in tree.body:
        values = []
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            values.append(statement.value)
        elif isinstance(statement, ast.Expr):
            values.append(statement.value)
        for value in values:
            if value is None:
                continue
            yield from (node for node in ast.walk(value) if isinstance(node, ast.Call))


def _target_files() -> list[Path]:
    targets = [ROOT / "app.py", ROOT / "extensions.py"]
    for pattern in (
        "backend/routes/*.py",
        "backend/*_api.py",
        "backend/services/*.py",
        "backend/mcp_server/*.py",
        "backend/storage/*.py",
        "backend/memory/*.py",
    ):
        targets.extend(ROOT.glob(pattern))
    return sorted({path.resolve() for path in targets if path.is_file()})


def build_report() -> dict:
    violations = []
    targets = _target_files()
    for path in targets:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for call in _module_scope_calls(tree):
            name = _call_name(call)
            if name in DISALLOWED_CALLS or name.endswith(".start"):
                violations.append(
                    {
                        "file": path.relative_to(ROOT).as_posix(),
                        "line": call.lineno,
                        "call": name,
                    }
                )
    return {
        "schema_version": 1,
        "scanned_files": len(targets),
        "violation_count": len(violations),
        "violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", dest="json_path", type=Path)
    args = parser.parse_args()
    report = build_report()
    encoded = json.dumps(report, indent=2, sort_keys=True)
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(f"{encoded}\n", encoding="utf-8")
    print(encoded)
    return 1 if report["violation_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

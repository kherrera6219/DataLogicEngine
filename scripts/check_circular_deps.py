"""Analyze Python imports and fail when a real dependency cycle is found."""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ModuleSource:
    name: str
    path: Path
    is_package: bool


def _module_name(root: Path, path: Path) -> ModuleSource:
    relative = path.relative_to(root)
    parts = list(relative.with_suffix("").parts)
    is_package = parts[-1] == "__init__"
    if is_package:
        parts.pop()
    return ModuleSource(".".join(parts), path, is_package)


def _resolve_from_module(source: ModuleSource, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    package_parts = source.name.split(".") if source.is_package else source.name.split(".")[:-1]
    keep = max(0, len(package_parts) - (node.level - 1))
    resolved = package_parts[:keep]
    if node.module:
        resolved.extend(node.module.split("."))
    return ".".join(part for part in resolved if part)


def _match_module(candidate: str, module_names: set[str]) -> str | None:
    current = candidate
    while current:
        if current in module_names:
            return current
        current = current.rpartition(".")[0]
    return None


def build_import_graph(
    root: Path,
    source_roots: Iterable[str] = ("backend", "core"),
) -> tuple[dict[str, set[str]], list[dict[str, str]], int]:
    root = root.resolve()
    sources: dict[str, ModuleSource] = {}
    for source_root in source_roots:
        directory = (root / source_root).resolve()
        if not directory.is_dir() or root not in directory.parents:
            continue
        for path in sorted(directory.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            source = _module_name(root, path)
            if source.name:
                sources[source.name] = source

    module_names = set(sources)
    graph = {name: set() for name in module_names}
    parse_errors: list[dict[str, str]] = []
    for name, source in sources.items():
        try:
            tree = ast.parse(source.path.read_text(encoding="utf-8"), filename=str(source.path))
        except (OSError, SyntaxError, UnicodeError) as exc:
            parse_errors.append(
                {"module": name, "path": str(source.path), "error": str(exc)}
            )
            continue

        for node in ast.walk(tree):
            candidates: list[str] = []
            if isinstance(node, ast.Import):
                candidates.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                base = _resolve_from_module(source, node)
                if base:
                    candidates.append(base)
                    candidates.extend(
                        f"{base}.{alias.name}"
                        for alias in node.names
                        if alias.name != "*"
                    )
            for candidate in candidates:
                dependency = _match_module(candidate, module_names)
                if dependency and dependency != name:
                    graph[name].add(dependency)

    return graph, parse_errors, len(sources)


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Return strongly connected components that contain a real cycle."""
    index = 0
    indexes: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    cycles: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indexes[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for dependency in sorted(graph[node]):
            if dependency not in indexes:
                visit(dependency)
                lowlinks[node] = min(lowlinks[node], lowlinks[dependency])
            elif dependency in on_stack:
                lowlinks[node] = min(lowlinks[node], indexes[dependency])

        if lowlinks[node] != indexes[node]:
            return
        component: list[str] = []
        while stack:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == node:
                break
        if len(component) > 1:
            cycles.append(sorted(component))

    for node in sorted(graph):
        if node not in indexes:
            visit(node)
    return sorted(cycles)


def analyze_dependencies(root: Path, source_roots: Iterable[str]) -> dict[str, object]:
    graph, parse_errors, scanned_files = build_import_graph(root, source_roots)
    cycles = find_cycles(graph)
    return {
        "schema_version": "dle.python-import-analysis.v1",
        "scanned_files": scanned_files,
        "module_count": len(graph),
        "parse_errors": parse_errors,
        "cycles": cycles,
        "cycle_count": len(cycles),
        "passed": not parse_errors and not cycles,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--source-root", action="append", dest="source_roots")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    source_roots = args.source_roots or ["backend", "core"]
    result = analyze_dependencies(args.root, source_roots)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if args.json:
        print(rendered)
    else:
        print(
            f"Analyzed {result['scanned_files']} Python files; "
            f"found {result['cycle_count']} cycles and "
            f"{len(result['parse_errors'])} parse errors."
        )
        for cycle in result["cycles"]:
            print("cycle: " + " -> ".join(cycle))
        for error in result["parse_errors"]:
            print(f"parse-error: {error['path']}: {error['error']}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reject direct exception values in public return statements."""

from __future__ import annotations

import ast
import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = (ROOT / "backend",)
ROOT_FILES = (ROOT / "app.py",)
SAFE_NORMALIZERS = {
    "normalize_public_error_message",
    "_public_error",
    "_policy_error",  # Typed MCPPolicyError exposes code-owned public_message only.
    "_workflow_error_response",  # Typed KA workflow errors expose public_message.
    "errors",
}


def call_name(node: ast.Call) -> str:
    function = node.func
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return ""


class ExceptionReferenceFinder(ast.NodeVisitor):
    def __init__(self, exception_name: str) -> None:
        self.exception_name = exception_name
        self.found = False
        self._safe_depth = 0

    def visit_Call(self, node: ast.Call) -> None:
        safe = call_name(node) in SAFE_NORMALIZERS
        self._safe_depth += int(safe)
        self.generic_visit(node)
        self._safe_depth -= int(safe)

    def visit_Name(self, node: ast.Name) -> None:
        if self._safe_depth == 0 and node.id == self.exception_name:
            self.found = True


def findings_for(path: Path) -> list[dict[str, object]]:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (UnicodeDecodeError, SyntaxError):
        return []
    findings: list[dict[str, object]] = []
    functions = (
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    for function in functions:
        public_handler = any(
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr in {"route", "errorhandler"}
            for decorator in function.decorator_list
        )
        if not public_handler:
            continue
        for handler in (
            node for node in ast.walk(function) if isinstance(node, ast.ExceptHandler)
        ):
            if not handler.name:
                continue
            for node in handler.body:
                for child in ast.walk(node):
                    if not isinstance(child, ast.Return) or child.value is None:
                        continue
                    finder = ExceptionReferenceFinder(handler.name)
                    finder.visit(child.value)
                    if finder.found:
                        findings.append(
                            {
                                "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                                "line": child.lineno,
                                "function": function.name,
                                "exception": handler.name,
                                "rule": "direct-exception-in-public-return",
                            }
                        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-report", type=Path)
    args = parser.parse_args()
    paths = list(ROOT_FILES)
    for source_root in SOURCE_ROOTS:
        paths.extend(source_root.rglob("*.py"))
    findings = [finding for path in paths for finding in findings_for(path)]
    result = {"files_scanned": len(paths), "findings": findings, "passed": not findings}
    print(json.dumps(result, indent=2))
    if args.json_report:
        output = args.json_report if args.json_report.is_absolute() else ROOT / args.json_report
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())

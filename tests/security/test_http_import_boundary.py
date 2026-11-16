"""Prevent direct HTTP-client imports in the installed backend and core."""

import ast
from pathlib import Path

import pytest


HTTP_CLIENTS = {"requests", "httpx", "aiohttp"}


def _direct_client_imports(source: str) -> list[tuple[int, str]]:
    found = []
    tree = ast.parse(source)
    module_aliases = {"importlib": {"importlib"}, "builtins": {"builtins"}}
    loader_aliases = {"__import__"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in module_aliases:
                    module_aliases[alias.name].add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module in {"importlib", "builtins"}:
                for alias in node.names:
                    if (node.module, alias.name) in {
                        ("importlib", "import_module"),
                        ("builtins", "__import__"),
                    }:
                        loader_aliases.add(alias.asname or alias.name)
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        elif (
            isinstance(node, ast.Call)
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            func = node.func
            if isinstance(func, ast.Name) and func.id in loader_aliases:
                names = [node.args[0].value]
            elif (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and (
                    (
                        func.value.id in module_aliases["importlib"]
                        and func.attr == "import_module"
                    )
                    or (
                        func.value.id in module_aliases["builtins"]
                        and func.attr == "__import__"
                    )
                )
            ):
                names = [node.args[0].value]
        found.extend(
            (node.lineno, name) for name in names if name.split(".")[0] in HTTP_CLIENTS
        )
    return found


@pytest.mark.parametrize(
    "source",
    [
        "import requests as client",
        "from httpx import Client",
        "def load():\n    import aiohttp",
        "__import__('requests.sessions')",
        "importlib.import_module('httpx')",
        "import importlib as loader\nloader.import_module('requests')",
        "from importlib import import_module as load\nload('httpx')",
        "import builtins as b\nb.__import__('aiohttp')",
    ],
)
def test_import_scan_identifies_direct_and_literal_dynamic_imports(source):
    assert _direct_client_imports(source)


def test_installed_application_imports_http_clients_only_in_guard():
    root = Path(__file__).resolve().parents[2]
    guard = root / "core" / "security" / "egress_guard.py"
    violations = []
    for directory in (root / "backend", root / "core"):
        for file in sorted(directory.rglob("*.py")):
            if file == guard:
                continue
            for line, name in _direct_client_imports(file.read_text(encoding="utf-8")):
                violations.append(f"{file.relative_to(root)}:{line}: {name}")
    assert not violations, "\n".join(violations)

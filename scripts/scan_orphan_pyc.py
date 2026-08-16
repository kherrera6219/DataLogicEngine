#!/usr/bin/env python3
"""Scan for .pyc modules that have no sibling .py, and optionally check imports.

Usage:
  python scripts/scan_orphan_pyc.py
  python scripts/scan_orphan_pyc.py --check-imports
  python scripts/scan_orphan_pyc.py --json
  python scripts/scan_orphan_pyc.py --fail-on-orphan

Exit codes:
  0 — no orphans (or only reported)
  1 — orphans found when --fail-on-orphan
  2 — usage / IO error
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCAN_ROOTS = (
    ROOT / "backend",
    ROOT / "core",
    ROOT / "sdk" / "UKG_Python_SDK" / "ukg_sdk",
)

IMPORT_SEARCH_ROOTS = (
    ROOT / "backend",
    ROOT / "core",
    ROOT / "tests",
    ROOT / "scripts",
    ROOT / "app.py",
    ROOT / "main.py",
    ROOT / "wsgi.py",
    ROOT / "models.py",
    ROOT / "sdk" / "UKG_Python_SDK",
)

EXCLUDE_DIR_NAMES = {
    ".claude",
    ".git",
    ".venv",
    ".venv311",
    ".venv-release311",
    "node_modules",
    "dist",
    "htmlcov",
    "htmlcov_phase3",
    "worktrees",
    "__pycache__",
    ".pytest_cache",
    "dist-electron",
    "dist-final",
    "dist-smoke",
}


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIR_NAMES for part in path.parts)


def find_orphans() -> list[dict[str, str]]:
    """List every orphan .pyc path (all Python tag variants).

    Dedupes only on the exact relative pyc path, not on module basename, so
    both ``foo.cpython-311.pyc`` and ``foo.cpython-313.pyc`` are reported when
    neither has a sibling ``foo.py``.
    """
    found: list[dict[str, str]] = []
    seen_pyc: set[str] = set()
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for pycache in root.rglob("__pycache__"):
            if any(part in EXCLUDE_DIR_NAMES - {"__pycache__"} for part in pycache.parts):
                continue
            parent = pycache.parent
            for pyc in pycache.glob("*.pyc"):
                name = pyc.name
                if ".cpython-" not in name:
                    continue
                base = name.split(".cpython-", 1)[0]
                if base == "__init__" or "-pytest" in base:
                    continue
                py = parent / f"{base}.py"
                if py.exists():
                    continue
                try:
                    rel_dir = str(parent.relative_to(ROOT)).replace("\\", "/")
                    rel_pyc = str(pyc.relative_to(ROOT)).replace("\\", "/")
                except ValueError:
                    rel_dir = str(parent)
                    rel_pyc = str(pyc)
                if rel_pyc in seen_pyc:
                    continue
                seen_pyc.add(rel_pyc)
                found.append({"dir": rel_dir, "module": base, "pyc": rel_pyc})
    found.sort(key=lambda row: (row["dir"], row["module"], row["pyc"]))
    return found


def _iter_py_files() -> list[Path]:
    files: list[Path] = []
    for root in IMPORT_SEARCH_ROOTS:
        if root.is_file() and root.suffix == ".py":
            files.append(root)
            continue
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
                continue
            files.append(path)
    return files


def check_imports(orphans: list[dict[str, str]]) -> tuple[list[dict], list[dict]]:
    """Return (blocked, safe) using *qualified* package path imports only.

    Short basenames (``config``, ``gateway``, ``openai``) produce too many false
    positives. An orphan is blocked only when some source imports the module via
    a dotted path that includes its package directory, e.g.::

        backend.security.mfa
        backend.local_model_acceleration.ollama_client
        from backend.security import mfa   # ImportFrom parent + name
    """
    py_files = _iter_py_files()
    # (qualified_module_or_parent, imported_name|None) -> files
    # We store every fully dotted import string seen.
    qualified_imports: dict[str, list[str]] = {}

    def add_qualified(name: str, file_path: Path) -> None:
        if not name or name == "*" or not name.replace(".", "").isidentifier() and not all(
            p.isidentifier() for p in name.split(".")
        ):
            # still allow dotted identifiers
            if not name or name == "*":
                return
            if not all(part.isidentifier() for part in name.split(".")):
                return
        rel = str(file_path.relative_to(ROOT)).replace("\\", "/")
        if rel.endswith("scan_orphan_pyc.py"):
            return
        qualified_imports.setdefault(name, [])
        if rel not in qualified_imports[name]:
            qualified_imports[name].append(rel)

    for path in py_files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            for match in re.finditer(
                r"^\s*(?:from\s+([\w.]+)\s+import\s+([\w* ,]+)|import\s+([\w.]+))",
                text,
                re.M,
            ):
                if match.group(3):
                    add_qualified(match.group(3), path)
                if match.group(1):
                    parent = match.group(1)
                    add_qualified(parent, path)
                    for part in match.group(2).split(","):
                        name = part.strip().split(" as ")[0].strip()
                        if name and name != "*":
                            add_qualified(f"{parent}.{name}", path)
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    add_qualified(alias.name, path)
            elif isinstance(node, ast.ImportFrom):
                if not node.module:
                    continue
                add_qualified(node.module, path)
                for alias in node.names:
                    if alias.name != "*":
                        add_qualified(f"{node.module}.{alias.name}", path)

        for match in re.finditer(
            r"""(?:import_module|__import__)\(\s*['"]([\w.]+)['"]""",
            text,
        ):
            add_qualified(match.group(1), path)

    blocked: list[dict] = []
    safe: list[dict] = []
    for row in orphans:
        module = row["module"]
        dir_path = row["dir"].replace("\\", "/")
        pkg = dir_path.replace("/", ".")
        qualified = f"{pkg}.{module}"
        hits = list(qualified_imports.get(qualified, []))

        # Also treat: from <pkg> import <module> already stored as pkg.module above.
        # Dynamic strings that include the full qualified name are in qualified_imports.

        if hits:
            blocked.append(
                {**row, "import_hits": hits[:5], "qualified": qualified}
            )
        else:
            safe.append(row)
    return blocked, safe


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-imports", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--fail-on-orphan",
        action="store_true",
        help="Exit 1 if any orphan pyc is found",
    )
    parser.add_argument(
        "--fail-on-blocked",
        action="store_true",
        help="With --check-imports, exit 1 if any orphan has importers",
    )
    args = parser.parse_args(argv)

    orphans = find_orphans()
    payload: dict = {"orphan_count": len(orphans), "orphans": orphans}

    if args.check_imports:
        blocked, safe = check_imports(orphans)
        payload["blocked_count"] = len(blocked)
        payload["safe_count"] = len(safe)
        payload["blocked"] = blocked
        payload["safe"] = safe

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"orphan_count={len(orphans)}")
        if args.check_imports:
            print(f"blocked_count={payload['blocked_count']}")
            print(f"safe_count={payload['safe_count']}")
            for row in payload.get("blocked", []):
                print(
                    f"  BLOCK {row['dir']}/{row['module']} <- {row.get('import_hits')}"
                )
            for row in payload.get("safe", [])[:20]:
                print(f"  SAFE  {row['dir']}/{row['module']}")
            if payload.get("safe_count", 0) > 20:
                print(f"  ... {payload['safe_count'] - 20} more safe")
        else:
            for row in orphans[:30]:
                print(f"  {row['dir']}/{row['module']}")
            if len(orphans) > 30:
                print(f"  ... {len(orphans) - 30} more")

    if args.fail_on_orphan and orphans:
        return 1
    if args.fail_on_blocked and payload.get("blocked_count", 0):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

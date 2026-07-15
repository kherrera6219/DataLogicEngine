"""Gate typed error coverage and broad-catch/root-logging regression."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.utils.exceptions import ErrorCategory, TYPED_ERROR_CLASSES  # noqa: E402

# Phase 13 inventory ceiling. The gate prevents increasing the legacy audit
# queue while core sites are converted deliberately instead of mechanically.
MAX_BROAD_CATCH_SITES = 1_105
MAX_BROAD_CATCH_FILES = 321


def _is_broad_handler(handler: ast.ExceptHandler) -> bool:
    if handler.type is None:
        return True
    exception_types = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
    return any(
        isinstance(exception_type, ast.Name)
        and exception_type.id in {"Exception", "BaseException"}
        for exception_type in exception_types
    )


def audit_source_tree(
    root: Path,
    source_roots: Iterable[str] = ("backend", "core"),
    *,
    max_broad_catch_sites: int = MAX_BROAD_CATCH_SITES,
    max_broad_catch_files: int = MAX_BROAD_CATCH_FILES,
) -> dict[str, object]:
    root = root.resolve()
    broad_by_file: Counter[str] = Counter()
    basic_config_sites: list[str] = []
    parse_errors: list[str] = []
    scanned_files = 0
    for source_root in source_roots:
        directory = (root / source_root).resolve()
        if not directory.is_dir() or root not in directory.parents:
            continue
        for path in sorted(directory.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            scanned_files += 1
            relative = path.relative_to(root).as_posix()
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (OSError, SyntaxError, UnicodeError) as exc:
                parse_errors.append(f"{relative}:{exc}")
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and _is_broad_handler(node):
                    broad_by_file[relative] += 1
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "basicConfig"
                ):
                    basic_config_sites.append(f"{relative}:{node.lineno}")

    required_categories = {category.value for category in ErrorCategory}
    implemented_categories = {category.value for category in TYPED_ERROR_CLASSES}
    broad_site_count = sum(broad_by_file.values())
    checks = {
        "broad_catch_site_ceiling": broad_site_count <= max_broad_catch_sites,
        "broad_catch_file_ceiling": len(broad_by_file) <= max_broad_catch_files,
        "module_root_logging_owned_by_entrypoint": not basic_config_sites,
        "typed_error_categories_complete": implemented_categories == required_categories,
        "all_sources_parse": not parse_errors,
    }
    return {
        "schema_version": "dle.failure-boundary-inventory.v1",
        "scanned_files": scanned_files,
        "broad_catch_site_count": broad_site_count,
        "broad_catch_file_count": len(broad_by_file),
        "broad_catch_ceiling": max_broad_catch_sites,
        "broad_catch_file_ceiling": max_broad_catch_files,
        "broad_catch_by_file": dict(sorted(broad_by_file.items())),
        "basic_config_sites": basic_config_sites,
        "typed_error_categories": sorted(implemented_categories),
        "missing_error_categories": sorted(required_categories - implemented_categories),
        "parse_errors": parse_errors,
        "checks": checks,
        "passed": all(checks.values()),
        "qualification_scope": (
            "source regression gate; individual legacy broad catches remain an audit queue"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_source_tree(args.root)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if args.json:
        print(rendered)
    else:
        print(
            f"Scanned {result['scanned_files']} files: "
            f"{result['broad_catch_site_count']} broad catches in "
            f"{result['broad_catch_file_count']} files; "
            f"{len(result['basic_config_sites'])} module basicConfig calls."
        )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

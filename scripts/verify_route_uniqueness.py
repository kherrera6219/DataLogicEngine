#!/usr/bin/env python3
"""Fail if the Flask app registers colliding (rule, methods) pairs.

Usage:
  python scripts/verify_route_uniqueness.py
  python scripts/verify_route_uniqueness.py --json

Environment:
  Uses the same testing-oriented create_app settings as unit tests when
  DATABASE_URL is unset (sqlite memory, no managed services).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _build_app():
    # Routes register before runtime.start(); skip runtime lock for this check.
    os.environ.setdefault("IS_DESKTOP_APP", "false")
    os.environ.setdefault("USE_REDIS", "False")
    os.environ.setdefault("RATELIMIT_STORAGE_URI", "memory://")
    os.environ.setdefault("SESSION_TYPE", "null")
    os.environ.setdefault("DLE_LEGACY_API_PREFIXES", "false")
    os.environ.setdefault(
        "ENCRYPTION_KEK_SECRET",
        "pytest-only-encryption-kek-secret-32-bytes",
    )
    runtime_root = ROOT / ".pytest_cache" / f"route-uniqueness-{os.getpid()}"
    runtime_root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("DLE_RUNTIME_ROOT", str(runtime_root))

    from app import create_app

    return create_app(
        "testing",
        {
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "TESTING": True,
            "DLE_RUNTIME_ROOT": str(runtime_root),
            "DLE_INITIALIZE_SCHEMA": False,
            "DLE_INITIALIZE_STORES": False,
            "DLE_START_MANAGED_SERVICES": False,
            "DLE_START_BACKGROUND_WORKERS": False,
            "WTF_CSRF_ENABLED": False,
        },
        start_runtime=False,
    )


def find_collisions(app) -> list[dict]:
    """Return collisions: same path + overlapping HTTP methods, different endpoints."""
    # key: (rule, method) -> list of endpoint names
    index: dict[tuple[str, str], list[str]] = defaultdict(list)
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue
        methods = sorted(m for m in (rule.methods or set()) if m not in {"HEAD", "OPTIONS"})
        for method in methods:
            index[(rule.rule, method)].append(rule.endpoint)

    collisions = []
    for (path, method), endpoints in sorted(index.items()):
        unique_endpoints = sorted(set(endpoints))
        if len(unique_endpoints) > 1:
            collisions.append(
                {
                    "path": path,
                    "method": method,
                    "endpoints": unique_endpoints,
                }
            )
    return collisions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    app = _build_app()
    collisions = find_collisions(app)
    payload = {
        "collision_count": len(collisions),
        "collisions": collisions,
        "legacy_api_prefixes": bool(app.config.get("DLE_LEGACY_API_PREFIXES")),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"collision_count={len(collisions)}")
        print(f"legacy_api_prefixes={payload['legacy_api_prefixes']}")
        for row in collisions:
            print(
                f"  COLLISION {row['method']} {row['path']} -> {', '.join(row['endpoints'])}"
            )
    return 1 if collisions else 0


if __name__ == "__main__":
    sys.exit(main())

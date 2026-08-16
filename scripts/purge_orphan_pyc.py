#!/usr/bin/env python3
"""Delete orphan .pyc files that have no sibling .py (after validation).

Safety rules:
  - Only deletes under backend/, core/, sdk/UKG_Python_SDK/ukg_sdk/
  - Refuses if a sibling .py exists
  - Refuses if the module still imports via qualified path (unless --force)
  - Dry-run by default; pass --apply to delete

Usage:
  python scripts/purge_orphan_pyc.py
  python scripts/purge_orphan_pyc.py --apply
  python scripts/purge_orphan_pyc.py --apply --include-local-model
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.scan_orphan_pyc import check_imports, find_orphans  # noqa: E402

# Deferred to Phase 3 B0 track unless --include-local-model
LOCAL_MODEL_PREFIXES = (
    "backend/local_model_acceleration/",
    "backend/llm_gateway/complexity_classifier",
    "backend/llm_gateway/escalation_config",
    "backend/llm_gateway/tier_availability",
)


def _is_local_model_cluster(row: dict) -> bool:
    key = f"{row['dir']}/{row['module']}".replace("\\", "/")
    return any(key.startswith(p.rstrip("/")) or key == p.rstrip("/") for p in LOCAL_MODEL_PREFIXES) or (
        row["dir"].replace("\\", "/") == "backend/local_model_acceleration"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Actually delete files")
    parser.add_argument(
        "--include-local-model",
        action="store_true",
        help="Also purge local_model_acceleration + gateway tier orphans (G-GEN=B0)",
    )
    parser.add_argument(
        "--force-blocked",
        action="store_true",
        help="Delete even if a stale qualified import reference remains",
    )
    args = parser.parse_args(argv)

    orphans = find_orphans()
    # Import check is per module basename+dir (any pyc variant shares the key)
    blocked, _safe = check_imports(orphans)
    blocked_keys = {f"{b['dir']}/{b['module']}" for b in blocked}

    to_delete: list[dict] = []
    skipped: list[str] = []
    seen_skip_keys: set[str] = set()

    for row in orphans:
        key = f"{row['dir']}/{row['module']}"
        if not args.include_local_model and _is_local_model_cluster(row):
            if key not in seen_skip_keys:
                skipped.append(f"DEFER local-model cluster: {key}")
                seen_skip_keys.add(key)
            continue
        if key in blocked_keys and not args.force_blocked:
            if key not in seen_skip_keys:
                skipped.append(f"BLOCKED import ref: {key}")
                seen_skip_keys.add(key)
            continue
        pyc = ROOT / row["pyc"]
        py = ROOT / row["dir"] / f"{row['module']}.py"
        if py.exists():
            skipped.append(f"HAS .py sibling: {row['pyc']}")
            continue
        if not pyc.exists():
            skipped.append(f"missing pyc: {row['pyc']}")
            continue
        to_delete.append(row)

    print(f"orphans_total={len(orphans)}")
    print(f"to_delete={len(to_delete)}")
    print(f"skipped={len(skipped)}")
    for s in skipped:
        print(f"  SKIP {s}")

    deleted = 0
    for row in to_delete:
        pyc = ROOT / row["pyc"]
        print(f"  {'DELETE' if args.apply else 'WOULD_DELETE'} {row['pyc']}")
        if args.apply:
            pyc.unlink()
            deleted += 1
            # remove empty __pycache__ if empty
            cache = pyc.parent
            try:
                if cache.is_dir() and cache.name == "__pycache__" and not any(cache.iterdir()):
                    cache.rmdir()
            except OSError:
                pass

    if args.apply:
        print(f"deleted={deleted}")
        # re-scan
        remaining = find_orphans()
        if not args.include_local_model:
            remaining = [r for r in remaining if not _is_local_model_cluster(r)]
        print(f"remaining_orphans_in_scope={len(remaining)}")
        return 0 if not remaining else 1

    print("dry-run only; pass --apply to delete")
    return 0


if __name__ == "__main__":
    sys.exit(main())

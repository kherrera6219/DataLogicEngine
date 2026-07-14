"""Offline entry point for a clean-root managed recovery drill."""

from __future__ import annotations

import argparse
import getpass
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.storage.managed_restore import restore_managed_backup_offline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("target_root", type=Path)
    parser.add_argument(
        "--lock",
        type=Path,
        default=ROOT / "deploy" / "internal-data-plane.candidate-lock.json",
    )
    parser.add_argument("--product-version", default="0.1.1")
    parser.add_argument("--profile", choices=("qualification", "production"), default="qualification")
    parser.add_argument("--runtime", default="podman")
    args = parser.parse_args()
    secret = getpass.getpass("Portable recovery secret: ")
    result = restore_managed_backup_offline(
        args.archive,
        args.target_root,
        recovery_secret=secret,
        product_version=args.product_version,
        lock_path=args.lock,
        profile=args.profile,
        runtime_binary=args.runtime,
    )
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate a normalized file/hash inventory for release payload comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory_tree(label: str, root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    normalized = hashlib.sha256()
    if root.is_file():
        candidates = [root]
        base = root.parent
    elif root.is_dir():
        candidates = sorted(path for path in root.rglob("*") if path.is_file())
        base = root
    else:
        return {
            "label": label,
            "root": str(root),
            "present": False,
            "file_count": 0,
            "size_bytes": 0,
            "normalized_sha256": None,
            "files": [],
        }

    for path in candidates:
        relative_path = path.relative_to(base).as_posix()
        digest = _sha256(path)
        size = path.stat().st_size
        normalized.update(f"{relative_path}\0{size}\0{digest}\n".encode())
        files.append({"path": relative_path, "size_bytes": size, "sha256": digest})
    return {
        "label": label,
        "root": str(root),
        "present": True,
        "file_count": len(files),
        "size_bytes": sum(item["size_bytes"] for item in files),
        "normalized_sha256": normalized.hexdigest(),
        "files": files,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installer", type=Path, required=True)
    parser.add_argument(
        "--backend-root",
        type=Path,
        default=ROOT / "dist" / "DataLogic_Backend",
    )
    parser.add_argument(
        "--portable-root",
        type=Path,
        default=ROOT / "frontend" / "dist" / "win-unpacked",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--prior-payload-inventory",
        type=Path,
        help="Reuse verified backend/portable rows when only the outer installer changed.",
    )
    args = parser.parse_args(argv)
    prior_by_label: dict[str, dict[str, Any]] = {}
    if args.prior_payload_inventory:
        prior = json.loads(args.prior_payload_inventory.read_text(encoding="utf-8"))
        prior_by_label = {item["label"]: item for item in prior.get("inventories", [])}
    inventories = [inventory_tree("installer", args.installer)]
    for label, path in (("backend", args.backend_root), ("portable", args.portable_root)):
        current = inventory_tree(label, path)
        if not current["present"] and label in prior_by_label:
            current = prior_by_label[label]
            current["reused_from_prior_signed_payload_inventory"] = True
        inventories.append(current)
    missing = [item["label"] for item in inventories if not item["present"]]
    payload = {
        "schema_version": "dle.release-content-inventory.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "inventories": inventories,
        "missing": missing,
        "status": "fail" if missing else "pass",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"Release content inventory: {args.output} "
        f"files={sum(item['file_count'] for item in inventories)} missing={len(missing)}"
    )
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())

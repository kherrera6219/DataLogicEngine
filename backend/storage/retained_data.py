"""Read-only discovery of retained desktop data before managed provisioning.

The released desktop stored authoritative state in SQLite plus embedded Chroma,
filesystem objects, and JSON files.  A rebuilt installer must identify that data
before it creates an installation identity or provisions an empty managed plane.
"""

from __future__ import annotations

import json
import hashlib
import sqlite3
from pathlib import Path
from typing import Any


RETAINED_DATA_DISCOVERY_SCHEMA_VERSION = "dle.retained-data-discovery.v1"
LEGACY_DESKTOP_SOURCE_VERSION = "0.1.1"
ADOPTION_RECEIPT_RELATIVE_PATH = Path("migrations") / "retained-data-adoption.json"


def _sqlite_source_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    for candidate in (path, Path(f"{path}-wal")):
        if not candidate.is_file():
            continue
        digest.update(candidate.name.encode("utf-8"))
        with candidate.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def _sqlite_inventory(path: Path, *, collection_database: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "present": path.is_file(),
        "size_bytes": path.stat().st_size if path.is_file() else 0,
        "table_count": 0,
        "nonempty_table_count": 0,
        "row_count": 0,
        "meaningful_record_count": 0,
        "sha256": _sqlite_source_sha256(path) if path.is_file() else None,
        "error": None,
    }
    if not path.is_file():
        return result
    try:
        connection = sqlite3.connect(
            f"file:{path.as_posix()}?mode=ro",
            uri=True,
        )
        connection.execute("PRAGMA query_only=ON")
        try:
            tables = [
                str(row[0])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
            ]
            counts: dict[str, int] = {}
            for table in tables:
                escaped = table.replace('"', '""')
                counts[table] = int(
                    connection.execute(
                        f'SELECT count(*) FROM "{escaped}"'  # nosec B608 -- identifier is SQLite-catalog-derived and quoted
                    ).fetchone()[0]
                )
        finally:
            connection.close()
    except (OSError, sqlite3.DatabaseError) as exc:
        result["error"] = f"{type(exc).__name__}"
        return result

    chroma_record_tables = {
        "embeddings",
        "embeddings_queue",
        "embedding_metadata",
        "embedding_metadata_array",
    }
    meaningful = sum(
        count
        for table, count in counts.items()
        if count > 0 and (not collection_database or table in chroma_record_tables)
    )
    result.update(
        table_count=len(tables),
        nonempty_table_count=sum(count > 0 for count in counts.values()),
        row_count=sum(counts.values()),
        meaningful_record_count=meaningful,
    )
    return result


def _file_inventory(root: Path) -> dict[str, Any]:
    files = sorted(path for path in root.rglob("*") if path.is_file()) if root.is_dir() else []
    return {
        "present": root.is_dir(),
        "file_count": len(files),
        "size_bytes": sum(path.stat().st_size for path in files),
    }


def _identity_version(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "invalid"
    version = str(payload.get("version") or "").strip()
    return version or "invalid"


def _graph_snapshot_inventory(path: Path) -> dict[str, Any]:
    result = {"present": path.is_file(), "sha256": None, "error": None}
    if not path.is_file():
        return result
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        result["sha256"] = str(payload.get("sha256") or "") or None
    except (OSError, TypeError, ValueError) as exc:
        result["error"] = type(exc).__name__
    return result


def _valid_adoption_receipt(
    path: Path,
    source_sha256: str | None,
    graph_sha256: str | None,
) -> bool:
    if not path.is_file() or not source_sha256:
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return False
    graph = payload.get("graph") or {}
    receipt_source_sha = str(payload.get("source_sha256") or "")
    exact_source_match = receipt_source_sha == source_sha256
    # SQLite WAL checkpoints can change the byte-level source digest after a
    # verified adoption without changing the retained logical records. Once
    # adoption completes, validate the immutable recovery copy recorded by the
    # receipt instead of attempting to import into a non-empty managed store.
    recovery_copy = (
        path.parents[1]
        / "recovery"
        / "retained-data"
        / f"ukg-database-{receipt_source_sha[:16]}.sqlite3"
    )
    backup_sha = str(payload.get("backup_sha256") or "")
    verified_recovery_copy = bool(
        receipt_source_sha
        and backup_sha
        and recovery_copy.is_file()
        and hashlib.sha256(recovery_copy.read_bytes()).hexdigest() == backup_sha
    )
    return bool(
        payload.get("schema_version") == "dle.retained-data-adoption.v1"
        and payload.get("status") == "verified"
        and (exact_source_match or verified_recovery_copy)
        and (not graph_sha256 or graph.get("sha256") == graph_sha256)
    )


def discover_retained_data(runtime_root: str | Path) -> dict[str, Any]:
    """Return a content-free retained-data disposition without mutating stores."""
    root = Path(runtime_root).expanduser().resolve()
    sqlite_state = _sqlite_inventory(root / "ukg_database.db")
    chroma_state = _sqlite_inventory(
        root / "databases" / "chroma" / "chroma.sqlite3",
        collection_database=True,
    )
    objects_state = _file_inventory(root / "databases" / "objects")
    memory_state = _file_inventory(root / "databases" / "memory")
    graph_snapshot_state = _graph_snapshot_inventory(
        root / "recovery" / "retained-data" / "legacy-neo4j.snapshot.json"
    )
    receipt_path = root / ADOPTION_RECEIPT_RELATIVE_PATH
    adoption_receipt_present = receipt_path.is_file()
    adoption_receipt_valid = _valid_adoption_receipt(
        receipt_path,
        sqlite_state.get("sha256"),
        graph_snapshot_state.get("sha256"),
    )
    meaningful = any(
        (
            int(sqlite_state["meaningful_record_count"]),
            int(chroma_state["meaningful_record_count"]),
            int(objects_state["file_count"]),
            int(memory_state["file_count"]),
            int(bool(graph_snapshot_state["present"])),
        )
    )
    identity_version = _identity_version(root / "installation.json")
    requires_adoption = meaningful and not adoption_receipt_valid
    source_version = (
        LEGACY_DESKTOP_SOURCE_VERSION
        if requires_adoption and identity_version in {None, "4.3.0"}
        else identity_version
    )
    return {
        "schema_version": RETAINED_DATA_DISCOVERY_SCHEMA_VERSION,
        "runtime_root_exists": root.is_dir(),
        "identity_version": identity_version,
        "source_version": source_version,
        "legacy_retained_data_present": meaningful,
        "adoption_receipt_present": adoption_receipt_present,
        "adoption_receipt_valid": adoption_receipt_valid,
        "requires_adoption": requires_adoption,
        "surfaces": {
            "sqlite": sqlite_state,
            "chroma": chroma_state,
            "objects": objects_state,
            "memory": memory_state,
            "legacy_neo4j_snapshot": graph_snapshot_state,
        },
    }

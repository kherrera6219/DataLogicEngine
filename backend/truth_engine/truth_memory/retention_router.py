"""Local cold-storage routing for long-retention TruthMemory artifacts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import gzip
import json
import os
from pathlib import Path
from typing import Any


class TruthMemoryRetentionRouter:
    """Archive 7-year retention payloads to app-owned local storage."""

    def __init__(self, archive_dir: str | Path | None = None, retention_years: int = 7):
        base = (
            archive_dir
            or os.environ.get("DLE_TRUTHMEMORY_ARCHIVE_DIR")
            or os.environ.get("TRUTHMEMORY_ARCHIVE_DIR")
            or Path("databases/archive/truth_memory")
        )
        self.archive_dir = Path(base)
        self.retention_years = retention_years

    def archive_payload(
        self,
        *,
        record_id: str,
        payload: dict[str, Any],
        category: str = "truthmemory",
    ) -> dict[str, Any]:
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        safe_category = self._safe_segment(category)
        safe_id = self._safe_segment(record_id)
        path = self.archive_dir / safe_category / f"{safe_id}.json.gz"
        path.parent.mkdir(parents=True, exist_ok=True)
        archive_payload = {
            "record_id": record_id,
            "category": category,
            "payload": payload,
            "archived_at": datetime.now(UTC).isoformat(),
            "retention_until": (datetime.now(UTC) + timedelta(days=365 * self.retention_years)).isoformat(),
        }
        with gzip.open(path, "wt", encoding="utf-8") as handle:
            json.dump(archive_payload, handle, sort_keys=True)
        return {
            "archived": True,
            "path": str(path),
            "category": category,
            "retention_years": self.retention_years,
            "retention_until": archive_payload["retention_until"],
        }

    def read_archive(self, path: str | Path) -> dict[str, Any]:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def _safe_segment(value: str) -> str:
        return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in str(value))[:160] or "record"

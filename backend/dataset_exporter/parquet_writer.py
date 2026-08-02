"""Parquet and JSONL dataset serializer for DataLogicEngine datasets."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .privacy_redactor import PrivacyRedactor, SecurityError

logger = logging.getLogger(__name__)

_ALLOWED_COMPRESSIONS = {"snappy", "zstd", "gzip", "none"}

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False


class ParquetWriter:
    """Serializes dataset rows to Parquet or JSONL format with fail-closed error handling."""

    @classmethod
    def is_pyarrow_available(cls) -> bool:
        """Return True if PyArrow is installed."""
        return HAS_PYARROW

    @classmethod
    def write_jsonl(
        cls,
        rows: Sequence[dict[str, Any]],
        output_path: str | Path,
        *,
        base_dir: str | Path = "./datasets",
    ) -> str:
        """Write records to a line-delimited JSON file (.jsonl) with path validation and error handling."""
        try:
            path = PrivacyRedactor.validate_safe_path(output_path, base_dir=base_dir)
            if path.suffix.lower() != ".jsonl":
                raise ValueError("JSONL output path must use the .jsonl extension.")
            path.parent.mkdir(parents=True, exist_ok=True)

            with path.open("w", encoding="utf-8") as f:
                for row in rows:
                    if isinstance(row, dict):
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")

            logger.info("Wrote %d rows to JSONL file: %s", len(rows), path)
            return str(path)
        except (SecurityError, ValueError) as exc:
            logger.error("Security validation failed for JSONL output path %s: %s", output_path, exc)
            raise
        except Exception as exc:
            logger.error("Failed to write JSONL dataset to %s: %s", output_path, exc)
            raise OSError(f"Dataset JSONL write failed: {exc}") from exc

    @classmethod
    def write_parquet(
        cls,
        rows: Sequence[dict[str, Any]],
        output_path: str | Path,
        *,
        compression: str = "snappy",
        base_dir: str | Path = "./datasets",
    ) -> str:
        """Write records to a Parquet file (.parquet). Fall back to JSONL if PyArrow is missing."""
        try:
            path = PrivacyRedactor.validate_safe_path(output_path, base_dir=base_dir)
            if path.suffix.lower() != ".parquet":
                raise ValueError("Parquet output path must use the .parquet extension.")
            normalized_compression = compression.lower().strip()
            if normalized_compression not in _ALLOWED_COMPRESSIONS:
                raise ValueError("Unsupported Parquet compression.")
            parquet_compression = None if normalized_compression == "none" else normalized_compression

            if not HAS_PYARROW:
                logger.warning("PyArrow is not installed. Falling back to JSONL export for %s", path)
                fallback_path = path.with_suffix(".jsonl")
                return cls.write_jsonl(rows, fallback_path, base_dir=base_dir)

            path.parent.mkdir(parents=True, exist_ok=True)

            if not rows:
                logger.warning("No rows provided for Parquet export to %s", path)
                table = pa.Table.from_batches([])
                pq.write_table(table, str(path), compression=parquet_compression)
                return str(path)

            pydict: dict[str, list[Any]] = {}
            first_row = rows[0] if isinstance(rows[0], dict) else {}
            keys = first_row.keys()

            for key in keys:
                pydict[key] = [row.get(key) if isinstance(row, dict) else None for row in rows]

            table = pa.Table.from_pydict(pydict)
            pq.write_table(table, str(path), compression=parquet_compression)

            logger.info("Wrote %d rows to Parquet file: %s (compression=%s)", len(rows), path, normalized_compression)
            return str(path)
        except (SecurityError, ValueError) as exc:
            logger.error("Security validation failed for Parquet output path %s: %s", output_path, exc)
            raise
        except Exception as exc:
            logger.error("Failed to write Parquet dataset to %s: %s", output_path, exc)
            raise OSError(f"Dataset Parquet write failed: {exc}") from exc

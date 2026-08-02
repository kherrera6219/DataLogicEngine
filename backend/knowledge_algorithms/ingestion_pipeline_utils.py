"""Deterministic helpers for the KA-071..KA-078 ingestion pipeline."""

from __future__ import annotations

import json
from typing import Any


def dependency_records(
    dependency_results: dict[str, dict[str, Any]],
    dependency_id: str,
    output_field: str,
    direct_records: list[Any],
) -> list[Any]:
    """Prefer the declared dependency output and fail closed on a broken chain."""
    if dependency_id not in dependency_results:
        return list(direct_records)
    dependency = dependency_results.get(dependency_id)
    if not isinstance(dependency, dict):
        raise TypeError(f"{dependency_id} dependency output must be an object")
    records = dependency.get(output_field)
    if not isinstance(records, list):
        raise TypeError(f"{dependency_id} dependency output requires {output_field}")
    return list(records)


def canonical_record(record: Any) -> str:
    """Return a stable representation used only for local comparison."""
    return json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

"""Local deterministic embeddings for historical TruthSession comparisons."""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Iterable, List

_DIMENSIONS = 32
_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


def text_to_embedding(text: str, dimensions: int = _DIMENSIONS) -> List[float]:
    """Convert text into a stable normalized hashing-vector embedding."""
    vector = [0.0] * dimensions
    for token in _TOKEN_PATTERN.findall((text or "").lower()):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % dimensions
        weight = 1.0 + (digest[2] / 255.0)
        vector[index] += weight

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 6) for value in vector]


def serialize_embedding(text: str) -> str:
    """Serialize a local embedding as JSON text for SQLite/PostgreSQL TEXT storage."""
    return json.dumps(text_to_embedding(text), separators=(",", ":"))


def parse_embedding(raw_embedding: str | Iterable[float] | None) -> List[float]:
    if raw_embedding is None:
        return []
    if isinstance(raw_embedding, str):
        try:
            values = json.loads(raw_embedding)
        except json.JSONDecodeError:
            return []
    else:
        values = list(raw_embedding)
    if not isinstance(values, list):
        return []
    parsed = []
    for value in values:
        try:
            parsed.append(float(value))
        except (TypeError, ValueError):
            return []
    return parsed


def cosine_similarity(left: Iterable[float], right: Iterable[float]) -> float:
    left_values = list(left)
    right_values = list(right)
    if not left_values or not right_values or len(left_values) != len(right_values):
        return 0.0
    numerator = sum(a * b for a, b in zip(left_values, right_values))
    left_norm = math.sqrt(sum(a * a for a in left_values))
    right_norm = math.sqrt(sum(b * b for b in right_values))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return max(0.0, min(1.0, numerator / (left_norm * right_norm)))

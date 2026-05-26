"""Shared helpers for Layer 10 KAs."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any


def text_from_inputs(inputs: dict[str, Any]) -> str:
    for key in ("content", "text", "answer", "output"):
        value = inputs.get(key)
        if value:
            return str(value)
    return str(inputs)


def token_entropy(text: str) -> float:
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return 0.0
    counts = Counter(tokens)
    total = len(tokens)
    entropy = -sum((count / total) * math.log2(count / total) for count in counts.values())
    max_entropy = math.log2(max(2, len(counts)))
    return round(min(1.0, entropy / max_entropy), 4)


def severity_rank(severity: str) -> int:
    return {"info": 0, "minor": 1, "major": 2, "critical": 3}.get(str(severity), 0)

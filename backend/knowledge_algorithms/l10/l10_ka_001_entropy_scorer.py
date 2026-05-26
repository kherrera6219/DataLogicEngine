"""L10-KA-001: entropy-based emergence scorer."""

from __future__ import annotations

from typing import Any

from backend.knowledge_algorithms.l10.common import text_from_inputs, token_entropy


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    content = text_from_inputs(inputs)
    entropy_score = token_entropy(content)
    return {
        "success": True,
        "entropy_score": entropy_score,
        "divergence_detected": entropy_score >= float(inputs.get("threshold", 0.82)),
        "token_count": len(content.split()),
    }

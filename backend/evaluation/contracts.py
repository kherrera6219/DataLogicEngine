"""Load and validate the Phase 6 evaluation baseline without provider calls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
CORPUS_PATH = ROOT / "docs" / "evaluation" / "golden_corpus_v1.json"
PROVIDER_MATRIX_PATH = ROOT / "docs" / "evaluation" / "provider_model_matrix_v1.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_golden_corpus() -> dict[str, Any]:
    return _load(CORPUS_PATH)


def load_provider_model_matrix() -> dict[str, Any]:
    return _load(PROVIDER_MATRIX_PATH)


def detect_provider_model_drift(
    matrix: Mapping[str, Any],
    defaults: Mapping[str, str],
) -> list[str]:
    """Return provider/model manifest mismatches that require re-evaluation."""

    declared = {
        str(row["provider"]): str(row["model"])
        for row in matrix.get("combinations", [])
        if row.get("provider") in defaults
    }
    return [
        f"{provider}:{declared.get(provider, 'missing')}->{model}"
        for provider, model in defaults.items()
        if declared.get(provider) != model
    ]


def provider_matrix_release_ready(matrix: Mapping[str, Any]) -> bool:
    required = [row for row in matrix.get("combinations", []) if row.get("release_required")]
    return bool(required) and all(
        row.get("automated_status") == "passed"
        and row.get("human_review_status") == "passed"
        and row.get("owner_approval") is True
        and row.get("quarantined") is False
        for row in required
    )

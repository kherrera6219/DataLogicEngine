from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .core import TruthEngine, TruthEngineConfig


def _load_any(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text) or {}
    return json.loads(text)


def load_truth_engine_from_specs(
    spec_dir: str | Path,
    config: Optional[TruthEngineConfig] = None,
) -> TruthEngine:
    """Load TruthEngine with spec documents present in a directory.

    Expected files (flexible):
    - truth_engine_v7_3_master.json / .yaml
    - truthgate_v7_3.json
    - truthmemory_v7_3.json
    - truthlink_v7_3.json
    """
    spec_dir = Path(spec_dir)
    # We currently treat the spec docs as metadata; the executable behavior is in code.
    specs: Dict[str, Any] = {}
    for p in spec_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in {".json", ".yaml", ".yml"}:
            try:
                specs[p.name] = _load_any(p)
            except Exception:
                continue

    engine = TruthEngine(config=config)
    # Attach specs for audit / introspection
    engine.frost.set("truth_engine_specs", specs)
    return engine

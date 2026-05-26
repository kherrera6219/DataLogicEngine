"""Desktop DMRF configuration loader."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = {
    "desktop_mode": True,
    "offline_tier_cap": "high_stakes",
    "frost_mode": "memory",
    "max_refinement_iterations": 3,
}


class DMRFDesktopConfig:
    """Load DMRF config from AppData with deterministic defaults."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else self.default_path()

    @staticmethod
    def default_path() -> Path:
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        return base / "DataLogicEngine" / "dmrf_config.json"

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return dict(DEFAULT_CONFIG)
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return {**DEFAULT_CONFIG, **data}
        except Exception:
            return dict(DEFAULT_CONFIG)


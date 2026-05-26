"""Local DSQP template registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DSQPRegistry:
    """Loads bundled DSQP question templates without network access."""

    def __init__(self, template_dir: str | Path | None = None):
        self.template_dir = Path(template_dir) if template_dir else Path(__file__).with_name("templates")

    def template_for(self, persona_type: str) -> dict[str, Any]:
        candidate = self.template_dir / f"{persona_type}.json"
        fallback = self.template_dir / "default.json"
        path = candidate if candidate.exists() else fallback
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

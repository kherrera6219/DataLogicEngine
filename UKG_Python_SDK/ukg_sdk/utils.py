from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def package_data_path(*parts: str) -> Path:
    """Return absolute path to a file shipped inside ukg_sdk/data."""
    here = Path(__file__).resolve().parent
    return (here / "data" / Path(*parts)).resolve()


def env_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def deep_get(d: Dict[str, Any], dotted: str, default=None):
    cur: Any = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur

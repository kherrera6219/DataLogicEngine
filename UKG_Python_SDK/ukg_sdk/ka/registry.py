from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .models import KAInfo, KARegistry


def load_registry_from_json(path: str | Path) -> KARegistry:
    """Load a KA registry from the canonical JSON-by-id format.

    Expected shape:
      {
        "KA-001": {...},
        "KA-002": {...},
        ...
      }
    """
    p = Path(path)
    data: Dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
    items: Dict[str, KAInfo] = {}
    for ka_id, row in data.items():
        # tolerate older key names
        norm = dict(row)
        norm.setdefault("ka_id", ka_id)
        norm.setdefault("name", norm.get("KA_Name") or norm.get("ka_name") or ka_id)
        norm.setdefault("short_name", norm.get("Short_Name") or norm.get("shortName"))
        norm.setdefault("primary_layers", _split_layers(norm.get("Primary_Layers") or norm.get("primary_layers")))
        norm.setdefault("allowed_layers", _split_layers(norm.get("Allowed_Layers") or norm.get("allowed_layers")))
        norm.setdefault("reads_memory", _bool(norm.get("Reads_Memory")))
        norm.setdefault("writes_memory", _bool(norm.get("Writes_Memory")))
        norm.setdefault("can_invoke_chaos", _bool(norm.get("Can_Invoke_Chaos")))
        norm.setdefault("can_invoke_external_research", _bool(norm.get("Can_Invoke_External_Research")))
        norm.setdefault("can_trigger_recursion", _bool(norm.get("Can_Trigger_Recursion")))
        norm.setdefault("can_veto", _bool(norm.get("Can_Veto")))
        norm.setdefault("dependencies", _split_list(norm.get("Dependencies") or norm.get("dependencies")))
        items[ka_id] = KAInfo(**{k: v for k, v in norm.items() if k in KAInfo.model_fields})
    return KARegistry(items=items)


def load_default_registry(package_data_dir: str | Path) -> Optional[KARegistry]:
    p = Path(package_data_dir) / "ka_registry_by_id.json"
    if not p.exists():
        return None
    return load_registry_from_json(p)


def _split_layers(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    s = str(v).strip()
    if not s:
        return []
    # tolerate "L1–L10" and "L1-L10"
    s = s.replace("–", "-")
    if "-" in s and "," not in s and s.startswith("L") and s.count("L") == 2:
        a, b = s.split("-", 1)
        try:
            start = int(a.strip()[1:])
            end = int(b.strip()[1:])
            return [f"L{i}" for i in range(start, end + 1)]
        except Exception:
            pass
    return [x.strip() for x in s.split(",") if x.strip()]


def _split_list(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    s = str(v).strip()
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


def _bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in {"1", "true", "yes", "y"}

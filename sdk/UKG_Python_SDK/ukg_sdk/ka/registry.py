from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
    data: dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
    items: dict[str, KAInfo] = {}
    for ka_id, row in data.items():
        # tolerate older key names
        norm = dict(row)
        norm.setdefault("ka_id", ka_id)
        norm.setdefault("name", norm.get("KA_Name") or norm.get("ka_name") or ka_id)
        norm.setdefault("short_name", norm.get("Short_Name") or norm.get("shortName"))
        norm.setdefault("primary_layers", _split_layers(norm.get("Primary_Layers") or norm.get("primary_layers")))
        norm.setdefault("allowed_layers", _split_layers(norm.get("Allowed_Layers") or norm.get("allowed_layers")))
        norm.setdefault("inputs", _split_list(norm.get("Inputs") or norm.get("inputs")))
        norm.setdefault("outputs", _split_list(norm.get("Outputs") or norm.get("outputs")))
        norm.setdefault("reads_memory", _bool(norm.get("Reads_Memory")))
        norm.setdefault("writes_memory", _bool(norm.get("Writes_Memory")))
        norm.setdefault("can_invoke_chaos", _bool(norm.get("Can_Invoke_Chaos")))
        norm.setdefault("can_invoke_external_research", _bool(norm.get("Can_Invoke_External_Research")))
        norm.setdefault("can_trigger_recursion", _bool(norm.get("Can_Trigger_Recursion")))
        norm.setdefault("can_veto", _bool(norm.get("Can_Veto")))
        norm.setdefault("dependencies", _split_list(norm.get("Dependencies") or norm.get("dependencies")))
        items[ka_id] = KAInfo(**{k: v for k, v in norm.items() if k in KAInfo.model_fields})
    return KARegistry(items=items)


def load_default_registry(package_data_dir: str | Path) -> KARegistry | None:
    data_dir = Path(package_data_dir)
    manifest_path = data_dir / "ka_manifest.v1.generated.json"
    if manifest_path.exists():
        return load_registry_from_manifest(manifest_path)
    legacy_path = data_dir / "ka_registry_by_id.json"
    if not legacy_path.exists():
        return None
    return load_registry_from_json(legacy_path)


def load_registry_from_manifest(path: str | Path) -> KARegistry:
    """Load the SDK catalog generated from the canonical runtime manifest."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = payload.get("entries", {})
    items: dict[str, KAInfo] = {}
    for ka_id, row in entries.items():
        contract = row.get("contract") or {}
        admission = row.get("admission") or {}
        implementation = row.get("implementation") or {}
        aliases = row.get("aliases") or {}
        items[ka_id] = KAInfo(
            ka_id=ka_id,
            name=row.get("name") or ka_id,
            purpose=row.get("purpose"),
            category=(
                contract.get("categories", [None])[0]
                if contract.get("categories")
                else None
            ),
            primary_layers=contract.get("layers", []),
            allowed_layers=contract.get("layers", []),
            inputs=contract.get("inputs", []),
            outputs=contract.get("outputs", []),
            reads_memory=bool(contract.get("reads_memory")),
            writes_memory=bool(contract.get("writes_memory")),
            can_invoke_chaos="may_invoke_chaos"
            in contract.get("triggers", []),
            can_invoke_external_research=(
                "may_invoke_external_research"
                in contract.get("triggers", [])
            ),
            can_trigger_recursion=(
                "may_trigger_recursion" in contract.get("triggers", [])
            ),
            can_veto="may_veto" in contract.get("triggers", []),
            risk_class=(
                contract.get("risk_classes", [None])[0]
                if contract.get("risk_classes")
                else None
            ),
            dependencies=contract.get("dependencies", []),
            produces_artifacts=bool(contract.get("produces_artifacts")),
            audit_events=bool(contract.get("audit_events", True)),
            version=row.get("version", "1.0.0"),
            status=(
                "Active"
                if implementation.get("entrypoint")
                else "Implementation Required"
            ),
            aliases=aliases.get("scoped", []),
            implementation_status=implementation.get("status"),
            production_enabled=bool(admission.get("production_enabled")),
            classification=admission.get("classification"),
            limitations=contract.get("limitations"),
        )
    return KARegistry(items=items)


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
        except ValueError:
            return [x.strip() for x in s.split(",") if x.strip()]
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

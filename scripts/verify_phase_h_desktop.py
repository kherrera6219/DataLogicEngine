"""Verify Phase H desktop packaging and cold-start evidence."""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "phase_h_desktop_evidence.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _contains(path: Path, needles: list[str]) -> dict[str, bool]:
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    return {needle: needle in text for needle in needles}


def _import_timing(module_name: str) -> dict[str, float | bool | str]:
    start = time.perf_counter()
    try:
        __import__(module_name)
    except Exception as exc:
        return {
            "ok": False,
            "duration_ms": round((time.perf_counter() - start) * 1000, 2),
            "error": str(exc),
        }
    return {
        "ok": True,
        "duration_ms": round((time.perf_counter() - start) * 1000, 2),
        "error": "",
    }


def main() -> int:
    backend_spec = ROOT / "backend.spec"
    electron_builder = ROOT / "frontend" / "electron-builder.yml"
    preload = ROOT / "frontend" / "electron" / "preload.ts"
    main_ts = ROOT / "frontend" / "electron" / "main.ts"

    evidence = {
        "generated_at": datetime.now(UTC).isoformat(),
        "packaging": {
            "backend_spec": _contains(
                backend_spec,
                [
                    "collect_submodules('backend.dsqp')",
                    "collect_submodules('backend.dmrf')",
                    "collect_submodules('backend.desktop')",
                    "collect_submodules('backend.knowledge_algorithms')",
                    "backend/dsqp/templates",
                ],
            ),
            "electron_builder": _contains(
                electron_builder,
                [
                    "../dist/DataLogic_Backend",
                    "../policies",
                ],
            ),
        },
        "ipc": {
            "preload": _contains(
                preload,
                [
                    "reasoning-layer-progress",
                    "ka-execution-feed",
                    "get-desktop-storage-metrics",
                    "run-database-backup",
                ],
            ),
            "main": _contains(
                main_ts,
                [
                    "reasoning-layer-progress",
                    "ka-execution-feed",
                    "choose-backup-folder",
                    "run-database-backup",
                ],
            ),
        },
        "cold_start_profile": {
            "backend.storage.runtime_settings": _import_timing("backend.storage.runtime_settings"),
            "backend.desktop.offline_queue": _import_timing("backend.desktop.offline_queue"),
        },
    }

    failures = []
    for section, checks in evidence["packaging"].items():
        failures.extend(f"packaging.{section}.{key}" for key, ok in checks.items() if not ok)
    for section, checks in evidence["ipc"].items():
        failures.extend(f"ipc.{section}.{key}" for key, ok in checks.items() if not ok)
    for module, result in evidence["cold_start_profile"].items():
        if not result["ok"]:
            failures.append(f"cold_start_profile.{module}")

    evidence["success"] = not failures
    evidence["failures"] = failures
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    print(json.dumps({"success": evidence["success"], "report": str(REPORT_PATH), "failures": failures}, indent=2))
    return 0 if evidence["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

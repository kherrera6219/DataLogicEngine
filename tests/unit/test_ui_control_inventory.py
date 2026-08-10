from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_production_ui_has_no_enabled_control_without_an_obvious_action(tmp_path: Path):
    output = tmp_path / "ui-controls.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "inventory_ui_controls.py"),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    summary = payload["summary"]
    assert summary["pages"] >= 27
    assert summary["controls"] >= 180
    assert summary["enabled_without_obvious_action"] == 0
    assert summary["controls_with_disabled_state"] >= summary["disabled_controls"]
    identities = {
        json.dumps(control, sort_keys=True)
        for control in payload["controls"]
    }
    assert len(identities) == summary["controls"]

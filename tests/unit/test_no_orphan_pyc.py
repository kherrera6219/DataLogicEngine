"""Guard: mainline packages must not keep orphan .pyc without sibling .py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_no_orphan_pyc_on_mainline():
    """Fail if any orphan bytecode remains (Phase 3 B0 completed local_model purge)."""
    script = ROOT / "scripts" / "scan_orphan_pyc.py"
    assert script.is_file()
    sys.path.insert(0, str(ROOT))
    from scripts.scan_orphan_pyc import find_orphans

    orphans = find_orphans()
    labels = [f"{row['dir']}/{row['module']} ({row['pyc']})" for row in orphans]
    assert labels == [], (
        "Orphan .pyc without sibling .py found:\n" + "\n".join(labels[:40])
    )


def test_orphan_scanner_script_runs():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "scan_orphan_pyc.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "orphan_count=" in result.stdout

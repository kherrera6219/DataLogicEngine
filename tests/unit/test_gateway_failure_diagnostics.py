"""Exercise the CI-only gateway diagnostic without changing test outcomes."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TARGET = "test_gateway_persists_full_governed_trace_when_legacy_bypass_is_requested"


def _run_synthetic(tmp_path: Path, name: str) -> subprocess.CompletedProcess[str]:
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (tmp_path / "test_synthetic.py").write_text(
        "from types import SimpleNamespace\n"
        f"def {name}():\n"
        "    response = SimpleNamespace(ok=False, status='failed', "
        "failure={'kind':'internal_failure','code':'SYNTHETIC_CODE',"
        "'stage':'synthetic_stage','message':'PRIVATE_MARKER'}, "
        "trace=[{'name':'synthetic_stage','status':'failed',"
        "'error_code':'SYNTHETIC_CODE','input':'PRIVATE_MARKER'}])\n"
        "    assert response.ok is True\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(ROOT), env.get("PYTHONPATH", "")])
    )
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "scripts.gateway_failure_diagnostics",
            "-q",
            "--tb=short",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def test_failed_target_keeps_failure_and_reports_only_bounded_fields(tmp_path):
    result = _run_synthetic(tmp_path, TARGET)
    assert result.returncode == 1
    assert "Gateway failure diagnostic" in result.stdout
    diagnostic = result.stdout.split("Gateway failure diagnostic", 1)[1].split(
        "===========================", 1
    )[0]
    assert "SYNTHETIC_CODE" in diagnostic
    assert "PRIVATE_MARKER" not in diagnostic


def test_unrelated_failure_is_not_given_gateway_diagnostics(tmp_path):
    result = _run_synthetic(tmp_path, "test_unrelated_failure")
    assert result.returncode == 1
    assert "Gateway failure diagnostic" not in result.stdout + result.stderr

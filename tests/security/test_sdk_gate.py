"""Run the separately packaged SDK's tests from its own project root."""

import os
from pathlib import Path
import re
import subprocess
import sys


def test_python_sdk_suite_runs_from_standalone_project():
    project = Path(__file__).resolve().parents[2] / "sdk" / "UKG_Python_SDK"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(project)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "--no-cov",
            "-q",
            "--tb=short",
            "-rE",
        ],
        cwd=project,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert re.search(r"\b[1-9]\d* passed\b", output), output

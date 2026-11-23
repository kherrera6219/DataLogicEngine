"""Coverage gate combines execution without removing measured statements."""

import json
from pathlib import Path
import subprocess
import sys


def _report(path, core_executed, core_missing, *, windows=False):
    prefix = "\\" if windows else "/"
    payload = {
        "files": {
            f"backend{prefix}security{prefix}audit.py": {
                "executed_lines": [1, 2, 3, 4, 5],
                "missing_lines": [],
            },
            f"core{prefix}connector.py": {
                "executed_lines": core_executed,
                "missing_lines": core_missing,
            },
        }
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _verify(*reports):
    script = (
        Path(__file__).resolve().parents[2] / "scripts" / "verify_python_coverage.py"
    )
    args = [sys.executable, str(script)]
    for report in reports:
        args.extend(["--report", str(report)])
    return subprocess.run(args, capture_output=True, text=True, check=False)


def test_platform_reports_combine_without_removing_uncovered_lines(tmp_path):
    linux = tmp_path / "linux.json"
    windows = tmp_path / "windows.json"
    _report(linux, [1], [2, 3, 4, 5])
    _report(windows, [2, 3, 4], [1, 5], windows=True)

    single = _verify(linux)
    assert single.returncode == 1
    assert "[FAIL] core: 20.00% (1/5)" in single.stdout

    combined = _verify(linux, windows)
    assert combined.returncode == 0
    assert "[PASS] core: 80.00% (4/5)" in combined.stdout
    assert "[PASS] backend/security: 100.00% (5/5)" in combined.stdout


def test_combined_reports_still_fail_when_coverage_is_below_threshold(tmp_path):
    linux = tmp_path / "linux.json"
    windows = tmp_path / "windows.json"
    _report(linux, [1], [2, 3, 4, 5])
    _report(windows, [2, 3], [1, 4, 5], windows=True)

    combined = _verify(linux, windows)
    assert combined.returncode == 1
    assert "[FAIL] core: 60.00% (3/5)" in combined.stdout

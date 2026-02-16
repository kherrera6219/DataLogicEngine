#!/usr/bin/env python3
"""Run repository pre-commit governance checks (lint + typecheck)."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NPM_BIN = shutil.which("npm") or shutil.which("npm.cmd") or "npm"


def _run(command: list[str], label: str) -> int:
    print(f"\n==> {label}")
    print(" ".join(command))
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode != 0:
        print(f"[FAIL] {label} exited with code {completed.returncode}")
        return completed.returncode
    print(f"[PASS] {label}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-python-lint",
        action="store_true",
        help="Skip Python lint step.",
    )
    args = parser.parse_args(argv)

    checks: list[tuple[list[str], str]] = []
    if not args.skip_python_lint:
        checks.append(([sys.executable, "-m", "ruff", "check", "."], "Python lint (ruff)"))
    checks.append(([NPM_BIN, "--prefix", "frontend", "run", "lint"], "Frontend lint"))
    checks.append(([NPM_BIN, "--prefix", "frontend", "run", "typecheck"], "Frontend typecheck"))

    for command, label in checks:
        exit_code = _run(command, label)
        if exit_code != 0:
            return exit_code

    print("\nAll pre-commit checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fast local smoke check for bootstrap readiness."""

from __future__ import annotations

import importlib
import sys

MIN_VERSION = (3, 11)
REQUIRED_MODULES = [
    "dotenv",
    "pytest",
    "flask",
]


def main() -> int:
    errors: list[str] = []

    if sys.version_info < MIN_VERSION:
        errors.append(
            f"Unsupported Python version: {sys.version_info.major}.{sys.version_info.minor}. "
            f"Expected >= {MIN_VERSION[0]}.{MIN_VERSION[1]}"
        )

    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Missing import `{module}`: {exc}")

    if errors:
        print("Smoke check failed:")
        for error in errors:
            print(f" - {error}")
        print("\nInstall dependencies with: python -m pip install -r requirements.txt")
        return 1

    print("Smoke check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

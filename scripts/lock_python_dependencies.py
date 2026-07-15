#!/usr/bin/env python3
"""Regenerate requirements.lock from the reviewed requirements.txt authority."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "requirements.txt"
LOCK = ROOT / "requirements.lock"
AUTHORITY = ROOT / "config" / "dependency-authority.json"


def main() -> int:
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))["python"]
    required_generator = str(authority["lock_generator"])
    version_result = subprocess.run(
        [sys.executable, "-m", "uv", "--version"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if required_generator not in version_result.stdout.strip():
        raise RuntimeError(
            f"dependency_lock_generator_mismatch: required {required_generator}, "
            f"found {version_result.stdout.strip()}"
        )
    command = [
        sys.executable,
        "-m",
        "uv",
        "pip",
        "compile",
        SOURCE.name,
        "--output-file",
        LOCK.name,
        "--generate-hashes",
        "--universal",
        "--python-version",
        str(authority["python_version"]),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    text = LOCK.read_text(encoding="utf-8")
    lines = text.splitlines()
    insert_at = 2 if len(lines) >= 2 else len(lines)
    lines.insert(insert_at, f"# source-sha256: {source_hash}")
    LOCK.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {LOCK.relative_to(ROOT)} from {SOURCE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

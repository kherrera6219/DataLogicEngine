"""Restrictive per-user ACL helpers for Windows-owned runtime files."""

from __future__ import annotations

import csv
import io
import os
import platform
import subprocess
from pathlib import Path


SYSTEM_SID = "S-1-5-18"


def _current_user_sid() -> str:
    result = subprocess.run(
        ["whoami", "/user", "/fo", "csv", "/nh"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    rows = list(csv.reader(io.StringIO(result.stdout.strip())))
    if not rows or len(rows[0]) < 2 or not rows[0][1].strip():
        raise RuntimeError("Unable to resolve the current Windows user SID")
    return rows[0][1].strip()


def ensure_restricted_user_acl(target: str | os.PathLike[str], *, required: bool = False) -> bool:
    """Restrict a file/directory to the current user and LocalSystem.

    On non-Windows development hosts, owner-only POSIX permissions are applied.
    Production callers can set ``required=True`` to fail closed on ACL errors.
    """

    path = Path(target).resolve()
    try:
        if platform.system() != "Windows":
            os.chmod(path, 0o700 if path.is_dir() else 0o600)
            return False

        user_sid = _current_user_sid()
        user_grant = f"*{user_sid}:{'(OI)(CI)' if path.is_dir() else ''}F"
        system_grant = f"*{SYSTEM_SID}:{'(OI)(CI)' if path.is_dir() else ''}F"
        subprocess.run(
            [
                "icacls",
                str(path),
                "/inheritance:r",
                "/grant:r",
                user_grant,
                "/grant:r",
                system_grant,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return True
    except Exception as exc:
        if required:
            raise RuntimeError(f"Unable to apply a restrictive Windows ACL to {path.name}") from exc
        return False

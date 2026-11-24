"""Prepare Windows ACL layouts on disposable test-owned paths only."""

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import secrets
import subprocess


def prepare_compatible_acl(path: Path) -> None:
    if os.name != "nt":
        return
    sid = "*S-1-15-2-" + "-".join(str(secrets.randbits(32)) for _ in range(7))
    rights = "(OI)(CI)R" if path.is_dir() else "R"
    subprocess.run(
        ["icacls", str(path), "/grant", f"{sid}:{rights}"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["icacls", str(path), "/remove:g", sid],
        check=True,
        capture_output=True,
    )


def prepare_incompatible_acl(path: Path) -> None:
    """Create the legacy control-bit layout on a test-owned path."""
    if os.name != "nt":
        raise RuntimeError("Windows is required")
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi.GetFileSecurityW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    advapi.SetSecurityDescriptorControl.argtypes = [
        ctypes.c_void_p,
        wintypes.WORD,
        wintypes.WORD,
    ]
    advapi.SetFileSecurityW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.c_void_p,
    ]
    required = wintypes.DWORD()
    advapi.GetFileSecurityW(str(path), 4, None, 0, ctypes.byref(required))
    if not required.value:
        raise ctypes.WinError(ctypes.get_last_error())
    descriptor = ctypes.create_string_buffer(required.value)
    if not advapi.GetFileSecurityW(
        str(path), 4, descriptor, required.value, ctypes.byref(required)
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    if not advapi.SetSecurityDescriptorControl(descriptor, 0x0400, 0):
        raise ctypes.WinError(ctypes.get_last_error())
    if not advapi.SetFileSecurityW(str(path), 4, descriptor):
        raise ctypes.WinError(ctypes.get_last_error())

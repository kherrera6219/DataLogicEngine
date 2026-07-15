"""Resource-growth profiles and evaluation for installed application soaks."""

from __future__ import annotations

import os
import platform
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SOAK_REPORT_SCHEMA = "dle.soak-report.v1"


@dataclass(frozen=True)
class SoakProfile:
    name: str
    required_duration_seconds: int
    sample_interval_seconds: int
    max_rss_growth_bytes: int
    max_thread_growth: int
    max_handle_growth: int
    max_child_process_growth: int
    max_log_growth_bytes: int
    max_support_archive_count: int = 5


SOAK_PROFILES = {
    "stress24": SoakProfile(
        name="stress24",
        required_duration_seconds=24 * 60 * 60,
        sample_interval_seconds=60,
        max_rss_growth_bytes=512 * 1024 * 1024,
        max_thread_growth=16,
        max_handle_growth=128,
        max_child_process_growth=0,
        max_log_growth_bytes=512 * 1024 * 1024,
    ),
    "idle72": SoakProfile(
        name="idle72",
        required_duration_seconds=72 * 60 * 60,
        sample_interval_seconds=300,
        max_rss_growth_bytes=256 * 1024 * 1024,
        max_thread_growth=8,
        max_handle_growth=64,
        max_child_process_growth=0,
        max_log_growth_bytes=256 * 1024 * 1024,
    ),
}


def collect_resource_sample(runtime_root: str | Path) -> dict[str, Any]:
    """Collect content-free local resource measurements for one process."""
    root = Path(runtime_root).resolve()
    sample: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "process_id": os.getpid(),
        "rss_bytes": None,
        "thread_count": None,
        "handle_count": None,
        "child_process_count": None,
        "log_bytes": _directory_size(root / "logs"),
        "support_archive_count": _support_archive_count(root / "support-bundles"),
        "sample_error": None,
    }
    try:
        import psutil

        process = psutil.Process()
        sample.update(
            {
                "rss_bytes": int(process.memory_info().rss),
                "thread_count": int(process.num_threads()),
                "handle_count": int(process.num_handles())
                if hasattr(process, "num_handles")
                else None,
                "child_process_count": len(process.children(recursive=True)),
            }
        )
    except ImportError:
        try:
            sample.update(_native_process_measurements())
        except Exception:  # noqa: BLE001 - outer observation boundary must not crash runtime
            sample["sample_error"] = "process_resource_observation_failed"
    except Exception:  # noqa: BLE001 - outer observation boundary must not crash runtime
        sample["sample_error"] = "process_resource_observation_failed"
    return sample


def evaluate_soak(
    profile: SoakProfile,
    samples: list[dict[str, Any]],
    *,
    observed_duration_seconds: float,
    installed_application: bool,
) -> dict[str, Any]:
    """Evaluate bounded growth without upgrading short runs into soak proof."""
    checks: dict[str, dict[str, Any]] = {}
    complete_duration = observed_duration_seconds >= profile.required_duration_seconds
    checks["required_duration"] = {
        "passed": complete_duration,
        "observed": round(observed_duration_seconds, 3),
        "limit": profile.required_duration_seconds,
    }
    checks["sample_integrity"] = {
        "passed": len(samples) >= 2 and all(not item.get("sample_error") for item in samples),
        "observed": len(samples),
        "limit": "at_least_2_error_free_samples",
    }

    _growth_check(checks, samples, "rss_bytes", profile.max_rss_growth_bytes)
    _growth_check(checks, samples, "thread_count", profile.max_thread_growth)
    _growth_check(checks, samples, "handle_count", profile.max_handle_growth)
    _growth_check(
        checks,
        samples,
        "child_process_count",
        profile.max_child_process_growth,
    )
    _growth_check(checks, samples, "log_bytes", profile.max_log_growth_bytes)
    archive_counts = [item.get("support_archive_count") for item in samples]
    checks["support_archive_count"] = {
        "passed": bool(archive_counts)
        and all(
            isinstance(value, int) and value <= profile.max_support_archive_count
            for value in archive_counts
        ),
        "observed": max(
            (value for value in archive_counts if isinstance(value, int)),
            default=None,
        ),
        "limit": profile.max_support_archive_count,
    }

    resource_checks_passed = all(
        result["passed"]
        for name, result in checks.items()
        if name != "required_duration"
    )
    qualifies_cp13_e = bool(
        installed_application and complete_duration and resource_checks_passed
    )
    return {
        "schema_version": SOAK_REPORT_SCHEMA,
        "profile": asdict(profile),
        "generated_at": datetime.now(UTC).isoformat(),
        "installed_application": installed_application,
        "observed_duration_seconds": round(observed_duration_seconds, 3),
        "sample_count": len(samples),
        "checks": checks,
        "resource_checks_passed": resource_checks_passed,
        "qualifies_cp13_e": qualifies_cp13_e,
        "status": "qualified" if qualifies_cp13_e else "engineering_observation_only",
        "samples": samples,
    }


def _growth_check(
    checks: dict[str, dict[str, Any]],
    samples: list[dict[str, Any]],
    field: str,
    limit: int,
) -> None:
    values = [item.get(field) for item in samples]
    numeric = [value for value in values if isinstance(value, int)]
    growth = max((value - numeric[0] for value in numeric), default=None)
    checks[f"{field}_growth"] = {
        "passed": len(numeric) == len(samples) and len(numeric) >= 2 and growth <= limit,
        "observed": growth,
        "limit": limit,
    }


def _directory_size(path: Path) -> int:
    if not path.is_dir():
        return 0
    total = 0
    for candidate in path.rglob("*"):
        try:
            if candidate.is_file():
                total += candidate.stat().st_size
        except OSError:
            continue
    return total


def _support_archive_count(path: Path) -> int:
    if not path.is_dir():
        return 0
    return sum(
        1
        for candidate in path.iterdir()
        if candidate.is_file()
        and candidate.name.startswith("support_bundle_")
        and candidate.suffix in {".zip", ".enc"}
    )


def _native_process_measurements() -> dict[str, int | None]:
    if platform.system() == "Windows":
        return _windows_process_measurements()
    proc_root = Path("/proc")
    if proc_root.is_dir():
        return _proc_process_measurements(proc_root)
    return {
        "rss_bytes": None,
        "thread_count": threading.active_count(),
        "handle_count": None,
        "child_process_count": None,
    }


def _windows_process_measurements() -> dict[str, int]:
    import ctypes
    from ctypes import wintypes

    class ProcessMemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("page_fault_count", wintypes.DWORD),
            ("peak_working_set_size", ctypes.c_size_t),
            ("working_set_size", ctypes.c_size_t),
            ("quota_peak_paged_pool_usage", ctypes.c_size_t),
            ("quota_paged_pool_usage", ctypes.c_size_t),
            ("quota_peak_non_paged_pool_usage", ctypes.c_size_t),
            ("quota_non_paged_pool_usage", ctypes.c_size_t),
            ("pagefile_usage", ctypes.c_size_t),
            ("peak_pagefile_usage", ctypes.c_size_t),
        ]

    class ProcessEntry32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.GetProcessHandleCount.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel32.GetProcessHandleCount.restype = wintypes.BOOL
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry32W)]
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry32W)]
    kernel32.Process32NextW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(ProcessMemoryCounters),
        wintypes.DWORD,
    ]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    process_handle = kernel32.GetCurrentProcess()
    counters = ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(
        process_handle,
        ctypes.byref(counters),
        counters.cb,
    ):
        raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo failed")
    handle_count = wintypes.DWORD()
    if not kernel32.GetProcessHandleCount(process_handle, ctypes.byref(handle_count)):
        raise OSError(ctypes.get_last_error(), "GetProcessHandleCount failed")

    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    invalid_handle = wintypes.HANDLE(-1).value
    if snapshot == invalid_handle:
        raise OSError(ctypes.get_last_error(), "CreateToolhelp32Snapshot failed")
    process_id = os.getpid()
    thread_count = 0
    child_count = 0
    try:
        entry = ProcessEntry32W()
        entry.dwSize = ctypes.sizeof(entry)
        available = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while available:
            if entry.th32ProcessID == process_id:
                thread_count = int(entry.cntThreads)
            if entry.th32ParentProcessID == process_id:
                child_count += 1
            available = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)
    return {
        "rss_bytes": int(counters.working_set_size),
        "thread_count": thread_count,
        "handle_count": int(handle_count.value),
        "child_process_count": child_count,
    }


def _proc_process_measurements(proc_root: Path) -> dict[str, int]:
    process_id = os.getpid()
    statm = (proc_root / "self" / "statm").read_text(encoding="ascii").split()
    rss_bytes = int(statm[1]) * int(os.sysconf("SC_PAGE_SIZE"))
    status_lines = (proc_root / "self" / "status").read_text(encoding="ascii").splitlines()
    thread_count = next(
        int(line.split(":", 1)[1].strip())
        for line in status_lines
        if line.startswith("Threads:")
    )
    child_count = 0
    for candidate in proc_root.iterdir():
        if not candidate.name.isdigit():
            continue
        try:
            fields = (candidate / "stat").read_text(encoding="ascii").split()
            if int(fields[3]) == process_id:
                child_count += 1
        except (OSError, ValueError, IndexError):
            continue
    return {
        "rss_bytes": rss_bytes,
        "thread_count": thread_count,
        "handle_count": len(list((proc_root / "self" / "fd").iterdir())),
        "child_process_count": child_count,
    }

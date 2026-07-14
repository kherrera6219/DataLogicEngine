"""Windows process-tree containment for local stdio MCP servers."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from typing import Any


JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9


class _IOCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_uint64),
        ("WriteOperationCount", ctypes.c_uint64),
        ("OtherOperationCount", ctypes.c_uint64),
        ("ReadTransferCount", ctypes.c_uint64),
        ("WriteTransferCount", ctypes.c_uint64),
        ("OtherTransferCount", ctypes.c_uint64),
    ]


class _BasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _ExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimitInformation),
        ("IoInfo", _IOCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class ProcessTreeGuard:
    """Own a Windows Job Object that kills the entire connector tree on close."""

    def __init__(self, handle: int | None, *, status: str):
        self.handle = handle
        self.status = status

    def close(self) -> None:
        handle = self.handle
        self.handle = None
        if handle and os.name == "nt":
            ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle(handle)


def _process_handle(process: Any) -> int:
    transport = getattr(process, "_transport", None)
    popen = transport.get_extra_info("subprocess") if transport is not None else None
    handle = getattr(popen, "_handle", None)
    if handle is None:
        raise RuntimeError("mcp_process_handle_unavailable")
    return int(handle)


def attach_process_tree_guard(process: Any, *, max_process_memory_mb: int) -> ProcessTreeGuard:
    """Attach a process to a kill-on-close, memory-bounded Windows Job Object."""

    if os.name != "nt":
        return ProcessTreeGuard(None, status="non_windows_test_only")

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL

    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise OSError(ctypes.get_last_error(), "CreateJobObjectW failed")
    try:
        limits = _ExtendedLimitInformation()
        limits.BasicLimitInformation.LimitFlags = (
            JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_PROCESS_MEMORY
        )
        limits.ProcessMemoryLimit = int(max_process_memory_mb) * 1024 * 1024
        if not kernel32.SetInformationJobObject(
            job,
            JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
        ):
            raise OSError(ctypes.get_last_error(), "SetInformationJobObject failed")
        if not kernel32.AssignProcessToJobObject(job, _process_handle(process)):
            raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject failed")
        return ProcessTreeGuard(int(job), status="windows_job_object_attached")
    except Exception:
        kernel32.CloseHandle(job)
        raise

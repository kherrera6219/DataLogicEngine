"""Windows process-tree containment for local stdio MCP servers."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from typing import Any


JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9
TH32CS_SNAPPROCESS = 0x00000002
PROCESS_TERMINATE = 0x0001
SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


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


class _ProcessEntry32W(ctypes.Structure):
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


class ProcessTreeGuard:
    """Own a Windows Job Object that kills the entire connector tree on close."""

    def __init__(self, handle: int | None, *, status: str, root_pid: int | None = None):
        self.handle = handle
        self.status = status
        self.root_pid = root_pid
        self.descendant_pids: set[int] = set()

    def capture_descendants(self) -> None:
        """Capture descendants while the connector root is still alive."""
        if self.root_pid and os.name == "nt":
            self.descendant_pids.update(_descendant_process_ids(self.root_pid))

    def close(self) -> None:
        handle = self.handle
        self.handle = None
        if handle and os.name == "nt":
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
            kernel32.TerminateJobObject.restype = wintypes.BOOL
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel32.CloseHandle.restype = wintypes.BOOL
            job = wintypes.HANDLE(handle)
            descendants = set(self.descendant_pids)
            if self.root_pid:
                descendants.update(_descendant_process_ids(self.root_pid))
            termination_error: OSError | None = None
            try:
                if not kernel32.TerminateJobObject(job, 1):
                    termination_error = OSError(
                        ctypes.get_last_error(),
                        "TerminateJobObject failed for MCP process tree",
                    )
                _terminate_process_ids(descendants)
            finally:
                if not kernel32.CloseHandle(job):
                    raise OSError(ctypes.get_last_error(), "CloseHandle failed for MCP job object")
            if termination_error is not None:
                raise termination_error


def _descendant_process_ids(root_pid: int) -> set[int]:
    """Snapshot descendants before the connector root can exit or be reused."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ProcessEntry32W)]
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ProcessEntry32W)]
    kernel32.Process32NextW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if not snapshot or int(snapshot) == INVALID_HANDLE_VALUE:
        raise OSError(ctypes.get_last_error(), "CreateToolhelp32Snapshot failed")
    parent_by_pid: dict[int, int] = {}
    try:
        entry = _ProcessEntry32W()
        entry.dwSize = ctypes.sizeof(entry)
        has_entry = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while has_entry:
            parent_by_pid[int(entry.th32ProcessID)] = int(entry.th32ParentProcessID)
            has_entry = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(snapshot)

    descendants: set[int] = set()
    frontier = {int(root_pid)}
    while frontier:
        children = {
            pid
            for pid, parent_pid in parent_by_pid.items()
            if parent_pid in frontier and pid not in descendants and pid != root_pid
        }
        descendants.update(children)
        frontier = children
    return descendants


def _terminate_process_ids(process_ids: set[int]) -> None:
    """Terminate captured breakaway descendants using PID-safe native handles."""
    if not process_ids:
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.TerminateProcess.restype = wintypes.BOOL
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    for pid in process_ids:
        process = kernel32.OpenProcess(PROCESS_TERMINATE | SYNCHRONIZE, False, pid)
        if not process:
            # ERROR_INVALID_PARAMETER means the captured process already exited.
            if ctypes.get_last_error() == 87:
                continue
            raise OSError(ctypes.get_last_error(), f"OpenProcess failed for MCP descendant {pid}")
        try:
            if not kernel32.TerminateProcess(process, 1) and ctypes.get_last_error() != 5:
                raise OSError(ctypes.get_last_error(), f"TerminateProcess failed for MCP descendant {pid}")
            wait_result = kernel32.WaitForSingleObject(process, 5_000)
            if wait_result not in {WAIT_OBJECT_0}:
                if wait_result == WAIT_TIMEOUT:
                    raise TimeoutError(f"MCP descendant {pid} did not terminate")
                raise OSError(ctypes.get_last_error(), f"WaitForSingleObject failed for MCP descendant {pid}")
        finally:
            kernel32.CloseHandle(process)


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
        return ProcessTreeGuard(None, status="non_windows_test_only", root_pid=getattr(process, "pid", None))

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
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

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
        return ProcessTreeGuard(
            int(job),
            status="windows_job_object_attached",
            root_pid=int(process.pid),
        )
    except Exception:
        kernel32.CloseHandle(job)
        raise

"""Start Windows connector processes inside a network-isolated AppContainer."""

from __future__ import annotations

import asyncio
from asyncio import base_subprocess
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import subprocess
import time
from typing import Any

from .process_containment import (
    ConnectorAccessLease,
    ConnectorIsolationError,
    ConnectorPathGrant,
    _appcontainer_folder,
    attach_process_tree_guard,
)


class _StartupInfo(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("reserved", wintypes.LPWSTR),
        ("desktop", wintypes.LPWSTR),
        ("title", wintypes.LPWSTR),
        ("x", wintypes.DWORD),
        ("y", wintypes.DWORD),
        ("x_size", wintypes.DWORD),
        ("y_size", wintypes.DWORD),
        ("x_count", wintypes.DWORD),
        ("y_count", wintypes.DWORD),
        ("fill", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("show", wintypes.WORD),
        ("reserved_size", wintypes.WORD),
        ("reserved_bytes", ctypes.c_void_p),
        ("stdin", wintypes.HANDLE),
        ("stdout", wintypes.HANDLE),
        ("stderr", wintypes.HANDLE),
    ]


class _StartupInfoEx(ctypes.Structure):
    _fields_ = [("startup", _StartupInfo), ("attributes", ctypes.c_void_p)]


class _SecurityCapabilities(ctypes.Structure):
    _fields_ = [
        ("sid", ctypes.c_void_p),
        ("capabilities", ctypes.c_void_p),
        ("count", wintypes.DWORD),
        ("reserved", wintypes.DWORD),
    ]


class _ProcessInformation(ctypes.Structure):
    _fields_ = [
        ("process", wintypes.HANDLE),
        ("thread", wintypes.HANDLE),
        ("pid", wintypes.DWORD),
        ("tid", wintypes.DWORD),
    ]


class _JobAccounting(ctypes.Structure):
    _fields_ = [
        ("total_user_time", ctypes.c_int64),
        ("total_kernel_time", ctypes.c_int64),
        ("period_user_time", ctypes.c_int64),
        ("period_kernel_time", ctypes.c_int64),
        ("page_faults", wintypes.DWORD),
        ("total_processes", wintypes.DWORD),
        ("active_processes", wintypes.DWORD),
        ("terminated_processes", wintypes.DWORD),
    ]


class _NativeProcess:
    """Small Popen-compatible owner of an AppContainer process and its pipes."""

    def __init__(
        self, command: list[str], env: dict[str, str], cwd: str | None, sid_text: str
    ):
        import _winapi
        from asyncio import windows_utils

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        advapi = ctypes.WinDLL("advapi32", use_last_error=True)
        kernel.InitializeProcThreadAttributeList.argtypes = [
            ctypes.c_void_p,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        kernel.InitializeProcThreadAttributeList.restype = wintypes.BOOL
        kernel.UpdateProcThreadAttribute.argtypes = [
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.c_size_t,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
        kernel.UpdateProcThreadAttribute.restype = wintypes.BOOL
        kernel.DeleteProcThreadAttributeList.argtypes = [ctypes.c_void_p]
        kernel.CreateProcessW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.LPWSTR,
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.BOOL,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.LPCWSTR,
            ctypes.POINTER(_StartupInfo),
            ctypes.POINTER(_ProcessInformation),
        ]
        kernel.CreateProcessW.restype = wintypes.BOOL
        kernel.SetHandleInformation.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.DWORD,
        ]
        kernel.SetHandleInformation.restype = wintypes.BOOL
        kernel.LocalFree.argtypes = [ctypes.c_void_p]
        advapi.ConvertStringSidToSidW.argtypes = [
            wintypes.LPCWSTR,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        advapi.ConvertStringSidToSidW.restype = wintypes.BOOL

        handles: list[int] = []
        sid = ctypes.c_void_p()
        attribute_list = ctypes.c_void_p()
        attributes_initialized = False
        process_info = None
        owned_pipes = []
        try:
            stdin_read, stdin_write = windows_utils.pipe(
                overlapped=(False, True), duplex=True
            )
            handles.extend([stdin_read, stdin_write])
            stdout_read, stdout_write = windows_utils.pipe(overlapped=(True, False))
            handles.extend([stdout_read, stdout_write])
            stderr_read, stderr_write = windows_utils.pipe(overlapped=(True, False))
            handles.extend([stderr_read, stderr_write])
            child_handles = (wintypes.HANDLE * 3)(
                stdin_read, stdout_write, stderr_write
            )
            for handle in child_handles:
                if not kernel.SetHandleInformation(handle, 1, 1):
                    raise ctypes.WinError(ctypes.get_last_error())

            size = ctypes.c_size_t()
            kernel.InitializeProcThreadAttributeList(None, 2, 0, ctypes.byref(size))
            if not size.value:
                raise ctypes.WinError(ctypes.get_last_error())
            attribute_buffer = ctypes.create_string_buffer(size.value)
            attribute_list = ctypes.cast(attribute_buffer, ctypes.c_void_p)
            if not kernel.InitializeProcThreadAttributeList(
                attribute_list, 2, 0, ctypes.byref(size)
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            attributes_initialized = True
            if not advapi.ConvertStringSidToSidW(sid_text, ctypes.byref(sid)):
                raise ctypes.WinError(ctypes.get_last_error())
            capabilities = _SecurityCapabilities(sid, None, 0, 0)
            if not kernel.UpdateProcThreadAttribute(
                attribute_list,
                0,
                0x20009,
                ctypes.byref(capabilities),
                ctypes.sizeof(capabilities),
                None,
                None,
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            if not kernel.UpdateProcThreadAttribute(
                attribute_list,
                0,
                0x20002,
                ctypes.byref(child_handles),
                ctypes.sizeof(child_handles),
                None,
                None,
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            startup = _StartupInfoEx()
            startup.startup.cb = ctypes.sizeof(startup)
            startup.startup.flags = 0x100
            startup.startup.stdin, startup.startup.stdout, startup.startup.stderr = (
                child_handles
            )
            startup.attributes = attribute_list
            if any(
                "\x00" in key or "=" in key or "\x00" in value
                for key, value in env.items()
            ):
                raise ConnectorIsolationError("Invalid connector environment")
            environment = ctypes.create_unicode_buffer(
                "\x00".join(
                    f"{key}={value}"
                    for key, value in sorted(
                        env.items(), key=lambda pair: pair[0].upper()
                    )
                )
                + "\x00\x00"
            )
            command_line = ctypes.create_unicode_buffer(
                subprocess.list2cmdline(command)
            )
            info = _ProcessInformation()
            flags = 0x00080000 | 0x08000000 | 0x00000400 | 0x00000004 | 0x00000200
            if not kernel.CreateProcessW(
                command[0],
                command_line,
                None,
                None,
                True,
                flags,
                ctypes.cast(environment, ctypes.c_void_p),
                cwd,
                ctypes.byref(startup.startup),
                ctypes.byref(info),
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            process_info = info
            for child in (stdin_read, stdout_write, stderr_write):
                _winapi.CloseHandle(child)
                handles.remove(child)
            self.stdin = windows_utils.PipeHandle(stdin_write)
            owned_pipes.append(self.stdin)
            handles.remove(stdin_write)
            self.stdout = windows_utils.PipeHandle(stdout_read)
            owned_pipes.append(self.stdout)
            handles.remove(stdout_read)
            self.stderr = windows_utils.PipeHandle(stderr_read)
            owned_pipes.append(self.stderr)
            handles.remove(stderr_read)
            self.pid = int(info.pid)
            self._handle = subprocess.Handle(info.process)
            self._thread = int(info.thread)
            self.returncode: int | None = None
            process_info = None
        except BaseException:
            for pipe in owned_pipes:
                pipe.close()
            if process_info is not None:
                _winapi.TerminateProcess(process_info.process, 1)
                _winapi.WaitForSingleObject(process_info.process, 5000)
                _winapi.CloseHandle(process_info.thread)
                _winapi.CloseHandle(process_info.process)
            raise
        finally:
            for handle in handles:
                _winapi.CloseHandle(handle)
            if attributes_initialized:
                kernel.DeleteProcThreadAttributeList(attribute_list)
            if sid.value:
                kernel.LocalFree(sid)

    def resume(self) -> None:
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.ResumeThread.argtypes = [wintypes.HANDLE]
        kernel.ResumeThread.restype = wintypes.DWORD
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        if kernel.ResumeThread(self._thread) == 0xFFFFFFFF:
            raise ConnectorIsolationError(
                "Cannot start isolated connector"
            ) from ctypes.WinError(ctypes.get_last_error())
        kernel.CloseHandle(self._thread)
        self._thread = 0

    def poll(self) -> int | None:
        if self.returncode is not None:
            return self.returncode
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetExitCodeProcess.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel.GetExitCodeProcess.restype = wintypes.BOOL
        code = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(int(self._handle), ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        if code.value != 259:
            self.returncode = int(code.value)
        return self.returncode

    def terminate(self) -> None:
        import _winapi

        if self.poll() is None:
            try:
                _winapi.TerminateProcess(int(self._handle), 1)
            except PermissionError:
                if self.poll() is None:
                    raise

    kill = terminate

    def send_signal(self, _signal: int) -> None:
        self.terminate()

    def close_unstarted(self) -> None:
        self.terminate()
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        if kernel.WaitForSingleObject(int(self._handle), 5000) != 0:
            raise ConnectorIsolationError("Cannot stop failed isolated connector")
        if self._thread:
            kernel.CloseHandle(wintypes.HANDLE(self._thread))
            self._thread = 0
        for pipe in (self.stdin, self.stdout, self.stderr):
            pipe.close()


class _ProcessHolder:
    def __init__(self, process: _NativeProcess):
        self.pid = process.pid
        self._handle = process._handle
        self._transport = self

    def get_extra_info(self, name: str) -> Any:
        return self if name == "subprocess" else None


class IsolatedConnectorGuard:
    """Terminate the full process tree before revoking its temporary grants."""

    def __init__(
        self, process: _NativeProcess, tree_guard: Any, lease: ConnectorAccessLease
    ):
        self.process = process
        self.tree_guard = tree_guard
        self.lease = lease
        self.status = "windows_appcontainer_network_isolated"

    def capture_descendants(self) -> None:
        # This job is assigned before the child starts and does not allow breakaway.
        # Do not reopen captured PIDs, which could have been reused.
        return None

    def close(self) -> None:
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel.TerminateJobObject.restype = wintypes.BOOL
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.QueryInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel.QueryInformationJobObject.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        job = self.tree_guard.handle
        if not job:
            raise ConnectorIsolationError("Connector job is unavailable for cleanup")
        try:
            if not kernel.TerminateJobObject(job, 1):
                raise ConnectorIsolationError(
                    "Cannot terminate connector job"
                ) from ctypes.WinError(ctypes.get_last_error())
            if kernel.WaitForSingleObject(int(self.process._handle), 5000) != 0:
                raise ConnectorIsolationError(
                    "Isolated connector did not stop before access cleanup"
                )
            deadline = time.monotonic() + 5
            while True:
                accounting = _JobAccounting()
                if not kernel.QueryInformationJobObject(
                    job, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None
                ):
                    raise ConnectorIsolationError(
                        "Cannot verify connector job cleanup"
                    ) from ctypes.WinError(ctypes.get_last_error())
                if not accounting.active_processes:
                    break
                if time.monotonic() >= deadline:
                    raise ConnectorIsolationError(
                        "Connector child processes are still active"
                    )
                time.sleep(0.02)
            self.lease.close()
        finally:
            self.tree_guard.handle = None
            if not kernel.CloseHandle(job):
                raise ConnectorIsolationError(
                    "Cannot close connector job"
                ) from ctypes.WinError(ctypes.get_last_error())


class _IsolatedTransport(base_subprocess.BaseSubprocessTransport):
    def _start(self, args, shell, stdin, stdout, stderr, bufsize, **kwargs):
        if shell or (stdin, stdout, stderr) != (subprocess.PIPE,) * 3 or bufsize != 0:
            raise ConnectorIsolationError("Unsupported isolated connector transport")
        lease = kwargs["lease"]
        self._proc = _NativeProcess(
            list(args), kwargs["env"], kwargs["cwd"], lease.lease["sid"]
        )
        tree_guard = None
        wait_future = None

        def exited(_future):
            self._process_exited(self._proc.poll())

        try:
            tree_guard = attach_process_tree_guard(
                _ProcessHolder(self._proc),
                max_process_memory_mb=kwargs["max_process_memory_mb"],
            )
            self.connector_guard = IsolatedConnectorGuard(self._proc, tree_guard, lease)
            wait_future = self._loop._proactor.wait_for_handle(int(self._proc._handle))
            wait_future.add_done_callback(exited)
            lease.preserve_profile()
            self._proc.resume()
        except BaseException:
            if wait_future is not None:
                wait_future.remove_done_callback(exited)
                wait_future.cancel()
            self._proc.close_unstarted()
            if tree_guard is not None:
                self.connector_guard.close()
            raise


async def launch_isolated_connector(
    command: list[str],
    *,
    env: dict[str, str],
    cwd: str | None,
    grants: list[ConnectorPathGrant],
    journal_dir: Path,
    max_process_memory_mb: int,
    limit: int,
) -> tuple[asyncio.subprocess.Process, IsolatedConnectorGuard]:
    """Launch a connector suspended, isolate it, attach its job, then resume it."""
    if os.name != "nt":
        raise ConnectorIsolationError("Windows connector isolation is required")
    lease = ConnectorAccessLease.create(journal_dir, grants)
    try:
        profile_folder = str(_appcontainer_folder(lease.lease["sid"]))
        isolated_env = {
            **env,
            "TEMP": profile_folder,
            "TMP": profile_folder,
            "APPDATA": profile_folder,
            "LOCALAPPDATA": profile_folder,
            "USERPROFILE": profile_folder,
        }
        loop = asyncio.get_running_loop()
        protocol = asyncio.subprocess.SubprocessStreamProtocol(limit=limit, loop=loop)
        waiter = loop.create_future()
        transport = _IsolatedTransport(
            loop,
            protocol,
            command,
            False,
            subprocess.PIPE,
            subprocess.PIPE,
            subprocess.PIPE,
            0,
            waiter=waiter,
            lease=lease,
            env=isolated_env,
            cwd=cwd,
            max_process_memory_mb=max_process_memory_mb,
        )
        try:
            await waiter
        except BaseException:
            transport.close()
            await transport._wait()
            transport.connector_guard.close()
            raise
        return asyncio.subprocess.Process(
            transport, protocol, loop
        ), transport.connector_guard
    except BaseException:
        if lease.path.exists():
            lease.close()
        raise

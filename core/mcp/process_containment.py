"""Windows process-tree containment for local stdio MCP servers."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from contextlib import contextmanager
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any
import uuid


JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9
TH32CS_SNAPPROCESS = 0x00000002
PROCESS_TERMINATE = 0x0001
SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

_FILE_READ_ATTRIBUTES = 0x0080
_READ_CONTROL = 0x00020000
_WRITE_DAC = 0x00040000
_FILE_SHARE_ALL = 0x00000007
_OPEN_EXISTING = 3
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
_DACL_SECURITY_INFORMATION = 0x00000004
_SE_DACL_AUTO_INHERITED = 0x0400
_SE_FILE_OBJECT = 1
_GRANT_ACCESS = 1
_REVOKE_ACCESS = 4
_OBJECT_AND_CONTAINER_INHERIT = 3
_CONTAINER_INHERIT = 2
_FILE_GENERIC_READ = 0x00120089
_FILE_GENERIC_WRITE = 0x00120116
_FILE_GENERIC_EXECUTE = 0x001200A0
_FILE_DELETE = 0x00010000
_DIRECTORY_TRAVERSE = 0x00120020
_PROFILE_PREFIX = "DataLogicEngine.Connector."
_APP_CONTAINER_SID = re.compile(r"^S-1-15-2-(?:[0-9]+-){6}[0-9]+$")


class ConnectorIsolationError(RuntimeError):
    """An isolated connector could not be safely started or cleaned up."""


class ConnectorPermissionsIncompatible(ConnectorIsolationError):
    """Windows would rewrite unrelated access rules on an approved path."""


@dataclass(frozen=True)
class ConnectorPathGrant:
    path: Path
    read: bool = False
    write: bool = False
    execute: bool = False


class _FileTime(ctypes.Structure):
    _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]


class _FileInformation(ctypes.Structure):
    _fields_ = [
        ("attributes", wintypes.DWORD),
        ("creation_time", _FileTime),
        ("access_time", _FileTime),
        ("write_time", _FileTime),
        ("volume_serial", wintypes.DWORD),
        ("size_high", wintypes.DWORD),
        ("size_low", wintypes.DWORD),
        ("link_count", wintypes.DWORD),
        ("file_index_high", wintypes.DWORD),
        ("file_index_low", wintypes.DWORD),
    ]


class _Trustee(ctypes.Structure):
    _fields_ = [
        ("multiple_trustee", ctypes.c_void_p),
        ("multiple_operation", wintypes.DWORD),
        ("trustee_form", wintypes.DWORD),
        ("trustee_type", wintypes.DWORD),
        ("name", ctypes.c_void_p),
    ]


class _ExplicitAccess(ctypes.Structure):
    _fields_ = [
        ("permissions", wintypes.DWORD),
        ("access_mode", wintypes.DWORD),
        ("inheritance", wintypes.DWORD),
        ("trustee", _Trustee),
    ]


class _AclSizeInformation(ctypes.Structure):
    _fields_ = [
        ("ace_count", wintypes.DWORD),
        ("bytes_in_use", wintypes.DWORD),
        ("bytes_free", wintypes.DWORD),
    ]


def _windows_acl_change(
    path: Path,
    sid_string: str,
    *,
    write: bool,
    revoke: bool | None,
    read: bool = True,
    execute: bool = True,
    expected_id: tuple[int, int, int] | None = None,
) -> tuple[int, int, int]:
    """Change only this identity's ACE through an opened, identity-checked handle."""
    if os.name != "nt" or not _APP_CONTAINER_SID.fullmatch(sid_string):
        raise ConnectorIsolationError("Invalid connector identity or platform")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.GetFileInformationByHandle.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_FileInformation),
    ]
    kernel.GetFileInformationByHandle.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    advapi.ConvertStringSidToSidW.argtypes = [
        wintypes.LPCWSTR,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi.ConvertStringSidToSidW.restype = wintypes.BOOL
    advapi.GetSecurityInfo.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi.GetSecurityInfo.restype = wintypes.DWORD
    advapi.GetSecurityDescriptorControl.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.WORD),
        ctypes.POINTER(wintypes.DWORD),
    ]
    advapi.GetSecurityDescriptorControl.restype = wintypes.BOOL
    advapi.SetEntriesInAclW.argtypes = [
        wintypes.DWORD,
        ctypes.POINTER(_ExplicitAccess),
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi.SetEntriesInAclW.restype = wintypes.DWORD
    advapi.SetSecurityInfo.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    advapi.SetSecurityInfo.restype = wintypes.DWORD
    handle = kernel.CreateFileW(
        str(path),
        _READ_CONTROL | _WRITE_DAC | _FILE_READ_ATTRIBUTES,
        _FILE_SHARE_ALL,
        None,
        _OPEN_EXISTING,
        _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    if not handle or handle == INVALID_HANDLE_VALUE:
        raise ConnectorIsolationError(
            "Unable to open approved connector path"
        ) from ctypes.WinError(ctypes.get_last_error())
    sid = ctypes.c_void_p()
    security = ctypes.c_void_p()
    old_acl = ctypes.c_void_p()
    new_acl = ctypes.c_void_p()
    try:
        info = _FileInformation()
        if not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        if info.attributes & _FILE_ATTRIBUTE_REPARSE_POINT:
            raise ConnectorIsolationError("Connector paths cannot be reparse points")
        file_id = (
            int(info.volume_serial),
            int(info.file_index_high),
            int(info.file_index_low),
        )
        if expected_id is not None and file_id != expected_id:
            raise ConnectorIsolationError("Approved connector path identity changed")
        if revoke is None:
            return file_id
        if not advapi.ConvertStringSidToSidW(sid_string, ctypes.byref(sid)):
            raise ctypes.WinError(ctypes.get_last_error())
        result = advapi.GetSecurityInfo(
            handle,
            _SE_FILE_OBJECT,
            _DACL_SECURITY_INFORMATION,
            None,
            None,
            ctypes.byref(old_acl),
            None,
            ctypes.byref(security),
        )
        if result:
            raise ctypes.WinError(result)
        if not old_acl:
            raise ConnectorIsolationError(
                "Connector path has an unrestricted access list"
            )
        control = wintypes.WORD()
        revision = wintypes.DWORD()
        if not advapi.GetSecurityDescriptorControl(
            security, ctypes.byref(control), ctypes.byref(revision)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        if not control.value & _SE_DACL_AUTO_INHERITED:
            raise ConnectorPermissionsIncompatible(
                "Connector path has incompatible permission inheritance"
            )
        if info.attributes & 0x10:
            _require_compatible_acl_tree(path)
        trustee = _Trustee(None, 0, 0, 0, sid.value)
        entries = []
        if revoke:
            entries.append(_ExplicitAccess(0, _REVOKE_ACCESS, 0, trustee))
        else:
            is_directory = bool(info.attributes & 0x10)
            if is_directory:
                entries.append(
                    _ExplicitAccess(
                        _DIRECTORY_TRAVERSE, _GRANT_ACCESS, _CONTAINER_INHERIT, trustee
                    )
                )
            rights = (
                (_FILE_GENERIC_READ if read else 0)
                | ((_FILE_GENERIC_WRITE | _FILE_DELETE) if write else 0)
                | (_FILE_GENERIC_EXECUTE if execute else 0)
            )
            if rights:
                entries.append(
                    _ExplicitAccess(
                        rights,
                        _GRANT_ACCESS,
                        _OBJECT_AND_CONTAINER_INHERIT if is_directory else 0,
                        trustee,
                    )
                )
            if not entries:
                raise ConnectorIsolationError("Connector file grant has no permissions")
        entry_array = (_ExplicitAccess * len(entries))(*entries)
        result = advapi.SetEntriesInAclW(
            len(entries), entry_array, old_acl, ctypes.byref(new_acl)
        )
        if result:
            raise ctypes.WinError(result)
        result = advapi.SetSecurityInfo(
            handle,
            _SE_FILE_OBJECT,
            _DACL_SECURITY_INFORMATION,
            None,
            None,
            new_acl,
            None,
        )
        if result:
            raise ctypes.WinError(result)
        return file_id
    finally:
        for allocation in (new_acl, security, sid):
            if allocation.value:
                kernel.LocalFree(allocation)
        kernel.CloseHandle(handle)


def _inspect_connector_acl(
    path: Path, sid_string: str | None
) -> tuple[bool, bool, bool, bool]:
    """Inspect an object's DACL without following its final reparse point."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.GetFileInformationByHandle.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_FileInformation),
    ]
    kernel.GetFileInformationByHandle.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    advapi.ConvertStringSidToSidW.argtypes = [
        wintypes.LPCWSTR,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi.ConvertStringSidToSidW.restype = wintypes.BOOL
    advapi.GetSecurityInfo.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi.GetSecurityInfo.restype = wintypes.DWORD
    advapi.GetSecurityDescriptorControl.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.WORD),
        ctypes.POINTER(wintypes.DWORD),
    ]
    advapi.GetSecurityDescriptorControl.restype = wintypes.BOOL
    advapi.GetAclInformation.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.c_int,
    ]
    advapi.GetAclInformation.restype = wintypes.BOOL
    advapi.GetAce.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi.GetAce.restype = wintypes.BOOL
    advapi.EqualSid.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    advapi.EqualSid.restype = wintypes.BOOL
    handle = kernel.CreateFileW(
        str(path),
        _READ_CONTROL | _FILE_READ_ATTRIBUTES,
        _FILE_SHARE_ALL,
        None,
        _OPEN_EXISTING,
        _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    if not handle or handle == INVALID_HANDLE_VALUE:
        raise ConnectorIsolationError(
            "Cannot verify connector access cleanup"
        ) from ctypes.WinError(ctypes.get_last_error())
    sid = ctypes.c_void_p()
    security = ctypes.c_void_p()
    acl = ctypes.c_void_p()
    try:
        info = _FileInformation()
        if not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        if sid_string is not None and not advapi.ConvertStringSidToSidW(
            sid_string, ctypes.byref(sid)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        result = advapi.GetSecurityInfo(
            handle,
            _SE_FILE_OBJECT,
            _DACL_SECURITY_INFORMATION,
            None,
            None,
            ctypes.byref(acl),
            None,
            ctypes.byref(security),
        )
        if result:
            raise ctypes.WinError(result)
        if not acl:
            raise ConnectorIsolationError(
                "Cannot verify an unrestricted connector path"
            )
        control = wintypes.WORD()
        revision = wintypes.DWORD()
        if not advapi.GetSecurityDescriptorControl(
            security, ctypes.byref(control), ctypes.byref(revision)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        found = False
        if sid_string is not None:
            size = _AclSizeInformation()
            if not advapi.GetAclInformation(
                acl, ctypes.byref(size), ctypes.sizeof(size), 2
            ):
                raise ctypes.WinError(ctypes.get_last_error())
            for index in range(size.ace_count):
                ace = ctypes.c_void_p()
                if not advapi.GetAce(acl, index, ctypes.byref(ace)):
                    raise ctypes.WinError(ctypes.get_last_error())
                if ctypes.c_ubyte.from_address(
                    ace.value
                ).value == 0 and advapi.EqualSid(sid, ace.value + 8):
                    found = True
                    break
        return (
            found,
            bool(info.attributes & 0x10),
            bool(info.attributes & _FILE_ATTRIBUTE_REPARSE_POINT),
            bool(control.value & _SE_DACL_AUTO_INHERITED),
        )
    finally:
        for allocation in (security, sid):
            if allocation.value:
                kernel.LocalFree(allocation)
        kernel.CloseHandle(handle)


def _require_compatible_acl_tree(root: Path) -> None:
    """Refuse trees Windows would convert while propagating a connector ACE."""
    pending = [root]
    while pending:
        current = pending.pop()
        _, is_directory, is_reparse, compatible = _inspect_connector_acl(current, None)
        if is_reparse:
            raise ConnectorIsolationError(
                "Connector paths cannot contain reparse points"
            )
        if not compatible:
            raise ConnectorPermissionsIncompatible(
                "Connector path has incompatible permission inheritance"
            )
        if is_directory:
            try:
                with os.scandir(current) as entries:
                    pending.extend(Path(entry.path) for entry in entries)
            except OSError as exc:
                raise ConnectorIsolationError(
                    "Cannot verify connector path permissions"
                ) from exc


def _verify_connector_access_removed(root: Path, sid: str) -> None:
    """Fail if any reachable approved object retains this connector's grant."""
    pending = [root]
    while pending:
        current = pending.pop()
        found, is_directory, is_reparse, _ = _inspect_connector_acl(current, sid)
        if found:
            raise ConnectorIsolationError(
                "Connector access remains on an approved path"
            )
        if is_directory and not is_reparse:
            try:
                with os.scandir(current) as entries:
                    pending.extend(Path(entry.path) for entry in entries)
            except OSError as exc:
                raise ConnectorIsolationError(
                    "Cannot verify connector access cleanup"
                ) from exc


def _process_start_time(pid: int) -> int | None:
    """Return the Windows process creation time, or None if it no longer exists."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_FileTime),
        ctypes.POINTER(_FileTime),
        ctypes.POINTER(_FileTime),
        ctypes.POINTER(_FileTime),
    ]
    kernel.GetProcessTimes.restype = wintypes.BOOL
    kernel.GetExitCodeProcess.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel.GetExitCodeProcess.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        error = ctypes.get_last_error()
        if error == 87:
            return None
        raise ConnectorIsolationError(
            "Cannot verify connector lease owner"
        ) from ctypes.WinError(error)
    try:
        exit_code = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            raise ConnectorIsolationError(
                "Cannot verify connector lease owner"
            ) from ctypes.WinError(ctypes.get_last_error())
        if exit_code.value != 259:
            return None
        creation, exit_time, kernel_time, user_time = (_FileTime() for _ in range(4))
        if not kernel.GetProcessTimes(
            handle,
            ctypes.byref(creation),
            ctypes.byref(exit_time),
            ctypes.byref(kernel_time),
            ctypes.byref(user_time),
        ):
            raise ConnectorIsolationError(
                "Cannot verify connector lease owner"
            ) from ctypes.WinError(ctypes.get_last_error())
        return (int(creation.high) << 32) | int(creation.low)
    finally:
        kernel.CloseHandle(handle)


def _create_appcontainer_profile(name: str) -> str:
    userenv = ctypes.WinDLL("userenv", use_last_error=True)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    userenv.CreateAppContainerProfile.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    userenv.CreateAppContainerProfile.restype = ctypes.c_long
    userenv.DeleteAppContainerProfile.argtypes = [wintypes.LPCWSTR]
    userenv.DeleteAppContainerProfile.restype = ctypes.c_long
    advapi.ConvertSidToStringSidW.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi.ConvertSidToStringSidW.restype = wintypes.BOOL
    advapi.FreeSid.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    sid = ctypes.c_void_p()
    result = userenv.CreateAppContainerProfile(
        name, name, "DataLogicEngine connector", None, 0, ctypes.byref(sid)
    )
    if result:
        raise ConnectorIsolationError(
            f"Cannot create connector isolation profile: {result & 0xFFFFFFFF:#x}"
        )
    sid_text = ctypes.c_void_p()
    try:
        if not advapi.ConvertSidToStringSidW(sid, ctypes.byref(sid_text)):
            raise ctypes.WinError(ctypes.get_last_error())
        value = ctypes.wstring_at(sid_text.value)
        if not _APP_CONTAINER_SID.fullmatch(value):
            raise ConnectorIsolationError("Unexpected connector identity")
        return value
    except BaseException:
        userenv.DeleteAppContainerProfile(name)
        raise
    finally:
        if sid_text.value:
            kernel.LocalFree(sid_text)
        if sid.value:
            advapi.FreeSid(sid)


def _delete_appcontainer_profile(name: str) -> None:
    if not re.fullmatch(re.escape(_PROFILE_PREFIX) + r"[0-9a-f]{32}", name):
        raise ConnectorIsolationError("Invalid connector profile name")
    userenv = ctypes.WinDLL("userenv", use_last_error=True)
    userenv.DeleteAppContainerProfile.argtypes = [wintypes.LPCWSTR]
    userenv.DeleteAppContainerProfile.restype = ctypes.c_long
    result = userenv.DeleteAppContainerProfile(name) & 0xFFFFFFFF
    if result not in {0, 0x80070002, 0x80070490}:
        raise ConnectorIsolationError(f"Cannot remove connector profile: {result:#x}")


def _profile_sid(name: str) -> str:
    """Derive the deterministic SID so recovery cannot use an unrelated SID."""
    userenv = ctypes.WinDLL("userenv", use_last_error=True)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    userenv.DeriveAppContainerSidFromAppContainerName.argtypes = [
        wintypes.LPCWSTR,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    userenv.DeriveAppContainerSidFromAppContainerName.restype = ctypes.c_long
    advapi.ConvertSidToStringSidW.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    advapi.ConvertSidToStringSidW.restype = wintypes.BOOL
    advapi.FreeSid.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    sid = ctypes.c_void_p()
    sid_text = ctypes.c_void_p()
    result = userenv.DeriveAppContainerSidFromAppContainerName(name, ctypes.byref(sid))
    if result:
        raise ConnectorIsolationError(
            f"Cannot derive connector identity: {result & 0xFFFFFFFF:#x}"
        )
    try:
        if not advapi.ConvertSidToStringSidW(sid, ctypes.byref(sid_text)):
            raise ctypes.WinError(ctypes.get_last_error())
        return ctypes.wstring_at(sid_text.value)
    finally:
        if sid_text.value:
            kernel.LocalFree(sid_text)
        if sid.value:
            advapi.FreeSid(sid)


def _appcontainer_folder(sid: str) -> Path:
    if not _APP_CONTAINER_SID.fullmatch(sid):
        raise ConnectorIsolationError("Invalid connector identity")
    userenv = ctypes.WinDLL("userenv", use_last_error=True)
    ole = ctypes.OleDLL("ole32")
    userenv.GetAppContainerFolderPath.argtypes = [
        wintypes.LPCWSTR,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    userenv.GetAppContainerFolderPath.restype = ctypes.c_long
    ole.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    result_path = ctypes.c_void_p()
    result = userenv.GetAppContainerFolderPath(sid, ctypes.byref(result_path))
    if result:
        raise ConnectorIsolationError(
            f"Cannot locate connector profile: {result & 0xFFFFFFFF:#x}"
        )
    try:
        return Path(ctypes.wstring_at(result_path.value))
    finally:
        if result_path.value:
            ole.CoTaskMemFree(result_path)


@contextmanager
def _lease_lock(directory: Path):
    import msvcrt

    with open(directory / ".lock", "a+b") as lock:
        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b"\0")
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise ConnectorIsolationError("Connector access journal is busy") from exc
        try:
            yield
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


def _save_lease(path: Path, lease: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with open(temporary, "x", encoding="utf-8") as stream:
            json.dump(lease, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _validate_lease(lease: Any) -> None:
    if not isinstance(lease, dict) or lease.get("version") != 1:
        raise ConnectorIsolationError("Invalid connector access journal")
    if not re.fullmatch(
        re.escape(_PROFILE_PREFIX) + r"[0-9a-f]{32}", str(lease.get("profile", ""))
    ):
        raise ConnectorIsolationError("Invalid connector access journal profile")
    if not _APP_CONTAINER_SID.fullmatch(str(lease.get("sid", ""))):
        raise ConnectorIsolationError("Invalid connector access journal identity")
    if _profile_sid(lease["profile"]) != lease["sid"]:
        raise ConnectorIsolationError("Connector access journal identity mismatch")
    if not isinstance(lease.get("preserve_profile", False), bool):
        raise ConnectorIsolationError("Invalid connector profile retention state")
    if (
        type(lease.get("owner_pid")) is not int
        or lease["owner_pid"] <= 0
        or type(lease.get("owner_start")) is not int
        or lease["owner_start"] <= 0
    ):
        raise ConnectorIsolationError("Invalid connector access journal owner")
    records = lease.get("paths")
    if not isinstance(records, list) or len(records) > 64:
        raise ConnectorIsolationError("Invalid connector access journal paths")
    for item in records:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("path"), str)
            or not Path(item["path"]).is_absolute()
            or not isinstance(item.get("write"), bool)
            or not isinstance(item.get("read", True), bool)
            or not isinstance(item.get("execute", True), bool)
            or not isinstance(item.get("id"), list)
            or len(item["id"]) != 3
            or not all(isinstance(part, int) for part in item["id"])
        ):
            raise ConnectorIsolationError("Invalid connector access journal path")


def _remove_lease(path: Path, lease: dict[str, Any]) -> None:
    _validate_lease(lease)
    for item in reversed(lease["paths"]):
        target = Path(item["path"])
        found, _, _, _ = _inspect_connector_acl(target, lease["sid"])
        if not found:
            continue
        _require_compatible_acl_tree(target)
        _windows_acl_change(
            target,
            lease["sid"],
            write=item["write"],
            revoke=True,
            read=item.get("read", True),
            execute=item.get("execute", True),
            expected_id=tuple(item["id"]),
        )
    for item in lease["paths"]:
        _windows_acl_change(
            Path(item["path"]),
            lease["sid"],
            write=item["write"],
            revoke=None,
            expected_id=tuple(item["id"]),
        )
        _verify_connector_access_removed(Path(item["path"]), lease["sid"])
    if lease.get("preserve_profile", False):
        retained = path.parent / "retained"
        retained.mkdir(exist_ok=True)
        _save_lease(retained / path.name, lease)
    else:
        _delete_appcontainer_profile(lease["profile"])
    path.unlink()


def recover_connector_access(directory: Path) -> int:
    """Revoke leases whose owning process exited, preserving active leases."""
    if os.name != "nt":
        raise ConnectorIsolationError("Windows connector isolation is required")
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    from backend.security.windows_acl import ensure_restricted_user_acl

    ensure_restricted_user_acl(directory, required=True)
    recovered = 0
    with _lease_lock(directory):
        for path in sorted(directory.glob("*.json")):
            with open(path, encoding="utf-8") as stream:
                lease = json.load(stream)
            _validate_lease(lease)
            if path.name != f"{lease['profile']}.json":
                raise ConnectorIsolationError("Connector access journal name mismatch")
            if _process_start_time(lease["owner_pid"]) == lease["owner_start"]:
                continue
            _remove_lease(path, lease)
            recovered += 1
    return recovered


class ConnectorAccessLease:
    """Journal and revoke only the ACL entries created for one connector."""

    def __init__(self, directory: Path, path: Path, lease: dict[str, Any]) -> None:
        self.directory = directory
        self.path = path
        self.lease = lease
        self.cleanup_safe = True

    @classmethod
    def create(
        cls, directory: Path, paths: list[ConnectorPathGrant | tuple[Path, bool]]
    ) -> ConnectorAccessLease:
        if os.name != "nt":
            raise ConnectorIsolationError("Windows connector isolation is required")
        directory = Path(directory).resolve()
        recover_connector_access(directory)
        normalized: dict[Path, ConnectorPathGrant] = {}
        for entry in paths:
            grant = (
                entry
                if isinstance(entry, ConnectorPathGrant)
                else ConnectorPathGrant(entry[0], True, entry[1], True)
            )
            original = grant.path
            path = Path(original).resolve(strict=True)
            if path == Path(path.anchor):
                raise ConnectorIsolationError(
                    "A drive root cannot be a connector access grant"
                )
            if (
                directory == path
                or directory.is_relative_to(path)
                or path.is_relative_to(directory)
            ):
                raise ConnectorIsolationError(
                    "Connector access cannot overlap its private journal"
                )
            previous = normalized.get(path, ConnectorPathGrant(path))
            normalized[path] = ConnectorPathGrant(
                path,
                previous.read or grant.read,
                previous.write or grant.write,
                previous.execute or grant.execute,
            )
        if not normalized or len(normalized) > 64:
            raise ConnectorIsolationError("Invalid connector access grant count")
        for target in normalized:
            _require_compatible_acl_tree(target)
        profile = _PROFILE_PREFIX + uuid.uuid4().hex
        with _lease_lock(directory):
            sid = _create_appcontainer_profile(profile)
            path = directory / f"{profile}.json"
            owner_start = _process_start_time(os.getpid())
            if owner_start is None:
                _delete_appcontainer_profile(profile)
                raise ConnectorIsolationError("Cannot identify connector lease owner")
            lease: dict[str, Any] = {
                "version": 1,
                "profile": profile,
                "sid": sid,
                "owner_pid": os.getpid(),
                "owner_start": owner_start,
                "preserve_profile": False,
                "paths": [],
            }
            try:
                _save_lease(path, lease)
                for target, grant in normalized.items():
                    _require_compatible_acl_tree(target)
                    identity = _windows_acl_change(
                        target,
                        sid,
                        write=grant.write,
                        revoke=None,
                        read=grant.read,
                        execute=grant.execute,
                    )
                    lease["paths"].append(
                        {
                            "path": str(target),
                            "read": grant.read,
                            "write": grant.write,
                            "execute": grant.execute,
                            "id": list(identity),
                        }
                    )
                    _save_lease(path, lease)
                    _require_compatible_acl_tree(target)
                    _windows_acl_change(
                        target,
                        sid,
                        write=grant.write,
                        revoke=False,
                        expected_id=identity,
                        read=grant.read,
                        execute=grant.execute,
                    )
            except BaseException:
                if path.exists():
                    _remove_lease(path, lease)
                else:
                    _delete_appcontainer_profile(profile)
                raise
        return cls(directory, path, lease)

    def preserve_profile(self) -> None:
        """Retain a profile that may contain connector-created files."""
        with _lease_lock(self.directory):
            if not self.path.exists():
                raise ConnectorIsolationError("Connector access journal is missing")
            self.lease["preserve_profile"] = True
            _save_lease(self.path, self.lease)

    def close(self) -> None:
        with _lease_lock(self.directory):
            if not self.path.exists():
                raise ConnectorIsolationError("Connector access journal is missing")
            _remove_lease(self.path, self.lease)


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
                    raise OSError(
                        ctypes.get_last_error(), "CloseHandle failed for MCP job object"
                    )
            if termination_error is not None:
                raise termination_error


def _descendant_process_ids(root_pid: int) -> set[int]:
    """Snapshot descendants before the connector root can exit or be reused."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.Process32FirstW.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_ProcessEntry32W),
    ]
    kernel32.Process32FirstW.restype = wintypes.BOOL
    kernel32.Process32NextW.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_ProcessEntry32W),
    ]
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
            raise OSError(
                ctypes.get_last_error(), f"OpenProcess failed for MCP descendant {pid}"
            )
        try:
            if (
                not kernel32.TerminateProcess(process, 1)
                and ctypes.get_last_error() != 5
            ):
                raise OSError(
                    ctypes.get_last_error(),
                    f"TerminateProcess failed for MCP descendant {pid}",
                )
            wait_result = kernel32.WaitForSingleObject(process, 5_000)
            if wait_result not in {WAIT_OBJECT_0}:
                if wait_result == WAIT_TIMEOUT:
                    raise TimeoutError(f"MCP descendant {pid} did not terminate")
                raise OSError(
                    ctypes.get_last_error(),
                    f"WaitForSingleObject failed for MCP descendant {pid}",
                )
        finally:
            kernel32.CloseHandle(process)


def _process_handle(process: Any) -> int:
    transport = getattr(process, "_transport", None)
    popen = transport.get_extra_info("subprocess") if transport is not None else None
    handle = getattr(popen, "_handle", None)
    if handle is None:
        raise RuntimeError("mcp_process_handle_unavailable")
    return int(handle)


def attach_process_tree_guard(
    process: Any, *, max_process_memory_mb: int
) -> ProcessTreeGuard:
    """Attach a process to a kill-on-close, memory-bounded Windows Job Object."""

    if os.name != "nt":
        return ProcessTreeGuard(
            None, status="non_windows_test_only", root_pid=getattr(process, "pid", None)
        )

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

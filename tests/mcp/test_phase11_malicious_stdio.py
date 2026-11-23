from __future__ import annotations

import asyncio
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import threading
import time

import pytest

from core.mcp.mcp_client import MCPClient
from core.mcp.mcp_manager import MCPManager
from core.mcp.mcp_protocol import MCPError
from core.mcp.process_containment import (
    _delete_appcontainer_profile,
    _descendant_process_ids,
)
from tests.fixtures.connector_acl import prepare_compatible_acl


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mcp_stdio_fixture.py"


@pytest.fixture(autouse=True)
def cleanup_test_profiles(tmp_path):
    yield
    if os.name == "nt":
        for record in (tmp_path / "journal" / "retained").glob("*.json"):
            profile = json.loads(record.read_text(encoding="utf-8"))["profile"]
            _delete_appcontainer_profile(profile)


@pytest.fixture(scope="module")
def stdio_runtime(tmp_path_factory):
    if os.name != "nt":
        fixtures = tmp_path_factory.mktemp("isolated-mcp-fixtures")
        script = fixtures / FIXTURE.name
        shutil.copy2(FIXTURE, script)
        return sys.executable, script, fixtures, [str(fixtures)]
    root = tmp_path_factory.mktemp("isolated-mcp-runtime")
    prepare_compatible_acl(root)
    runtime = root / "python"
    runtime.mkdir()
    base = Path(sys.base_prefix)
    for pattern in ("python.exe", "python3.dll", "python3*.dll", "vcruntime*.dll"):
        for source in base.glob(pattern):
            shutil.copy2(source, runtime / source.name)
    for name in ("Lib", "DLLs"):
        shutil.copytree(
            base / name,
            runtime / name,
            ignore=shutil.ignore_patterns(
                "site-packages", "__pycache__", "test", "tests"
            ),
        )
    fixtures = root / "fixtures"
    fixtures.mkdir()
    script = fixtures / FIXTURE.name
    shutil.copy2(FIXTURE, script)
    return str(runtime / "python.exe"), script, fixtures, [str(runtime), str(fixtures)]


async def _connected_client(
    stdio_runtime, journal_dir, *, timeout: int = 2, max_message_bytes: int = 65_536
) -> MCPClient:
    executable, fixture, cwd, roots = stdio_runtime
    client = MCPClient(name="Phase11FixtureClient", journal_dir=journal_dir)
    await client.connect_via_stdio(
        [executable, str(fixture)],
        cwd=str(cwd),
        file_roots=roots,
        approved_scopes=["connector:fixture:read", "connector:fixture:execute"],
        limits={
            "request_timeout_seconds": timeout,
            "max_message_bytes": max_message_bytes,
            "max_stderr_bytes": 4096,
            "max_process_memory_mb": 128,
        },
    )
    return client


@pytest.mark.asyncio
async def test_real_stdio_fixture_discovery_call_and_shutdown(stdio_runtime, tmp_path):
    client = await _connected_client(stdio_runtime, tmp_path / "journal")
    process = client.process

    tools = await client.list_tools()
    result = await client.call_tool(name="echo", arguments={})
    resource = await client.read_resource(uri="fixture://real")
    prompt = await client.get_prompt(name="fixture_prompt", arguments={})

    assert any(tool["name"] == "echo" for tool in tools)
    assert result["content"][0]["text"] == "real echo"
    assert resource["contents"][0]["text"] == "real resource"
    assert prompt["messages"][0]["content"]["text"] == "real prompt"
    await client.disconnect_async()
    assert client.process is None
    if process is not None:
        await asyncio.wait_for(process.wait(), timeout=5)


@pytest.mark.asyncio
async def test_real_connector_network_and_file_boundaries(stdio_runtime, tmp_path):
    _executable, _fixture, fixture_dir, _roots = stdio_runtime
    allowed = fixture_dir / "approved-test-file.txt"
    forbidden = tmp_path / "not-approved.txt"
    allowed.write_text("allowed", encoding="utf-8")
    forbidden.write_text("private", encoding="utf-8")
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    listener.setblocking(False)
    client = None
    try:
        client = await _connected_client(stdio_runtime, tmp_path / "journal")
        allowed_result = await client.call_tool(
            name="file_probe", arguments={"path": str(allowed)}
        )
        denied_result = await client.call_tool(
            name="file_probe", arguments={"path": str(forbidden)}
        )
        network_result = await client.call_tool(
            name="local_network_probe", arguments={"port": listener.getsockname()[1]}
        )
        assert allowed_result["content"][0]["text"] == "readable"
        if os.name == "nt":
            assert denied_result["content"][0]["text"] == "blocked"
            assert network_result["content"][0]["text"] == "blocked"
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(
                    asyncio.get_running_loop().sock_accept(listener), 0.25
                )
        else:
            assert client.containment_status == "non_windows_test_only"
            assert denied_result["content"][0]["text"] == "readable"
            assert network_result["content"][0]["text"] == "connected"
            accepted, _ = await asyncio.wait_for(
                asyncio.get_running_loop().sock_accept(listener), 1
            )
            accepted.close()
    finally:
        if client is not None:
            await client.disconnect_async()
        listener.close()
        allowed.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_delayed_server_hits_request_timeout_and_can_be_stopped(
    stdio_runtime, tmp_path
):
    client = await _connected_client(stdio_runtime, tmp_path / "journal", timeout=1)
    try:
        with pytest.raises(MCPError) as exc:
            await client.call_tool(name="delay", arguments={})
        assert exc.value.data["reason"] == "MCP_REQUEST_TIMEOUT"
    finally:
        await client.disconnect_async()


@pytest.mark.asyncio
async def test_malformed_json_rpc_fails_pending_request_and_disconnects(
    stdio_runtime, tmp_path
):
    client = await _connected_client(stdio_runtime, tmp_path / "journal")
    with pytest.raises(Exception):
        await client.call_tool(name="malformed", arguments={})
    assert client.connected is False
    await client.disconnect_async()


@pytest.mark.asyncio
async def test_oversized_stdout_is_rejected_and_disconnects(stdio_runtime, tmp_path):
    client = await _connected_client(
        stdio_runtime, tmp_path / "journal", max_message_bytes=4096
    )
    with pytest.raises(Exception):
        await client.call_tool(name="oversized", arguments={})
    assert client.connected is False
    await client.disconnect_async()


def _windows_process_is_active(pid: int) -> bool:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.GetExitCodeProcess.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        return False
    try:
        exit_code = wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return False
        return exit_code.value == 259
    finally:
        kernel32.CloseHandle(handle)


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object qualification")
@pytest.mark.asyncio
async def test_job_object_stop_terminates_spawned_child_process_tree(
    stdio_runtime, tmp_path
):
    client = await _connected_client(stdio_runtime, tmp_path / "journal")
    result = await client.call_tool(name="spawn_child", arguments={})
    child_pid = int(result["content"][0]["text"])
    assert _windows_process_is_active(child_pid)
    assert client.process is not None
    assert child_pid in _descendant_process_ids(client.process.pid)

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.GetExitCodeProcess.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.GetExitCodeProcess.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    child_handle = kernel32.OpenProcess(0x00100000 | 0x1000, False, child_pid)
    assert child_handle

    try:
        await client.disconnect_async()
        assert kernel32.WaitForSingleObject(child_handle, 5_000) == 0
        exit_code = wintypes.DWORD()
        assert kernel32.GetExitCodeProcess(child_handle, ctypes.byref(exit_code))
        assert exit_code.value != 259
    finally:
        kernel32.CloseHandle(child_handle)


def test_manager_runtime_loop_keeps_stdio_readers_alive_across_requests(
    stdio_runtime, tmp_path
):
    executable, fixture, cwd, roots = stdio_runtime
    manager = MCPManager(journal_dir=tmp_path / "journal")
    definition = {
        "name": "runtime-fixture",
        "command": executable,
        "args": [str(fixture)],
        "cwd": str(cwd),
        "file_roots": roots,
        "env": {},
        "limits": {
            "request_timeout_seconds": 2,
            "max_message_bytes": 65536,
            "max_stderr_bytes": 4096,
            "max_process_memory_mb": 128,
        },
    }
    try:
        started = manager.start_external_server_sync(
            "fixture",
            definition,
            {},
            ["connector:fixture:read", "connector:fixture:execute"],
        )
        result = manager.call_external_tool_sync(
            "fixture",
            "echo",
            {},
            timeout=3,
        )

        assert started["client"]["connected"] is True
        assert any(tool["name"] == "echo" for tool in started["discovery"]["tools"])
        assert result["content"][0]["text"] == "real echo"
        assert manager.stop_external_server_sync("fixture") is True
    finally:
        manager.shutdown()


def test_manager_cancels_named_in_flight_operation(stdio_runtime, tmp_path):
    executable, fixture, cwd, roots = stdio_runtime
    manager = MCPManager(journal_dir=tmp_path / "journal")
    definition = {
        "name": "runtime-cancel-fixture",
        "command": executable,
        "args": [str(fixture)],
        "cwd": str(cwd),
        "file_roots": roots,
        "env": {},
        "limits": {
            "request_timeout_seconds": 10,
            "max_message_bytes": 65536,
            "max_stderr_bytes": 4096,
            "max_process_memory_mb": 128,
        },
    }
    outcome = []
    try:
        manager.start_external_server_sync(
            "cancel-fixture",
            definition,
            {},
            ["connector:fixture:read", "connector:fixture:execute"],
        )

        def call_delayed_tool():
            try:
                manager.call_external_tool_sync(
                    "cancel-fixture",
                    "delay",
                    {},
                    timeout=12,
                    operation_id="execution-cancel-test",
                )
            except BaseException as exc:  # cancellation crosses a thread boundary
                outcome.append(type(exc).__name__)

        worker = threading.Thread(target=call_delayed_tool)
        worker.start()
        deadline = time.monotonic() + 3
        cancelled = False
        while time.monotonic() < deadline:
            cancelled = manager.cancel_external_operation("execution-cancel-test")
            if cancelled:
                break
            time.sleep(0.01)
        assert cancelled is True
        worker.join(timeout=3)

        assert worker.is_alive() is False
        assert outcome
    finally:
        manager.shutdown()

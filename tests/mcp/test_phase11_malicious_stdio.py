from __future__ import annotations

import asyncio
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import sys
import threading
import time

import pytest

from core.mcp.mcp_client import MCPClient
from core.mcp.mcp_manager import MCPManager
from core.mcp.mcp_protocol import MCPError
from core.mcp.process_containment import _descendant_process_ids


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mcp_stdio_fixture.py"


async def _connected_client(*, timeout: int = 2, max_message_bytes: int = 65_536) -> MCPClient:
    client = MCPClient(name="Phase11FixtureClient")
    await client.connect_via_stdio(
        [sys.executable, str(FIXTURE)],
        cwd=str(FIXTURE.parents[2]),
        limits={
            "request_timeout_seconds": timeout,
            "max_message_bytes": max_message_bytes,
            "max_stderr_bytes": 4096,
            "max_process_memory_mb": 128,
        },
    )
    return client


@pytest.mark.asyncio
async def test_real_stdio_fixture_discovery_call_and_shutdown():
    client = await _connected_client()
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
async def test_delayed_server_hits_request_timeout_and_can_be_stopped():
    client = await _connected_client(timeout=1)
    try:
        with pytest.raises(MCPError) as exc:
            await client.call_tool(name="delay", arguments={})
        assert exc.value.data["reason"] == "MCP_REQUEST_TIMEOUT"
    finally:
        await client.disconnect_async()


@pytest.mark.asyncio
async def test_malformed_json_rpc_fails_pending_request_and_disconnects():
    client = await _connected_client()
    with pytest.raises(Exception):
        await client.call_tool(name="malformed", arguments={})
    assert client.connected is False
    await client.disconnect_async()


@pytest.mark.asyncio
async def test_oversized_stdout_is_rejected_and_disconnects():
    client = await _connected_client(max_message_bytes=4096)
    with pytest.raises(Exception):
        await client.call_tool(name="oversized", arguments={})
    assert client.connected is False
    await client.disconnect_async()


def _windows_process_is_active(pid: int) -> bool:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
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
async def test_job_object_stop_terminates_spawned_child_process_tree():
    client = await _connected_client()
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
    kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
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


def test_manager_runtime_loop_keeps_stdio_readers_alive_across_requests():
    manager = MCPManager()
    definition = {
        "name": "runtime-fixture",
        "command": sys.executable,
        "args": [str(FIXTURE)],
        "cwd": str(FIXTURE.parents[2]),
        "env": {},
        "limits": {
            "request_timeout_seconds": 2,
            "max_message_bytes": 65536,
            "max_stderr_bytes": 4096,
            "max_process_memory_mb": 128,
        },
    }
    try:
        started = manager.start_external_server_sync("fixture", definition, {})
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


def test_manager_cancels_named_in_flight_operation():
    manager = MCPManager()
    definition = {
        "name": "runtime-cancel-fixture",
        "command": sys.executable,
        "args": [str(FIXTURE)],
        "cwd": str(FIXTURE.parents[2]),
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
        manager.start_external_server_sync("cancel-fixture", definition, {})

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

"""Real Windows checks for connector process isolation and lifecycle."""

import asyncio
import os
from pathlib import Path
import socket

import pytest

import core.mcp.isolated_process as isolated
from core.mcp.isolated_process import launch_isolated_connector
from core.mcp.process_containment import (
    ConnectorIsolationError,
    ConnectorPathGrant,
    _delete_appcontainer_profile,
)


async def _launch(tmp_path, command):
    root = tmp_path / "approved"
    root.mkdir()
    return await launch_isolated_connector(
        command,
        env={"SystemRoot": os.environ.get("SystemRoot", "")},
        cwd=None,
        grants=[ConnectorPathGrant(root, read=True)],
        journal_dir=tmp_path / "journal",
        max_process_memory_mb=256,
        limit=65536,
    )


def _cleanup_test_profile(guard):
    profile = guard.lease.lease["profile"]
    guard.close()
    # Only this test-created profile is removed; no customer profile is touched.
    _delete_appcontainer_profile(profile)


@pytest.mark.asyncio
async def test_isolated_process_can_use_stdio_and_terminate(tmp_path):
    if os.name != "nt":
        with pytest.raises(ConnectorIsolationError, match="Windows"):
            await _launch(tmp_path, ["fixture"])
        return
    executable = str(Path(os.environ["SystemRoot"]) / "System32" / "cmd.exe")
    process, guard = await _launch(
        tmp_path, [executable, "/d", "/c", "echo isolated-ok"]
    )
    try:
        assert (
            await asyncio.wait_for(process.stdout.read(), 10)
        ).strip() == b"isolated-ok"
        assert await asyncio.wait_for(process.wait(), 10) == 0
        assert guard.status == "windows_appcontainer_network_isolated"
    finally:
        _cleanup_test_profile(guard)


@pytest.mark.asyncio
async def test_isolated_process_cannot_connect_to_local_listener(tmp_path):
    if os.name != "nt":
        with pytest.raises(ConnectorIsolationError, match="Windows"):
            await _launch(tmp_path, ["fixture"])
        return
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    listener.setblocking(False)
    executable = str(Path(os.environ["SystemRoot"]) / "System32" / "curl.exe")
    url = f"http://127.0.0.1:{listener.getsockname()[1]}/"
    guard = None
    try:
        process, guard = await _launch(
            tmp_path, [executable, "--noproxy", "*", "--connect-timeout", "2", url]
        )
        assert await asyncio.wait_for(process.wait(), 10) != 0
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(
                asyncio.get_running_loop().sock_accept(listener), 0.5
            )
    finally:
        listener.close()
        if guard is not None:
            _cleanup_test_profile(guard)


@pytest.mark.asyncio
async def test_failure_to_attach_job_revokes_grants_before_returning(
    tmp_path, monkeypatch
):
    if os.name != "nt":
        with pytest.raises(ConnectorIsolationError, match="Windows"):
            await _launch(tmp_path, ["fixture"])
        return

    def fail_attach(*_args, **_kwargs):
        raise ConnectorIsolationError("simulated job failure")

    monkeypatch.setattr(isolated, "attach_process_tree_guard", fail_attach)
    executable = str(Path(os.environ["SystemRoot"]) / "System32" / "cmd.exe")
    with pytest.raises(ConnectorIsolationError, match="simulated job failure"):
        await _launch(tmp_path, [executable, "/d", "/c", "echo must-not-run"])
    assert not list((tmp_path / "journal").glob("*.json"))
    assert not (tmp_path / "journal" / "retained").exists()

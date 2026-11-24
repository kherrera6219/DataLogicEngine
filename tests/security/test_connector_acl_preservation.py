"""Connector grants must not change unrelated Windows access rules."""

import os
import subprocess

import pytest

import core.mcp.mcp_client as client_module
import core.mcp.process_containment as containment
from core.mcp.mcp_client import MCPClient
from core.mcp.mcp_manager import MCPManager
from core.mcp.mcp_protocol import MCPError
from core.mcp.process_containment import (
    ConnectorAccessLease,
    ConnectorIsolationError,
    ConnectorPermissionsIncompatible,
)
from tests.fixtures.connector_acl import (
    prepare_compatible_acl,
    prepare_incompatible_acl,
)


def _saved_acl(path, snapshot):
    subprocess.run(
        ["icacls", str(path), "/save", str(snapshot)],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = snapshot.read_text(encoding="utf-16-le").lstrip("\ufeff").splitlines()
    assert len(lines) == 2
    return lines[1]


def test_connector_cleanup_preserves_folder_and_existing_child_acl(tmp_path):
    if os.name != "nt":
        with pytest.raises(ConnectorIsolationError, match="Windows"):
            ConnectorAccessLease.create(tmp_path / "journal", [(tmp_path, False)])
        return

    root = tmp_path / "approved"
    root.mkdir()
    child = root / "existing.txt"
    child.write_text("test fixture", encoding="utf-8")
    prepare_compatible_acl(root)
    root_before = _saved_acl(root, tmp_path / "root-before.acl")
    child_before = _saved_acl(child, tmp_path / "child-before.acl")

    lease = ConnectorAccessLease.create(tmp_path / "journal", [(root, True)])
    lease.close()

    root_after = _saved_acl(root, tmp_path / "root-after.acl")
    child_after = _saved_acl(child, tmp_path / "child-after.acl")
    assert root_after == root_before, (
        f"folder ACL changed: {root_before} -> {root_after}"
    )
    assert child_after == child_before, (
        f"child ACL changed: {child_before} -> {child_after}"
    )


def test_connector_cleanup_preserves_unrelated_deny_rules(tmp_path):
    if os.name != "nt":
        with pytest.raises(ConnectorIsolationError, match="Windows"):
            ConnectorAccessLease.create(tmp_path / "journal", [(tmp_path, False)])
        return

    root = tmp_path / "approved"
    root.mkdir()
    child = root / "existing.txt"
    child.write_text("test fixture", encoding="utf-8")
    prepare_compatible_acl(root)
    subprocess.run(
        ["icacls", str(root), "/deny", "*S-1-5-32-546:(OI)(CI)W"],
        check=True,
        capture_output=True,
    )
    root_before = _saved_acl(root, tmp_path / "root-before.acl")
    child_before = _saved_acl(child, tmp_path / "child-before.acl")

    lease = ConnectorAccessLease.create(tmp_path / "journal", [(root, True)])
    lease.close()

    assert _saved_acl(root, tmp_path / "root-after.acl") == root_before
    assert _saved_acl(child, tmp_path / "child-after.acl") == child_before


@pytest.mark.parametrize("incompatible", ["root", "child"])
def test_incompatible_permissions_are_rejected_without_changes(tmp_path, incompatible):
    if os.name != "nt":
        with pytest.raises(ConnectorIsolationError, match="Windows"):
            ConnectorAccessLease.create(tmp_path / "journal", [(tmp_path, False)])
        return

    root = tmp_path / "approved"
    root.mkdir()
    child = root / "existing.txt"
    child.write_text("test fixture", encoding="utf-8")
    prepare_compatible_acl(root)
    prepare_incompatible_acl(root if incompatible == "root" else child)
    root_before = _saved_acl(root, tmp_path / "root-before.acl")
    child_before = _saved_acl(child, tmp_path / "child-before.acl")

    with pytest.raises(ConnectorPermissionsIncompatible, match="inheritance"):
        ConnectorAccessLease.create(tmp_path / "journal", [(root, True)])

    assert _saved_acl(root, tmp_path / "root-after.acl") == root_before
    assert _saved_acl(child, tmp_path / "child-after.acl") == child_before
    assert child.read_text(encoding="utf-8") == "test fixture"
    assert not list((tmp_path / "journal").glob("*.json"))


@pytest.mark.asyncio
async def test_client_reports_incompatible_permissions(tmp_path, monkeypatch):
    if os.name != "nt":
        assert issubclass(ConnectorPermissionsIncompatible, ConnectorIsolationError)
        return

    executable = tmp_path / "connector.exe"
    executable.write_bytes(b"fixture")
    root = tmp_path / "approved"
    root.mkdir()

    async def refuse(*_args, **_kwargs):
        raise ConnectorPermissionsIncompatible("incompatible permission inheritance")

    monkeypatch.setattr(client_module, "launch_isolated_connector", refuse)
    client = MCPClient(journal_dir=tmp_path / "journal")
    with pytest.raises(MCPError, match="permissions are incompatible") as error:
        await client.connect_via_stdio(
            [str(executable)],
            cwd=str(root),
            file_roots=[str(root)],
            approved_scopes=["connector:fixture:read"],
        )
    assert error.value.data["reason"] == "MCP_PROCESS_CONTAINMENT_FAILED"


def test_permission_change_before_grant_is_rejected(tmp_path, monkeypatch):
    if os.name != "nt":
        with pytest.raises(ConnectorIsolationError, match="Windows"):
            ConnectorAccessLease.create(tmp_path / "journal", [(tmp_path, False)])
        return

    root = tmp_path / "approved"
    root.mkdir()
    child = root / "existing.txt"
    child.write_text("test fixture", encoding="utf-8")
    prepare_compatible_acl(root)
    root_before = _saved_acl(root, tmp_path / "root-before.acl")
    change = containment._windows_acl_change
    child_after_change = []

    def change_child_before_grant(path, sid, *, write, revoke, **kwargs):
        if revoke is False:
            prepare_incompatible_acl(child)
            child_after_change.append(
                _saved_acl(child, tmp_path / "child-injected.acl")
            )
        return change(path, sid, write=write, revoke=revoke, **kwargs)

    monkeypatch.setattr(containment, "_windows_acl_change", change_child_before_grant)
    with pytest.raises(ConnectorPermissionsIncompatible, match="inheritance"):
        ConnectorAccessLease.create(tmp_path / "journal", [(root, True)])

    assert _saved_acl(root, tmp_path / "root-after.acl") == root_before
    assert _saved_acl(child, tmp_path / "child-after.acl") == child_after_change[0]
    assert not list((tmp_path / "journal").glob("*.json"))


def test_manager_reports_incompatible_permissions_without_starting(tmp_path):
    if os.name != "nt":
        assert issubclass(ConnectorPermissionsIncompatible, ConnectorIsolationError)
        return

    executable = tmp_path / "connector.exe"
    executable.write_bytes(b"fixture")
    root = tmp_path / "approved"
    root.mkdir()
    child = root / "existing.txt"
    child.write_text("test fixture", encoding="utf-8")
    prepare_compatible_acl(executable)
    prepare_compatible_acl(root)
    prepare_incompatible_acl(child)
    root_before = _saved_acl(root, tmp_path / "root-before.acl")
    child_before = _saved_acl(child, tmp_path / "child-before.acl")
    manager = MCPManager(journal_dir=tmp_path / "journal")
    definition = {
        "name": "fixture",
        "command": str(executable),
        "args": [],
        "cwd": str(root),
        "file_roots": [str(root)],
        "limits": {"request_timeout_seconds": 2},
    }
    try:
        with pytest.raises(MCPError, match="permissions are incompatible") as error:
            manager.start_external_server_sync(
                "fixture", definition, {}, ["connector:fixture:read"]
            )
        assert isinstance(error.value.__cause__, ConnectorPermissionsIncompatible)
        assert manager.external_clients == {}
        assert _saved_acl(root, tmp_path / "root-after.acl") == root_before
        assert _saved_acl(child, tmp_path / "child-after.acl") == child_before
        assert not list((tmp_path / "journal").glob("*.json"))
    finally:
        manager.shutdown()


def test_reparse_point_inside_approved_root_is_rejected(tmp_path):
    if os.name != "nt":
        with pytest.raises(ConnectorIsolationError, match="Windows"):
            ConnectorAccessLease.create(tmp_path / "journal", [(tmp_path, False)])
        return

    root = tmp_path / "approved"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel.txt"
    sentinel.write_text("test fixture", encoding="utf-8")
    prepare_compatible_acl(root)
    prepare_compatible_acl(outside)
    link = root / "junction"
    subprocess.run(
        ["cmd.exe", "/c", "mklink", "/J", str(link), str(outside)],
        check=True,
        capture_output=True,
    )
    try:
        root_before = _saved_acl(root, tmp_path / "root-before.acl")
        outside_before = _saved_acl(outside, tmp_path / "outside-before.acl")
        with pytest.raises(ConnectorIsolationError, match="reparse"):
            ConnectorAccessLease.create(tmp_path / "journal", [(root, True)])
        assert _saved_acl(root, tmp_path / "root-after.acl") == root_before
        assert _saved_acl(outside, tmp_path / "outside-after.acl") == outside_before
        assert sentinel.read_text(encoding="utf-8") == "test fixture"
    finally:
        link.rmdir()


def test_incompatible_cleanup_retains_journal_without_rewriting_acl(tmp_path):
    if os.name != "nt":
        with pytest.raises(ConnectorIsolationError, match="Windows"):
            ConnectorAccessLease.create(tmp_path / "journal", [(tmp_path, False)])
        return

    root = tmp_path / "approved"
    root.mkdir()
    child = root / "existing.txt"
    child.write_text("test fixture", encoding="utf-8")
    prepare_compatible_acl(root)
    lease = ConnectorAccessLease.create(tmp_path / "journal", [(root, True)])
    try:
        prepare_incompatible_acl(child)
        root_before = _saved_acl(root, tmp_path / "root-before.acl")
        child_before = _saved_acl(child, tmp_path / "child-before.acl")
        with pytest.raises(ConnectorPermissionsIncompatible, match="inheritance"):
            lease.close()
        assert lease.path.exists()
        assert _saved_acl(root, tmp_path / "root-after.acl") == root_before
        assert _saved_acl(child, tmp_path / "child-after.acl") == child_before
        assert child.read_text(encoding="utf-8") == "test fixture"
    finally:
        prepare_compatible_acl(root)
        lease.close()

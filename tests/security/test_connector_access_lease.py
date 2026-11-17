"""Connector-specific access grants must be narrow, recoverable and reversible."""

import json
import os
import subprocess
import uuid

import pytest

import core.mcp.process_containment as containment
from core.mcp.process_containment import (
    ConnectorAccessLease,
    ConnectorIsolationError,
    recover_connector_access,
)


def _acl(path):
    return subprocess.run(
        ["icacls", str(path)], check=True, capture_output=True, text=True
    ).stdout


def test_connector_grant_is_removed_without_changing_other_access(tmp_path):
    if os.name != "nt":
        with pytest.raises(ConnectorIsolationError, match="Windows"):
            ConnectorAccessLease.create(tmp_path / "journal", [(tmp_path, False)])
        return
    target = tmp_path / "approved.txt"
    target.write_text("fixture", encoding="utf-8")
    before = _acl(target)
    lease = ConnectorAccessLease.create(tmp_path / "journal", [(target, False)])
    sid = lease.lease["sid"]
    try:
        assert sid in _acl(target)
        assert lease.path.is_file()
        assert recover_connector_access(tmp_path / "journal") == 0
    finally:
        lease.close()
    assert sid not in _acl(target)
    assert _acl(target) == before
    assert not lease.path.exists()


def test_stale_connector_grant_is_recovered(tmp_path):
    if os.name != "nt":
        with pytest.raises(ConnectorIsolationError, match="Windows"):
            recover_connector_access(tmp_path / "journal")
        return
    target = tmp_path / "approved.txt"
    target.write_text("fixture", encoding="utf-8")
    journal = tmp_path / "journal"
    lease = ConnectorAccessLease.create(journal, [(target, True)])
    sid = lease.lease["sid"]
    try:
        record = json.loads(lease.path.read_text(encoding="utf-8"))
        record["owner_pid"] = 2147483647
        lease.path.write_text(json.dumps(record), encoding="utf-8")
        assert recover_connector_access(journal) == 1
        assert sid not in _acl(target)
        assert not lease.path.exists()
    finally:
        if lease.path.exists():
            lease.close()


def test_replaced_path_is_not_modified_during_cleanup(tmp_path):
    if os.name != "nt":
        with pytest.raises(ConnectorIsolationError, match="Windows"):
            ConnectorAccessLease.create(tmp_path / "journal", [(tmp_path, False)])
        return
    target = tmp_path / "approved.txt"
    target.write_text("original", encoding="utf-8")
    lease = ConnectorAccessLease.create(tmp_path / "journal", [(target, False)])
    original = tmp_path / "original.txt"
    target.rename(original)
    target.write_text("replacement", encoding="utf-8")
    replacement_acl = _acl(target)
    try:
        with pytest.raises(ConnectorIsolationError, match="identity changed"):
            lease.close()
        assert _acl(target) == replacement_acl
        assert lease.path.exists()
    finally:
        target.unlink()
        original.rename(target)
        lease.close()


def test_directory_grant_and_inheritance_are_removed(tmp_path):
    if os.name != "nt":
        with pytest.raises(ConnectorIsolationError, match="Windows"):
            ConnectorAccessLease.create(tmp_path / "journal", [(tmp_path, False)])
        return
    target = tmp_path / "approved"
    target.mkdir()
    existing = target / "existing.txt"
    existing.write_text("fixture", encoding="utf-8")
    before = _acl(target)
    lease = ConnectorAccessLease.create(tmp_path / "journal", [(target, True)])
    sid = lease.lease["sid"]
    try:
        new_file = target / "new.txt"
        new_file.write_text("fixture", encoding="utf-8")
        assert sid in _acl(target)
        assert sid in _acl(existing)
        assert sid in _acl(new_file)
    finally:
        lease.close()
    assert sid not in _acl(target)
    assert sid not in _acl(existing)
    assert sid not in _acl(new_file)
    assert _acl(target) == before


def test_partial_grant_failure_rolls_back_prior_entries(tmp_path, monkeypatch):
    if os.name != "nt":
        with pytest.raises(ConnectorIsolationError, match="Windows"):
            ConnectorAccessLease.create(tmp_path / "journal", [(tmp_path, False)])
        return
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("one", encoding="utf-8")
    second.write_text("two", encoding="utf-8")
    before = _acl(first)
    change = containment._windows_acl_change

    def fail_second(path, sid, *, write, revoke, expected_id=None):
        if path == second and revoke is False:
            raise ConnectorIsolationError("simulated grant failure")
        return change(path, sid, write=write, revoke=revoke, expected_id=expected_id)

    monkeypatch.setattr(containment, "_windows_acl_change", fail_second)
    with pytest.raises(ConnectorIsolationError, match="simulated grant failure"):
        ConnectorAccessLease.create(
            tmp_path / "journal", [(first, False), (second, False)]
        )
    assert _acl(first) == before
    assert not list((tmp_path / "journal").glob("*.json"))


def test_recovery_rejects_a_journal_with_an_unrelated_identity(tmp_path):
    if os.name != "nt":
        with pytest.raises(ConnectorIsolationError, match="Windows"):
            recover_connector_access(tmp_path / "journal")
        return
    target = tmp_path / "approved.txt"
    target.write_text("fixture", encoding="utf-8")
    journal = tmp_path / "journal"
    lease = ConnectorAccessLease.create(journal, [(target, False)])
    original = lease.path.read_text(encoding="utf-8")
    try:
        record = json.loads(original)
        record["profile"] = "DataLogicEngine.Connector." + uuid.uuid4().hex
        lease.path.write_text(json.dumps(record), encoding="utf-8")
        with pytest.raises(ConnectorIsolationError, match="identity mismatch"):
            recover_connector_access(journal)
        assert lease.lease["sid"] in _acl(target)
    finally:
        lease.path.write_text(original, encoding="utf-8")
        lease.close()


def test_started_connector_profile_is_retained_after_permissions_are_revoked(tmp_path):
    if os.name != "nt":
        with pytest.raises(ConnectorIsolationError, match="Windows"):
            ConnectorAccessLease.create(tmp_path / "journal", [(tmp_path, False)])
        return
    target = tmp_path / "approved.txt"
    target.write_text("fixture", encoding="utf-8")
    journal = tmp_path / "journal"
    lease = ConnectorAccessLease.create(journal, [(target, False)])
    sid = lease.lease["sid"]
    profile = lease.lease["profile"]
    profile_folder = containment._appcontainer_folder(sid)
    marker = profile_folder / "phase-b-test-owned-marker.txt"
    marker.write_text("preserve", encoding="utf-8")
    try:
        lease.preserve_profile()
        lease.close()
        assert sid not in _acl(target)
        assert not lease.path.exists()
        retained = journal / "retained" / f"{profile}.json"
        assert json.loads(retained.read_text(encoding="utf-8"))["profile"] == profile
        assert marker.read_text(encoding="utf-8") == "preserve"
    finally:
        if lease.path.exists():
            lease.close()
        marker.unlink(missing_ok=True)
        # This test profile was created solely for this test and holds no user data.
        containment._delete_appcontainer_profile(profile)

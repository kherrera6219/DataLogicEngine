"""Phase 1 loopback, Host, Origin, and gateway-owner boundary checks."""

from __future__ import annotations

from types import SimpleNamespace
import time

import pytest

from backend.security.listener_policy import resolve_loopback_listener_host


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1", "[::1]"])
def test_listener_policy_accepts_only_loopback_hosts(host):
    assert resolve_loopback_listener_host(host) in {"127.0.0.1", "localhost", "::1"}


@pytest.mark.parametrize(
    "host",
    ["0.0.0.0", "10.0.0.20", "192.168.1.20", "datalogicengine.internal", "8.8.8.8"],
)
def test_listener_policy_rejects_private_and_public_exposure(host):
    with pytest.raises(RuntimeError, match="Phase 8|loopback"):
        resolve_loopback_listener_host(host)


def test_desktop_listener_rejects_untrusted_host(monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module, "IS_DESKTOP_MODE", True)
    response = app_module.app.test_client().get("/health", headers={"Host": "attacker.example"})
    assert response.status_code == 400
    assert response.get_json()["code"] == "UNTRUSTED_DESKTOP_HOST"


def test_desktop_listener_accepts_loopback_host(monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module, "IS_DESKTOP_MODE", True)
    response = app_module.app.test_client().get(
        "/phase1-host-policy-probe",
        headers={"Host": "127.0.0.1:5000"},
    )
    assert response.status_code != 400


def test_desktop_listener_rejects_untrusted_origin(monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module, "IS_DESKTOP_MODE", True)
    response = app_module.app.test_client().get(
        "/health",
        headers={"Host": "127.0.0.1:5000", "Origin": "https://attacker.example"},
    )
    assert response.status_code == 403
    assert response.get_json()["code"] == "UNTRUSTED_DESKTOP_ORIGIN"


def test_gateway_key_cannot_mutate_owner_admin_surface(monkeypatch):
    import app as app_module
    from backend.auth import api_decorators

    monkeypatch.setattr(
        api_decorators.ExternalAPIKey,
        "verify_key",
        staticmethod(lambda _key: SimpleNamespace(user_id=1)),
    )
    response = app_module.app.test_client().post(
        "/api/v1/compliance/standards",
        headers={"X-API-Key": "ukg_external_client"},
        json={"name": "blocked"},
    )
    assert response.status_code == 401
    assert response.get_json()["code"] == "UNAUTHORIZED"


def test_desktop_file_operation_requires_main_process_capability(monkeypatch):
    import app as app_module
    from backend.security.desktop_ipc import require_desktop_ipc_capability

    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setenv("DESKTOP_INSTALL_SECRET", "phase1-ipc-secret")
    with app_module.app.test_request_context(
        "/api/v1/storage/backup",
        method="POST",
        headers={"X-Desktop-Auth-Timestamp": str(int(time.time()))},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
    ):
        response, status_code = require_desktop_ipc_capability("backup")
        assert status_code == 403
        assert response.get_json()["code"] == "DESKTOP_IPC_CAPABILITY_REQUIRED"


def test_desktop_file_operation_accepts_valid_main_process_capability(monkeypatch):
    import app as app_module
    from backend.security.desktop_ipc import require_desktop_ipc_capability
    from backend.security.desktop_local_auth import build_desktop_ipc_signature

    secret = "phase1-ipc-secret"
    timestamp = str(int(time.time()))
    signature = build_desktop_ipc_signature(
        "POST",
        "/api/v1/storage/backup",
        timestamp,
        "backup",
        secret,
    )
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setenv("DESKTOP_INSTALL_SECRET", secret)
    with app_module.app.test_request_context(
        "/api/v1/storage/backup",
        method="POST",
        headers={
            "X-Desktop-Auth-Timestamp": timestamp,
            "X-Desktop-IPC-Capability": "backup",
            "X-Desktop-IPC-Signature": signature,
        },
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
    ):
        assert require_desktop_ipc_capability("backup") is None

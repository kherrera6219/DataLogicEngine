"""Chroma health checks cannot redirect to an external service."""

from types import SimpleNamespace

import httpx
import pytest

from backend.runtime.podman_data_plane import (
    PodmanDataPlaneError,
    PodmanDataPlaneManager,
)
from backend.storage.connection_manager import ConnectionManager
from core.security.egress_guard import EgressDenied


def _connection_manager(host):
    manager = object.__new__(ConnectionManager)
    manager.config = SimpleNamespace(vector=SimpleNamespace(host=host, port=8000))
    return manager


def _podman_manager(host):
    manager = object.__new__(PodmanDataPlaneManager)
    manager.connection_settings = lambda: {"chroma_host": host, "chroma_port": 8000}
    return manager


def test_local_chroma_health_checks_accept_heartbeat(monkeypatch):
    def respond(_transport, _request):
        return httpx.Response(200, json={"nanosecond heartbeat": 42})

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", respond)
    assert _connection_manager("127.0.0.1").check_health("vector") is True
    assert _podman_manager("127.0.0.1")._probe_protocol("chroma") is None


def test_health_checks_reject_redirect_without_contacting_destination(monkeypatch):
    contacted = []

    def redirect(_transport, request):
        contacted.append(str(request.url))
        return httpx.Response(302, headers={"location": "https://outside.example/"})

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", redirect)
    assert _connection_manager("127.0.0.1").check_health("vector") is False
    with pytest.raises(PodmanDataPlaneError, match="chroma_heartbeat_failed"):
        _podman_manager("127.0.0.1")._probe_protocol("chroma")
    assert contacted == ["http://127.0.0.1:8000/api/v2/heartbeat"] * 2


def test_health_checks_propagate_nonlocal_egress_denial(monkeypatch):
    def fail_if_called(*_args):
        pytest.fail("nonlocal health check reached HTTP transport")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", fail_if_called)
    with pytest.raises(EgressDenied):
        _connection_manager("outside.example").check_health("vector")
    with pytest.raises(EgressDenied):
        _podman_manager("outside.example")._probe_protocol("chroma")


def test_podman_start_does_not_swallow_policy_denial():
    manager = object.__new__(PodmanDataPlaneManager)
    manager._last_failure = {}
    manager._require_spec = lambda _service: SimpleNamespace()

    def denied():
        raise EgressDenied()

    manager.ensure_preflight = denied
    with pytest.raises(EgressDenied):
        manager.start_service("chroma")

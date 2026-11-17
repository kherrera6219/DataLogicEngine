"""Diagnostic probes must not escape their loopback destination."""

import httpx
import pytest

from backend.observability.support_bundle import probe_http_endpoint
from core.security.egress_guard import EgressDenied, local_http_get


def test_probe_does_not_follow_redirect_or_environment_proxy(monkeypatch):
    contacted = []

    def redirect(_transport, request):
        contacted.append(str(request.url))
        return httpx.Response(302, headers={"location": "https://outside.example/"})

    monkeypatch.setenv("HTTP_PROXY", "http://outside.example:8080")
    monkeypatch.setenv("NO_PROXY", "")
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", redirect)
    result = probe_http_endpoint("http://127.0.0.1:5000/health")
    assert result["ok"] is False
    assert result["status_code"] == 302
    assert contacted == ["http://127.0.0.1:5000/health"]


def test_probe_returns_local_response(monkeypatch):
    def respond(_transport, request):
        assert request.url.host == "127.0.0.1"
        return httpx.Response(
            200, text="healthy", headers={"content-type": "text/plain"}
        )

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", respond)
    result = probe_http_endpoint("http://127.0.0.1:5000/health")
    assert result["ok"] is True
    assert result["status_code"] == 200
    assert result["body_preview"] == "healthy"


@pytest.mark.parametrize(
    "url",
    [
        "https://localhost/health",
        "http://outside.example/health",
        "http://user@localhost/health",
    ],
)
def test_local_transport_rejects_unapproved_urls_before_http(monkeypatch, url):
    def fail_if_called(*_args):
        pytest.fail("unapproved request reached HTTP transport")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", fail_if_called)
    with pytest.raises(EgressDenied):
        local_http_get(url, timeout=2)

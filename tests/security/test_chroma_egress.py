"""The Chroma client may contact only its configured local service."""

import httpx
import pytest

from backend.storage.chroma_http import ChromaHttpClient
from core.security.egress_guard import EgressDenied, loopback_http_client


@pytest.mark.parametrize("host", ["127.0.0.1", "::1"])
def test_chroma_transport_allows_only_its_configured_origin(monkeypatch, host):
    contacted = []

    def respond(_transport, request):
        contacted.append(request.url)
        return httpx.Response(200, json={"nanosecond heartbeat": 42})

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", respond)
    with ChromaHttpClient(host=host, port=18000) as client:
        assert client.heartbeat() == 42
        with pytest.raises(EgressDenied):
            client._session.get("http://127.0.0.1:18001/api/v2/heartbeat")
        with pytest.raises(EgressDenied):
            client._session.get("https://outside.example/api/v2/heartbeat")

    assert len(contacted) == 1
    assert contacted[0].host == host


@pytest.mark.parametrize(
    "endpoint",
    ["http://outside.example:8000", "http://192.0.2.1:8000", "https://127.0.0.1:8000"],
)
def test_local_client_factory_rejects_nonloopback_or_non_http(endpoint):
    with pytest.raises(EgressDenied):
        loopback_http_client(
            endpoint,
            timeout=5,
            max_connections=16,
            max_keepalive_connections=8,
            headers={},
        )

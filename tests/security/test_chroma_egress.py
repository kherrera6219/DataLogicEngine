"""The Chroma client may contact only its configured local service."""

import httpx
import pytest

from backend.storage.chroma_http import ChromaHttpClient
from core.security.egress_guard import EgressDenied


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

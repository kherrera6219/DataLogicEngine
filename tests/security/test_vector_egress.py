"""The legacy external vector adapter fails closed before network activity."""

import socket

import pytest

from backend.storage.vector_store import PineconeBackend
from core.security.egress_guard import EgressDenied


@pytest.mark.parametrize(
    "operation",
    [
        lambda backend: backend.index,
        lambda backend: backend.add_embeddings("docs", ["id"], ["text"], [[0.1]]),
        lambda backend: backend.search("docs", [0.1]),
        lambda backend: backend.delete("docs", ["id"]),
        lambda backend: backend.get_collection_stats("docs"),
        lambda backend: backend.list_collection_stats(),
        lambda backend: backend.delete_collection("docs"),
    ],
)
def test_legacy_external_vector_adapter_denies_network(monkeypatch, operation):
    def fail_if_resolved(*_args, **_kwargs):
        pytest.fail("external vector adapter reached DNS")

    monkeypatch.setattr(socket, "getaddrinfo", fail_if_resolved)
    backend = PineconeBackend(api_key="test", environment="test")
    with pytest.raises(EgressDenied, match="External vector storage"):
        operation(backend)

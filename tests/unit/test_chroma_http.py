"""Contract and adversarial tests for the restricted Chroma HTTP client."""

from __future__ import annotations

import json

import httpx
import pytest

from backend.storage.chroma_http import ChromaHttpClient, ChromaHttpError


def _client(handler):
    client = ChromaHttpClient(host="127.0.0.1", port=18000)
    client._session.close()
    client._session = httpx.Client(
        transport=httpx.MockTransport(handler),
        follow_redirects=False,
        trust_env=False,
    )
    return client


def _model(**overrides):
    value = {
        "id": "11111111-1111-4111-8111-111111111111",
        "name": "knowledge_nodes",
        "metadata": {"schema_version": "1"},
        "configuration_json": {},
        "serialized_schema": None,
    }
    value.update(overrides)
    return value


def test_client_is_loopback_only_and_rejects_redirects():
    with pytest.raises(ChromaHttpError, match="chroma_host_must_be_loopback_literal"):
        ChromaHttpClient(host="example.com", port=8000)
    with pytest.raises(ChromaHttpError, match="chroma_host_must_be_loopback_literal"):
        ChromaHttpClient(host="192.168.1.10", port=8000)

    client = _client(lambda _request: httpx.Response(302, headers={"location": "http://evil.invalid"}))
    with pytest.raises(ChromaHttpError, match="chroma_redirect_rejected"):
        client.heartbeat()
    client.close()


def test_vector_only_contract_never_sends_embedding_configuration():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        path = request.url.path
        if path.endswith("/collections"):
            body = json.loads(request.content)
            assert body["configuration"] is None
            assert body["schema"] is None
            assert "embedding_function" not in body
            return httpx.Response(200, json=_model())
        if path.endswith("/upsert"):
            body = json.loads(request.content)
            assert body["embeddings"] == [[0.1, 0.2]]
            assert "embedding_function" not in json.dumps(body)
            return httpx.Response(200, json=None)
        if path.endswith("/query"):
            return httpx.Response(
                200,
                json={
                    "ids": [["doc-1"]],
                    "documents": [["safe"]],
                    "metadatas": [[{"source": "unit"}]],
                    "distances": [[0.2]],
                },
            )
        raise AssertionError(path)

    client = _client(handler)
    collection = client.get_or_create_collection(
        "knowledge_nodes",
        embedding_function=None,
        configuration={},
    )
    collection.upsert(
        ids=["doc-1"],
        embeddings=[[0.1, 0.2]],
        documents=["safe"],
        metadatas=[{"source": "unit"}],
    )
    result = collection.query(query_embeddings=[[0.1, 0.2]], n_results=1)
    assert result["ids"] == [["doc-1"]]
    assert len(requests) == 3
    client.close()


@pytest.mark.parametrize(
    "hostile_model",
    [
        _model(
            configuration_json={
                "embedding_function": {
                    "name": "sentence_transformer",
                    "config": {"kwargs": {"trust_remote_code": True}},
                }
            }
        ),
        _model(
            serialized_schema={
                "defaults": {
                    "float_list": {
                        "vector_index": {
                            "config": {"trustRemoteCode": True}
                        }
                    }
                }
            }
        ),
    ],
)
def test_hostile_server_models_fail_closed_without_deserialization(hostile_model):
    client = _client(lambda _request: httpx.Response(200, json=hostile_model))
    with pytest.raises(ChromaHttpError, match="chroma_server_embedding_configuration_rejected"):
        client.get_collection("knowledge_nodes", embedding_function=None)
    client.close()


def test_caller_supplied_vectors_and_bounded_inputs_are_required():
    client = _client(lambda _request: httpx.Response(200, json=_model()))
    collection = client.get_collection("knowledge_nodes")

    with pytest.raises(ChromaHttpError, match="chroma_embeddings_required"):
        collection.upsert(ids=["doc-1"], embeddings=[])
    with pytest.raises(ChromaHttpError, match="chroma_embedding_invalid"):
        collection.upsert(ids=["doc-1"], embeddings=[[float("nan")]])
    with pytest.raises(ChromaHttpError, match="chroma_delete_selector_required"):
        collection.delete()
    with pytest.raises(ChromaHttpError, match="chroma_collection_name_invalid"):
        client.get_collection("../escape")
    client.close()

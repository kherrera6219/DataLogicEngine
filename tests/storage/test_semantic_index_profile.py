"""Semantic stores must bind namespace, metric, model and write provenance."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from backend.storage.semantic_index_profile import (
    SemanticIndexProfile, SemanticProfileError, ProfiledChromaBackend,
    provision_profile_collections,
)


def _profile():
    return SemanticIndexProfile(weights_sha256="0"*64, manifest_sha256="1"*64)


class Collection:
    def __init__(self, name, metadata, metric="cosine"):
        self.name=name
        self.id=name
        self.metadata=metadata
        self._model=SimpleNamespace(configuration_json={"hnsw":{"space":metric}}, serialized_schema=None)
        self.mutations=[]

    def delete(self, **kwargs):
        self.mutations.append(kwargs)

    def get(self, **kwargs):
        return {"ids":[]}


class Client:
    def __init__(self):
        self.collections={"documents":Collection("documents",{})}

    def list_collections(self, limit=None, offset=0):
        return list(self.collections.values())[offset:offset+limit]

    def create_collection(self, name, metadata, configuration, embedding_function=None):
        assert configuration == {"hnsw":{"space":"cosine"}}
        assert embedding_function is None
        assert name not in self.collections
        self.collections[name]=Collection(name,metadata)
        return self.collections[name]

    def get_collection(self, name, embedding_function=None):
        assert embedding_function is None
        return self.collections[name]


def test_profiles_are_versioned_and_provisioning_preserves_legacy_collections():
    profile=_profile()
    client=Client()
    provision_profile_collections(client,profile)
    assert "documents" in client.collections
    assert profile.collection_name("documents") != "documents"
    assert replace(profile,weights_sha256="2"*64).collection_name("documents") != profile.collection_name("documents")
    assert len(client.collections) == 7
    provision_profile_collections(client,profile)
    assert len(client.collections) == 7


@pytest.mark.parametrize("tamper",["model","metric"])
def test_wrong_model_or_metric_is_rejected_before_any_deletion(tamper):
    profile=_profile(); client=Client()
    provision_profile_collections(client,profile)
    collection=client.collections[profile.collection_name("knowledge_nodes")]
    if tamper == "model":
        collection.metadata["dle_embedding_manifest"]="f"*64
    else:
        collection._model.configuration_json["hnsw"]["space"]="l2"
    backend=ProfiledChromaBackend(client,profile)
    with pytest.raises(SemanticProfileError):
        backend.delete_parent_embeddings("knowledge_nodes","parent")
    assert collection.mutations == []


def test_unknown_collection_and_unproven_vector_writes_fail_closed():
    profile=_profile(); client=Client()
    provision_profile_collections(client,profile)
    backend=ProfiledChromaBackend(client,profile)
    with pytest.raises(SemanticProfileError):
        backend._get_collection("arbitrary_collection")
    with pytest.raises(SemanticProfileError):
        backend.replace_embeddings("knowledge_nodes","parent",ids=["parent"],texts=["source"],
            embeddings=[[1.0]+[0.0]*383],metadata=[{"vector_parent_id":"parent"}])
    assert all(collection.mutations == [] for collection in client.collections.values())


def test_wrong_vector_dimensions_and_unapproved_collection_deletion_are_rejected():
    profile=_profile(); client=Client()
    provision_profile_collections(client,profile)
    backend=ProfiledChromaBackend(client,profile)
    with pytest.raises(SemanticProfileError):
        backend.search("documents",[1.0,0.0])
    with pytest.raises(SemanticProfileError):
        backend.delete_collection("documents")
    assert "documents" in client.collections

"""Regression coverage for GHSA-f4j7-r4q5-qw2c / CVE-2026-45829."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import pytest

from backend.storage.chroma_security import (
    ChromaCollectionSecurityError,
    safe_create_collection,
    safe_get_collection,
    safe_get_or_create_collection,
    validate_collection_configuration,
)


@dataclass
class _Model:
    configuration_json: dict
    serialized_schema: dict | None = None


class _Collection:
    def __init__(self, configuration=None, schema=None):
        self._model = _Model(configuration or {}, schema)


class _Client:
    def __init__(self, collection=None):
        self.collection = collection or _Collection()
        self.calls = []

    def get_collection(self, **kwargs):
        self.calls.append(("get", kwargs))
        return self.collection

    def get_or_create_collection(self, **kwargs):
        self.calls.append(("get_or_create", kwargs))
        return self.collection

    def create_collection(self, **kwargs):
        self.calls.append(("create", kwargs))
        return self.collection


def test_every_collection_entry_point_disables_server_embedding_functions():
    client = _Client()

    safe_get_collection(client, name="documents")
    safe_get_or_create_collection(client, name="documents", metadata={"v": "1"})
    safe_create_collection(client, name="restored", metadata={"v": "1"})

    for _operation, arguments in client.calls:
        assert arguments["embedding_function"] is None
    assert client.calls[1][1]["configuration"] == {}
    assert client.calls[2][1]["configuration"] == {}


@pytest.mark.parametrize(
    "configuration,schema",
    [
        (
            {
                "embedding_function": {
                    "name": "sentence_transformer",
                    "config": {
                        "model_name": "attacker/model",
                        "kwargs": {"trust_remote_code": True},
                    },
                }
            },
            None,
        ),
        (
            {},
            {
                "defaults": {
                    "float_list": {
                        "vector_index": {
                            "config": {
                                "embedding_function": {
                                    "name": "sentence_transformer"
                                }
                            }
                        }
                    }
                }
            },
        ),
    ],
)
def test_hostile_persisted_embedding_configuration_is_rejected(configuration, schema):
    collection = _Collection(configuration, schema)

    with pytest.raises(
        ChromaCollectionSecurityError,
        match="chroma_server_embedding_configuration_rejected",
    ):
        validate_collection_configuration(collection)


def test_locked_chroma_service_is_rust_and_remains_production_disabled():
    root = Path(__file__).resolve().parents[2]
    lock = json.loads(
        (root / "deploy" / "internal-data-plane.candidate-lock.json").read_text(
            encoding="utf-8"
        )
    )
    chroma = lock["services"]["chromadb"]

    assert chroma["server_implementation"] == "rust_single_node_binary"
    assert chroma["python_server_advisory_applicable"] is False
    assert chroma["production_approved"] is False
    assert lock["production_provisioning_authorized"] is False


def test_storage_and_qualification_code_cannot_bypass_safe_collection_helpers():
    root = Path(__file__).resolve().parents[2]
    files = [
        root / "backend" / "storage" / "vector_store.py",
        root / "backend" / "storage" / "store_migration_adapters.py",
        root / "backend" / "storage" / "managed_backup.py",
        root / "backend" / "storage" / "user_deletion.py",
        root / "scripts" / "qualify_phase4_data_lifecycle.py",
        root / "scripts" / "verify_internal_data_plane.py",
    ]
    forbidden = (
        "self.client.get_collection(",
        "self.client.get_or_create_collection(",
        "self.client.create_collection(",
        "chroma_client.get_collection(",
        "chroma_client.get_or_create_collection(",
        "chroma_client.create_collection(",
        "client.get_collection(",
        "client.get_or_create_collection(",
        "client.create_collection(",
    )
    for path in files:
        source = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source, f"unsafe Chroma collection access in {path}: {token}"

"""Fail-closed Chroma collection access for the unpatched 1.5.9 advisory."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class ChromaCollectionSecurityError(RuntimeError):
    """A collection attempted to supply executable embedding configuration."""


def _reject_embedding_configuration(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if key == "embedding_function" and nested not in (None, {}):
                raise ChromaCollectionSecurityError(
                    "chroma_server_embedding_configuration_rejected"
                )
            _reject_embedding_configuration(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _reject_embedding_configuration(nested)


def validate_collection_configuration(collection: Any) -> Any:
    """Inspect raw transport fields without deserializing embedding functions."""

    model = getattr(collection, "_model", None)
    if model is None:
        if collection.__class__.__module__.startswith("chromadb."):
            raise ChromaCollectionSecurityError("chroma_collection_model_missing")
        return collection
    _reject_embedding_configuration(getattr(model, "configuration_json", None))
    _reject_embedding_configuration(getattr(model, "serialized_schema", None))
    return collection


def safe_get_collection(client: Any, *, name: str) -> Any:
    """Open a collection without accepting its persisted embedding function."""

    collection = client.get_collection(name=name, embedding_function=None)
    return validate_collection_configuration(collection)


def safe_get_or_create_collection(
    client: Any,
    *,
    name: str,
    metadata: Mapping[str, Any] | None = None,
) -> Any:
    """Open/create a collection that only accepts caller-supplied vectors."""

    arguments: dict[str, Any] = {
        "name": name,
        "configuration": {},
        "embedding_function": None,
    }
    if metadata:
        arguments["metadata"] = dict(metadata)
    collection = client.get_or_create_collection(**arguments)
    return validate_collection_configuration(collection)


def safe_create_collection(
    client: Any,
    *,
    name: str,
    metadata: Mapping[str, Any] | None = None,
) -> Any:
    """Create a collection with no server-persisted embedding implementation."""

    arguments: dict[str, Any] = {
        "name": name,
        "configuration": {},
        "embedding_function": None,
    }
    if metadata:
        arguments["metadata"] = dict(metadata)
    collection = client.create_collection(**arguments)
    return validate_collection_configuration(collection)

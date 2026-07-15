"""Fail-closed helpers for the restricted Chroma Rust HTTP contract."""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any


class ChromaCollectionSecurityError(RuntimeError):
    """A collection attempted to supply executable embedding configuration."""


def _reject_embedding_configuration(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = re.sub(r"[^a-z0-9_]", "", str(key).lower())
            if normalized in {"embedding_function", "embeddingfunction"}:
                if nested not in (None, {}) and nested != {"type": "unknown"}:
                    raise ChromaCollectionSecurityError(
                        "chroma_server_embedding_configuration_rejected"
                    )
                continue
            if normalized in {"trust_remote_code", "trustremotecode"}:
                if nested not in (None, {}, False):
                    raise ChromaCollectionSecurityError(
                        "chroma_server_embedding_configuration_rejected"
                    )
                continue
            _reject_embedding_configuration(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _reject_embedding_configuration(nested)
    elif isinstance(value, str):
        normalized = re.sub(r"[^a-z0-9_]", "", value.lower())
        if "trust_remote_code" in normalized or "trustremotecode" in normalized:
            raise ChromaCollectionSecurityError(
                "chroma_server_embedding_configuration_rejected"
            )


def validate_collection_configuration(collection: Any) -> Any:
    """Inspect raw transport fields without deserializing embedding functions."""

    model = getattr(collection, "_model", None)
    if model is None:
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

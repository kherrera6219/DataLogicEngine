"""Restricted HTTP client for the app-owned Chroma Rust service.

The production application intentionally does not depend on Chroma's Python SDK.
That SDK can deserialize server-controlled embedding-function configuration and is
affected by GHSA-f4j7-r4q5-qw2c.  This module exposes only the vector operations
DataLogicEngine owns, always requires caller-supplied embeddings, and treats all
collection configuration returned by the service as untrusted data.
"""

from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import json
import math
import re
from typing import Any
from urllib.parse import quote

import httpx


DEFAULT_TENANT = "default_tenant"
DEFAULT_DATABASE = "default_database"
_COLLECTION_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$")
_MAX_BATCH_SIZE = 5_000
_MAX_JSON_BYTES = 64 * 1024 * 1024
_ALLOWED_INCLUDES = frozenset({"documents", "embeddings", "metadatas", "uris", "distances"})
_FORBIDDEN_CONFIGURATION_KEYS = frozenset(
    {
        "embedding_function",
        "embeddingfunction",
        "trust_remote_code",
        "trustremotecode",
    }
)


class ChromaHttpError(RuntimeError):
    """Safely reportable Chroma transport or contract failure."""


def _normalise_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9_]", "", str(value).strip().lower())


def _contains_forbidden_configuration(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized_key = _normalise_key(key)
            if normalized_key in {"embedding_function", "embeddingfunction"}:
                if nested not in (None, {}) and nested != {"type": "unknown"}:
                    return True
                continue
            if normalized_key in {"trust_remote_code", "trustremotecode"}:
                if nested not in (None, {}, False):
                    return True
                continue
            if _contains_forbidden_configuration(nested):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_forbidden_configuration(item) for item in value)
    elif isinstance(value, str):
        normalised = _normalise_key(value)
        return "trust_remote_code" in normalised or "trustremotecode" in normalised
    return False


def validate_untrusted_collection_model(model: dict[str, Any]) -> None:
    """Reject any server model capable of describing executable embeddings."""
    if not isinstance(model, dict):
        raise ChromaHttpError("chroma_collection_model_invalid")
    for key in ("configuration", "configuration_json", "schema", "serialized_schema"):
        value = model.get(key)
        if value is not None and _contains_forbidden_configuration(value):
            raise ChromaHttpError("chroma_server_embedding_configuration_rejected")


def _collection_name(value: str) -> str:
    name = str(value or "")
    if not _COLLECTION_NAME.fullmatch(name):
        raise ChromaHttpError("chroma_collection_name_invalid")
    return name


def _segment(value: str) -> str:
    return quote(str(value), safe="")


def _metadata(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ChromaHttpError("chroma_metadata_invalid")
    try:
        encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ChromaHttpError("chroma_metadata_invalid") from exc
    if len(encoded) > 64 * 1024:
        raise ChromaHttpError("chroma_metadata_too_large")
    return value


def _where(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ChromaHttpError("chroma_filter_invalid")
    try:
        encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ChromaHttpError("chroma_filter_invalid") from exc
    if len(encoded) > 64 * 1024:
        raise ChromaHttpError("chroma_filter_too_large")
    return value


def _ids(values: Any, *, required: bool) -> list[str] | None:
    if values is None and not required:
        return None
    if not isinstance(values, (list, tuple)) or not values or len(values) > _MAX_BATCH_SIZE:
        raise ChromaHttpError("chroma_ids_invalid")
    result = [str(value) for value in values]
    if any(not value or len(value) > 512 for value in result) or len(set(result)) != len(result):
        raise ChromaHttpError("chroma_ids_invalid")
    return result


def _embeddings(values: Any, *, expected: int | None = None) -> list[list[float]]:
    if not isinstance(values, (list, tuple)) or not values or len(values) > _MAX_BATCH_SIZE:
        raise ChromaHttpError("chroma_embeddings_required")
    result: list[list[float]] = []
    dimension: int | None = None
    for vector in values:
        if not isinstance(vector, (list, tuple)) or not vector:
            raise ChromaHttpError("chroma_embedding_invalid")
        converted = [float(component) for component in vector]
        if any(not math.isfinite(component) for component in converted):
            raise ChromaHttpError("chroma_embedding_invalid")
        dimension = dimension or len(converted)
        if len(converted) != dimension:
            raise ChromaHttpError("chroma_embedding_dimension_mismatch")
        result.append(converted)
    if expected is not None and len(result) != expected:
        raise ChromaHttpError("chroma_batch_length_mismatch")
    return result


def _optional_columns(values: Any, *, expected: int, metadata: bool = False) -> list[Any] | None:
    if values is None:
        return None
    if not isinstance(values, (list, tuple)) or len(values) != expected:
        raise ChromaHttpError("chroma_batch_length_mismatch")
    result = list(values)
    if metadata:
        result = [_metadata(value) for value in result]
    return result


@dataclass(frozen=True)
class ChromaCollectionModel:
    id: str
    name: str
    metadata: dict[str, Any]
    configuration_json: dict[str, Any]
    serialized_schema: dict[str, Any] | None


class ChromaCollection:
    """A collection facade that never computes or loads embeddings."""

    def __init__(self, client: "ChromaHttpClient", raw_model: dict[str, Any]) -> None:
        validate_untrusted_collection_model(raw_model)
        collection_id = str(raw_model.get("id") or "")
        if not collection_id:
            raise ChromaHttpError("chroma_collection_id_missing")
        name = _collection_name(str(raw_model.get("name") or ""))
        metadata = _metadata(raw_model.get("metadata")) or {}
        configuration = raw_model.get("configuration_json", raw_model.get("configuration"))
        configuration = configuration if isinstance(configuration, dict) else {}
        schema = raw_model.get("serialized_schema", raw_model.get("schema"))
        schema = schema if isinstance(schema, dict) else None
        self._client = client
        self._model = ChromaCollectionModel(
            id=collection_id,
            name=name,
            metadata=metadata,
            configuration_json=configuration,
            serialized_schema=schema,
        )

    @property
    def id(self) -> str:
        return self._model.id

    @property
    def name(self) -> str:
        return self._model.name

    @property
    def metadata(self) -> dict[str, Any]:
        return dict(self._model.metadata)

    def get_model(self) -> ChromaCollectionModel:
        return self._model

    def _path(self, suffix: str) -> str:
        return self._client._collection_path(self.id, suffix)

    def count(self) -> int:
        value = self._client._request("GET", self._path("count"))
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ChromaHttpError("chroma_count_response_invalid")
        return value

    def get(
        self,
        *,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        where_document: dict[str, Any] | None = None,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        checked_ids = _ids(ids, required=False)
        checked_include = self._client._includes(include or ["documents", "metadatas"])
        if limit is not None and (not isinstance(limit, int) or limit < 1 or limit > _MAX_BATCH_SIZE):
            raise ChromaHttpError("chroma_limit_invalid")
        if offset is not None and (not isinstance(offset, int) or offset < 0):
            raise ChromaHttpError("chroma_offset_invalid")
        value = self._client._request(
            "POST",
            self._path("get"),
            {
                "ids": checked_ids,
                "where": _where(where),
                "limit": limit,
                "offset": offset,
                "where_document": _where(where_document),
                "include": checked_include,
            },
        )
        if not isinstance(value, dict) or not isinstance(value.get("ids"), list):
            raise ChromaHttpError("chroma_get_response_invalid")
        return value

    def _write(
        self,
        operation: str,
        *,
        ids: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]] | None = None,
        documents: list[str] | None = None,
        uris: list[str] | None = None,
    ) -> None:
        checked_ids = _ids(ids, required=True) or []
        checked_embeddings = _embeddings(embeddings, expected=len(checked_ids))
        body = {
            "ids": checked_ids,
            "embeddings": checked_embeddings,
            "metadatas": _optional_columns(metadatas, expected=len(checked_ids), metadata=True),
            "documents": _optional_columns(documents, expected=len(checked_ids)),
            "uris": _optional_columns(uris, expected=len(checked_ids)),
        }
        self._client._request("POST", self._path(operation), body)

    def add(self, **kwargs: Any) -> None:
        self._write("add", **kwargs)

    def upsert(self, **kwargs: Any) -> None:
        self._write("upsert", **kwargs)

    def query(
        self,
        *,
        query_embeddings: list[list[float]],
        n_results: int = 10,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(n_results, int) or n_results < 1 or n_results > _MAX_BATCH_SIZE:
            raise ChromaHttpError("chroma_query_limit_invalid")
        value = self._client._request(
            "POST",
            self._path("query"),
            {
                "ids": _ids(ids, required=False),
                "query_embeddings": _embeddings(query_embeddings),
                "n_results": n_results,
                "where": _where(where),
                "where_document": _where(where_document),
                "include": self._client._includes(
                    include or ["documents", "metadatas", "distances"]
                ),
            },
        )
        if not isinstance(value, dict) or not isinstance(value.get("ids"), list):
            raise ChromaHttpError("chroma_query_response_invalid")
        return value

    def delete(
        self,
        *,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> None:
        if ids is None and where is None and where_document is None:
            raise ChromaHttpError("chroma_delete_selector_required")
        self._client._request(
            "POST",
            self._path("delete"),
            {
                "ids": _ids(ids, required=False),
                "where": _where(where),
                "where_document": _where(where_document),
            },
        )

    def modify(self, *, name: str | None = None, metadata: dict[str, Any] | None = None) -> None:
        if name is None and metadata is None:
            raise ChromaHttpError("chroma_modify_value_required")
        self._client._request(
            "PUT",
            self._client._collection_path(self.id),
            {
                "new_name": _collection_name(name) if name is not None else None,
                "new_metadata": _metadata(metadata),
                "new_configuration": None,
            },
        )


class ChromaHttpClient:
    """Loopback-only client for the Chroma v2 HTTP vector contract."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        tenant: str = DEFAULT_TENANT,
        database: str = DEFAULT_DATABASE,
        timeout_seconds: float = 10.0,
    ) -> None:
        try:
            address = ipaddress.ip_address(str(host))
        except ValueError as exc:
            raise ChromaHttpError("chroma_host_must_be_loopback_literal") from exc
        if not address.is_loopback:
            raise ChromaHttpError("chroma_host_must_be_loopback_literal")
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            raise ChromaHttpError("chroma_port_invalid")
        self.tenant = _collection_name(tenant)
        self.database = _collection_name(database)
        rendered_host = f"[{address}]" if address.version == 6 else str(address)
        self._base_url = f"http://{rendered_host}:{port}/api/v2"
        self._session = httpx.Client(
            timeout=httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 3.0)),
            limits=httpx.Limits(max_connections=16, max_keepalive_connections=8),
            follow_redirects=False,
            trust_env=False,
            headers={"Content-Type": "application/json", "User-Agent": "DataLogicEngine-Chroma-Vector-Client/1"},
        )

    def __enter__(self) -> "ChromaHttpClient":
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()

    def close(self) -> None:
        self._session.close()

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        if not path.startswith("/") or "://" in path or ".." in path:
            raise ChromaHttpError("chroma_request_path_invalid")
        content: bytes | None = None
        if body is not None:
            try:
                content = json.dumps(body, allow_nan=False, separators=(",", ":")).encode("utf-8")
            except (TypeError, ValueError) as exc:
                raise ChromaHttpError("chroma_request_body_invalid") from exc
            if len(content) > _MAX_JSON_BYTES:
                raise ChromaHttpError("chroma_request_body_too_large")
        try:
            response = self._session.request(method, self._base_url + path, content=content)
        except httpx.HTTPError as exc:
            raise ChromaHttpError("chroma_transport_failure") from exc
        if response.is_redirect:
            raise ChromaHttpError("chroma_redirect_rejected")
        if response.status_code < 200 or response.status_code >= 300:
            raise ChromaHttpError(f"chroma_http_status_{response.status_code}")
        if len(response.content) > _MAX_JSON_BYTES:
            raise ChromaHttpError("chroma_response_too_large")
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise ChromaHttpError("chroma_response_json_invalid") from exc

    def _collections_path(self, name: str | None = None) -> str:
        path = f"/tenants/{_segment(self.tenant)}/databases/{_segment(self.database)}/collections"
        return f"{path}/{_segment(_collection_name(name))}" if name is not None else path

    def _collection_path(self, collection_id: str, suffix: str | None = None) -> str:
        path = f"{self._collections_path()}/{_segment(collection_id)}"
        return f"{path}/{_segment(suffix)}" if suffix else path

    @staticmethod
    def _includes(values: list[str]) -> list[str]:
        if not isinstance(values, list) or not values:
            raise ChromaHttpError("chroma_include_invalid")
        result = [str(value) for value in values]
        if any(value not in _ALLOWED_INCLUDES for value in result):
            raise ChromaHttpError("chroma_include_invalid")
        return result

    def heartbeat(self) -> int:
        value = self._request("GET", "/heartbeat")
        if not isinstance(value, dict) or not isinstance(value.get("nanosecond heartbeat"), int):
            raise ChromaHttpError("chroma_heartbeat_response_invalid")
        return int(value["nanosecond heartbeat"])

    def get_version(self) -> str:
        value = self._request("GET", "/version")
        if not isinstance(value, str) or not value:
            raise ChromaHttpError("chroma_version_response_invalid")
        return value

    def list_collections(self, limit: int | None = None, offset: int | None = None) -> list[ChromaCollection]:
        query: list[str] = []
        if limit is not None:
            if not isinstance(limit, int) or limit < 1 or limit > _MAX_BATCH_SIZE:
                raise ChromaHttpError("chroma_limit_invalid")
            query.append(f"limit={limit}")
        if offset is not None:
            if not isinstance(offset, int) or offset < 0:
                raise ChromaHttpError("chroma_offset_invalid")
            query.append(f"offset={offset}")
        path = self._collections_path() + ("?" + "&".join(query) if query else "")
        value = self._request("GET", path)
        if not isinstance(value, list):
            raise ChromaHttpError("chroma_collection_list_invalid")
        return [ChromaCollection(self, item) for item in value]

    def get_collection(self, name: str, *, embedding_function: None = None) -> ChromaCollection:
        if embedding_function is not None:
            raise ChromaHttpError("chroma_client_embedding_function_rejected")
        value = self._request("GET", self._collections_path(name))
        return ChromaCollection(self, value)

    def create_collection(
        self,
        name: str,
        *,
        metadata: dict[str, Any] | None = None,
        embedding_function: None = None,
        configuration: dict[str, Any] | None = None,
        schema: dict[str, Any] | None = None,
        get_or_create: bool = False,
    ) -> ChromaCollection:
        if embedding_function is not None or configuration or schema:
            raise ChromaHttpError("chroma_server_embedding_configuration_rejected")
        value = self._request(
            "POST",
            self._collections_path(),
            {
                "name": _collection_name(name),
                "metadata": _metadata(metadata),
                "configuration": None,
                "schema": None,
                "get_or_create": bool(get_or_create),
            },
        )
        return ChromaCollection(self, value)

    def get_or_create_collection(self, name: str, **kwargs: Any) -> ChromaCollection:
        return self.create_collection(name, get_or_create=True, **kwargs)

    def delete_collection(self, name: str) -> None:
        self._request("DELETE", self._collections_path(name))

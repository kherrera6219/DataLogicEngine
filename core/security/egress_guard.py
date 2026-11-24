"""Default-deny HTTP transport policy for configured model endpoints."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import ipaddress
import os
import re
import threading
from typing import Any, Callable, NoReturn
from urllib.parse import unquote, urlsplit

import httpx
import requests
from requests import exceptions

GuardedHTTPError = httpx.HTTPError
requests_exceptions = exceptions


class EgressDenied(RuntimeError):
    """The transport refused an outbound request before opening a connection."""

    def __init__(
        self,
        message: str = "Blocked by security policy: unapproved outbound HTTP destination",
    ) -> None:
        super().__init__(message)


class EgressAuditStateError(RuntimeError):
    """An HTTP body cannot continue after its audit record was finalized."""


class _DisabledPasswordBreachHTTP:
    """Reject the legacy external breach service under the installed policy."""

    @staticmethod
    def get(url: str, *, timeout: int) -> NoReturn:
        raise EgressDenied(
            "External password-breach lookup is disabled by the egress policy"
        )


disabled_password_breach_http = _DisabledPasswordBreachHTTP()


def require_loopback_host(host: str) -> str:
    """Return a loopback IP literal without resolving a hostname over DNS."""
    if host.lower() == "localhost":
        return "127.0.0.1"
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise EgressDenied("Local service host must be a loopback IP literal") from exc
    if not address.is_loopback:
        raise EgressDenied("Local service host must be a loopback IP literal")
    return str(address)


def local_database_url(value: str) -> str:
    """Keep the application database on this machine without resolving DNS."""
    from sqlalchemy.engine import make_url
    from sqlalchemy.exc import ArgumentError

    try:
        url = make_url(value)
    except ArgumentError as exc:
        raise EgressDenied("Invalid local database configuration") from exc
    if url.drivername in {"sqlite", "sqlite+pysqlite"}:
        name = (url.database or "").replace("\\", "/")
        # SQLite URI filenames and UNC paths can name network filesystems.
        if name.startswith("//") or name.lower().startswith("file:"):
            raise EgressDenied("The application database must use a local file")
        return value
    if url.drivername not in {"postgresql", "postgresql+psycopg2"} or not url.host:
        raise EgressDenied(
            "The application database must use local PostgreSQL or SQLite"
        )
    forbidden = {"host", "hostaddr", "service", "servicefile"}
    if any(key.lower() in forbidden for key in url.query):
        raise EgressDenied("Database connection overrides are not permitted")
    host = require_loopback_host(url.host)
    # An explicit libpq hostaddr also overrides PGHOSTADDR from the environment.
    normalized = url.set(host=host, query={**url.query, "hostaddr": host})
    return normalized.render_as_string(hide_password=False)


def loopback_service_url(url: str, *, schemes: frozenset[str]) -> str:
    """Normalize an approved local service URL without DNS resolution."""
    try:
        parts = urlsplit(url)
        if parts.scheme not in schemes or not parts.hostname or parts.fragment:
            raise EgressDenied("Local service URL is not permitted")
        host = require_loopback_host(parts.hostname)
        port = parts.port
    except ValueError as exc:
        raise EgressDenied("Local service URL is not permitted") from exc
    if port == 0:
        raise EgressDenied("Local service URL is not permitted")
    rendered_host = f"[{host}]" if ":" in host else host
    userinfo, separator, _ = parts.netloc.rpartition("@")
    authority = f"{userinfo}@" if separator else ""
    authority += rendered_host
    if port is not None:
        authority += f":{port}"
    return parts._replace(netloc=authority).geturl()


def require_local_tracking_uri(uri: str) -> None:
    """Reject network-backed MLflow URIs before the optional SDK is invoked."""
    if not uri or uri.startswith(("//", "\\\\")):
        raise EgressDenied()
    if re.match(r"^[A-Za-z]:[\\/]", uri):
        return
    try:
        parsed = urlsplit(uri)
    except ValueError as exc:
        raise EgressDenied() from exc
    if parsed.scheme:
        if (
            parsed.scheme != "file"
            or parsed.netloc
            or not parsed.path
            or unquote(parsed.path).replace("\\", "/").startswith("//")
            or parsed.query
            or parsed.fragment
        ):
            raise EgressDenied()


def _origin(url: httpx.URL) -> tuple[str, bytes, int]:
    if (
        url.scheme not in {"http", "https"}
        or not url.raw_host
        or url.userinfo
        or b"*" in url.raw_host
        or url.port == 0
    ):
        raise EgressDenied()
    port = url.port if url.port is not None else (443 if url.scheme == "https" else 80)
    return url.scheme, url.raw_host, port


def _require_airgap_origin(origin: tuple[str, bytes, int]) -> None:
    """Fail closed on remote model origins when the experimental mode is set."""
    setting = os.environ.get("DLE_EXPERIMENTAL_AIR_GAP", "false").strip().lower()
    if setting in {"0", "false", "no", "off"}:
        return
    if setting not in {"1", "true", "yes", "on"}:
        raise EgressDenied("Invalid DLE_EXPERIMENTAL_AIR_GAP setting")
    try:
        address = ipaddress.ip_address(origin[1].decode("ascii"))
    except ValueError as exc:
        raise EgressDenied(
            "Air-gap mode requires a loopback IP address for the model endpoint"
        ) from exc
    if not address.is_loopback:
        raise EgressDenied(
            "Air-gap mode requires a loopback IP address for the model endpoint"
        )


@dataclass(frozen=True, slots=True)
class EgressPolicy:
    """Allow only the exact scheme, host and port of configured endpoints."""

    allowed_origins: frozenset[tuple[str, bytes, int]] = frozenset()

    @classmethod
    def for_endpoint(cls, endpoint: str) -> EgressPolicy:
        try:
            url = httpx.URL(endpoint)
        except httpx.InvalidURL as exc:
            raise EgressDenied() from exc
        if url.query or url.fragment:
            raise EgressDenied()
        origin = _origin(url)
        _require_airgap_origin(origin)
        return cls(frozenset({origin}))

    def check(self, request: httpx.Request) -> None:
        origin = _origin(request.url)
        _require_airgap_origin(origin)
        if origin not in self.allowed_origins:
            raise EgressDenied()
        if request.headers.get_list("host") != [request.url.netloc.decode("ascii")]:
            raise EgressDenied()

    def origins(self) -> tuple[str, ...]:
        """Return the policy without path, query, headers or credentials."""
        return tuple(
            str(httpx.URL(scheme=scheme, host=host.decode("ascii"), port=port))
            for scheme, host, port in sorted(self.allowed_origins)
        )


class _AuditAttempt:
    """Track body bytes and emit one metadata-only event for an HTTP attempt."""

    def __init__(
        self, sink: Callable[..., object], request: httpx.Request, request_id: str
    ) -> None:
        self.sink = sink
        self.host = request.url.raw_host.decode("ascii")
        self.request_id = request_id
        self.bytes_out = 0
        self.bytes_in = 0
        self.emitted = False
        self._lock = threading.Lock()
        self._completed = threading.Condition(self._lock)
        self._writing = False
        self._failure: BaseException | None = None

    def count(self, *, outgoing: bool, size: int) -> None:
        with self._lock:
            if self.emitted:
                raise EgressAuditStateError(
                    "HTTP body continued after audit finalization"
                )
            if outgoing:
                self.bytes_out += size
            else:
                self.bytes_in += size

    def emit(self, result: str) -> None:
        with self._completed:
            while self._writing:
                self._completed.wait()
            if self.emitted:
                if self._failure is not None:
                    raise self._failure
                return
            # A failed durable write must not be retried automatically: the
            # record may already have reached the filesystem.
            self.emitted = True
            self._writing = True
            bytes_out, bytes_in = self.bytes_out, self.bytes_in
        try:
            self.sink(
                destination_host=self.host,
                bytes_out=bytes_out,
                bytes_in=bytes_in,
                result=result,
                request_id=self.request_id,
            )
        except BaseException as exc:
            with self._completed:
                self._failure = exc
            raise
        finally:
            with self._completed:
                self._writing = False
                self._completed.notify_all()


class _CountingSyncRequest(httpx.SyncByteStream):
    def __init__(self, stream: httpx.SyncByteStream, audit: _AuditAttempt) -> None:
        self.stream, self.audit = stream, audit

    def __iter__(self):
        for chunk in self.stream:
            self.audit.count(outgoing=True, size=len(chunk))
            yield chunk

    def close(self) -> None:
        self.stream.close()


class _CountingSyncResponse(httpx.SyncByteStream):
    def __init__(self, stream: httpx.SyncByteStream, audit: _AuditAttempt) -> None:
        self.stream, self.audit = stream, audit

    def __iter__(self):
        try:
            for chunk in self.stream:
                self.audit.count(outgoing=False, size=len(chunk))
                yield chunk
        finally:
            self.audit.emit("allow")

    def close(self) -> None:
        try:
            self.stream.close()
        finally:
            self.audit.emit("allow")


class _CountingAsyncRequest(httpx.AsyncByteStream):
    def __init__(self, stream: httpx.AsyncByteStream, audit: _AuditAttempt) -> None:
        self.stream, self.audit = stream, audit

    async def __aiter__(self):
        async for chunk in self.stream:
            self.audit.count(outgoing=True, size=len(chunk))
            yield chunk

    async def aclose(self) -> None:
        await self.stream.aclose()


class _CountingAsyncResponse(httpx.AsyncByteStream):
    def __init__(self, stream: httpx.AsyncByteStream, audit: _AuditAttempt) -> None:
        self.stream, self.audit = stream, audit

    async def __aiter__(self):
        try:
            async for chunk in self.stream:
                self.audit.count(outgoing=False, size=len(chunk))
                yield chunk
        finally:
            await asyncio.to_thread(self.audit.emit, "allow")

    async def aclose(self) -> None:
        try:
            await self.stream.aclose()
        finally:
            await asyncio.to_thread(self.audit.emit, "allow")


class GuardedHTTPTransport(httpx.HTTPTransport):
    """Check the request before HTTPX resolves or connects to the destination."""

    def __init__(
        self,
        policy: EgressPolicy,
        *,
        limits: httpx.Limits | None = None,
        audit_sink: Callable[..., object] | None = None,
        request_id: str | None = None,
    ) -> None:
        if limits is None:
            super().__init__(trust_env=False)
        else:
            super().__init__(trust_env=False, limits=limits)
        self.policy = policy
        if audit_sink is not None and not request_id:
            raise ValueError("An audit request ID is required")
        self.audit_sink, self.request_id = audit_sink, request_id

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        if self.audit_sink is None:
            self.policy.check(request)
            return super().handle_request(request)
        audit = _AuditAttempt(self.audit_sink, request, self.request_id or "")
        try:
            self.policy.check(request)
        except EgressDenied:
            audit.emit("deny")
            raise
        request.stream = _CountingSyncRequest(request.stream, audit)
        try:
            response = super().handle_request(request)
        except BaseException:
            audit.emit("allow")
            raise
        if response.is_stream_consumed:
            audit.count(outgoing=False, size=len(response.content))
            audit.emit("allow")
        else:
            response.stream = _CountingSyncResponse(response.stream, audit)
        return response


class GuardedAsyncHTTPTransport(httpx.AsyncHTTPTransport):
    """Check each async request at the same boundary as synchronous requests."""

    def __init__(
        self,
        policy: EgressPolicy,
        *,
        audit_sink: Callable[..., object] | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(trust_env=False)
        self.policy = policy
        if audit_sink is not None and not request_id:
            raise ValueError("An audit request ID is required")
        self.audit_sink, self.request_id = audit_sink, request_id

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if self.audit_sink is None:
            self.policy.check(request)
            return await super().handle_async_request(request)
        audit = _AuditAttempt(self.audit_sink, request, self.request_id or "")
        try:
            self.policy.check(request)
        except EgressDenied:
            await asyncio.to_thread(audit.emit, "deny")
            raise
        request.stream = _CountingAsyncRequest(request.stream, audit)
        try:
            response = await super().handle_async_request(request)
        except BaseException:
            await asyncio.to_thread(audit.emit, "allow")
            raise
        if response.is_stream_consumed:
            audit.count(outgoing=False, size=len(response.content))
            await asyncio.to_thread(audit.emit, "allow")
        else:
            response.stream = _CountingAsyncResponse(response.stream, audit)
        return response


class _LoopbackRequestsAdapter(requests.adapters.HTTPAdapter):
    """Enforce one local origin for libraries that require requests.Session."""

    def __init__(self, policy: EgressPolicy) -> None:
        self.policy = policy
        super().__init__()

    def send(
        self, request: requests.PreparedRequest, **kwargs: object
    ) -> requests.Response:
        try:
            target = httpx.URL(request.url or "")
            if _origin(target) not in self.policy.allowed_origins:
                raise EgressDenied()
            host = request.headers.get("Host")
            if host is not None and host != target.netloc.decode("ascii"):
                raise EgressDenied()
        except httpx.InvalidURL as exc:
            raise EgressDenied() from exc
        kwargs["proxies"] = {}
        return super().send(request, **kwargs)


class _LocalRequestsSession(requests.Session):
    def send(
        self, request: requests.PreparedRequest, **kwargs: object
    ) -> requests.Response:
        kwargs["allow_redirects"] = False
        return super().send(request, **kwargs)


def loopback_requests_session(endpoint: str) -> tuple[str, requests.Session]:
    """Bind a third-party requests client to one loopback HTTP origin."""
    local_endpoint = loopback_service_url(endpoint, schemes=frozenset({"http"}))
    policy = EgressPolicy.for_endpoint(local_endpoint)
    session = _LocalRequestsSession()
    session.trust_env = False
    adapter = _LoopbackRequestsAdapter(policy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return local_endpoint, session


def loopback_s3_client(
    endpoint: str | None,
    *,
    access_key: str | None,
    secret_key: str | None,
    region: str,
    read_timeout: int = 3,
    max_attempts: int = 1,
) -> Any:
    """Create an S3 client that can send only to one local HTTP origin."""
    if not endpoint or not access_key or not secret_key:
        raise EgressDenied("Local object storage endpoint and credentials are required")
    local_endpoint = loopback_service_url(endpoint, schemes=frozenset({"http"}))
    policy = EgressPolicy.for_endpoint(local_endpoint)

    import boto3
    from botocore.config import Config

    client = boto3.client(
        "s3",
        endpoint_url=local_endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            connect_timeout=3,
            read_timeout=read_timeout,
            retries={"max_attempts": max_attempts, "mode": "standard"},
            proxies={},
        ),
    )

    def check_request(request: Any, **_kwargs: Any) -> None:
        try:
            url = httpx.URL(request.url)
            if _origin(url) not in policy.allowed_origins:
                raise EgressDenied()
            host = request.headers.get("Host")
            if host is not None:
                host_text = host.decode("ascii") if isinstance(host, bytes) else host
                if host_text != url.netloc.decode("ascii"):
                    raise EgressDenied()
        except (httpx.InvalidURL, UnicodeDecodeError) as exc:
            raise EgressDenied() from exc

    client.meta.events.register("before-send.s3.*", check_request)
    return client


def loopback_http_client(
    endpoint: str,
    *,
    timeout: float,
    max_connections: int,
    max_keepalive_connections: int,
    headers: dict[str, str],
) -> httpx.Client:
    """Create a guarded client for a literal loopback service endpoint."""
    try:
        url = httpx.URL(endpoint)
        address = ipaddress.ip_address(url.host)
    except (httpx.InvalidURL, ValueError) as exc:
        raise EgressDenied() from exc
    if url.scheme != "http" or not address.is_loopback:
        raise EgressDenied()
    policy = EgressPolicy.for_endpoint(endpoint)
    limits = httpx.Limits(
        max_connections=max_connections,
        max_keepalive_connections=max_keepalive_connections,
    )
    return httpx.Client(
        transport=GuardedHTTPTransport(policy, limits=limits),
        timeout=httpx.Timeout(timeout, connect=min(timeout, 3.0)),
        follow_redirects=False,
        trust_env=False,
        headers=headers,
    )


def local_http_get(url: str, *, timeout: float) -> httpx.Response:
    """Fetch one loopback URL without proxies or automatic redirects."""
    try:
        request_url = httpx.URL(url)
    except httpx.InvalidURL as exc:
        raise EgressDenied() from exc
    if request_url.scheme != "http" or request_url.host not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        raise EgressDenied()
    policy = EgressPolicy(frozenset({_origin(request_url)}))
    with httpx.Client(
        transport=GuardedHTTPTransport(policy),
        trust_env=False,
        follow_redirects=False,
        timeout=timeout,
    ) as client:
        return client.get(request_url)


def model_async_client(policy: EgressPolicy, *, timeout: float) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=GuardedAsyncHTTPTransport(policy),
        follow_redirects=False,
        trust_env=False,
        timeout=timeout,
    )

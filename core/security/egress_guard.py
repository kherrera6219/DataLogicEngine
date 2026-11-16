"""Default-deny HTTP transport policy for configured model endpoints."""

from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import re
from typing import NoReturn
from urllib.parse import unquote, urlsplit

import httpx
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
        return cls(frozenset({_origin(url)}))

    def check(self, request: httpx.Request) -> None:
        if _origin(request.url) not in self.allowed_origins:
            raise EgressDenied()
        if request.headers.get_list("host") != [request.url.netloc.decode("ascii")]:
            raise EgressDenied()

    def origins(self) -> tuple[str, ...]:
        """Return the policy without path, query, headers or credentials."""
        return tuple(
            str(httpx.URL(scheme=scheme, host=host.decode("ascii"), port=port))
            for scheme, host, port in sorted(self.allowed_origins)
        )


class GuardedHTTPTransport(httpx.HTTPTransport):
    """Check the request before HTTPX resolves or connects to the destination."""

    def __init__(
        self, policy: EgressPolicy, *, limits: httpx.Limits | None = None
    ) -> None:
        if limits is None:
            super().__init__(trust_env=False)
        else:
            super().__init__(trust_env=False, limits=limits)
        self.policy = policy

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.policy.check(request)
        return super().handle_request(request)


class GuardedAsyncHTTPTransport(httpx.AsyncHTTPTransport):
    """Check each async request at the same boundary as synchronous requests."""

    def __init__(self, policy: EgressPolicy) -> None:
        super().__init__(trust_env=False)
        self.policy = policy

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.policy.check(request)
        return await super().handle_async_request(request)


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

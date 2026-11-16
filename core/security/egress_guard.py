"""Default-deny HTTP transport policy for configured model endpoints."""

from __future__ import annotations

from dataclasses import dataclass

import httpx


class EgressDenied(RuntimeError):
    """The transport refused an outbound request before opening a connection."""

    def __init__(self) -> None:
        super().__init__(
            "Blocked by security policy: unapproved outbound HTTP destination"
        )


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


def model_async_client(policy: EgressPolicy, *, timeout: float) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=GuardedAsyncHTTPTransport(policy),
        follow_redirects=False,
        trust_env=False,
        timeout=timeout,
    )

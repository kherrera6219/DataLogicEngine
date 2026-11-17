"""Constrain SDK-owned HTTP clients to their configured API origin."""

from __future__ import annotations

import httpx

from .exceptions import SDKDestinationDenied


def _origin(url: httpx.URL) -> tuple[str, bytes, int]:
    if (
        url.scheme not in {"http", "https"}
        or not url.raw_host
        or url.userinfo
        or b"*" in url.raw_host
        or url.port == 0
    ):
        raise SDKDestinationDenied("Invalid or unapproved DataLogicEngine API origin")
    port = url.port if url.port is not None else (443 if url.scheme == "https" else 80)
    return url.scheme, url.raw_host, port


def _configured_origin(endpoint: str) -> tuple[str, bytes, int]:
    try:
        url = httpx.URL(endpoint)
    except httpx.InvalidURL as exc:
        raise SDKDestinationDenied("Invalid DataLogicEngine API origin") from exc
    if url.query or url.fragment:
        raise SDKDestinationDenied("API endpoint must not include a query or fragment")
    return _origin(url)


def _check(request: httpx.Request, origin: tuple[str, bytes, int]) -> None:
    if _origin(request.url) != origin or request.headers.get_list("host") != [
        request.url.netloc.decode("ascii")
    ]:
        raise SDKDestinationDenied(
            "Request is outside the configured DataLogicEngine API origin"
        )


class _SyncTransport(httpx.HTTPTransport):
    def __init__(self, endpoint: str, *, verify: bool) -> None:
        self.origin = _configured_origin(endpoint)
        super().__init__(verify=verify, trust_env=False)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        _check(request, self.origin)
        return super().handle_request(request)


class _AsyncTransport(httpx.AsyncHTTPTransport):
    def __init__(self, endpoint: str, *, verify: bool) -> None:
        self.origin = _configured_origin(endpoint)
        super().__init__(verify=verify, trust_env=False)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        _check(request, self.origin)
        return await super().handle_async_request(request)


def sync_client(
    endpoint: str,
    *,
    timeout: float,
    verify: bool = True,
    headers: dict[str, str] | None = None,
) -> httpx.Client:
    return httpx.Client(
        base_url=endpoint,
        timeout=timeout,
        headers=headers,
        transport=_SyncTransport(endpoint, verify=verify),
        follow_redirects=False,
        trust_env=False,
    )


def async_client(
    endpoint: str, *, timeout: float, verify: bool = True
) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=endpoint,
        timeout=timeout,
        transport=_AsyncTransport(endpoint, verify=verify),
        follow_redirects=False,
        trust_env=False,
    )

"""SDK-owned HTTP clients stay within their configured API origin."""

from pathlib import Path
import shutil
import subprocess
import sys

import httpx
import pytest

from ukg_sdk import UKGAsyncClient, UKGClient
from ukg_sdk.client import UKGClient as LegacyClient
from ukg_sdk.client import UKGClientConfig
from ukg_sdk.dsqp import DSQPClient
from ukg_sdk.egress import async_client, sync_client
from ukg_sdk.exceptions import SDKDestinationDenied
from ukg_sdk.overlay import UKGOverlay


@pytest.mark.parametrize(
    "endpoint",
    [
        "",
        "file:///tmp/api",
        "https://*.example",
        "https://user:secret@example.com/api",
        "https://example.com/api?token=secret",
    ],
)
def test_invalid_sdk_origins_are_rejected(endpoint):
    with pytest.raises(SDKDestinationDenied):
        sync_client(endpoint, timeout=2)


@pytest.mark.parametrize(
    "url",
    [
        "https://outside.example/api",
        "http://dle.example/api",
        "https://dle.example:444/api",
    ],
)
def test_sync_sdk_rejects_other_origins_before_transport(monkeypatch, url):
    def fail_if_called(*_args):
        pytest.fail("unapproved request reached HTTP transport")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", fail_if_called)
    with sync_client("https://dle.example/api", timeout=2) as client:
        with pytest.raises(SDKDestinationDenied):
            client.get(url)


def test_sync_sdk_allows_configured_origin_and_does_not_follow_redirect(monkeypatch):
    contacted = []

    def redirect(_transport, request):
        contacted.append(str(request.url))
        return httpx.Response(307, headers={"location": "https://outside.example/"})

    monkeypatch.setenv("HTTPS_PROXY", "http://outside.example:8080")
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", redirect)
    with sync_client("https://dle.example/api", timeout=2) as client:
        assert client.get("https://dle.example/api").status_code == 307
        assert client._trust_env is False
    assert contacted == ["https://dle.example/api"]


def test_sync_sdk_rejects_a_spoofed_host_header(monkeypatch):
    def fail_if_called(*_args):
        pytest.fail("spoofed host reached HTTP transport")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", fail_if_called)
    with sync_client("https://dle.example/api", timeout=2) as client:
        with pytest.raises(SDKDestinationDenied):
            client.get("https://dle.example/api", headers={"Host": "outside.example"})


def test_sdk_source_imports_without_application_package(tmp_path):
    sdk_package = Path(__file__).resolve().parents[1] / "ukg_sdk"
    shutil.copytree(sdk_package, tmp_path / "ukg_sdk")
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys; sys.path.insert(0, sys.argv[1]); "
            "import ukg_sdk; from ukg_sdk.egress import sync_client; "
            "assert 'core.security.egress_guard' not in sys.modules",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("client_type", ["primary", "legacy"])
def test_sdk_client_instances_reject_other_origins(monkeypatch, client_type):
    def fail_if_called(*_args):
        pytest.fail("unapproved request reached HTTP transport")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", fail_if_called)
    client = (
        UKGClient(base_url="https://dle.example/api")
        if client_type == "primary"
        else LegacyClient(UKGClientConfig(base_url="https://dle.example/api"))
    )
    try:
        with pytest.raises(SDKDestinationDenied):
            client._client.get("https://outside.example/")
    finally:
        client.close()


def test_dsqp_security_denial_does_not_return_offline_result():
    client = DSQPClient(backend_url="https://user:secret@dle.example")
    with pytest.raises(SDKDestinationDenied):
        client.construct("question")


@pytest.mark.asyncio
async def test_async_sdk_rejects_other_origins_before_transport(monkeypatch):
    async def fail_if_called(*_args):
        pytest.fail("unapproved request reached HTTP transport")

    monkeypatch.setattr(
        httpx.AsyncHTTPTransport, "handle_async_request", fail_if_called
    )
    client = UKGAsyncClient(base_url="https://dle.example/api")
    try:
        with pytest.raises(SDKDestinationDenied):
            await client._client.get("https://outside.example/")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_async_sdk_stays_on_configured_origin_during_redirect(monkeypatch):
    contacted = []

    async def redirect(_transport, request):
        contacted.append(str(request.url))
        return httpx.Response(307, headers={"location": "https://outside.example/"})

    monkeypatch.setenv("HTTPS_PROXY", "http://outside.example:8080")
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", redirect)
    async with async_client("https://dle.example/api", timeout=2) as client:
        assert (await client.get("https://dle.example/api")).status_code == 307
        assert client._trust_env is False
    assert contacted == ["https://dle.example/api"]


@pytest.mark.asyncio
async def test_overlay_injected_transport_remains_caller_controlled():
    contacted = []

    def respond(request):
        contacted.append(str(request.url))
        return httpx.Response(200, json={"data": {"response": "ok"}})

    async with httpx.AsyncClient(
        base_url="https://caller.example/api", transport=httpx.MockTransport(respond)
    ) as supplied:
        overlay = UKGOverlay(base_url="https://dle.example/api", client=supplied)
        assert (await overlay.run(query="hello"))["answer"] == "ok"
    assert contacted == ["https://caller.example/api/gateway/chat"]

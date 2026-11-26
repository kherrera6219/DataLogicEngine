"""Opt-in HTTP audit instrumentation; application wiring remains separate."""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import pytest

from backend.security.audit_logger import AuditLogger, AuditReplicaError
from core.security.egress_guard import (
    _AuditAttempt,
    EgressDenied,
    EgressPolicy,
    GuardedAsyncHTTPTransport,
    GuardedHTTPTransport,
)


def _logger(tmp_path: Path, *, enabled: bool = True) -> AuditLogger:
    return AuditLogger(
        {
            "log_dir": str(tmp_path / "ordinary"),
            "immutable_replica_dir": str(tmp_path / "replica"),
            "immutable_replica_enabled": enabled,
            "immutable_hmac_secret": "test-key",
        },
        auto_start=False,
    )


def _events(logger: AuditLogger):
    path = Path(logger._immutable_log_file_path())
    return [
        json.loads(line)["event"]
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


@pytest.fixture
def local_model():
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            response = b"model response"
            self.send_response(200)
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        def log_message(self, _format, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


@pytest.mark.parametrize("preloaded", [True, False])
def test_sync_allowed_attempt_records_body_counts_without_content(
    tmp_path, monkeypatch, preloaded
):
    logger = _logger(tmp_path)
    prompt, answer = b"private prompt", b"private response"

    def respond(_transport, request):
        assert b"".join(request.stream) == prompt
        return (
            httpx.Response(200, content=answer)
            if preloaded
            else httpx.Response(200, stream=httpx.ByteStream(answer))
        )

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", respond)
    transport = GuardedHTTPTransport(
        EgressPolicy.for_endpoint("https://models.example/v1"),
        audit_sink=logger.log_egress_event,
        request_id="request-123",
    )
    with httpx.Client(transport=transport, trust_env=False) as client:
        assert (
            client.post("https://models.example/v1", content=prompt).content == answer
        )
    events = _events(logger)
    assert len(events) == 1
    assert events[0]["status"] == "allow"
    assert events[0]["request_id"] == "request-123"
    assert events[0]["details"] == {
        "destination_host": "models.example",
        "bytes_out": len(prompt),
        "bytes_in": len(answer),
    }
    contents = Path(logger._immutable_log_file_path()).read_bytes()
    assert prompt not in contents and answer not in contents
    assert logger.verify_immutable_replica_integrity()["verified"] is True


def test_denied_attempt_records_once_without_sending(tmp_path, monkeypatch):
    logger = _logger(tmp_path)

    def fail_if_sent(_transport, _request):
        pytest.fail("Denied request reached the transport")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", fail_if_sent)
    with httpx.Client(
        transport=GuardedHTTPTransport(
            EgressPolicy(), audit_sink=logger.log_egress_event, request_id="request-123"
        )
    ) as client:
        with pytest.raises(EgressDenied):
            client.post("https://models.example/v1", content=b"private prompt")
    events = _events(logger)
    assert len(events) == 1
    assert events[0]["status"] == "deny"
    assert events[0]["details"] == {
        "destination_host": "models.example",
        "bytes_out": 0,
        "bytes_in": 0,
    }
    assert b"private prompt" not in Path(logger._immutable_log_file_path()).read_bytes()


def test_allowed_transport_failure_is_recorded_and_propagated(tmp_path, monkeypatch):
    logger = _logger(tmp_path)

    def fail(_transport, request):
        list(request.stream)
        raise httpx.ConnectError("synthetic failure", request=request)

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", fail)
    with httpx.Client(
        transport=GuardedHTTPTransport(
            EgressPolicy.for_endpoint("https://models.example"),
            audit_sink=logger.log_egress_event,
            request_id="request-123",
        )
    ) as client:
        with pytest.raises(httpx.ConnectError):
            client.post("https://models.example", content=b"payload")
    events = _events(logger)
    assert len(events) == 1
    assert events[0]["details"]["bytes_out"] == len(b"payload")
    assert events[0]["details"]["bytes_in"] == 0


def test_partial_stream_close_records_only_observed_bytes_once(tmp_path, monkeypatch):
    logger = _logger(tmp_path)

    class SplitStream(httpx.SyncByteStream):
        def __iter__(self):
            yield b"first"
            yield b"second"

    def respond(_transport, request):
        list(request.stream)
        return httpx.Response(200, stream=SplitStream())

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", respond)
    with httpx.Client(
        transport=GuardedHTTPTransport(
            EgressPolicy.for_endpoint("https://models.example"),
            audit_sink=logger.log_egress_event,
            request_id="request-123",
        )
    ) as client:
        with client.stream(
            "POST", "https://models.example", content=b"payload"
        ) as response:
            chunks = response.iter_raw()
            assert next(chunks) == b"first"
    events = _events(logger)
    assert len(events) == 1
    assert events[0]["details"]["bytes_out"] == len(b"payload")
    assert events[0]["details"]["bytes_in"] == len(b"first")


def test_audit_failure_is_not_reported_as_a_policy_success(tmp_path):
    logger = _logger(tmp_path, enabled=False)
    with httpx.Client(
        transport=GuardedHTTPTransport(
            EgressPolicy(), audit_sink=logger.log_egress_event, request_id="request-123"
        )
    ) as client:
        with pytest.raises(AuditReplicaError, match="replica_disabled"):
            client.get("https://models.example")


def test_audit_failure_after_response_is_explicit(tmp_path, monkeypatch):
    logger = _logger(tmp_path, enabled=False)
    monkeypatch.setattr(
        httpx.HTTPTransport,
        "handle_request",
        lambda _transport, _request: httpx.Response(200, content=b"private response"),
    )
    with httpx.Client(
        transport=GuardedHTTPTransport(
            EgressPolicy.for_endpoint("https://models.example"),
            audit_sink=logger.log_egress_event,
            request_id="request-123",
        )
    ) as client:
        with pytest.raises(AuditReplicaError, match="replica_disabled"):
            client.get("https://models.example")


def test_audited_transport_requires_correlation_id(tmp_path):
    logger = _logger(tmp_path)
    with pytest.raises(ValueError, match="request ID"):
        GuardedHTTPTransport(EgressPolicy(), audit_sink=logger.log_egress_event)


def test_concurrent_finalization_reports_audit_failure_to_both_callers():
    entered = threading.Event()
    release = threading.Event()
    calls = []

    def fail(**_metadata):
        calls.append(1)
        entered.set()
        assert release.wait(timeout=5)
        raise AuditReplicaError("audit write failed")

    attempt = _AuditAttempt(
        fail, httpx.Request("GET", "https://models.example"), "request-123"
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(attempt.emit, "allow")
        assert entered.wait(timeout=5)
        second = pool.submit(attempt.emit, "allow")
        release.set()
        for result in (first, second):
            with pytest.raises(AuditReplicaError, match="audit write failed"):
                result.result(timeout=5)
    assert calls == [1]


@pytest.mark.asyncio
async def test_async_denied_attempt_is_recorded(tmp_path):
    logger = _logger(tmp_path)
    async with httpx.AsyncClient(
        transport=GuardedAsyncHTTPTransport(
            EgressPolicy(), audit_sink=logger.log_egress_event, request_id="request-123"
        )
    ) as client:
        with pytest.raises(EgressDenied):
            await client.get("https://models.example")
    events = _events(logger)
    assert len(events) == 1
    assert events[0]["status"] == "deny"


@pytest.mark.asyncio
@pytest.mark.parametrize("preloaded", [True, False])
async def test_async_attempt_records_counts_once_without_content(
    tmp_path, monkeypatch, preloaded
):
    logger = _logger(tmp_path)
    prompt, answer = b"private prompt", b"private response"

    async def respond(_transport, request):
        assert b"".join([chunk async for chunk in request.stream]) == prompt
        return (
            httpx.Response(200, content=answer)
            if preloaded
            else httpx.Response(200, stream=httpx.ByteStream(answer))
        )

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", respond)
    async with httpx.AsyncClient(
        transport=GuardedAsyncHTTPTransport(
            EgressPolicy.for_endpoint("https://models.example"),
            audit_sink=logger.log_egress_event,
            request_id="request-123",
        ),
        trust_env=False,
    ) as client:
        assert (
            await client.post("https://models.example", content=prompt)
        ).content == answer
    events = _events(logger)
    assert len(events) == 1
    assert events[0]["details"] == {
        "destination_host": "models.example",
        "bytes_out": len(prompt),
        "bytes_in": len(answer),
    }
    contents = Path(logger._immutable_log_file_path()).read_bytes()
    assert prompt not in contents and answer not in contents


def test_sync_real_loopback_request_is_audited(tmp_path, local_model):
    logger = _logger(tmp_path)
    transport = GuardedHTTPTransport(
        EgressPolicy.for_endpoint(local_model),
        audit_sink=logger.log_egress_event,
        request_id="request-123",
    )
    with httpx.Client(transport=transport, trust_env=False) as client:
        assert (
            client.post(local_model, content=b"private prompt").content
            == b"model response"
        )
    event = _events(logger)[0]
    assert event["details"] == {
        "destination_host": "127.0.0.1",
        "bytes_out": 14,
        "bytes_in": 14,
    }
    assert b"private prompt" not in Path(logger._immutable_log_file_path()).read_bytes()


@pytest.mark.asyncio
async def test_async_real_loopback_request_is_audited(tmp_path, local_model):
    logger = _logger(tmp_path)
    transport = GuardedAsyncHTTPTransport(
        EgressPolicy.for_endpoint(local_model),
        audit_sink=logger.log_egress_event,
        request_id="request-123",
    )
    async with httpx.AsyncClient(transport=transport, trust_env=False) as client:
        assert (
            await client.post(local_model, content=b"private prompt")
        ).content == b"model response"
    event = _events(logger)[0]
    assert event["details"] == {
        "destination_host": "127.0.0.1",
        "bytes_out": 14,
        "bytes_in": 14,
    }
    assert b"model response" not in Path(logger._immutable_log_file_path()).read_bytes()

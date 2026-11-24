"""Opt-in model auditing uses the app-owned chain and request context."""

from __future__ import annotations

import json
import asyncio
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from flask import Flask

from backend.observability.context import bound_observation_context
from backend.security.audit_logger import AuditLogger, AuditReplicaError
from backend.security.egress_audit_context import EgressAuditConfigurationError
from core.security.egress_guard import EgressDenied, EgressPolicy


@pytest.fixture(scope="module", autouse=True)
def _close_implicit_test_loop():
    """Close only a default loop created for this module's async test runner."""
    policy = asyncio.get_event_loop_policy()
    original_factory = policy.new_event_loop
    created = []

    def create_owned_loop():
        loop = original_factory()
        created.append(loop)
        return loop

    with patch.object(policy, "new_event_loop", side_effect=create_owned_loop):
        try:
            loop = policy.get_event_loop()
        except RuntimeError:
            loop = None
    yield
    if loop is not None and loop in created:
        assert not loop.is_running()
        if not loop.is_closed():
            loop.close()
        try:
            current = policy.get_event_loop()
        except RuntimeError:
            current = None
        if current is loop:
            policy.set_event_loop(None)


@pytest.fixture
def model_server():
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            requests.append(self.path)
            self.rfile.read(int(self.headers["Content-Length"]))
            if "/models/" in self.path:
                payload = {
                    "candidates": [
                        {
                            "content": {
                                "role": "model",
                                "parts": [{"text": "private model response"}],
                            },
                            "finishReason": "STOP",
                        }
                    ],
                    "usageMetadata": {
                        "promptTokenCount": 1,
                        "candidatesTokenCount": 2,
                        "totalTokenCount": 3,
                    },
                }
            else:
                payload = {
                    "id": "resp_local",
                    "object": "response",
                    "created_at": 1,
                    "status": "completed",
                    "model": "gpt-6-sol",
                    "output": [
                        {
                            "id": "msg_local",
                            "type": "message",
                            "status": "completed",
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": "private model response",
                                    "annotations": [],
                                }
                            ],
                        }
                    ],
                    "usage": {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
                }
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1", requests
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def _app(tmp_path: Path, *, replica_enabled: bool = True):
    app = Flask(__name__)
    app.config["DLE_EXPERIMENTAL_EGRESS_AUDIT"] = True
    logger = AuditLogger(
        {
            "log_dir": str(tmp_path / "ordinary"),
            "immutable_replica_dir": str(tmp_path / "replica"),
            "immutable_replica_enabled": replica_enabled,
            "immutable_hmac_secret": "test-key",
        },
        auto_start=False,
    )
    app.extensions["dle_audit_logger"] = logger
    return app, logger


def test_app_security_setup_enables_owned_replica(tmp_path, monkeypatch):
    from app import _configure_owned_security_services

    monkeypatch.setenv("DLE_EXPERIMENTAL_EGRESS_AUDIT", "true")
    app = Flask(__name__)
    with patch("backend.security.encryption_manager.EncryptionManager"):
        _configure_owned_security_services(app, SimpleNamespace(runtime_root=tmp_path))
    assert app.config["DLE_EXPERIMENTAL_EGRESS_AUDIT"] is True
    assert app.extensions["dle_audit_logger"].immutable_replica_enabled is True
    assert Path(
        app.extensions["dle_audit_logger"].immutable_replica_dir
    ).is_relative_to(tmp_path)


@pytest.mark.asyncio
async def test_real_model_request_writes_correlated_metadata(
    tmp_path, model_server, monkeypatch
):
    from backend.llm_gateway.providers.openai import OpenAIProvider

    monkeypatch.setenv("DLE_EXPERIMENTAL_EGRESS_AUDIT", "true")
    endpoint, requests = model_server
    app, logger = _app(tmp_path)
    with app.app_context(), bound_observation_context("request-123"):
        provider = OpenAIProvider(api_key="test-key", base_url=endpoint)
        try:
            response = await provider.complete(
                messages=[{"role": "user", "content": "private prompt"}],
                model="gpt-6-sol",
            )
        finally:
            await provider.close()
    assert response.text == "private model response"
    assert requests == ["/v1/responses"]
    path = Path(logger._immutable_log_file_path())
    entries = [
        json.loads(line)["event"]
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert len(entries) == 1
    assert entries[0]["request_id"] == "request-123"
    assert entries[0]["status"] == "allow"
    assert entries[0]["details"]["destination_host"] == "127.0.0.1"
    assert entries[0]["details"]["bytes_out"] > 0
    assert entries[0]["details"]["bytes_in"] > 0
    contents = path.read_bytes()
    assert (
        b"private prompt" not in contents and b"private model response" not in contents
    )
    assert logger.verify_immutable_replica_integrity()["verified"] is True


@pytest.mark.asyncio
async def test_google_model_request_writes_correlated_metadata(
    tmp_path, model_server, monkeypatch
):
    from backend.llm_gateway.providers.google import GoogleProvider

    monkeypatch.setenv("DLE_EXPERIMENTAL_EGRESS_AUDIT", "true")
    endpoint, requests = model_server
    app, logger = _app(tmp_path)
    with app.app_context(), bound_observation_context("request-google"):
        provider = GoogleProvider(api_key="test-key", base_url=endpoint)
        try:
            response = await provider.complete(
                messages=[{"role": "user", "content": "private prompt"}],
                model="gemini-3.8-flash",
            )
        finally:
            await provider.close()
    assert response.text == "private model response"
    assert len(requests) == 1 and "/models/" in requests[0]
    path = Path(logger._immutable_log_file_path())
    events = [
        json.loads(line)["event"]
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert len(events) == 1 and events[0]["request_id"] == "request-google"
    assert (
        events[0]["details"]["bytes_out"] > 0 and events[0]["details"]["bytes_in"] > 0
    )
    contents = path.read_bytes()
    assert (
        b"private prompt" not in contents and b"private model response" not in contents
    )


@pytest.mark.asyncio
async def test_governed_request_records_model_attempt(
    app, tmp_path, model_server, monkeypatch
):
    from backend.llm_gateway.gateway import GatewayRequest, LLMGateway
    from extensions import db

    monkeypatch.setenv("DLE_EXPERIMENTAL_EGRESS_AUDIT", "true")
    endpoint, requests = model_server
    _test_app, logger = _app(tmp_path)
    monkeypatch.setitem(app.config, "DLE_EXPERIMENTAL_EGRESS_AUDIT", True)
    monkeypatch.setitem(app.extensions, "dle_audit_logger", logger)
    provider = MagicMock()
    provider.id = uuid.uuid4()
    provider.name = "LocalMock"
    provider.provider_type = "openai"
    provider.model_id = "gpt-6-sol"
    provider.endpoint = endpoint
    provider.get_api_key.return_value = "test-key"
    provider.max_retries = 1
    provider.timeout_seconds = 30
    with app.app_context(), bound_observation_context("governed-123"):
        gateway = LLMGateway(db_session=db.session)
        with (
            patch.object(
                gateway, "_get_eligible_providers", AsyncMock(return_value=[provider])
            ),
            patch.object(gateway, "_record_usage", AsyncMock()),
            patch.object(gateway, "_save_chat_message", AsyncMock()),
        ):
            result = await gateway.process(
                GatewayRequest(
                    messages=[{"role": "user", "content": "private prompt"}],
                    run_ukg_pipeline=False,
                )
            )
    assert result.ok is True, result.error
    assert requests == ["/v1/responses"]
    path = Path(logger._immutable_log_file_path())
    events = [
        json.loads(line)["event"]
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    assert len(events) == 1 and events[0]["request_id"] == "governed-123"
    assert events[0]["status"] == "allow"
    assert b"private prompt" not in path.read_bytes()


@pytest.mark.asyncio
async def test_missing_correlation_fails_before_model_connection(
    tmp_path, model_server, monkeypatch
):
    from backend.llm_gateway.providers.openai import OpenAIProvider

    monkeypatch.setenv("DLE_EXPERIMENTAL_EGRESS_AUDIT", "true")
    endpoint, requests = model_server
    app, _logger = _app(tmp_path)
    with app.app_context():
        provider = OpenAIProvider(api_key="test-key", base_url=endpoint)
        try:
            with pytest.raises(EgressAuditConfigurationError, match="correlation"):
                await provider.complete(
                    messages=[{"role": "user", "content": "test"}], model="gpt-6-sol"
                )
        finally:
            await provider.close()
    assert requests == []


@pytest.mark.asyncio
async def test_google_missing_correlation_fails_before_model_connection(
    tmp_path, model_server, monkeypatch
):
    from backend.llm_gateway.providers.google import GoogleProvider

    monkeypatch.setenv("DLE_EXPERIMENTAL_EGRESS_AUDIT", "true")
    endpoint, requests = model_server
    app, _logger = _app(tmp_path)
    with app.app_context():
        provider = GoogleProvider(api_key="test-key", base_url=endpoint)
        try:
            with pytest.raises(EgressAuditConfigurationError, match="correlation"):
                await provider.complete(
                    messages=[{"role": "user", "content": "test"}],
                    model="gemini-3.8-flash",
                )
        finally:
            await provider.close()
    assert requests == []


@pytest.mark.asyncio
async def test_model_audit_write_failure_is_visible(
    tmp_path, model_server, monkeypatch
):
    from backend.llm_gateway.providers.openai import OpenAIProvider

    monkeypatch.setenv("DLE_EXPERIMENTAL_EGRESS_AUDIT", "true")
    endpoint, requests = model_server
    app, logger = _app(tmp_path)

    def fail(**_kwargs):
        raise AuditReplicaError("audit write failed")

    monkeypatch.setattr(logger, "log_egress_event", fail)
    with app.app_context(), bound_observation_context("request-123"):
        provider = OpenAIProvider(api_key="test-key", base_url=endpoint)
        try:
            with pytest.raises(AuditReplicaError, match="audit write failed"):
                await provider.complete(
                    messages=[{"role": "user", "content": "test"}], model="gpt-6-sol"
                )
        finally:
            await provider.close()
    assert requests == ["/v1/responses"]


@pytest.mark.asyncio
async def test_google_audit_write_failure_is_visible(
    tmp_path, model_server, monkeypatch
):
    from backend.llm_gateway.providers.google import GoogleProvider

    monkeypatch.setenv("DLE_EXPERIMENTAL_EGRESS_AUDIT", "true")
    endpoint, requests = model_server
    app, logger = _app(tmp_path)

    def fail(**_kwargs):
        raise AuditReplicaError("audit write failed")

    monkeypatch.setattr(logger, "log_egress_event", fail)
    with app.app_context(), bound_observation_context("request-123"):
        provider = GoogleProvider(api_key="test-key", base_url=endpoint)
        try:
            with pytest.raises(AuditReplicaError, match="audit write failed"):
                await provider.complete(
                    messages=[{"role": "user", "content": "test"}],
                    model="gemini-3.8-flash",
                )
        finally:
            await provider.close()
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_denied_model_attempt_is_audited_without_connecting(
    tmp_path, model_server, monkeypatch
):
    from backend.llm_gateway.providers.openai import OpenAIProvider

    monkeypatch.setenv("DLE_EXPERIMENTAL_EGRESS_AUDIT", "true")
    endpoint, requests = model_server
    app, logger = _app(tmp_path)
    monkeypatch.setattr(
        EgressPolicy, "for_endpoint", classmethod(lambda cls, _endpoint: cls())
    )
    with app.app_context(), bound_observation_context("request-123"):
        provider = OpenAIProvider(api_key="test-key", base_url=endpoint)
        try:
            with pytest.raises(EgressDenied):
                await provider.complete(
                    messages=[{"role": "user", "content": "private prompt"}],
                    model="gpt-6-sol",
                )
        finally:
            await provider.close()
    assert requests == []
    events = [
        json.loads(line)["event"]
        for line in Path(logger._immutable_log_file_path())
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert len(events) == 1 and events[0]["status"] == "deny"


def test_enabled_without_app_context_fails_closed(monkeypatch):
    from backend.security.egress_audit_context import resolve_model_egress_audit

    monkeypatch.setenv("DLE_EXPERIMENTAL_EGRESS_AUDIT", "true")
    with pytest.raises(EgressAuditConfigurationError, match="application context"):
        resolve_model_egress_audit()


def test_enabled_app_without_writer_fails_closed(monkeypatch):
    from backend.security.egress_audit_context import resolve_model_egress_audit

    monkeypatch.setenv("DLE_EXPERIMENTAL_EGRESS_AUDIT", "true")
    app = Flask(__name__)
    app.config["DLE_EXPERIMENTAL_EGRESS_AUDIT"] = True
    with app.app_context(), bound_observation_context("request-123"):
        with pytest.raises(
            EgressAuditConfigurationError, match="writer is unavailable"
        ):
            resolve_model_egress_audit()


def test_enabled_app_with_disabled_replica_fails_closed(tmp_path, monkeypatch):
    from backend.security.egress_audit_context import resolve_model_egress_audit

    monkeypatch.setenv("DLE_EXPERIMENTAL_EGRESS_AUDIT", "true")
    app, _logger = _app(tmp_path, replica_enabled=False)
    with app.app_context(), bound_observation_context("request-123"):
        with pytest.raises(EgressAuditConfigurationError, match="replica is disabled"):
            resolve_model_egress_audit()


def test_enabled_environment_with_unconfigured_app_fails_closed(monkeypatch):
    from backend.security.egress_audit_context import resolve_model_egress_audit

    monkeypatch.setenv("DLE_EXPERIMENTAL_EGRESS_AUDIT", "true")
    app = Flask(__name__)
    with app.app_context(), bound_observation_context("request-123"):
        with pytest.raises(EgressAuditConfigurationError, match="not configured"):
            resolve_model_egress_audit()


@pytest.mark.parametrize("value", ["", "tru"])
def test_invalid_audit_setting_is_not_silently_disabled(monkeypatch, value):
    from backend.security.egress_audit_context import experimental_egress_audit_enabled

    monkeypatch.setenv("DLE_EXPERIMENTAL_EGRESS_AUDIT", value)
    with pytest.raises(EgressAuditConfigurationError, match="Invalid"):
        experimental_egress_audit_enabled()

"""Exercise a governed request against a local mock model."""

from __future__ import annotations

import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.llm_gateway.gateway import GatewayRequest, LLMGateway


@pytest.mark.asyncio
async def test_governed_request_uses_loopback_model(app, monkeypatch):
    calls = []

    class ModelHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            calls.append(self.path)
            self.rfile.read(int(self.headers["Content-Length"]))
            body = json.dumps(
                {
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
                                    "text": "Local response",
                                    "annotations": [],
                                }
                            ],
                        }
                    ],
                    "usage": {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _format, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), ModelHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        endpoint = f"http://127.0.0.1:{server.server_port}/v1"
        monkeypatch.setenv("DLE_EXPERIMENTAL_AIR_GAP", "true")
        monkeypatch.setenv("OPENAI_BASE_URL", endpoint)
        monkeypatch.setenv("OPENAI_API_KEY", "local-test-key")
        from extensions import db
        from models import TraceRun, TraceStage

        with app.app_context():
            gateway = LLMGateway(db_session=db.session)
            provider = MagicMock()
            provider.id = uuid.uuid4()
            provider.name = "LocalMock"
            provider.provider_type = "openai"
            provider.model_id = "gpt-6-sol"
            provider.endpoint = endpoint
            provider.get_api_key.return_value = "local-test-key"
            provider.max_retries = 1
            provider.timeout_seconds = 30
            with (
                patch.object(
                    gateway,
                    "_get_eligible_providers",
                    AsyncMock(return_value=[provider]),
                ),
                patch.object(gateway, "_record_usage", AsyncMock()),
                patch.object(gateway, "_save_chat_message", AsyncMock()),
            ):
                response = await gateway.process(
                    GatewayRequest(
                        messages=[{"role": "user", "content": "Test local model"}],
                        run_ukg_pipeline=False,
                    )
                )
            assert response.ok is True, response.error
            assert calls == ["/v1/responses"]
            run = db.session.get(TraceRun, uuid.UUID(response.run_id))
            assert run is not None
            assert run.final_answer == "Local response"
            stages = run.stages.order_by(TraceStage.layer_index).all()
            assert {
                "admission",
                "provider_execution",
                "layer_10_release_gate",
                "persistence",
            }.issubset({stage.name for stage in stages})
            assert all(stage.status == "completed" for stage in stages)
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

"""Phase 8 public gateway OpenAPI contract checks."""

from __future__ import annotations

from pathlib import Path

import yaml


OPENAPI_PATH = Path(__file__).resolve().parents[2] / "docs" / "openapi.yaml"


def _spec() -> dict:
    return yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))


def test_gateway_authentication_schemes_are_publicly_documented() -> None:
    schemes = _spec()["components"]["securitySchemes"]
    assert schemes["clientBearer"] == {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "ukg_<copy-once-client-key>",
    }
    assert schemes["clientApiKey"]["in"] == "header"
    assert schemes["clientApiKey"]["name"] == "X-API-Key"


def test_gateway_openapi_covers_live_external_routes() -> None:
    paths = _spec()["paths"]
    assert {
        "/gateway/chat",
        "/gateway/chat/stream",
        "/gateway/requests/{request_id}/cancel",
        "/gateway/capabilities",
    }.issubset(paths)
    assert paths["/gateway/chat"]["post"]["security"] == [
        {"clientBearer": []},
        {"clientApiKey": []},
        {"sessionCookie": [], "csrfToken": []},
    ]
    assert "text/event-stream" in paths["/gateway/chat/stream"]["post"]["responses"]["200"]["content"]
    assert {
        "/gateway/runs",
        "/gateway/runs/{job_id}",
        "/gateway/runs/{job_id}/result",
        "/gateway/runs/{job_id}/cancel",
    }.issubset(paths)


def test_gateway_openapi_documents_live_validated_sse_and_bounded_compatibility() -> None:
    paths = _spec()["paths"]
    stream = paths["/gateway/chat/stream"]["post"]
    assert "live governed stage" in stream["description"].lower()
    assert "validation" in stream["description"].lower()

    assert {"/v1/models", "/v1/chat/completions"}.issubset(paths)
    compatibility = paths["/v1/chat/completions"]["post"]
    assert compatibility["servers"] == [{"url": "http://localhost:5000"}]
    assert "Unknown OpenAI fields are rejected" in compatibility["description"]
    schema = _spec()["components"]["schemas"]["OpenAIChatCompletionRequest"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["model"]["enum"] == [
        "dle-standard",
        "dle-enhanced",
        "dle-local-review",
    ]


def test_gateway_job_contract_requires_durable_idempotency_and_typed_states() -> None:
    spec = _spec()
    create_schema = spec["paths"]["/gateway/runs"]["post"]["requestBody"]["content"]["application/json"]["schema"]
    assert create_schema["allOf"][1]["required"] == ["idempotency_key"]
    job = spec["components"]["schemas"]["GatewayJob"]
    assert job["properties"]["status"]["enum"] == [
        "queued",
        "running",
        "completed",
        "failed",
        "cancelled",
        "expired",
    ]


def test_gateway_request_contract_is_strict_and_versioned() -> None:
    schemas = _spec()["components"]["schemas"]
    request_schema = schemas["ChatRequest"]
    assert request_schema["additionalProperties"] is False
    assert request_schema["properties"]["messages"]["items"]["additionalProperties"] is False
    assert request_schema["properties"]["virtual_model"]["enum"] == [
        "dle-standard",
        "dle-enhanced",
        "dle-local-review",
    ]
    assert request_schema["properties"]["request_id"]["minLength"] == 8
    assert request_schema["properties"]["idempotency_key"]["minLength"] == 8
    assert request_schema["properties"]["max_tokens"]["minimum"] == 1
    assert schemas["GatewayCapabilities"]["properties"]["contract_version"]["example"] == "dle-gateway.v1"


def test_gateway_openapi_documents_typed_boundary_failures() -> None:
    paths = _spec()["paths"]
    chat_responses = paths["/gateway/chat"]["post"]["responses"]
    for status in ("401", "403", "409", "413", "422", "429", "503"):
        assert status in chat_responses
        assert chat_responses[status]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/GatewayError"
        }


def test_owner_client_key_lifecycle_is_in_the_openapi_contract() -> None:
    paths = _spec()["paths"]
    expected = {
        "/admin/api-keys": {"get", "post"},
        "/admin/api-keys/{key_id}/rotate": {"post"},
        "/admin/api-keys/{key_id}/revoke": {"post"},
        "/admin/api-keys/{key_id}/expire": {"post"},
        "/admin/api-keys/{key_id}": {"delete"},
    }
    for path, methods in expected.items():
        assert methods.issubset(paths[path])
        for method in methods:
            operation = paths[path][method]
            expected_security = (
                [{"sessionCookie": []}]
                if method == "get"
                else [{"sessionCookie": [], "csrfToken": []}]
            )
            assert operation["security"] == expected_security

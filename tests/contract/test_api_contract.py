from __future__ import annotations

import os
from pathlib import Path

import pytest

from app import app

ROOT = Path(__file__).resolve().parents[2]
STATIC_OPENAPI_PATH = ROOT / "docs" / "openapi.yaml"

try:
    import schemathesis

    SCHEMATHESIS_INSTALLED = True
except ImportError:
    schemathesis = None
    SCHEMATHESIS_INSTALLED = False


def _load_static_openapi() -> dict:
    assert STATIC_OPENAPI_PATH.exists(), f"OpenAPI spec not found at {STATIC_OPENAPI_PATH}"
    try:
        import yaml  # type: ignore[import-untyped]
        payload = yaml.safe_load(STATIC_OPENAPI_PATH.read_text(encoding="utf-8"))
    except ImportError:
        import json
        payload = json.loads(STATIC_OPENAPI_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict), "OpenAPI payload must be an object"
    return payload


def test_openapi_spec_has_required_core_contracts() -> None:
    spec = _load_static_openapi()

    assert spec.get("openapi"), "OpenAPI version must be declared"
    assert isinstance(spec.get("paths"), dict), "OpenAPI paths must be present"

    paths = spec["paths"]
    for required_path in (
        "/gateway/chat",
        "/gateway/chat/stream",
        "/truth/gate/evaluate",
        "/ka/algorithms",
    ):
        assert required_path in paths, f"Missing required API path contract: {required_path}"

    gateway_post = paths["/gateway/chat"].get("post") or {}
    assert gateway_post, "Supported contract must document POST /gateway/chat"
    request_body = gateway_post.get("requestBody") or {}
    assert request_body.get("required") is True, "Gateway request body must be required"


@pytest.mark.parametrize(
    ("method", "path", "payload", "expected_statuses"),
    [
        # The supported static integration contract is docs/openapi.yaml.
        ("GET", "/live", None, {200}),
        ("GET", "/ready", None, {200, 503}),
        ("GET", "/metrics", None, {401}),
        ("POST", "/api/v1/gateway/chat", {"messages": [{"role": "user", "content": "hi"}]}, {400, 401, 403}),
        ("POST", "/api/v1/gateway/chat/stream", {"messages": [{"role": "user", "content": "hi"}]}, {400, 401, 403}),
    ],
)
def test_runtime_api_contract_smoke(
    method: str,
    path: str,
    payload: dict | None,
    expected_statuses: set[int],
) -> None:
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = (
            client.open(path, method=method, json=payload)
            if payload is not None
            else client.open(path, method=method)
        )
        assert (
            response.status_code in expected_statuses
        ), f"Unexpected status for {method} {path}: {response.status_code}"


if SCHEMATHESIS_INSTALLED:
    _SCHEMATHESIS_SCHEMA = schemathesis.from_wsgi(str(STATIC_OPENAPI_PATH), app)

    @_SCHEMATHESIS_SCHEMA.parametrize()
    def test_api_contract_property_fuzz(case) -> None:  # type: ignore[no-untyped-def]
        if os.environ.get("RUN_SCHEMATHESIS", "0") != "1":
            pytest.skip("Set RUN_SCHEMATHESIS=1 to enable property-based OpenAPI fuzzing.")
        response = case.call_wsgi()
        case.validate_response(response)
        assert response.status_code < 500, f"Server error on {case.method} {case.formatted_path}"
else:

    @pytest.mark.skip(reason="Schemathesis not installed")
    def test_api_contract_property_fuzz() -> None:
        pass

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.api_gateway.api_gateway import verify_token


def _request_with_bearer(token: str | None) -> Request:
    headers = []
    if token is not None:
        headers.append((b"authorization", f"Bearer {token}".encode()))
    return Request({"type": "http", "method": "GET", "path": "/", "headers": headers})


def _token(secret: str, **claims):
    payload = {
        "sub": "user-123",
        "roles": ["user"],
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    payload.update(claims)
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.mark.asyncio
async def test_verify_token_rejects_missing_bearer():
    with pytest.raises(HTTPException) as exc:
        await verify_token(_request_with_bearer(None))

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_verify_token_rejects_unsigned_placeholder_token(monkeypatch):
    monkeypatch.setenv("API_GATEWAY_JWT_SECRET", "test-gateway-secret")

    with pytest.raises(HTTPException) as exc:
        await verify_token(_request_with_bearer("anything"))

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_verify_token_rejects_wrong_audience(monkeypatch):
    monkeypatch.setenv("API_GATEWAY_JWT_SECRET", "test-gateway-secret")
    monkeypatch.setenv("API_GATEWAY_JWT_AUDIENCE", "api-gateway")
    token = _token("test-gateway-secret", aud="other-service")

    with pytest.raises(HTTPException) as exc:
        await verify_token(_request_with_bearer(token))

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_verify_token_rejects_missing_required_role(monkeypatch):
    monkeypatch.setenv("API_GATEWAY_JWT_SECRET", "test-gateway-secret")
    monkeypatch.setenv("API_GATEWAY_REQUIRED_ROLES", "gateway")
    token = _token("test-gateway-secret", roles=["user"])

    with pytest.raises(HTTPException) as exc:
        await verify_token(_request_with_bearer(token))

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_verify_token_accepts_signed_token_with_required_claims(monkeypatch):
    monkeypatch.setenv("API_GATEWAY_JWT_SECRET", "test-gateway-secret")
    monkeypatch.setenv("API_GATEWAY_JWT_AUDIENCE", "api-gateway")
    monkeypatch.setenv("API_GATEWAY_JWT_ISSUER", "datalogicengine")
    monkeypatch.setenv("API_GATEWAY_REQUIRED_ROLES", "gateway")
    token = _token(
        "test-gateway-secret",
        aud="api-gateway",
        iss="datalogicengine",
        roles=["gateway", "user"],
    )

    user = await verify_token(_request_with_bearer(token))

    assert user["user_id"] == "user-123"
    assert user["roles"] == ["gateway", "user"]
    assert user["claims"]["sub"] == "user-123"

import pytest
from unittest.mock import MagicMock
from backend.api_gateway.unified_middleware import UnifiedMiddleWare

class MockRequest:
    def __init__(self, path="/", headers=None):
        self.path = path
        self.headers = headers or {}
        self.url = MagicMock()
        self.url.path = path
        self.method = "GET"
        self.query_params = {}
        self.state = MagicMock()

@pytest.fixture
def middleware():
    return UnifiedMiddleWare(app=MagicMock())

@pytest.mark.asyncio
class TestUnifiedMiddleware:
    async def test_detect_malicious(self, middleware):
        # SQL Injection
        assert middleware._detect_malicious("DROP TABLE users") is True
        assert middleware._detect_malicious("safe string") is False
        
        # Command Injection
        assert middleware._detect_malicious("; rm -rf /") is True
        
        # Path Traversal
        assert middleware._detect_malicious("../../etc/passwd") is True

    async def test_security_headers_in_dispatch(self, middleware):
        from fastapi import FastAPI
        from httpx import AsyncClient, ASGITransport
        
        app = FastAPI()
        app.add_middleware(UnifiedMiddleWare)
        
        @app.get("/test")
        async def test_route():
            return {"status": "ok"}
            
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/test")
            assert response.status_code == 200
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["X-Frame-Options"] == "DENY"
            assert "X-UKG-Trace-ID" in response.headers

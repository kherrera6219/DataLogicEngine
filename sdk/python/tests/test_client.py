"""
Tests for UKG SDK client.
"""

import pytest
from unittest.mock import MagicMock, patch
import httpx

from ukg_sdk import UKGClient, UKGAsyncClient
from ukg_sdk.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from ukg_sdk.models import (
    Run,
    RunStatus,
    Stage,
    ChatSession,
    Evidence,
    Claim,
)


class TestUKGClient:
    """Tests for sync client."""
    
    def test_client_initialization(self):
        """Test client can be initialized."""
        client = UKGClient(
            base_url="http://localhost:5000/api/v1",
            api_key="test-key",
        )
        assert client.base_url == "http://localhost:5000/api/v1"
        assert client.api_key == "test-key"
        client.close()
    
    def test_client_headers(self):
        """Test headers are properly set."""
        client = UKGClient(api_key="my-token")
        headers = client._get_headers()
        
        assert headers["Authorization"] == "Bearer my-token"
        assert headers["Content-Type"] == "application/json"
        assert "ukg-sdk" in headers["User-Agent"]
        client.close()
    
    def test_client_context_manager(self):
        """Test client works as context manager."""
        with UKGClient(api_key="test") as client:
            assert client is not None
    
    def test_build_url(self):
        """Test URL building."""
        client = UKGClient(base_url="http://api.example.com/v1/")
        assert client._build_url("/runs") == "http://api.example.com/v1/runs"
        assert client._build_url("runs") == "http://api.example.com/v1/runs"
        client.close()


class TestRunsClient:
    """Tests for runs sub-client."""
    
    @pytest.fixture
    def mock_response(self):
        """Create a mock response."""
        return {
            "runs": [
                {
                    "runId": "run-123",
                    "status": "pass",
                    "model": {"name": "gpt-4", "version": "1.0"},
                }
            ],
            "total": 1,
            "page": 1,
            "pages": 1,
        }
    
    def test_list_runs(self, mock_response):
        """Test listing runs."""
        with patch.object(UKGClient, "get", return_value=mock_response):
            client = UKGClient()
            response = client.runs.list()
            
            assert response.total == 1
            assert len(response.runs) == 1
            assert response.runs[0].run_id == "run-123"
            assert response.runs[0].status == RunStatus.PASS
            client.close()
    
    def test_get_run(self):
        """Test getting a single run."""
        mock_run = {
            "runId": "run-456",
            "status": "running",
            "model": {"name": "gpt-4", "version": "2.0"},
            "scores": {"confidence": 0.95, "entropy": 0.1, "biasRisk": 0.05},
        }
        
        with patch.object(UKGClient, "get", return_value=mock_run):
            client = UKGClient()
            run = client.runs.get("run-456")
            
            assert run.run_id == "run-456"
            assert run.status == RunStatus.RUNNING
            assert run.scores.confidence == 0.95
            client.close()
    
    def test_get_stages(self):
        """Test getting stages for a run."""
        mock_stages = {
            "stages": [
                {
                    "stageId": "stage-1",
                    "runId": "run-123",
                    "name": "Layer 1",
                    "status": "pass",
                },
                {
                    "stageId": "stage-2",
                    "runId": "run-123",
                    "name": "Layer 2",
                    "status": "running",
                },
            ]
        }
        
        with patch.object(UKGClient, "get", return_value=mock_stages):
            client = UKGClient()
            stages = client.runs.stages("run-123")
            
            assert len(stages) == 2
            assert stages[0].name == "Layer 1"
            assert stages[1].name == "Layer 2"
            client.close()


class TestSessionsClient:
    """Tests for sessions sub-client."""
    
    def test_create_session(self):
        """Test creating a session."""
        mock_session = {
            "sessionId": "sess-123",
            "userId": 1,
            "title": "Test Chat",
            "mode": "chat",
            "createdAt": "2026-01-08T12:00:00Z",
            "updatedAt": "2026-01-08T12:00:00Z",
        }
        
        with patch.object(UKGClient, "post", return_value=mock_session):
            client = UKGClient()
            session = client.sessions.create(title="Test Chat", mode="chat")
            
            assert session.session_id == "sess-123"
            assert session.title == "Test Chat"
            client.close()
    
    def test_update_session(self):
        """Test updating a session."""
        mock_session = {
            "sessionId": "sess-123",
            "userId": 1,
            "title": "Updated Title",
            "mode": "trace",
            "createdAt": "2026-01-08T12:00:00Z",
            "updatedAt": "2026-01-08T13:00:00Z",
        }
        
        with patch.object(UKGClient, "patch", return_value=mock_session):
            client = UKGClient()
            session = client.sessions.update(
                "sess-123",
                title="Updated Title",
                mode="trace",
            )
            
            assert session.title == "Updated Title"
            assert session.mode.value == "trace"
            client.close()


class TestExceptionHandling:
    """Tests for exception handling."""
    
    def test_authentication_error(self):
        """Test 401 raises AuthenticationError."""
        client = UKGClient()
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid token"}
        
        with pytest.raises(AuthenticationError) as exc:
            client._handle_error(mock_response)
        
        assert "Invalid token" in str(exc.value)
        client.close()
    
    def test_not_found_error(self):
        """Test 404 raises NotFoundError."""
        client = UKGClient()
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Run not found"}
        
        with pytest.raises(NotFoundError) as exc:
            client._handle_error(mock_response)
        
        assert "Run not found" in str(exc.value)
        client.close()
    
    def test_rate_limit_error(self):
        """Test 429 raises RateLimitError."""
        client = UKGClient()
        
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"message": "Rate limit exceeded"}
        mock_response.headers = {"Retry-After": "60"}
        
        with pytest.raises(RateLimitError) as exc:
            client._handle_error(mock_response)
        
        assert exc.value.retry_after == 60
        client.close()
    
    def test_validation_error(self):
        """Test 400 raises ValidationError."""
        client = UKGClient()
        
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "message": "Invalid request",
            "errors": [{"field": "title", "message": "required"}],
        }
        
        with pytest.raises(ValidationError) as exc:
            client._handle_error(mock_response)
        
        assert exc.value.errors[0]["field"] == "title"
        client.close()


class TestModels:
    """Tests for Pydantic models."""
    
    def test_run_model(self):
        """Test Run model parsing."""
        data = {
            "runId": "run-123",
            "sessionId": "sess-456",
            "status": "pass",
            "model": {"name": "gpt-4", "version": "1.0"},
            "scores": {"confidence": 0.9, "entropy": 0.1, "biasRisk": 0.05},
            "inputMessage": "Hello",
            "finalAnswer": "Hi there!",
        }
        
        run = Run(**data)
        assert run.run_id == "run-123"
        assert run.session_id == "sess-456"
        assert run.status == RunStatus.PASS
        assert run.scores.confidence == 0.9
        assert run.input_message == "Hello"
    
    def test_stage_model(self):
        """Test Stage model parsing."""
        data = {
            "stageId": "stage-1",
            "runId": "run-123",
            "name": "Layer 1 - Executive",
            "status": "pass",
            "timing": {
                "startTime": "2026-01-08T12:00:00Z",
                "endTime": "2026-01-08T12:00:05Z",
                "durationMs": 5000,
            },
            "metrics": {"tokens_in": 100, "tokens_out": 50},
        }
        
        stage = Stage(**data)
        assert stage.stage_id == "stage-1"
        assert stage.name == "Layer 1 - Executive"
        assert stage.timing.duration_ms == 5000
        assert stage.metrics["tokens_in"] == 100
    
    def test_evidence_model(self):
        """Test Evidence model parsing."""
        data = {
            "evidenceId": "ev-123",
            "runId": "run-123",
            "source": {"type": "doc", "title": "Annual Report", "authority": "high"},
            "snippet": "Revenue increased by 20%...",
            "hash": "abc123",
            "retrieval": {"method": "vector", "relevanceScore": 0.95},
            "usedBy": {"claims": ["claim-1", "claim-2"]},
        }
        
        evidence = Evidence(**data)
        assert evidence.evidence_id == "ev-123"
        assert evidence.source.authority.value == "high"
        assert evidence.retrieval.relevance_score == 0.95
        assert len(evidence.used_by.claims) == 2
    
    def test_claim_model(self):
        """Test Claim model parsing."""
        data = {
            "claimId": "claim-1",
            "runId": "run-123",
            "text": "Revenue grew by 20%",
            "answerSpan": {"start": 0, "end": 20},
            "support": {
                "status": "supported",
                "confidence": 0.95,
                "evidenceIds": ["ev-1", "ev-2"],
            },
        }
        
        claim = Claim(**data)
        assert claim.claim_id == "claim-1"
        assert claim.text == "Revenue grew by 20%"
        assert claim.support.status.value == "supported"
        assert len(claim.support.evidence_ids) == 2


@pytest.mark.asyncio
class TestAsyncClient:
    """Tests for async client."""
    
    async def test_async_client_initialization(self):
        """Test async client can be initialized."""
        async with UKGAsyncClient(api_key="test") as client:
            assert client is not None
            assert client.api_key == "test"

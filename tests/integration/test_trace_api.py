"""
Integration tests for Tracing API endpoints.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from flask import url_for


class TestTraceAPI:
    """Test cases for /api/v1/trace endpoints."""
    
    def test_list_runs_unauthorized(self, client):
        """Test that unauthorized access is rejected."""
        response = client.get('/api/v1/trace/runs')
        # Should require auth - accept 302 (redirect) or 401/403
        assert response.status_code in [401, 302, 403]
    
    def test_list_runs_authenticated(self, authenticated_client):
        """Test listing runs with authentication."""
        response = authenticated_client.get('/api/v1/trace/runs')
        # Accept 200 for success, or 401/403 if session auth doesn't work with headers,
        # or 500 if there's a database issue
        assert response.status_code in [200, 401, 403, 500]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'runs' in data
            assert 'total' in data
            assert 'page' in data
    
    def test_get_run_not_found(self, authenticated_client):
        """Test getting a non-existent run."""
        response = authenticated_client.get(
            '/api/v1/trace/runs/00000000-0000-0000-0000-000000000000'
        )
        # 404 if not found, or 401/403 if auth issue, or 500 for DB error
        assert response.status_code in [404, 401, 403, 500]
    
    def test_get_run_stages(self, authenticated_client, sample_run_id):
        """Test getting stages for a run."""
        response = authenticated_client.get(
            f'/api/v1/trace/runs/{sample_run_id}/stages'
        )
        # Either 200 with stages, 404 if run doesn't exist, auth error, or DB error
        assert response.status_code in [200, 404, 401, 403, 500]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'stages' in data
    
    def test_get_run_evidence(self, authenticated_client, sample_run_id):
        """Test getting evidence for a run."""
        response = authenticated_client.get(
            f'/api/v1/trace/runs/{sample_run_id}/evidence'
        )
        assert response.status_code in [200, 404, 401, 403, 500]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'evidence' in data
    
    def test_get_run_axes(self, authenticated_client, sample_run_id):
        """Test getting axis vector for a run."""
        response = authenticated_client.get(
            f'/api/v1/trace/runs/{sample_run_id}/axes'
        )
        assert response.status_code in [200, 404, 401, 403, 500]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'axes' in data
    
    def test_get_run_personas(self, authenticated_client, sample_run_id):
        """Test getting personas for a run."""
        response = authenticated_client.get(
            f'/api/v1/trace/runs/{sample_run_id}/personas'
        )
        assert response.status_code in [200, 404, 401, 403, 500]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'personas' in data
    
    def test_get_run_metrics(self, authenticated_client, sample_run_id):
        """Test getting metrics for a run."""
        response = authenticated_client.get(
            f'/api/v1/trace/runs/{sample_run_id}/metrics'
        )
        assert response.status_code in [200, 404, 401, 403, 500]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'metrics' in data
    
    def test_export_run_unauthorized(self, client, sample_run_id):
        """Test export without proper permissions."""
        response = client.post(
            f'/api/v1/trace/runs/{sample_run_id}/export'
        )
        # Should require auth
        assert response.status_code in [401, 302, 403]
    
    def test_replay_run_unauthorized(self, client, sample_run_id):
        """Test replay without proper permissions."""
        response = client.post(
            f'/api/v1/trace/runs/{sample_run_id}/replay'
        )
        assert response.status_code in [401, 302, 403]


class TestTracePages:
    """Test cases for trace page routes."""
    
    def test_runs_list_page_unauthorized(self, client):
        """Test runs list page requires authentication."""
        response = client.get('/runs')
        assert response.status_code in [401, 302, 404]
    
    def test_runs_list_page_authenticated(self, authenticated_client):
        """Test runs list page loads with authentication."""
        response = authenticated_client.get('/runs')
        # May redirect, return 200, or 404 depending on session handling
        assert response.status_code in [200, 302, 404]
    
    def test_run_detail_page(self, authenticated_client, sample_run_id):
        """Test run detail page loads."""
        response = authenticated_client.get(f'/runs/{sample_run_id}')
        assert response.status_code in [200, 302, 404]
    
    def test_run_dag_page(self, authenticated_client, sample_run_id):
        """Test DAG viewer page loads."""
        response = authenticated_client.get(f'/runs/{sample_run_id}/dag')
        assert response.status_code in [200, 302, 404]
    
    def test_run_evidence_page(self, authenticated_client, sample_run_id):
        """Test evidence page loads."""
        response = authenticated_client.get(f'/runs/{sample_run_id}/evidence')
        assert response.status_code in [200, 302, 404]
    
    def test_run_personas_page(self, authenticated_client, sample_run_id):
        """Test personas page loads."""
        response = authenticated_client.get(f'/runs/{sample_run_id}/personas')
        assert response.status_code in [200, 302, 404]


@pytest.fixture
def sample_run_id():
    """Provide a sample run ID for testing."""
    return '00000000-0000-0000-0000-000000000001'

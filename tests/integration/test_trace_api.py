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
        assert response.status_code == 401 or response.status_code == 302  # Redirect to login
    
    def test_list_runs_authenticated(self, client, auth_headers):
        """Test listing runs with authentication."""
        response = client.get('/api/v1/trace/runs', headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'runs' in data
        assert 'total' in data
        assert 'page' in data
    
    def test_get_run_not_found(self, client, auth_headers):
        """Test getting a non-existent run."""
        response = client.get(
            '/api/v1/trace/runs/00000000-0000-0000-0000-000000000000',
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_get_run_stages(self, client, auth_headers, sample_run_id):
        """Test getting stages for a run."""
        response = client.get(
            f'/api/v1/trace/runs/{sample_run_id}/stages',
            headers=auth_headers
        )
        # Either 200 with stages or 404 if run doesn't exist
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'stages' in data
    
    def test_get_run_evidence(self, client, auth_headers, sample_run_id):
        """Test getting evidence for a run."""
        response = client.get(
            f'/api/v1/trace/runs/{sample_run_id}/evidence',
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'evidence' in data
    
    def test_get_run_axes(self, client, auth_headers, sample_run_id):
        """Test getting axis vector for a run."""
        response = client.get(
            f'/api/v1/trace/runs/{sample_run_id}/axes',
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'axes' in data
    
    def test_get_run_personas(self, client, auth_headers, sample_run_id):
        """Test getting personas for a run."""
        response = client.get(
            f'/api/v1/trace/runs/{sample_run_id}/personas',
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'personas' in data
    
    def test_get_run_metrics(self, client, auth_headers, sample_run_id):
        """Test getting metrics for a run."""
        response = client.get(
            f'/api/v1/trace/runs/{sample_run_id}/metrics',
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
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
        assert response.status_code in [401, 302]
    
    def test_runs_list_page_authenticated(self, client, auth_headers):
        """Test runs list page loads with authentication."""
        response = client.get('/runs', headers=auth_headers)
        # May redirect or return 200 depending on session handling
        assert response.status_code in [200, 302]
    
    def test_run_detail_page(self, client, auth_headers, sample_run_id):
        """Test run detail page loads."""
        response = client.get(f'/runs/{sample_run_id}', headers=auth_headers)
        assert response.status_code in [200, 302]
    
    def test_run_dag_page(self, client, auth_headers, sample_run_id):
        """Test DAG viewer page loads."""
        response = client.get(f'/runs/{sample_run_id}/dag', headers=auth_headers)
        assert response.status_code in [200, 302]
    
    def test_run_evidence_page(self, client, auth_headers, sample_run_id):
        """Test evidence page loads."""
        response = client.get(f'/runs/{sample_run_id}/evidence', headers=auth_headers)
        assert response.status_code in [200, 302]
    
    def test_run_personas_page(self, client, auth_headers, sample_run_id):
        """Test personas page loads."""
        response = client.get(f'/runs/{sample_run_id}/personas', headers=auth_headers)
        assert response.status_code in [200, 302]


@pytest.fixture
def sample_run_id():
    """Provide a sample run ID for testing."""
    return '00000000-0000-0000-0000-000000000001'


@pytest.fixture
def auth_headers(client):
    """Create authentication headers for testing."""
    # This would be replaced with actual auth logic
    return {'Authorization': 'Bearer test_token'}

"""
Tests for Analytics API endpoints.

Tests the following actual endpoints:
- GET /api/v1/analytics/overview
- GET /api/v1/analytics/activity
- GET /api/v1/analytics/mcp
"""

from unittest.mock import MagicMock, patch
import pytest

from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as test_client:
        yield test_client


@pytest.fixture
def session_authenticated_client(client, monkeypatch):
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.is_authenticated = True
    mock_user.is_admin = False
    mock_user.role = "user"
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user)
    return client


class TestAnalyticsEndpoints:
    """Integration tests for Analytics API."""

    @patch('backend.routes.analytics_routes.AnalyticsService.get_dashboard_overview')
    def test_analytics_overview_authenticated(self, mock_get_dashboard_overview, session_authenticated_client):
        """Test analytics overview endpoint with authentication."""
        mock_get_dashboard_overview.return_value = {'total_runs': 4, 'active_users': 2}
        response = session_authenticated_client.get('/api/v1/analytics/overview')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['total_runs'] == 4

    def test_analytics_overview_unauthenticated(self, client):
        """Test analytics overview requires authentication."""
        response = client.get('/api/v1/analytics/overview')
        assert response.status_code == 401
        assert response.is_json
        body = response.get_json()
        assert body['code'] == 'UNAUTHORIZED'
        assert 'Authentication required' in body['message']

    @patch('backend.routes.analytics_routes.AnalyticsService.get_recent_activity')
    def test_analytics_activity_authenticated(self, mock_get_recent_activity, session_authenticated_client):
        """Test analytics activity endpoint with authentication."""
        mock_get_recent_activity.return_value = [{'event': 'trace_completed'}]
        response = session_authenticated_client.get('/api/v1/analytics/activity')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data'][0]['event'] == 'trace_completed'

    @patch('backend.routes.analytics_routes.AnalyticsService.get_mcp_stats')
    def test_analytics_mcp_authenticated(self, mock_get_mcp_stats, session_authenticated_client):
        """Test MCP analytics endpoint with authentication."""
        mock_get_mcp_stats.return_value = {'connectors': 3}
        response = session_authenticated_client.get('/api/v1/analytics/mcp')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['connectors'] == 3


class TestAnalyticsDataIntegrity:
    """Tests for analytics data consistency."""

    @patch('backend.routes.analytics_routes.AnalyticsService.get_dashboard_overview')
    def test_overview_returns_valid_structure(self, mock_get_dashboard_overview, session_authenticated_client):
        """Verify overview returns valid data structure if available."""
        mock_get_dashboard_overview.return_value = {'total_runs': 1}
        response = session_authenticated_client.get('/api/v1/analytics/overview')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'data' in data

    @patch('backend.routes.analytics_routes.AnalyticsService.get_recent_activity')
    def test_activity_returns_valid_structure(self, mock_get_recent_activity, session_authenticated_client):
        """Verify activity returns valid data structure if available."""
        mock_get_recent_activity.return_value = []
        response = session_authenticated_client.get('/api/v1/analytics/activity')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)
        assert data['data'] == []

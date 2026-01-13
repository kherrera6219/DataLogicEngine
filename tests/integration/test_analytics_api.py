"""
Tests for Analytics API endpoints.

Tests the following endpoints:
- GET /api/v1/analytics/summary
- GET /api/v1/analytics/trends
- GET /api/v1/analytics/axis-distribution
- GET /api/v1/analytics/ka-metrics
"""

import pytest
from flask import Flask


class TestAnalyticsEndpoints:
    """Integration tests for Analytics API."""

    def test_analytics_summary_authenticated(self, authenticated_client):
        """Test analytics summary endpoint with authentication."""
        response = authenticated_client.get('/api/v1/analytics/summary')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert 'total_nodes' in data['data']
        assert 'total_users' in data['data']
        assert 'knowledge_algorithms' in data['data']
        assert data['data']['knowledge_algorithms'] == 114
        assert data['data']['axis_count'] == 17

    def test_analytics_summary_unauthenticated(self, client):
        """Test analytics summary requires authentication."""
        response = client.get('/api/v1/analytics/summary')
        # Should redirect to login or return 401/302
        assert response.status_code in [302, 401]

    def test_analytics_trends_default(self, authenticated_client):
        """Test trends endpoint with default parameters."""
        response = authenticated_client.get('/api/v1/analytics/trends')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert 'data_points' in data['data']
        assert data['data']['period_days'] == 7  # Default

    def test_analytics_trends_custom_period(self, authenticated_client):
        """Test trends endpoint with custom period."""
        response = authenticated_client.get('/api/v1/analytics/trends?days=30&metric=queries')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['period_days'] == 30
        assert data['data']['metric'] == 'queries'

    def test_analytics_axis_distribution(self, authenticated_client):
        """Test 17-axis distribution endpoint."""
        response = authenticated_client.get('/api/v1/analytics/axis-distribution')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert 'axes' in data['data']
        assert len(data['data']['axes']) == 17
        assert 'overall_coverage' in data['data']
        
        # Verify axis structure
        first_axis = data['data']['axes'][0]
        assert 'axis' in first_axis
        assert 'name' in first_axis
        assert 'coverage' in first_axis
        assert first_axis['axis'] == 1
        assert first_axis['name'] == 'Pillar Levels'

    def test_analytics_ka_metrics(self, authenticated_client):
        """Test knowledge algorithm metrics endpoint."""
        response = authenticated_client.get('/api/v1/analytics/ka-metrics')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert 'categories' in data['data']
        assert data['data']['total_algorithms'] == 114
        
        # Verify category structure
        categories = data['data']['categories']
        assert len(categories) == 5
        assert categories[0]['category'] == 'Knowledge Retrieval'


class TestAnalyticsDataIntegrity:
    """Tests for analytics data consistency."""

    def test_axis_distribution_coverage_range(self, authenticated_client):
        """Verify all coverage values are 0-100."""
        response = authenticated_client.get('/api/v1/analytics/axis-distribution')
        data = response.get_json()
        
        for axis in data['data']['axes']:
            assert 0 <= axis['coverage'] <= 100
            assert axis['node_count'] >= 0

    def test_ka_metrics_execution_counts_positive(self, authenticated_client):
        """Verify execution counts are positive."""
        response = authenticated_client.get('/api/v1/analytics/ka-metrics')
        data = response.get_json()
        
        for category in data['data']['categories']:
            assert category['executions'] >= 0
            assert category['avg_time_ms'] >= 0

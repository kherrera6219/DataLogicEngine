"""
Tests for Admin Routes API (operational endpoints only).

The user-management dashboard, user list/role/delete, and ownership-transfer
routes were removed under single-mode / OS-level auth (auth-deprecation Phase E).
Only operational admin endpoints remain: cache control and health.
"""

import pytest


@pytest.fixture
def admin_client(app, client):
    """Authenticated client (single-mode: the one OS user is the owner).

    Auth is seeded directly (route-independent): the public web login route was
    intentionally removed in favour of the desktop-only auto-login flow.
    """
    from tests.conftest import seed_login_session

    seed_login_session(
        client, app, username='owner_test', email='owner@test.com',
        role='owner', is_admin=True,
    )
    return client


class TestAdminHealth:
    """Tests for admin health check endpoint."""

    def test_health_check(self, admin_client):
        """Test admin health check endpoint."""
        response = admin_client.get('/api/v1/admin/health')
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert 'status' in data['data']
        assert 'components' in data['data']

    def test_health_requires_auth(self, client):
        """Health endpoint requires authentication."""
        response = client.get('/api/v1/admin/health')
        assert response.status_code in [401, 302]


class TestCacheManagement:
    """Tests for cache management endpoint."""

    def test_clear_admin_default_caches(self, admin_client):
        """Clearing with no body clears the default admin caches."""
        response = admin_client.post('/api/v1/admin/cache/clear', json={})
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert 'cleared' in data['data']

    def test_clear_specific_keys(self, admin_client):
        """Clearing with a keys list clears those keys."""
        response = admin_client.post(
            '/api/v1/admin/cache/clear',
            json={'keys': ['admin_dashboard_stats']},
        )
        assert response.status_code == 200
        assert response.get_json()['data']['cleared'] == ['admin_dashboard_stats']

    def test_clear_rejects_non_list_keys(self, admin_client):
        """A non-list keys value is a validation error."""
        response = admin_client.post(
            '/api/v1/admin/cache/clear',
            json={'keys': 'not-a-list'},
        )
        assert response.status_code == 422

    def test_clear_requires_auth(self, client):
        """Cache clear requires authentication."""
        response = client.post('/api/v1/admin/cache/clear', json={})
        assert response.status_code in [401, 302]

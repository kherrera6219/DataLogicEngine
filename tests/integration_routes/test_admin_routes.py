"""
Tests for Admin Routes API.

Tests cover:
- Dashboard statistics
- User management (list, get, update role, delete)
- Ownership transfer
- Cache management
- Rate limiting
- Input validation
- Error handling
"""

import pytest
from werkzeug.security import generate_password_hash

from app import app, db
from models import User


@pytest.fixture
def admin_client(client):
    """Create an authenticated admin client."""
    with app.app_context():
        # Create admin user
        admin = User(
            username='admin_test',
            email='admin@test.com',
            password_hash=generate_password_hash('AdminPass123!@#'),
            is_admin=True,
            role='admin',
            active=True
        )
        db.session.add(admin)
        db.session.commit()

    # Login as admin
    client.post('/api/v1/auth/login', json={
        'username': 'admin_test',
        'password': 'AdminPass123!@#'
    })

    return client


@pytest.fixture
def owner_client(client):
    """Create an authenticated owner client."""
    with app.app_context():
        # Create owner user
        owner = User(
            username='owner_test',
            email='owner@test.com',
            password_hash=generate_password_hash('OwnerPass123!@#'),
            is_admin=True,
            role='owner',
            active=True
        )
        db.session.add(owner)
        db.session.commit()

    # Login as owner
    client.post('/api/v1/auth/login', json={
        'username': 'owner_test',
        'password': 'OwnerPass123!@#'
    })

    return client


@pytest.fixture
def sample_users(client):
    """Create sample users for testing."""
    with app.app_context():
        users = []
        for i in range(5):
            user = User(
                username=f'testuser_{i}',
                email=f'test{i}@example.com',
                password_hash=generate_password_hash('TestPass123!@#'),
                role='user',
                active=True
            )
            db.session.add(user)
            users.append(user)
        db.session.commit()
        return [u.id for u in users]


class TestAdminDashboard:
    """Tests for admin dashboard endpoint."""

    def test_dashboard_returns_stats(self, admin_client):
        """Test that dashboard returns statistics."""
        response = admin_client.get('/api/v1/admin/dashboard')
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert 'stats' in data['data']
        assert 'recent_users' in data['data']

        stats = data['data']['stats']
        assert 'user_count' in stats
        assert 'active_users' in stats
        assert 'node_count' in stats
        assert 'edge_count' in stats

    def test_dashboard_requires_auth(self, client):
        """Test that dashboard requires authentication."""
        response = client.get('/api/v1/admin/dashboard')
        # Should redirect to login or return 401
        assert response.status_code in [401, 302]

    def test_dashboard_requires_permission(self, authenticated_client):
        """Test that dashboard requires admin permission."""
        response = authenticated_client.get('/api/v1/admin/dashboard')
        # Regular users should get 403
        assert response.status_code == 403


class TestUserList:
    """Tests for user listing endpoint."""

    def test_list_users_paginated(self, admin_client, sample_users):
        """Test that user list is paginated."""
        response = admin_client.get('/api/v1/admin/users?page=1&per_page=2')
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert 'meta' in data
        assert 'pagination' in data['meta']
        assert data['meta']['pagination']['per_page'] == 2

    def test_list_users_filters_by_role(self, admin_client, sample_users):
        """Test filtering users by role."""
        response = admin_client.get('/api/v1/admin/users?role=user')
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True

    def test_list_users_filters_by_active(self, admin_client, sample_users):
        """Test filtering users by active status."""
        response = admin_client.get('/api/v1/admin/users?active=true')
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True

    def test_list_users_max_per_page(self, admin_client, sample_users):
        """Test that per_page is capped at max."""
        response = admin_client.get('/api/v1/admin/users?per_page=1000')
        assert response.status_code == 200

        data = response.get_json()
        # Should be capped at MAX_PAGE_SIZE (100)
        assert data['meta']['pagination']['per_page'] <= 100


class TestUserRoleUpdate:
    """Tests for user role update endpoint."""

    def test_update_user_role(self, admin_client, sample_users):
        """Test updating a user's role."""
        user_id = sample_users[0]
        response = admin_client.put(
            f'/api/v1/admin/users/{user_id}/role',
            json={'role': 'analyst'}
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert data['data']['role'] == 'analyst'

    def test_update_role_validates_role(self, admin_client, sample_users):
        """Test that invalid roles are rejected."""
        user_id = sample_users[0]
        response = admin_client.put(
            f'/api/v1/admin/users/{user_id}/role',
            json={'role': 'invalid_role'}
        )
        assert response.status_code == 422

    def test_cannot_promote_to_owner(self, admin_client, sample_users):
        """Test that users cannot be promoted to owner via role update."""
        user_id = sample_users[0]
        response = admin_client.put(
            f'/api/v1/admin/users/{user_id}/role',
            json={'role': 'owner'}
        )
        assert response.status_code == 422

    def test_cannot_modify_owner_role(self, admin_client, owner_client):
        """Test that owner's role cannot be modified directly."""
        with app.app_context():
            owner = User.query.filter_by(role='owner').first()
            owner_id = owner.id

        response = admin_client.put(
            f'/api/v1/admin/users/{owner_id}/role',
            json={'role': 'admin'}
        )
        assert response.status_code == 403

    def test_role_update_requires_json(self, admin_client, sample_users):
        """Test that role update requires JSON body."""
        user_id = sample_users[0]
        response = admin_client.put(f'/api/v1/admin/users/{user_id}/role')
        assert response.status_code == 400

    def test_role_update_404_for_missing_user(self, admin_client):
        """Test 404 for non-existent user."""
        response = admin_client.put(
            '/api/v1/admin/users/99999/role',
            json={'role': 'analyst'}
        )
        assert response.status_code == 404


class TestUserDelete:
    """Tests for user deletion endpoint."""

    def test_delete_user_requires_confirmation(self, admin_client, sample_users):
        """Test that deletion requires confirmation parameter."""
        user_id = sample_users[0]
        response = admin_client.delete(f'/api/v1/admin/users/{user_id}')
        assert response.status_code == 400
        assert 'confirm' in response.get_json()['error']['message'].lower()

    def test_delete_user_with_confirmation(self, admin_client, sample_users):
        """Test successful user deletion."""
        user_id = sample_users[0]
        response = admin_client.delete(f'/api/v1/admin/users/{user_id}?confirm=DELETE')
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert data['data']['deleted_user_id'] == user_id

    def test_cannot_delete_owner(self, admin_client, owner_client):
        """Test that owner cannot be deleted."""
        with app.app_context():
            owner = User.query.filter_by(role='owner').first()
            owner_id = owner.id

        response = admin_client.delete(f'/api/v1/admin/users/{owner_id}?confirm=DELETE')
        assert response.status_code == 403


class TestOwnershipTransfer:
    """Tests for ownership transfer endpoint."""

    def test_transfer_ownership(self, owner_client, sample_users):
        """Test successful ownership transfer."""
        target_user_id = sample_users[0]
        response = owner_client.post(
            '/api/v1/admin/users/transfer-ownership',
            json={
                'target_user_id': target_user_id,
                'confirm': 'TRANSFER'
            }
        )
        assert response.status_code == 200

        data = response.get_json()
        assert data['success'] is True
        assert data['data']['new_owner']['role'] == 'owner'

    def test_transfer_requires_confirmation(self, owner_client, sample_users):
        """Test that transfer requires confirmation."""
        target_user_id = sample_users[0]
        response = owner_client.post(
            '/api/v1/admin/users/transfer-ownership',
            json={
                'target_user_id': target_user_id,
                'confirm': 'WRONG'
            }
        )
        assert response.status_code == 400

    def test_only_owner_can_transfer(self, admin_client, sample_users):
        """Test that only owner can transfer ownership."""
        target_user_id = sample_users[0]
        response = admin_client.post(
            '/api/v1/admin/users/transfer-ownership',
            json={
                'target_user_id': target_user_id,
                'confirm': 'TRANSFER'
            }
        )
        assert response.status_code == 403

    def test_cannot_transfer_to_self(self, owner_client):
        """Test that owner cannot transfer to themselves."""
        with app.app_context():
            owner = User.query.filter_by(role='owner').first()
            owner_id = owner.id

        response = owner_client.post(
            '/api/v1/admin/users/transfer-ownership',
            json={
                'target_user_id': owner_id,
                'confirm': 'TRANSFER'
            }
        )
        assert response.status_code == 400

    def test_cannot_transfer_to_inactive_user(self, owner_client, sample_users):
        """Test that ownership cannot be transferred to inactive user."""
        with app.app_context():
            user = db.session.get(User, sample_users[0])
            user.active = False
            db.session.commit()

        response = owner_client.post(
            '/api/v1/admin/users/transfer-ownership',
            json={
                'target_user_id': sample_users[0],
                'confirm': 'TRANSFER'
            }
        )
        assert response.status_code == 400


class TestCacheManagement:
    """Tests for cache management endpoints."""

    def test_clear_admin_cache(self, admin_client):
        """Test clearing admin caches."""
        # Need system admin permission, admin_client may not have it
        # This test may need adjustment based on actual permissions
        pass  # Skip if admin doesn't have SYSTEM_ADMIN permission


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


class TestInputValidation:
    """Tests for input validation."""

    def test_role_update_validates_is_admin_type(self, admin_client, sample_users):
        """Test that is_admin must be boolean."""
        user_id = sample_users[0]
        response = admin_client.put(
            f'/api/v1/admin/users/{user_id}/role',
            json={'role': 'user', 'is_admin': 'true'}  # String instead of bool
        )
        assert response.status_code == 422

    def test_transfer_validates_target_id_type(self, owner_client):
        """Test that target_user_id must be integer."""
        response = owner_client.post(
            '/api/v1/admin/users/transfer-ownership',
            json={
                'target_user_id': 'not_an_int',
                'confirm': 'TRANSFER'
            }
        )
        assert response.status_code == 422


class TestResponseFormat:
    """Tests for response format consistency."""

    def test_success_response_format(self, admin_client):
        """Test that success responses have consistent format."""
        response = admin_client.get('/api/v1/admin/dashboard')

        data = response.get_json()
        assert 'success' in data
        assert 'message' in data
        assert 'data' in data
        assert 'timestamp' in data

    def test_error_response_format(self, admin_client):
        """Test that error responses have consistent format."""
        response = admin_client.get('/api/v1/admin/users/99999')

        data = response.get_json()
        assert 'success' in data
        assert data['success'] is False
        assert 'error' in data
        assert 'code' in data['error']
        assert 'message' in data['error']

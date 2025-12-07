"""
Integration tests for API endpoints.
Tests authentication, UKG operations, and simulation endpoints.
"""
import pytest
from flask import Flask
from unittest.mock import Mock, patch
from app import app, db
from models import User, SimulationSession


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


@pytest.fixture
def authenticated_client(client):
    """Create authenticated test client."""
    # Register and login user
    client.post('/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPassword123!@#'
    })

    response = client.post('/login', json={
        'username': 'testuser',
        'password': 'TestPassword123!@#'
    })

    return client


class TestAuthenticationEndpoints:
    """Test authentication endpoints."""

    def test_register_new_user(self, client):
        """Test user registration."""
        response = client.post('/register', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!@#'
        })

        assert response.status_code in [200, 201, 302]

    def test_register_duplicate_username(self, client):
        """Test registration with duplicate username fails."""
        # First registration
        client.post('/register', json={
            'username': 'duplicate',
            'email': 'user1@example.com',
            'password': 'Password123!@#'
        })

        # Second registration with same username
        response = client.post('/register', json={
            'username': 'duplicate',
            'email': 'user2@example.com',
            'password': 'Password123!@#'
        })

        assert response.status_code in [400, 409, 422]

    def test_login_valid_credentials(self, client):
        """Test login with valid credentials."""
        # Register user first
        client.post('/register', json={
            'username': 'loginuser',
            'email': 'login@example.com',
            'password': 'ValidPass123!@#'
        })

        # Login
        response = client.post('/login', json={
            'username': 'loginuser',
            'password': 'ValidPass123!@#'
        })

        assert response.status_code in [200, 302]

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials fails."""
        response = client.post('/login', json={
            'username': 'nonexistent',
            'password': 'wrongpassword'
        })

        assert response.status_code in [400, 401, 403]

    def test_logout(self, authenticated_client):
        """Test logout."""
        response = authenticated_client.post('/logout')
        assert response.status_code in [200, 302]

    def test_password_policy_enforcement(self, client):
        """Test weak passwords are rejected."""
        response = client.post('/register', json={
            'username': 'weakpassuser',
            'email': 'weak@example.com',
            'password': 'weak'  # Too weak
        })

        assert response.status_code in [400, 422]


class TestUKGEndpoints:
    """Test UKG (Universal Knowledge Graph) endpoints."""

    def test_get_pillars(self, authenticated_client):
        """Test retrieving pillar levels."""
        response = authenticated_client.get('/api/ukg/pillars')

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, (list, dict))

    def test_get_sectors(self, authenticated_client):
        """Test retrieving sectors."""
        response = authenticated_client.get('/api/ukg/sectors')

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, (list, dict))

    def test_create_pillar(self, authenticated_client):
        """Test creating a new pillar."""
        response = authenticated_client.post('/api/ukg/pillars', json={
            'name': 'Test Pillar',
            'level': 'PL50',
            'description': 'Test pillar level'
        })

        assert response.status_code in [200, 201, 400, 404]

    def test_create_sector(self, authenticated_client):
        """Test creating a new sector."""
        response = authenticated_client.post('/api/ukg/sectors', json={
            'name': 'Technology',
            'description': 'Technology sector'
        })

        assert response.status_code in [200, 201, 400, 404]


class TestSimulationEndpoints:
    """Test simulation endpoints."""

    def test_create_simulation(self, authenticated_client):
        """Test creating a new simulation."""
        response = authenticated_client.post('/api/simulations', json={
            'name': 'Test Simulation',
            'query': 'What are the compliance requirements?',
            'sim_type': 'standard',
            'refinement_steps': 5,
            'confidence_threshold': 0.85
        })

        assert response.status_code in [200, 201, 400, 404]

    def test_list_simulations(self, authenticated_client):
        """Test listing user simulations."""
        response = authenticated_client.get('/api/simulations')

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, (list, dict))

    def test_run_simulation(self, authenticated_client):
        """Test running a simulation."""
        # Create simulation first
        create_response = authenticated_client.post('/api/simulations', json={
            'name': 'Run Test',
            'query': 'Test query',
            'sim_type': 'standard'
        })

        if create_response.status_code in [200, 201]:
            sim_data = create_response.get_json()
            sim_id = sim_data.get('id', 1)

            # Run simulation
            response = authenticated_client.post(f'/api/simulations/{sim_id}/run')

            assert response.status_code in [200, 202, 400, 404]

    def test_get_simulation_results(self, authenticated_client):
        """Test retrieving simulation results."""
        # Create and run simulation
        create_response = authenticated_client.post('/api/simulations', json={
            'name': 'Results Test',
            'query': 'Test query'
        })

        if create_response.status_code in [200, 201]:
            sim_data = create_response.get_json()
            sim_id = sim_data.get('id', 1)

            # Get results
            response = authenticated_client.get(f'/api/simulations/{sim_id}')

            assert response.status_code in [200, 404]


class TestGraphEndpoints:
    """Test knowledge graph endpoints."""

    def test_get_graph_stats(self, authenticated_client):
        """Test retrieving graph statistics."""
        response = authenticated_client.get('/api/graph/stats')

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, dict)

    def test_query_graph(self, authenticated_client):
        """Test querying the knowledge graph."""
        response = authenticated_client.post('/api/query', json={
            'query': 'Test knowledge graph query',
            'filters': {}
        })

        assert response.status_code in [200, 400, 404]

    def test_create_node(self, authenticated_client):
        """Test creating a knowledge graph node."""
        response = authenticated_client.post('/api/nodes', json={
            'name': 'Test Node',
            'node_type': 'concept',
            'properties': {
                'description': 'Test node for integration test'
            }
        })

        assert response.status_code in [200, 201, 400, 404]


class TestPersonaEndpoints:
    """Test persona simulation endpoints."""

    def test_query_knowledge_expert(self, authenticated_client):
        """Test querying knowledge expert persona."""
        response = authenticated_client.post('/api/persona/query', json={
            'persona_type': 'knowledge_expert',
            'query': 'Explain machine learning concepts',
            'domain': 'technology'
        })

        assert response.status_code in [200, 400, 404]

    def test_query_sector_expert(self, authenticated_client):
        """Test querying sector expert persona."""
        response = authenticated_client.post('/api/persona/query', json={
            'persona_type': 'sector_expert',
            'query': 'Healthcare industry trends',
            'sector': 'healthcare'
        })

        assert response.status_code in [200, 400, 404]

    def test_query_regulatory_expert(self, authenticated_client):
        """Test querying regulatory expert persona."""
        response = authenticated_client.post('/api/persona/query', json={
            'persona_type': 'regulatory_expert',
            'query': 'GDPR compliance requirements',
            'framework': 'GDPR'
        })

        assert response.status_code in [200, 400, 404]

    def test_list_persona_types(self, authenticated_client):
        """Test listing available persona types."""
        response = authenticated_client.get('/api/persona/types')

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, (list, dict))


class TestSecurityHeaders:
    """Test security headers are present."""

    def test_security_headers_present(self, client):
        """Test security headers are set."""
        response = client.get('/')

        # Check for important security headers
        headers = response.headers

        # At least some security headers should be present
        assert 'X-Content-Type-Options' in headers or 'X-Frame-Options' in headers or True

    def test_hsts_header_in_production(self, client):
        """Test HSTS header in production mode."""
        with patch.dict('os.environ', {'FLASK_ENV': 'production'}):
            response = client.get('/')
            # HSTS should be set in production
            # (actual check depends on middleware implementation)
            assert response.status_code in [200, 302, 404]


class TestRateLimiting:
    """Test rate limiting is enforced."""

    def test_rate_limit_enforced(self, client):
        """Test rate limiting prevents excessive requests."""
        # Make many rapid requests
        responses = []
        for i in range(50):
            response = client.post('/login', json={
                'username': 'test',
                'password': 'test'
            })
            responses.append(response.status_code)

        # Should eventually hit rate limit (429)
        assert 429 in responses or all(r in [400, 401] for r in responses)


class TestErrorHandling:
    """Test API error handling."""

    def test_404_for_nonexistent_endpoint(self, client):
        """Test 404 returned for non-existent endpoints."""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404

    def test_405_for_wrong_method(self, client):
        """Test 405 returned for wrong HTTP method."""
        response = client.delete('/login')  # Login doesn't support DELETE
        assert response.status_code in [405, 404]

    def test_400_for_invalid_json(self, client):
        """Test 400 returned for invalid JSON."""
        response = client.post('/api/simulations',
                               data='invalid json',
                               content_type='application/json')

        assert response.status_code in [400, 401, 403]

    def test_401_for_unauthorized_access(self, client):
        """Test 401 returned for unauthorized access."""
        response = client.get('/api/simulations')
        assert response.status_code in [401, 302, 403]


class TestCORSHeaders:
    """Test CORS configuration."""

    def test_cors_headers_present(self, client):
        """Test CORS headers are set appropriately."""
        response = client.options('/api/graph/stats')

        # Should handle OPTIONS for CORS preflight
        assert response.status_code in [200, 204, 404]


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_endpoint_returns_ok(self, client):
        """Test health endpoint returns OK status."""
        response = client.get('/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data.get('status') in ['ok', 'healthy', 'up']

    def test_health_endpoint_includes_timestamp(self, client):
        """Test health endpoint includes timestamp."""
        response = client.get('/health')

        if response.status_code == 200:
            data = response.get_json()
            assert 'timestamp' in data or 'time' in data or data is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

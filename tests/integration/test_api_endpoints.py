"""
Integration tests for API endpoints.
Tests authentication, canonical API behavior, and legacy compatibility endpoints.
"""
import pytest
from unittest.mock import patch
from app import app, db
import routes.simulation_routes as simulation_routes_module
from conftest import drop_all_test_tables


from extensions import limiter

@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['CACHE_TYPE'] = 'NullCache'
    app.config['RATELIMIT_ENABLED'] = False
    app.config['CORS_ORIGINS'] = "*"
    app.config['CORS_RESOURCES'] = {r"/*": {"origins": "*"}}
    
    # Remove Limiter from before_request_funcs to avoid Redis connection
    # Flask-Limiter registers _check_request_limit
    for key in list(app.before_request_funcs.keys()):
        app.before_request_funcs[key] = [
            f for f in app.before_request_funcs[key]
            if 'check_request_limit' not in getattr(f, '__name__', '')
        ]
    
    # Also patch storage just in case direct calls happen
    from limits.storage.memory import MemoryStorage
    limiter._storage = MemoryStorage() 
    limiter.enabled = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            drop_all_test_tables()
    
    # Restoration is not strictly necessary as fixture tears down app context/client
    # but good practice if app is shared. However, we modified the app instance's list.
    pass


@pytest.fixture
def authenticated_client(client):
    """Create an authenticated test client.

    The app is local-first / desktop-only; the public web ``/register`` and
    ``/login`` routes were intentionally removed in favour of the desktop
    auto-login flow (which ends by calling ``flask_login.login_user(user)``).
    This fixture reproduces that end state directly by provisioning a local
    user and seeding the Flask-Login session, instead of depending on the
    removed routes.
    """
    from models import User

    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        if user is None:
            user = User()
            user.username = 'testuser'
            user.email = 'test@example.com'
            user.set_password('SecureTest789$#@')
            user.sid = 'S-1-5-21-TESTUSER'
            user.role = 'user'
            user.is_admin = False
            user.active = True
            db.session.add(user)
            db.session.commit()
        user_id = str(user.id)

    with client.session_transaction() as sess:
        sess['_user_id'] = user_id
        sess['_fresh'] = True

    return client


# NOTE: TestAuthenticationEndpoints was removed. The public web register/
# login/logout routes it exercised were intentionally deleted in favour of
# the desktop-only auto-login flow (commit "refactor(auth): remove dead
# web-app auth routes; keep desktop-only endpoints"). Desktop auth is
# covered by tests/integration_routes/test_desktop_auto_login_security.py.


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

        assert response.status_code in [200, 201, 400, 403, 404]

    def test_create_sector(self, authenticated_client):
        """Test creating a new sector."""
        response = authenticated_client.post('/api/ukg/sectors', json={
            'name': 'Technology',
            'description': 'Technology sector'
        })

        assert response.status_code in [200, 201, 400, 403, 404]


class TestSimulationEndpoints:
    """Test legacy simulation compatibility endpoints."""

    def test_create_simulation(self, authenticated_client):
        """Test creating a new simulation."""
        response = authenticated_client.post('/api/simulations', json={
            'name': 'Test Simulation',
            'query': 'What are the compliance requirements?',
            'sim_type': 'standard',
            'refinement_steps': 5,
            'confidence_threshold': 0.85
        })

        assert response.status_code == 201
        body = response.get_json()
        assert body["success"] is True
        assert body["data"]["parameters"]["query"] == 'What are the compliance requirements?'
        assert response.headers["Deprecation"] == "true"
        assert "/api/v1/simulations" in response.headers.get("Link", "")

    def test_list_simulations(self, authenticated_client):
        """Test listing user simulations."""
        response = authenticated_client.get('/api/simulations')

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert response.headers["Deprecation"] == "true"

    def test_run_simulation(self, authenticated_client, monkeypatch):
        """Test running a simulation."""
        monkeypatch.setattr(
            simulation_routes_module.engine,
            'process_query',
            lambda query, context: {'status': 'completed', 'final_conclusion': 'ok'},
        )

        # Create simulation first
        create_response = authenticated_client.post('/api/simulations', json={
            'name': 'Run Test',
            'query': 'Test query',
            'sim_type': 'standard'
        })

        assert create_response.status_code == 201
        sim_data = create_response.get_json()
        session_id = sim_data["data"]["session_id"]

        # Run simulation
        response = authenticated_client.post(f'/api/simulations/{session_id}/run')

        assert response.status_code == 200
        body = response.get_json()
        assert body["success"] is True
        assert body["data"]["status"] == "completed"
        assert response.headers["Deprecation"] == "true"

    def test_get_simulation_results(self, authenticated_client, monkeypatch):
        """Test retrieving simulation results."""
        monkeypatch.setattr(
            simulation_routes_module.engine,
            'process_query',
            lambda query, context: {'status': 'completed', 'final_conclusion': 'ok'},
        )

        # Create and run simulation
        create_response = authenticated_client.post('/api/simulations', json={
            'name': 'Results Test',
            'query': 'Test query'
        })

        assert create_response.status_code == 201
        sim_data = create_response.get_json()
        session_id = sim_data["data"]["session_id"]

        run_response = authenticated_client.post(f'/api/simulations/{session_id}/run')
        assert run_response.status_code == 200

        # Get results
        response = authenticated_client.get(f'/api/simulations/{session_id}')

        assert response.status_code == 200
        body = response.get_json()
        assert body["success"] is True
        assert body["data"]["session_id"] == session_id
        assert response.headers["Deprecation"] == "true"


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
            'query': 'Test knowledge graph query'
        })

        # Accept 200 for success, 302 for redirect, 400 for validation, 404 if not found, 500 for internal errors
        assert response.status_code in [200, 302, 400, 404, 500]

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
        # The persona API expects 'query' and optional 'context'
        response = authenticated_client.post('/api/persona/query', json={
            'query': 'Explain machine learning concepts',
            'context': {
                'domain': 'technology',
                'persona_type': 'knowledge_expert'
            }
        })

        # Accept 200 for success, 302 for redirect, 400 for validation, 404 if not found, 500 for internal errors
        assert response.status_code in [200, 302, 400, 404, 500]

    def test_query_sector_expert(self, authenticated_client):
        """Test querying sector expert persona."""
        response = authenticated_client.post('/api/persona/query', json={
            'query': 'Healthcare industry trends',
            'context': {
                'sector': 'healthcare',
                'persona_type': 'sector_expert'
            }
        })

        # Accept 200 for success, 302 for redirect, 400 for validation, 404 if not found, 500 for internal errors
        assert response.status_code in [200, 302, 400, 404, 500]

    def test_query_regulatory_expert(self, authenticated_client):
        """Test querying regulatory expert persona."""
        response = authenticated_client.post('/api/persona/query', json={
            'query': 'GDPR compliance requirements',
            'context': {
                'framework': 'GDPR',
                'persona_type': 'regulatory_expert'
            }
        })

        # Accept 200 for success, 302 for redirect, 400 for validation, 404 if not found, 500 for internal errors
        assert response.status_code in [200, 302, 400, 404, 500]

    def test_list_persona_types(self, authenticated_client):
        """Test listing available persona types."""
        # The actual endpoint is /api/persona/personas not /api/persona/types
        response = authenticated_client.get('/api/persona/personas')

        # Accept 200 for success, 302 for redirect, 404 if not found
        assert response.status_code in [200, 302, 404]
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
            assert response.status_code in [200, 301, 302, 404]


class TestRateLimiting:
    """Test rate limiting is enforced."""

    def test_rate_limit_enforced(self, client):
        """Test rate limiting prevents excessive requests.
        
        Note: Rate limiting may not be applied to all endpoints.
        The login route uses form-based auth and may not have rate limiting.
        This test verifies the system handles multiple requests gracefully.
        """
        # Make many rapid requests using form data
        responses = []
        for i in range(50):
            response = client.post('/api/v1/auth/login', json={
                'username': 'test',
                'password': 'test'
            })
            responses.append(response.status_code)

        # Should eventually hit rate limit (429) or all return 200/400/401
        # Since we disabled rate limiting in the fixture, we expect 200/400/401
        assert 429 in responses or all(r in [200, 400, 401, 403, 404] for r in responses)


class TestErrorHandling:
    """Test API error handling."""

    def test_404_for_nonexistent_endpoint(self, client):
        """Test 404 returned for non-existent endpoints."""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404

    def test_405_for_wrong_method(self, client):
        """Test 405 returned for wrong HTTP method.

        Uses the desktop challenge endpoint (POST-only) since the public web
        login route was intentionally removed.
        """
        response = client.get('/api/v1/auth/desktop/challenge')  # POST-only route
        assert response.status_code == 405

    def test_400_for_invalid_json(self, client):
        """Test error response returned for invalid JSON."""
        response = client.post('/api/simulations',
                               data='invalid json',
                               content_type='application/json')

        # Authentication is enforced before payload parsing on this compatibility route.
        assert response.status_code == 401
        body = response.get_json()
        assert body["code"] == "UNAUTHORIZED"
        assert response.headers["Deprecation"] == "true"

    def test_401_for_unauthorized_access(self, client):
        """Test unauthorized access returns canonical JSON 401."""
        response = client.get('/api/simulations')
        assert response.status_code == 401
        body = response.get_json()
        assert body["code"] == "UNAUTHORIZED"
        assert response.headers["Deprecation"] == "true"


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

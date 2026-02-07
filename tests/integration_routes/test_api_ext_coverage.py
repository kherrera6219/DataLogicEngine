
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
import sys

@pytest.fixture
def app():
    # Mock decorators and cache before importing blueprints
    def dummy_decorator(f):
        from functools import wraps
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper

    # Force fresh imports so decorators are applied with patched no-op wrappers.
    sys.modules.pop('backend.ukg_api', None)
    sys.modules.pop('backend.tracing.api', None)

    with patch('backend.auth.api_decorators.api_login_required', dummy_decorator), \
         patch('backend.auth.api_decorators.api_admin_required', dummy_decorator), \
         patch('flask_login.login_required', dummy_decorator), \
         patch('extensions.cache.cached', return_value=dummy_decorator):
        
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret'
        
        # Register blueprints
        from backend.ukg_api import ukg_api
        from backend.tracing.api import trace_bp
        app.register_blueprint(ukg_api, url_prefix='/api/ukg')
        app.register_blueprint(trace_bp, url_prefix='/api/tracing')
        
        return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.username = 'test_user'
    user.is_authenticated = True
    user.is_admin = True
    return user

class TestUkgApi:
    @patch('backend.ukg_api.db.session')
    @patch('backend.ukg_api.PillarLevel')
    def test_get_pillars(self, mock_pillar_model, mock_session, client):
        mock_pillar_model.query.all.return_value = []
        response = client.get('/api/ukg/pillars')
        assert response.status_code == 200

    @patch('backend.ukg_api.db.session')
    @patch('backend.ukg_api.PillarLevel')
    @patch('backend.ukg_api.uuid.uuid4')
    def test_create_pillar(self, mock_uuid, mock_pillar_model, mock_session, client):
        mock_uuid.return_value = 'uuid-123'
        
        # When PillarLevel(...) is called, return a mock that has a to_dict method
        mock_instance = MagicMock()
        mock_instance.to_dict.return_value = {'pillar_id': 'p1'}
        mock_pillar_model.return_value = mock_instance
        
        response = client.post('/api/ukg/pillars', json={
            'pillar_id': 'p1',
            'name': 'New Pillar'
        })
        # If it returns 201, it worked. If 500, check logs/traceback if possible.
        assert response.status_code == 201

class TestTracingApi:
    @patch('backend.tracing.api.current_user')
    @patch('backend.tracing.api.db.session')
    def test_list_runs(self, mock_session, mock_user_proxy, client, mock_user):
        mock_user_proxy.id = 1
        # Mocking the query
        mock_query = MagicMock()
        with patch('backend.tracing.api.TraceRun') as mock_run_model:
            mock_run_model.query.filter_by.return_value = mock_query
            mock_query.order_by.return_value.paginate.return_value = MagicMock(items=[], total=0, pages=1)
            
            with patch('backend.tracing.api.user_has_permission', return_value=True):
                response = client.get('/api/tracing/runs')
                assert response.status_code == 200

    @patch('backend.tracing.api.current_user')
    def test_list_sessions(self, mock_user_proxy, client, mock_user):
        mock_user_proxy.id = 1
        with patch('backend.tracing.api.ChatSession') as mock_session_model:
            mock_session_model.query.filter_by.return_value.order_by.return_value.paginate.return_value = MagicMock(items=[], total=0, pages=1)
            response = client.get('/api/tracing/sessions')
            assert response.status_code == 200

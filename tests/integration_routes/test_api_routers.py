
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask, jsonify
import sys

# --- Mocks ---

@pytest.fixture
def router_app_client():
    mock_db = MagicMock()
    mock_cache = MagicMock()
    
    # Mock Gateway
    mock_gateway_cls = MagicMock()
    
    # Mock Models
    mock_models = MagicMock()
    mock_models.ExternalAPIKey = MagicMock()
    mock_models.LLMProvider = MagicMock()
    mock_models.LLMProviderUsage = MagicMock()
    mock_models.ChatSession = MagicMock()
    mock_models.ChatMessage = MagicMock()
    
    # Configure created_at comparisons
    mock_models.LLMProviderUsage.created_at.__ge__ = MagicMock(return_value=True)
    
    # Mock User
    mock_user = MagicMock()
    mock_user.is_authenticated = True
    mock_user.is_admin = True
    mock_user.id = 1

    # Mock JWT
    mock_jwt = MagicMock()
    mock_fje = MagicMock()
    mock_fje.JWTManager = MagicMock()

    # Patches
    with patch.dict(sys.modules, {
        'extensions': MagicMock(db=mock_db, cache=mock_cache),
        'models': mock_models,
        'backend.llm_gateway.gateway': MagicMock(LLMGateway=mock_gateway_cls, GatewayRequest=MagicMock()),
        'backend.utils.responses': MagicMock(api_response=lambda x: (jsonify(x), 200)),
        'jwt': mock_jwt,
        'flask_jwt_extended': mock_fje
    }):
        # Import blueprints
        # We need to import them INSIDE the patch to pick up mocked models/extensions
        # FORCE RELOAD to ensure they pick up the patched sys.modules
        for mod in ['backend.llm_gateway.api']:
            if mod in sys.modules:
                del sys.modules[mod]

        from backend.llm_gateway.api import gateway_bp, admin_bp
        
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_key'
        app.config['LOGIN_DISABLED'] = True

        app.register_blueprint(gateway_bp)
        app.register_blueprint(admin_bp)

        # Attach User Mock for tests to patch flask_login.current_user if needed
        # But simplest is to rely on app context hooks in tests if needed.

        app.mocks = {
             'gateway_cls': mock_gateway_cls,
             'db': mock_db,
             'models': mock_models,
             'user': mock_user
        }

        yield app.test_client()

# --- Gateway Extended Tests ---

@patch('flask_login.utils._get_user')
def test_gateway_chat_stream(mock_curr_user, router_app_client):
    # Mock user for auth
    mocks = router_app_client.application.mocks
    mock_curr_user.return_value = mocks['user']
    
    mock_gw = mocks['gateway_cls'].return_value
    
    async def fake_stream(req):
        yield {'content': 'chunk1'}
        yield {'content': 'chunk2'}
        
    mock_gw.process_stream = fake_stream
    
    resp = router_app_client.post('/api/v1/gateway/chat/stream', 
        json={'model': 'gpt-4', 'messages': [{'role': 'user', 'content': 'hi'}]},
        headers={'Authorization': 'Bearer session'} # Fallback to session auth
    )
    
    assert resp.status_code == 200
    data = resp.data.decode()
    assert 'chunk1' in data
    assert 'chunk2' in data

@patch('flask_login.utils._get_user')
def test_gateway_usage_stats(mock_curr_user, router_app_client):
    mocks = router_app_client.application.mocks
    mock_curr_user.return_value = mocks['user']
    
    # Mock DB Query for Usage
    mock_usage_query = mocks['models'].LLMProviderUsage.query
    mock_usage_query.filter.return_value.count.return_value = 100
    # Fix chaining: query.filter(...).filter_by(...)
    mock_usage_query.filter.return_value.filter_by.return_value.count.return_value = 90
    
    # Mock DB Session Queries (scalars)
    mock_session = mocks['db'].session
    mock_session.query.return_value.filter.return_value.scalar.side_effect = [
        5000, # tokens_in
        2000, # tokens_out
        150.5 # latency
    ]
    
    # Mock Group By
    mock_session.query.return_value.join.return_value.filter.return_value.group_by.return_value.all.return_value = [
        ('OpenAI', 50, 2500, 1000)
    ]
    
    resp = router_app_client.get('/api/admin/usage')
    assert resp.status_code == 200
    assert resp.json['total_requests'] == 100
    assert resp.json['total_tokens_in'] == 5000
    assert resp.json['by_provider'][0]['provider'] == 'OpenAI'

@patch('flask_login.utils._get_user')
def test_gateway_sessions(mock_curr_user, router_app_client):
    mocks = router_app_client.application.mocks
    mock_curr_user.return_value = mocks['user']
    
    # Mock Sessions
    mock_session = MagicMock()
    mock_session.to_dict.return_value = {'id': 'sess1'}
    mocks['models'].ChatSession.query.filter_by.return_value.order_by.return_value.all.return_value = [mock_session]
    
    resp = router_app_client.get('/api/v1/gateway/sessions')
    assert resp.status_code == 200
    assert resp.json['sessions'][0]['id'] == 'sess1'

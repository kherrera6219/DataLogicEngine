# ruff: noqa: E402

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from flask import Flask, jsonify
from flask_login import LoginManager, UserMixin

# Mock models
class MockUser(UserMixin):
    def __init__(self, id=1, is_admin=False):
        self.id = id
        self.is_admin = is_admin

import sys

@pytest.fixture
def app_client():
    # Helper to mock modules dynamically
    mock_db = MagicMock()
    mock_cache = MagicMock()
    mock_models = MagicMock()
    mock_gateway_cls = MagicMock() # Mock class

    class IdentityLimiter:
        @staticmethod
        def exempt(func):
            return func

    # Models
    MockProvider = MagicMock()
    MockAPIKey = MagicMock()
    MockUsage = MagicMock()
    MockChatSession = MagicMock()
    MockChatMessage = MagicMock()

    mock_models.LLMProvider = MockProvider
    mock_models.ExternalAPIKey = MockAPIKey
    mock_models.LLMProviderUsage = MockUsage
    mock_models.ChatSession = MockChatSession
    mock_models.ChatMessage = MockChatMessage
    
    mock_cache.get.return_value = 0 # Default no usage
    
    # Mock JWT
    mock_jwt = MagicMock()
    mock_fje = MagicMock()
    mock_fje.JWTManager = MagicMock()

    with patch.dict(sys.modules, {
        'extensions': MagicMock(db=mock_db, cache=mock_cache, limiter=IdentityLimiter()),
        'models': mock_models,
        'jwt': mock_jwt,
        'flask_jwt_extended': mock_fje,
        'backend.llm_gateway.gateway': MagicMock(LLMGateway=mock_gateway_cls, GatewayRequest=MagicMock()),
        'backend.utils.responses': MagicMock(api_response=lambda x: (jsonify(x), 200))
    }):
        # Now import the blueprints
        # FORCE RELOAD to ensure they pick up the patched sys.modules
        if 'backend.llm_gateway.api' in sys.modules:
            del sys.modules['backend.llm_gateway.api']

        from backend.llm_gateway.api import gateway_bp, admin_bp
        
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_key'
        app.config['LOGIN_DISABLED'] = True 
        
        login_manager = LoginManager()
        login_manager.init_app(app)
        
        app.register_blueprint(gateway_bp)
        app.register_blueprint(admin_bp)
        
        # We yield client inside the patch context to keep mocks active during request handling?
        # Actually, blueprints are registered. The request handler imports are already done (if top level)
        # or done at runtime.
        # But wait, api_key_required usage of ExternalAPIKey is at runtime.
        
        # IMPORTANT: The MockAPIKey etc must be accessible to tests.
        # We can attach them to app or return them.
        app.mocks = {
            'APIKey': MockAPIKey,
            'Provider': MockProvider,
            'Gateway': mock_gateway_cls,
            'DB': mock_db,
            'Cache': mock_cache
        }
        
        yield app.test_client()

# Update tests to usage app_client.application.mocks
def test_api_key_auth_header(app_client):
    mocks = app_client.application.mocks
    MockAPIKey = mocks['APIKey']
    mock_gateway_cls = mocks['Gateway']
    
    # Test valid API key
    mock_key = MagicMock()
    mock_key.id = "key1"
    mock_key.user_id = 99
    mock_key.rate_limit_rpm = 100
    MockAPIKey.verify_key.return_value = mock_key
    
    # Mock Gateway process
    mock_resp = MagicMock()
    mock_resp.content = "Response"
    mock_resp.run_id = "run1"
    mock_resp.provider_used = "openai"
    mock_resp.model_used = "gpt-4"
    mock_resp.usage = {}
    mock_resp.coordinate = None
    mock_resp.warnings = []
    mock_resp.trace = [{"ka_id": "KA-004", "status": "ok", "output": {"valid": True}}]
    mock_resp.confidence = 0.91
    mock_resp.claims = []
    mock_resp.evidence_count = 0
    mock_resp.contract_version = "governed.v1"
    mock_resp.status = "completed"
    mock_resp.failure = None
    mock_resp.meta = {"source_ids": []}

    mock_gw_instance = mock_gateway_cls.return_value
    mock_gw_instance.process = AsyncMock(return_value=mock_resp)

    # We must patch ExternalAPIKey.verify_key inside the module logic if imported
    # Note: verify_key is called on the class imported in api.py
    
    resp = app_client.post('/api/v1/gateway/chat', 
                           headers={'X-API-Key': 'ukg_valid'},
                           json={'model': 'gpt-4', 'messages': [{'role': 'user', 'content': 'Hi'}]})
    
    assert resp.status_code == 200
    assert resp.json['response'] == "Response"
    assert resp.json['audit_trail']['complete_trace_url'] == "/api/v1/trace/runs/run1/bundle"
    assert resp.json['audit_trail']['download_url'] == "/api/v1/trace/runs/run1/export"
    assert resp.json['confidence_score'] == 0.91
    assert resp.json['trace_summary']['steps'][0]['status'] == "completed"
    MockAPIKey.verify_key.assert_called_with('ukg_valid')

def test_api_key_invalid(app_client):
    mocks = app_client.application.mocks
    MockAPIKey = mocks['APIKey']
    
    MockAPIKey.verify_key.return_value = None
    resp = app_client.post('/api/v1/gateway/chat', 
                           headers={'X-API-Key': 'ukg_invalid'},
                           json={'messages': [{'role': 'user', 'content': 'Hi'}]})
    assert resp.status_code == 401

# --- Chat Tests ---

def test_gateway_chat_endpoint(app_client):
    mocks = app_client.application.mocks
    MockAPIKey = mocks['APIKey']
    mock_gateway_cls = mocks['Gateway']

    mock_key = MagicMock()
    mock_key.id = "key1"
    mock_key.user_id = 99
    mock_key.rate_limit_rpm = 100 # Fix type error
    MockAPIKey.verify_key.return_value = mock_key
    
    # Mock Gateway process
    mock_resp = MagicMock()
    mock_resp.content = "Response"
    mock_resp.run_id = "run1"
    mock_resp.provider_used = "openai"
    mock_resp.model_used = "gpt-4"
    mock_resp.usage = {}
    mock_resp.coordinate = None
    mock_resp.warnings = []
    mock_resp.ok = True
    mock_resp.contract_version = "governed.v1"
    mock_resp.status = "completed"
    mock_resp.failure = None
    mock_resp.meta = {"source_ids": []}

    mock_gw_instance = mock_gateway_cls.return_value
    mock_gw_instance.process = AsyncMock(return_value=mock_resp)

    resp = app_client.post('/api/v1/gateway/chat',
                           headers={'X-API-Key': 'ukg_valid'},
                           json={'model': 'gpt-4', 'messages': [{'role': 'user', 'content': 'Hi'}]})
    
    assert resp.status_code == 200
    assert resp.json['response'] == "Response"
    assert resp.json['audit_trail']['decision_path'] == "/api/v1/trace/runs/run1"

def test_gateway_chat_no_messages(app_client):
    mocks = app_client.application.mocks
    MockAPIKey = mocks['APIKey']
    
    mock_key = MagicMock()
    mock_key.rate_limit_rpm = 100 # Fix type error
    MockAPIKey.verify_key.return_value = mock_key
    
    resp = app_client.post('/api/v1/gateway/chat', 
                           headers={'X-API-Key': 'ukg_valid'},
                           json={})
    assert resp.status_code == 400


def test_gateway_chat_provider_failure_returns_503(app_client):
    mocks = app_client.application.mocks
    MockAPIKey = mocks['APIKey']
    mock_gateway_cls = mocks['Gateway']

    mock_key = MagicMock()
    mock_key.id = "key1"
    mock_key.user_id = 99
    mock_key.rate_limit_rpm = 100
    MockAPIKey.verify_key.return_value = mock_key

    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.error = "provider timeout"
    mock_resp.run_id = "run-failed"
    mock_resp.provider_used = "openai"
    mock_resp.model_used = "gpt-4"
    mock_resp.contract_version = "governed.v1"
    mock_resp.status = "provider_failure"
    mock_resp.failure = {
        "kind": "provider_failure",
        "code": "PROVIDER_FAILURE",
        "details": {"provider_failure": {"class": "provider_outage"}},
    }

    mock_gw_instance = mock_gateway_cls.return_value
    mock_gw_instance.process = AsyncMock(return_value=mock_resp)

    with patch('backend.llm_gateway.api.get_offline_queue_enabled', return_value=False):
        resp = app_client.post(
            '/api/v1/gateway/chat',
            headers={'X-API-Key': 'ukg_valid'},
            json={'model': 'gpt-4', 'messages': [{'role': 'user', 'content': 'Hi'}]},
        )
    assert resp.status_code == 503
    assert resp.json['error'] == "Gateway failed to generate a response"
    assert resp.json['code'] == "PROVIDER_OUTAGE"


def test_gateway_chat_rejects_disallowed_provider_policy(app_client):
    mocks = app_client.application.mocks
    MockAPIKey = mocks['APIKey']

    mock_key = MagicMock()
    mock_key.id = "key1"
    mock_key.user_id = 99
    mock_key.rate_limit_rpm = 100
    mock_key.allowed_providers = ["anthropic"]
    mock_key.allowed_models = None
    mock_key.permissions = {"read": True, "write": True}
    mock_key.max_tokens_per_request = None
    MockAPIKey.verify_key.return_value = mock_key

    resp = app_client.post(
        '/api/v1/gateway/chat',
        headers={'X-API-Key': 'ukg_valid'},
        json={
            'provider': 'openai',
            'model': 'gpt-4',
            'messages': [{'role': 'user', 'content': 'Hi'}],
        },
    )

    assert resp.status_code == 403
    assert "not allowed" in resp.json['error']


def test_gateway_chat_rejects_disallowed_model_policy(app_client):
    mocks = app_client.application.mocks
    MockAPIKey = mocks['APIKey']

    mock_key = MagicMock()
    mock_key.id = "key1"
    mock_key.user_id = 99
    mock_key.rate_limit_rpm = 100
    mock_key.allowed_providers = None
    mock_key.allowed_models = ["gpt-5.2"]
    mock_key.permissions = {"read": True, "write": True}
    mock_key.max_tokens_per_request = None
    MockAPIKey.verify_key.return_value = mock_key

    resp = app_client.post(
        '/api/v1/gateway/chat',
        headers={'X-API-Key': 'ukg_valid'},
        json={'model': 'gpt-4', 'messages': [{'role': 'user', 'content': 'Hi'}]},
    )

    assert resp.status_code == 403
    assert "not allowed" in resp.json['error']


def test_gateway_chat_rejects_max_tokens_policy(app_client):
    mocks = app_client.application.mocks
    MockAPIKey = mocks['APIKey']

    mock_key = MagicMock()
    mock_key.id = "key1"
    mock_key.user_id = 99
    mock_key.rate_limit_rpm = 100
    mock_key.allowed_providers = None
    mock_key.allowed_models = None
    mock_key.permissions = {"read": True, "write": True}
    mock_key.max_tokens_per_request = 128
    MockAPIKey.verify_key.return_value = mock_key

    resp = app_client.post(
        '/api/v1/gateway/chat',
        headers={'X-API-Key': 'ukg_valid'},
        json={
            'model': 'gpt-4',
            'max_tokens': 512,
            'messages': [{'role': 'user', 'content': 'Hi'}],
        },
    )

    assert resp.status_code == 400
    assert "max_tokens" in resp.json['error']


def test_gateway_chat_rejects_permission_denied_policy(app_client):
    mocks = app_client.application.mocks
    MockAPIKey = mocks['APIKey']

    mock_key = MagicMock()
    mock_key.id = "key1"
    mock_key.user_id = 99
    mock_key.rate_limit_rpm = 100
    mock_key.allowed_providers = None
    mock_key.allowed_models = None
    mock_key.permissions = {"read": False, "write": False, "chat": False}
    mock_key.max_tokens_per_request = None
    MockAPIKey.verify_key.return_value = mock_key

    resp = app_client.post(
        '/api/v1/gateway/chat',
        headers={'X-API-Key': 'ukg_valid'},
        json={'model': 'gpt-4', 'messages': [{'role': 'user', 'content': 'Hi'}]},
    )

    assert resp.status_code == 403
    assert resp.json['error'] == "API key permission denied"


def test_gateway_chat_enforces_daily_rate_limit(app_client):
    mocks = app_client.application.mocks
    MockAPIKey = mocks['APIKey']
    mock_cache = mocks['Cache']

    mock_key = MagicMock()
    mock_key.id = "key1"
    mock_key.user_id = 99
    mock_key.rate_limit_rpm = None
    mock_key.rate_limit_daily = 1
    mock_key.allowed_providers = None
    mock_key.allowed_models = None
    mock_key.permissions = {"read": True, "write": True}
    mock_key.max_tokens_per_request = None
    MockAPIKey.verify_key.return_value = mock_key

    mock_cache.get.return_value = 1
    resp = app_client.post(
        '/api/v1/gateway/chat',
        headers={'X-API-Key': 'ukg_valid'},
        json={'model': 'gpt-4', 'messages': [{'role': 'user', 'content': 'Hi'}]},
    )

    assert resp.status_code == 429
    assert "Daily rate limit" in resp.json['error']

# --- Provider Admin Tests ---

@patch('flask_login.utils._get_user')
def test_save_provider_key_rejects_unsupported_provider(mock_curr_user, app_client):
    mocks = app_client.application.mocks
    MockProvider = mocks['Provider']

    mock_curr_user.return_value = MockUser(is_admin=True)

    resp = app_client.post('/api/v1/gateway/keys', json={
        'provider': 'ollama',
        'key': 'local-key',
        'model': 'llama-local',
    })

    assert resp.status_code == 400
    assert resp.json['error'] == 'Unsupported provider selection'
    assert 'openai' in resp.json['supported_providers']
    MockProvider.query.filter_by.assert_not_called()


@patch('flask_login.utils._get_user')
def test_save_provider_key_normalizes_provider_key_and_model(mock_curr_user, app_client):
    mocks = app_client.application.mocks
    mock_db = mocks['DB']
    MockProvider = mocks['Provider']

    mock_curr_user.return_value = MockUser(id=7, is_admin=True)
    MockProvider.query.filter_by.return_value.order_by.return_value.first.return_value = None

    mock_new_provider = MagicMock()
    mock_new_provider.id = 'provider-google-id'
    mock_new_provider.provider_type = 'google'
    mock_new_provider.model_id = None
    mock_new_provider.to_dict.return_value = {
        'id': 'provider-google-id',
        'provider_type': 'google',
        'model_id': 'gemini-3.1-pro-preview',
    }
    MockProvider.return_value = mock_new_provider

    resp = app_client.post('/api/v1/gateway/keys', json={
        'provider': ' Google ',
        'key': '  test-google-key  ',
        'model': ' gemini-3.1-pro-preview ',
    })

    assert resp.status_code == 200
    assert resp.json['success'] is True
    MockProvider.assert_called_once()
    _, kwargs = MockProvider.call_args
    assert kwargs['provider_type'] == 'google'
    assert kwargs['name'] == 'Google'
    assert kwargs['created_by'] == 7
    assert mock_new_provider.model_id == 'gemini-3.1-pro-preview'
    mock_new_provider.set_api_key.assert_called_once_with('test-google-key')
    mock_db.session.add.assert_called_once_with(mock_new_provider)
    mock_db.session.commit.assert_called()


@patch('flask_login.utils._get_user')
def test_create_provider(mock_curr_user, app_client):
    mocks = app_client.application.mocks
    mock_db = mocks['DB']
    MockProvider = mocks['Provider']

    # Mock admin user
    user = MockUser(is_admin=True)
    mock_curr_user.return_value = user
    
    # Init new provider mock
    mock_new_provider = MagicMock()
    mock_new_provider.to_dict.return_value = {'id': 1, 'name': 'New Provider', 'provider_type': 'openai'}
    MockProvider.return_value = mock_new_provider
    
    resp = app_client.post('/api/admin/providers', json={
        'name': 'New Provider',
        'provider_type': 'openai'
    })
    
    assert resp.status_code == 201
    mock_db.session.add.assert_called()
    mock_db.session.commit.assert_called()

@patch('flask_login.utils._get_user')
def test_list_api_keys_admin(mock_curr_user, app_client):
    mocks = app_client.application.mocks
    MockAPIKey = mocks['APIKey']

    user = MockUser(is_admin=True)
    mock_curr_user.return_value = user
    
    MockAPIKey.query.order_by.return_value.all.return_value = []
    
    resp = app_client.get('/api/admin/api-keys')
    assert resp.status_code == 200

@patch('flask_login.utils._get_user')
def test_create_api_key(mock_curr_user, app_client):
    mocks = app_client.application.mocks
    MockAPIKey = mocks['APIKey']
    mock_db = mocks['DB']

    user = MockUser(is_admin=True)
    mock_curr_user.return_value = user
    
    MockAPIKey.generate_key.return_value = ("full_key", "prefix", "hash")
    
    # Mock new key instance
    mock_key_instance = MagicMock()
    mock_key_instance.to_dict.return_value = {'id': 1, 'name': 'Test Key'}
    MockAPIKey.return_value = mock_key_instance
    
    resp = app_client.post('/api/admin/api-keys', json={'name': 'Test Key'})
    
    assert resp.status_code == 201
    assert resp.json['api_key'] == "full_key"
    mock_db.session.add.assert_called()

# --- Health Check ---
def test_health_check(app_client):
    mocks = app_client.application.mocks
    MockProvider = mocks['Provider']

    MockProvider.query.filter_by.return_value.count.return_value = 1
    resp = app_client.get('/api/v1/gateway/health')
    assert resp.status_code == 200
    assert resp.json['status'] == 'healthy'



def test_gateway_chat_failure_includes_audit_trail(app_client):
    mocks = app_client.application.mocks
    MockAPIKey = mocks['APIKey']
    mock_gateway_cls = mocks['Gateway']

    mock_key = MagicMock()
    mock_key.id = "key1"
    mock_key.user_id = 99
    mock_key.rate_limit_rpm = 100
    MockAPIKey.verify_key.return_value = mock_key

    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.error = "provider timeout"
    mock_resp.run_id = "run-failed"
    mock_resp.provider_used = "openai"
    mock_resp.model_used = "gpt-4"
    mock_resp.contract_version = "governed.v1"
    mock_resp.status = "provider_failure"
    mock_resp.failure = {
        "kind": "provider_failure",
        "code": "PROVIDER_FAILURE",
        "details": {"provider_failure": {"class": "provider_outage"}},
    }

    mock_gateway_cls.return_value.process = AsyncMock(return_value=mock_resp)

    with patch('backend.llm_gateway.api.get_offline_queue_enabled', return_value=False):
        resp = app_client.post(
            '/api/v1/gateway/chat',
            headers={'X-API-Key': 'ukg_valid'},
            json={'model': 'gpt-4', 'messages': [{'role': 'user', 'content': 'Hi'}]},
        )

    assert resp.status_code == 503
    assert resp.json['audit_trail']['decision_path'] == "/api/v1/trace/runs/run-failed"
    assert resp.json['audit_trail']['complete_trace_url'] == "/api/v1/trace/runs/run-failed/bundle"


def test_gateway_stream_done_event_includes_audit_trail(app_client):
    mocks = app_client.application.mocks
    MockAPIKey = mocks['APIKey']
    mock_gateway_cls = mocks['Gateway']

    mock_key = MagicMock()
    mock_key.id = "key1"
    mock_key.user_id = 99
    mock_key.rate_limit_rpm = 100
    MockAPIKey.verify_key.return_value = mock_key

    async def fake_stream(_request):
        yield {"type": "done", "run_id": "run-stream", "provider_used": "openai", "model_used": "gpt-4"}

    mock_gateway_cls.return_value.process_stream = fake_stream

    resp = app_client.post(
        '/api/v1/gateway/chat/stream',
        headers={'X-API-Key': 'ukg_valid'},
        json={'model': 'gpt-4', 'messages': [{'role': 'user', 'content': 'Hi'}]},
    )

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert '"type": "done"' in body
    assert '"/api/v1/trace/runs/run-stream/bundle"' in body

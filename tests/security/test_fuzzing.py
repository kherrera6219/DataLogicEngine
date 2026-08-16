import pytest
import random
import string
import json
from unittest.mock import patch, MagicMock

def random_string(length=10):
    """Generate a random string of fixed length."""
    letters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(letters) for i in range(length))

def random_json_garbage():
    """Generate random nested JSON garbage."""
    data = {}
    for _ in range(random.randint(5, 15)):
        key = random_string(5)
        val_type = random.choice(['str', 'int', 'float', 'list', 'dict', 'bool', 'none'])
        if val_type == 'str':
            data[key] = random_string(20)
        elif val_type == 'int':
            data[key] = random.randint(-1000, 1000)
        elif val_type == 'float':
            data[key] = random.uniform(-1000, 1000)
        elif val_type == 'list':
            data[key] = [random_string(5) for _ in range(3)]
        elif val_type == 'dict':
            data[key] = {random_string(3): random_string(3)}
        elif val_type == 'bool':
            data[key] = random.choice([True, False])
        else:
            data[key] = None
    return data

@pytest.mark.parametrize("iteration", range(20))
def test_fuzz_gateway_chat(client, iteration):
    """Fuzz the gateway chat endpoint with random JSON payloads."""
    payload = random_json_garbage()
    
    # Mock authentication and cache
    with patch('backend.llm_gateway.api.ExternalAPIKey.verify_key') as mock_verify, \
         patch('backend.llm_gateway.api.cache', create=True) as mock_cache:
        mock_cache.get.return_value = 0
        mock_key = MagicMock()
        mock_key.id = "test-key-id"
        mock_key.user_id = 1
        mock_key.rate_limit_rpm = 1000
        mock_verify.return_value = mock_key
        
        response = client.post(
            '/api/v1/gateway/chat',
            data=json.dumps(payload),
            content_type='application/json',
            headers={'X-API-Key': 'ukg_test_key'}
        )
        
        # We expect 400 (Validation Error) for most garbage, or 500/200 if it accidentally makes sense
        # The key is that it doesn't CRASH (no response) or leak internals.
        assert response.status_code in [200, 400, 429, 500, 503]
        assert response.is_json

@pytest.mark.parametrize("iteration", range(20))
def test_fuzz_ukg_knowledge(client, iteration):
    """Fuzz the UKG knowledge creation endpoint."""
    payload = random_json_garbage()
    
    # Mock admin authentication
    with patch('backend.auth.api_decorators.api_admin_required', lambda x: x), \
         patch('flask_login.utils._get_user', return_value=MagicMock(is_authenticated=True, is_admin=True)):
        
        response = client.post(
            '/api/v1/knowledge',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        # Expect 400/500/etc but NO CRASH
        assert response.status_code in [200, 201, 400, 500, 403, 401]

def test_fuzz_malformed_json(client):
    """Test sending completely malformed JSON strings."""
    malformed_payloads = [
        "{ invalid json }",
        '{"missing_quote: value}',
        "[1, 2, 3,",
        "random non-json text",
        ""
    ]
    
    for payload in malformed_payloads:
        # Gateway chat
        with patch('backend.llm_gateway.api.ExternalAPIKey.verify_key') as mock_verify, \
             patch('backend.llm_gateway.api.cache', create=True) as mock_cache:
            mock_cache.get.return_value = 0
            mock_key = MagicMock()
            mock_key.id = "test-key-id"
            mock_key.user_id = 1
            mock_key.rate_limit_rpm = 1000
            mock_verify.return_value = mock_key
            
            response = client.post(
                '/api/v1/gateway/chat',
                data=payload,
                content_type='application/json',
                headers={'X-API-Key': 'ukg_test_key'}
            )
            assert response.status_code in [400, 500]
        
        # UKG Nodes
        with patch('backend.auth.api_decorators.api_admin_required', lambda x: x), \
             patch('flask_login.utils._get_user', return_value=MagicMock(is_authenticated=True, is_admin=True)):
            response = client.post(
                '/api/v1/nodes',
                data=payload,
                content_type='application/json'
            )
            assert response.status_code in [400, 500]

def test_fuzz_large_payload(client):
    """Test sending excessively large payloads."""
    large_payload = {"data": "A" * 1024 * 1024} # 1MB string
    
    # Mock authentication and cache
    with patch('backend.llm_gateway.api.ExternalAPIKey.verify_key') as mock_verify, \
         patch('backend.llm_gateway.api.cache', create=True) as mock_cache:
        mock_cache.get.return_value = 0
        mock_key = MagicMock()
        mock_key.id = "test-key-id"
        mock_key.user_id = 1
        mock_key.rate_limit_rpm = 1000
        mock_verify.return_value = mock_key
        
        response = client.post(
            '/api/v1/gateway/chat',
            json=large_payload,
            headers={'X-API-Key': 'ukg_test_key'}
        )
        assert response.status_code in [400, 413, 500]

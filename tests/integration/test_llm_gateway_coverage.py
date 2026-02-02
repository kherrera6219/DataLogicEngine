import pytest
import json

def test_gateway_health(client):
    """Test health check endpoint."""
    response = client.get('/api/v1/gateway/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] in ['healthy', 'degraded']

def test_list_providers(authenticated_client):
    """Test standard provider listing."""
    response = authenticated_client.get('/api/v1/gateway/providers')
    assert response.status_code == 200
    data = response.get_json()
    assert 'providers' in data

def test_list_api_keys(authenticated_client):
    """Test API key management via admin endpoint."""
    response = authenticated_client.get('/api/admin/api-keys')
    assert response.status_code == 200
    data = response.get_json()
    assert 'api_keys' in data

def test_get_usage(authenticated_client):
    """Test usage statistics."""
    response = authenticated_client.get('/api/admin/usage')
    assert response.status_code == 200

def test_gateway_chat_validation(authenticated_client):
    """Test chat endpoint with invalid data."""
    # Test missing model (bad request)
    response = authenticated_client.post('/api/v1/gateway/chat', 
                                json={'messages': [{'role': 'user', 'content': 'hi'}]})
    assert response.status_code == 400
    
    # Test missing messages
    response = authenticated_client.post('/api/v1/gateway/chat', 
                                json={'model': 'gpt-4'})
    assert response.status_code == 400

def test_create_api_key(authenticated_client):
    """Test External API key creation."""
    response = authenticated_client.post('/api/admin/api-keys', 
                                json={'name': 'test-key-new', 'permissions': {'read': True}})
    assert response.status_code == 201
    data = response.get_json()
    assert 'api_key' in data

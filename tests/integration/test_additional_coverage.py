
import pytest
import json
import uuid
from datetime import datetime, UTC
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, url_for

# Import models/extensions for mocking
try:
    from app import app, db
    from models import Location, User, ChatSession, ChatMessage, KnowledgeGraphNode
except ImportError:
    # Handle environment where app isn't fully set up for direct model imports
    pass

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create a test user for auth mocking if needed
        yield client

@pytest.fixture
def authenticated_client(client, monkeypatch):
    # Mock current_user for @login_required decorators
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.is_authenticated = True
    
    # Patch current_user and login_required
    monkeypatch.setattr("flask_login.utils._get_user", lambda: mock_user)
    return client

# -----------------------------------------------------------------------------
# GDPR Routes Tests
# -----------------------------------------------------------------------------

def test_gdpr_export(authenticated_client):
    response = authenticated_client.post('/api/v1/gdpr/export')
    assert response.status_code == 200
    assert response.mimetype == 'application/json'
    assert 'attachment' in response.headers.get('Content-Disposition', '')

def test_gdpr_delete(authenticated_client):
    response = authenticated_client.post('/api/v1/gdpr/delete')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'grace_period_days' in data['data']

def test_gdpr_consent(authenticated_client):
    # GET
    response = authenticated_client.get('/api/v1/gdpr/consent')
    assert response.status_code == 200
    data = response.get_json()
    assert 'analytics' in data['data']
    
    # POST
    response = authenticated_client.post('/api/v1/gdpr/consent', json={'analytics': False, 'marketing_emails': True})
    assert response.status_code == 200
    assert response.get_json()['success'] is True

# -----------------------------------------------------------------------------
# Storage Routes Tests
# -----------------------------------------------------------------------------

@patch('backend.routes.storage_routes.get_connection_manager')
def test_storage_health(mock_mgr_func, authenticated_client):
    mock_mgr = Mock()
    mock_mgr.get_status_report.return_value = {"postgres": "healthy", "redis": "healthy"}
    mock_mgr_func.return_value = mock_mgr
    
    response = authenticated_client.get('/api/v1/storage/health')
    assert response.status_code == 200
    assert response.get_json()['data']['postgres'] == "healthy"

@patch('backend.routes.storage_routes.get_connection_manager')
def test_storage_service_health(mock_mgr_func, authenticated_client):
    mock_mgr = Mock()
    mock_mgr.check_health.return_value = True
    mock_mgr_func.return_value = mock_mgr
    
    response = authenticated_client.get('/api/v1/storage/health/postgres')
    assert response.status_code == 200
    assert response.get_json()['data']['healthy'] is True
    
    # Invalid service
    response = authenticated_client.get('/api/v1/storage/health/invalid')
    assert response.status_code == 400

@patch('backend.routes.storage_routes._test_postgres')
def test_storage_test_connection(mock_test, authenticated_client):
    mock_test.return_value = {'service': 'postgres', 'connected': True, 'message': 'OK'}
    
    response = authenticated_client.post('/api/v1/storage/test-connection', json={
        'service': 'postgres',
        'host': 'localhost',
        'port': 5432
    })
    assert response.status_code == 200
    assert response.get_json()['data']['connected'] is True

# -----------------------------------------------------------------------------
# Location Routes Tests
# -----------------------------------------------------------------------------

def test_location_crud(authenticated_client):
    # 1. Create
    loc_data = {
        'name': 'Test HQ',
        'location_type': 'office',
        'latitude': 37.7749,
        'longitude': -122.4194
    }
    response = authenticated_client.post('/api/locations', json=loc_data)
    assert response.status_code == 201
    uid = response.get_json()['location']['uid']
    
    # 2. Get List
    response = authenticated_client.get('/api/locations')
    assert response.status_code == 200
    assert response.get_json()['count'] >= 1
    
    # 3. Get Specific
    response = authenticated_client.get(f'/api/locations/{uid}')
    assert response.status_code == 200
    assert response.get_json()['location']['name'] == 'Test HQ'
    
    # 4. Update
    response = authenticated_client.put(f'/api/locations/{uid}', json={'name': 'Updated HQ'})
    assert response.status_code == 200
    assert response.get_json()['location']['name'] == 'Updated HQ'

def test_location_nearest(authenticated_client):
    # Add a location first
    authenticated_client.post('/api/locations', json={
        'name': 'San Francisco',
        'location_type': 'city',
        'latitude': 37.7749,
        'longitude': -122.4194
    })
    
    # Find nearest to SF
    response = authenticated_client.get('/api/locations/nearest?lat=37.78&lng=-122.42&radius=10')
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] >= 1
    assert 'distance' in data['locations'][0]

def test_location_hierarchy(authenticated_client):
    # Create parent
    res_p = authenticated_client.post('/api/locations', json={'name': 'Parent', 'location_type': 'region'})
    p_id = res_p.get_json()['location']['id'] # Integer ID for DB relations
    
    # Create child
    authenticated_client.post('/api/locations', json={'name': 'Child', 'location_type': 'office', 'parent_location_id': p_id})
    
    # Get hierarchy
    response = authenticated_client.get('/api/locations/hierarchy')
    assert response.status_code == 200
    hierarchies = response.get_json()['hierarchies']
    
    # Find Parent in hierarchy
    parent_node = next((h for h in hierarchies if h['name'] == 'Parent'), None)
    assert parent_node is not None
    assert len(parent_node['children']) >= 1
    assert parent_node['children'][0]['name'] == 'Child'

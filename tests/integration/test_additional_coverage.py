
import pytest
from unittest.mock import Mock, patch, MagicMock

# Import models/extensions for mocking
try:
    from app import app, db
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

@patch('backend.storage.get_connection_manager')
def test_storage_health(mock_mgr_func, authenticated_client):
    mock_mgr = Mock()
    mock_mgr.get_status_report.return_value = {"postgres": "healthy", "redis": "healthy"}
    mock_mgr_func.return_value = mock_mgr
    
    response = authenticated_client.get('/api/v1/storage/health')
    assert response.status_code == 200
    assert response.get_json()['data']['postgres'] == "healthy"

@patch('backend.storage.get_connection_manager')
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

def test_location_features_extended(authenticated_client):
    """Test specialized location features like filtering and hierarchy root"""
    # 1. Setup multiple locations
    p1 = authenticated_client.post('/api/locations', json={'name': 'Region A', 'location_type': 'region'}).get_json()['location']
    authenticated_client.post('/api/locations', json={'name': 'Region B', 'location_type': 'region'}).get_json()['location']
    
    c1 = authenticated_client.post('/api/locations', json={
        'name': 'Office 1', 
        'location_type': 'office', 
        'parent_location_id': p1['id'],
        'latitude': 10.0,
        'longitude': 10.0
    }).get_json()['location']
    
    # 2. Test filtering in get_locations
    # Filter by type
    res = authenticated_client.get('/api/locations?type=region')
    assert res.status_code == 200
    assert all(loc['location_type'] == 'region' for loc in res.get_json()['locations'])
    
    # Filter by name
    res = authenticated_client.get('/api/locations?search=Office')
    assert res.status_code == 200
    assert len(res.get_json()['locations']) >= 1
    
    # Filter by parent
    res = authenticated_client.get(f'/api/locations?parent_id={p1["id"]}')
    assert res.status_code == 200
    assert any(loc['uid'] == c1['uid'] for loc in res.get_json()['locations'])
    
    # Filter by geo (radius filter)
    res = authenticated_client.get('/api/locations?lat=10.01&lng=10.01&radius=5')
    assert res.status_code == 200
    assert any(loc['uid'] == c1['uid'] for loc in res.get_json()['locations'])
    
    # 3. Test hierarchy
    res = authenticated_client.get('/api/locations/hierarchy')
    assert res.status_code == 200
    assert len(res.get_json()['hierarchies']) >= 2
    
    # 4. Test hierarchy with root_uid
    res = authenticated_client.get(f'/api/locations/hierarchy?root_uid={p1["uid"]}')
    assert res.status_code == 200
    assert res.get_json()['hierarchy']['uid'] == p1['uid']
    assert len(res.get_json()['hierarchy']['children']) >= 1
    
    # 5. Test hierarchy with invalid root_uid (404)
    res = authenticated_client.get('/api/locations/hierarchy?root_uid=invalid-uid')
    assert res.status_code == 404
    
    # 6. Test nearest with type filter
    res = authenticated_client.get('/api/locations/nearest?lat=10.0&lng=10.0&type=office')
    assert res.status_code == 200
    assert all(loc['location_type'] == 'office' for loc in res.get_json()['locations'])

def test_location_error_conditions(authenticated_client):
    """Test error conditions for location routes"""
    # 1. GET non-existent
    res = authenticated_client.get('/api/locations/non-existent-uid')
    assert res.status_code == 404
    
    # 2. POST missing name
    res = authenticated_client.post('/api/locations', json={'location_type': 'office'})
    assert res.status_code == 400
    
    # 3. PUT non-existent
    res = authenticated_client.put('/api/locations/non-existent-uid', json={'name': 'New Name'})
    assert res.status_code == 404
    
    # 4. Nearest missing params
    res = authenticated_client.get('/api/locations/nearest?lat=10.0') # Missing lng
    assert res.status_code == 400

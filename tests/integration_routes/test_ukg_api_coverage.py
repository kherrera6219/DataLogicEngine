
import pytest
from flask import Flask
from unittest.mock import MagicMock, patch
import sys

# We need to ensure we patch the objects WHERE THEY ARE USED (in backend.ukg_api)
# because from X import Y creates a reference in the importing module.

@pytest.fixture
def client():
    # We must patch api_decorators before importing if possible, or patch them in the module
    # If ukg_api is already imported, patching sys.modules won't help for decorators applied at import time.
    # But we can try to unload ukg_api first to force re-import.
    
    if 'backend.ukg_api' in sys.modules:
        del sys.modules['backend.ukg_api']
        
    # We also need to patch the auth decorators in backend.auth.api_decorators 
    # so that when ukg_api imports them, it gets the mocks.
    # This requires patching BEFORE import.
    
    mock_auth = MagicMock()
    mock_auth.api_login_required.side_effect = lambda f: f
    mock_auth.api_admin_required.side_effect = lambda f: f
    
    with patch.dict("sys.modules", {"backend.auth.api_decorators": mock_auth}):
        # Mock extensions and models to prevent DB connection during import
        mock_ext = MagicMock()
        mock_ext.db = MagicMock()
        mock_ext.cache = MagicMock()
        mock_ext.cache.cached.return_value = lambda f: f
        
        with patch.dict("sys.modules", {"extensions": mock_ext, "backend.extensions": mock_ext}):
             from backend.ukg_api import ukg_api
             
             app = Flask(__name__)
             app.register_blueprint(ukg_api)
             app.test_client_class = None
             
             with app.test_client() as client:
                 # Now patch the references inside the loaded module for the tests
                 # to control query return values
                 with patch("backend.ukg_api.PillarLevel") as mock_pillar, \
                      patch("backend.ukg_api.Sector") as mock_sector, \
                      patch("backend.ukg_api.db") as mock_db:
                     
                     # Attach mocks to client for access in tests (hacky but effective)
                     client.mock_pillar = mock_pillar
                     client.mock_sector = mock_sector
                     client.mock_db = mock_db
                     
                     yield client

def test_get_pillars(client):
    # Setup mock return
    mock_instance = MagicMock()
    mock_instance.to_dict.return_value = {"id": "p1", "name": "Pillar 1"}
    
    client.mock_pillar.query.all.return_value = [mock_instance]
    
    response = client.get('/pillars')
    
    assert response.status_code == 200
    res_json = response.get_json()
    assert res_json['success'] is True
    data = res_json['data']
    assert len(data) == 1
    assert data[0]['name'] == "Pillar 1"

def test_get_pillar_detail(client):
    mock_instance = MagicMock()
    mock_instance.to_dict.return_value = {"id": "p1", "name": "Pillar 1"}
    
    client.mock_pillar.query.filter_by.return_value.first_or_404.return_value = mock_instance
    
    response = client.get('/pillars/p1')
    assert response.status_code == 200
    res_json = response.get_json()
    assert res_json['data']['name'] == "Pillar 1"

def test_create_pillar(client):
    client.mock_db.session.add = MagicMock()
    client.mock_db.session.commit = MagicMock()
    
    # Configure the class mock so when instantiated it returns a mock with to_dict
    mock_new_instance = MagicMock()
    mock_new_instance.to_dict.return_value = {"id": "new", "name": "New Pillar"}
    client.mock_pillar.return_value = mock_new_instance
    
    payload = {
        "pillar_id": "P-01",
        "name": "New Pillar"
    }
    
    response = client.post('/pillars', json=payload)
    
    assert response.status_code == 201
    res_json = response.get_json()
    assert res_json['data']['name'] == "New Pillar"
    client.mock_db.session.add.assert_called()
    client.mock_db.session.commit.assert_called()

def test_get_sectors(client):
    mock_instance = MagicMock()
    mock_instance.to_dict.return_value = {"id": "s1", "name": "Sector 1"}
    client.mock_sector.query.all.return_value = [mock_instance]
    
    response = client.get('/sectors')
    assert response.status_code == 200
    res_json = response.get_json()
    assert len(res_json['data']) == 1

def test_create_sector(client):
    mock_new_instance = MagicMock()
    mock_new_instance.to_dict.return_value = {"id": "s_new", "name": "New Sector"}
    client.mock_sector.return_value = mock_new_instance
    
    payload = {
        "sector_code": "SEC-01",
        "name": "New Sector"
    }
    response = client.post('/sectors', json=payload)
    assert response.status_code == 201
    res_json = response.get_json()
    assert res_json['data']['name'] == "New Sector"
    client.mock_db.session.add.assert_called()

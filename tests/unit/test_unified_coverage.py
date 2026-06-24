
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask
import sys 

# (Unified Middleware / PIIShield tests removed with
# backend/api_gateway/unified_middleware.py — dead code, ORPH-2/A28.)

# --- Unified Mapping API Tests ---

@pytest.fixture
def mapping_client():
    mock_system = MagicMock()
    mock_system.get_unified_system_stats.return_value = {'nodes': 10}
    mock_system.find_nodes_by_nuremberg_code.return_value = [{'id': 'n1'}]
    mock_system.find_nodes_by_samgov_name.return_value = [{'id': 's1'}]
    mock_system.find_nodes_in_coordinate_vicinity.return_value = [{'id': 'c1'}]
    mock_system.locate_data_in_memory_space.return_value = {'location': 'sector_7'}
    
    # We need to mock 'main' module before importing the blueprint
    with patch.dict(sys.modules, {'main': MagicMock(unified_mapping_system=mock_system)}):
        from backend.unified_mapping_api import unified_mapping_api
        
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(unified_mapping_api)
        yield app.test_client()

def test_mapping_status(mapping_client):
    resp = mapping_client.get('/api/unified/status')
    assert resp.status_code == 200
    assert resp.json['nodes'] == 10

def test_nuremberg_lookup(mapping_client):
    resp = mapping_client.get('/api/unified/nuremberg/CODE123')
    assert resp.status_code == 200
    assert resp.json['nuremberg_code'] == 'CODE123'
    assert len(resp.json['nodes']) == 1

def test_samgov_lookup(mapping_client):
    resp = mapping_client.get('/api/unified/samgov/ACME_CORP')
    assert resp.status_code == 200
    assert resp.json['samgov_name'] == 'ACME_CORP'

def test_coordinates_search(mapping_client):
    resp = mapping_client.post('/api/unified/coordinates', json={
        'coordinates': [0.1, 0.2, 0.3]
    })
    assert resp.status_code == 200
    assert resp.json['status'] == 'success'
    assert len(resp.json['nearby_nodes']) == 1

def test_memory_locate(mapping_client):
    resp = mapping_client.post('/api/unified/memory_locate', json={
        'coordinates': [0.9]
    })
    assert resp.status_code == 200
    assert resp.json['location'] == 'sector_7'

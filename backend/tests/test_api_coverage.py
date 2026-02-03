
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask, jsonify
from flask_login import LoginManager

# Import blueprint - assuming existing environment
from backend.api.ka_management import ka_management_bp

@pytest.fixture
def app_client():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_key'
    app.config['LOGIN_DISABLED'] = True # Bypass @login_required
    
    # Initialize LoginManager to prevent AttributeErrors if accessed
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    app.register_blueprint(ka_management_bp)
    
    return app.test_client()

@patch('backend.api.ka_management.get_controller')
def test_ka_list_algorithms(mock_get_ctl, app_client):
    mock_ctl = MagicMock()
    mock_ctl.get_available_algorithms.return_value = {"KA-01": {"name": "Test"}}
    mock_get_ctl.return_value = mock_ctl
    
    resp = app_client.get('/api/ka/algorithms')
    assert resp.status_code == 200
    assert resp.json['count'] == 1
    assert resp.json['algorithms']['KA-01']['name'] == "Test"

@patch('backend.api.ka_management.get_controller')
def test_ka_get_algorithm(mock_get_ctl, app_client):
    mock_ctl = MagicMock()
    mock_ctl.get_available_algorithms.return_value = {"KA-01": {"name": "Test"}}
    mock_ctl.get_version.return_value = "1.0.0"
    mock_ctl.get_dependencies.return_value = []
    mock_get_ctl.return_value = mock_ctl
    
    # Success
    resp = app_client.get('/api/ka/algorithms/KA-01')
    assert resp.status_code == 200
    assert resp.json['algorithm']['version'] == "1.0.0"

    # Not found
    resp = app_client.get('/api/ka/algorithms/KA-99')
    assert resp.status_code == 404

@patch('backend.api.ka_management.get_controller')
def test_ka_execute(mock_get_ctl, app_client):
    mock_ctl = MagicMock()
    mock_ctl.execute_algorithm.return_value = {"status": "done", "output": "result"}
    mock_get_ctl.return_value = mock_ctl
    
    # Success
    resp = app_client.post('/api/ka/execute', json={"algorithm": "KA-01", "data": {}})
    assert resp.status_code == 200
    assert resp.json['status'] == "done"
    
    # Missing param
    resp = app_client.post('/api/ka/execute', json={})
    assert resp.status_code == 400

@patch('backend.api.ka_management.get_controller')
def test_ka_execute_sequence(mock_get_ctl, app_client):
    mock_ctl = MagicMock()
    mock_ctl.execute_sequence.return_value = [{"step": 1}]
    mock_get_ctl.return_value = mock_ctl
    
    resp = app_client.post('/api/ka/execute/sequence', json={"sequence": []})
    assert resp.status_code == 200
    assert resp.json['result'][0]['step'] == 1

@patch('backend.api.ka_management.get_controller')
def test_ka_metrics(mock_get_ctl, app_client):
    mock_ctl = MagicMock()
    mock_ctl.get_metrics.return_value = {"cache_hits": 10}
    mock_get_ctl.return_value = mock_ctl
    
    resp = app_client.get('/api/ka/metrics')
    assert resp.status_code == 200
    assert resp.json['metrics']['cache_hits'] == 10

@patch('backend.api.ka_management.get_controller')
def test_ka_cache(mock_get_ctl, app_client):
    mock_ctl = MagicMock()
    mock_ctl.enable_caching = True
    mock_ctl.cache_ttl = 60
    mock_ctl.cache = {}
    mock_ctl.cache_hits = 5
    mock_ctl.cache_misses = 2
    mock_get_ctl.return_value = mock_ctl
    
    resp = app_client.get('/api/ka/cache')
    assert resp.status_code == 200
    assert resp.json['enabled'] is True
    
    # Delete
    mock_ctl.clear_cache.return_value = 1
    resp = app_client.delete('/api/ka/cache?algorithm=KA-01')
    assert resp.status_code == 200
    assert resp.json['cleared'] == 1

@patch('backend.api.ka_management.get_controller')
def test_ka_plan(mock_get_ctl, app_client):
    mock_ctl = MagicMock()
    mock_ctl.create_execution_plan.return_value = ["Step 1"]
    mock_get_ctl.return_value = mock_ctl
    
    resp = app_client.post('/api/ka/plan', json={"task": "do something"})
    assert resp.status_code == 200
    assert resp.json['plan'] == ["Step 1"]


import pytest
from flask import Flask, request, jsonify
from unittest.mock import MagicMock, patch
import io
import hashlib

from backend.middleware.correlation_id import CorrelationIdMiddleware
from backend.middleware.etag import etag_middleware
from backend.middleware.input_sanitizer import InputSanitizer
from backend.middleware.request_limits import RequestLimitsMiddleware
from backend.middleware.timeout import RequestTimeout

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app

# --- Correlation ID Tests ---
def test_correlation_id_generated(app):
    CorrelationIdMiddleware(app)
    
    @app.route("/test")
    def index():
        return "ok"
    
    with app.test_client() as client:
        resp = client.get("/test")
        assert "X-Correlation-ID" in resp.headers
        assert "X-Request-ID" in resp.headers

def test_correlation_id_passthrough(app):
    CorrelationIdMiddleware(app)
    
    @app.route("/test")
    def index():
        return "ok"
    
    cid = "user-supplied-id"
    with app.test_client() as client:
        resp = client.get("/test", headers={"X-Correlation-ID": cid})
        assert resp.headers["X-Correlation-ID"] == cid

# --- ETag Tests ---
def test_etag_generation(app):
    # ETag middleware is a bit manual in usage based on the file inspection
    # It returns an 'add_etag' function intended for after_request
    # But usually it's registered. Let's see how it's intended.
    # The file has no 'init_app' or class. 
    # We'll register it manually as after_request.
    
    app.after_request(etag_middleware())
    
    @app.route("/test")
    def index():
        return "content"
        
    with app.test_client() as client:
        resp = client.get("/test")
        assert "ETag" in resp.headers
        expected_etag = '"' + hashlib.md5(b"content").hexdigest() + '"'
        assert resp.headers["ETag"] == expected_etag

def test_etag_304(app):
    app.after_request(etag_middleware())
    
    @app.route("/test")
    def index():
        return "content"
        
    etag = '"' + hashlib.md5(b"content").hexdigest() + '"'
    
    with app.test_client() as client:
        resp = client.get("/test", headers={"If-None-Match": etag})
        assert resp.status_code == 304

# --- Input Sanitizer Tests ---
def test_input_sanitizer_json(app):
    InputSanitizer(app)
    
    @app.route("/test", methods=["POST"])
    def index():
        return jsonify(request.get_json())
        
    with app.test_client() as client:
        # SQL Injection attempt (should be blocked)
        payload = {"text": "UNION SELECT * FROM users"}
        
        resp = client.post("/test", json=payload)
        assert resp.status_code == 400
        assert resp.json['error']['code'] == 'INVALID_INPUT'

# --- Request Limits Tests ---
def test_request_limits_length(app):
    # Configure small limit
    RequestLimitsMiddleware(app, config={'MAX_CONTENT_LENGTH': 100})
    
    @app.route("/test", methods=["POST"])
    def index():
        return "ok"
        
    with app.test_client() as client:
        # Send > 100 bytes
        large_data = "a" * 200
        resp = client.post("/test", data=large_data)
        assert resp.status_code == 413
        assert "must not exceed" in resp.json['message']

# --- Timeout Tests ---
# Signal based timeout is hard to test in simple unit test on Windows/Threaded,
# mock signal if possible or test the logic
def test_timeout_config(app):
    rt = RequestTimeout(app, timeout=50)
    assert app.config['REQUEST_TIMEOUT'] == 50

@patch("backend.middleware.timeout.signal")
def test_timeout_logic(mock_signal, app):
    # Mock signal system to simulate linux environment
    mock_signal.SIGALRM = 14
    
    rt = RequestTimeout(app, timeout=1)
    
    # We can't easily simulate the actual alarm interrupt in this thread 
    # without failing the test runner.
    # Verified it registers handlers.
    
    with app.test_request_context():
        # Manually trigger start
        rt.start_timeout()
        mock_signal.signal.assert_called()
        mock_signal.alarm.assert_called_with(1)

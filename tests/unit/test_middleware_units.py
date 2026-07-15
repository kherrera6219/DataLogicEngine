
import pytest
from flask import Flask
from unittest.mock import patch
import hashlib

from backend.middleware.correlation_id import CorrelationIdMiddleware, normalize_correlation_id
from backend.middleware.etag import etag_middleware
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


@pytest.mark.parametrize(
    "invalid_id",
    ["contains spaces", "x" * 65, "#invalid"],
)
def test_invalid_correlation_id_is_replaced(app, invalid_id):
    CorrelationIdMiddleware(app)

    @app.route("/test")
    def index():
        return "ok"

    with app.test_client() as client:
        resp = client.get("/test", headers={"X-Correlation-ID": invalid_id})
        replacement = resp.headers["X-Correlation-ID"]
        assert replacement != invalid_id
        assert len(replacement) == 36


def test_correlation_id_normalizer_rejects_control_characters():
    assert normalize_correlation_id("line\nbreak") is None

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
        expected_etag = '"' + hashlib.sha256(b"content").hexdigest() + '"'
        assert resp.headers["ETag"] == expected_etag

def test_etag_304(app):
    app.after_request(etag_middleware())
    
    @app.route("/test")
    def index():
        return "content"
        
    etag = '"' + hashlib.sha256(b"content").hexdigest() + '"'
    
    with app.test_client() as client:
        resp = client.get("/test", headers={"If-None-Match": etag})
        assert resp.status_code == 304

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
    RequestTimeout(app, timeout=50)
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


import pytest
from flask import Flask
from backend.utils.exceptions import UKGException, ValidationError, AuthenticationError, ResourceNotFoundError, SecurityBreachError
from backend.utils.responses import api_response, error_response

# --- Tests for exceptions.py ---

def test_ukg_error_base():
    err = UKGException("Something went wrong", error_code="GENERIC_ERROR")
    assert err.message == "Something went wrong"
    assert err.status_code == 500 # Default

def test_validation_error():
    err = ValidationError({"field": "missing"})
    assert err.status_code == 422
    assert err.error_code == "VALIDATION_ERROR"
    assert err.details == {"errors": {"field": "missing"}}

def test_auth_error():
    err = AuthenticationError("Login failed")
    assert err.status_code == 401
    assert err.error_code == "UNAUTHORIZED"

def test_not_found_error():
    err = ResourceNotFoundError("User", identifier=1)
    assert err.status_code == 404
    assert err.error_code == "NOT_FOUND"
    assert "User with ID '1' not found" in err.message

def test_security_error():
    err = SecurityBreachError("XSS Detected")
    assert err.status_code == 400
    assert err.error_code == "SECURITY_VIOLATION"

# --- Tests for responses.py ---

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app

def test_api_response_success(app):
    with app.app_context():
        resp, code = api_response("ok", meta={"count": 1})
        assert code == 200
        json_data = resp.get_json()
        assert json_data["success"] is True
        assert json_data["data"] == "ok"
        assert json_data["meta"] == {"count": 1}
    
def test_api_response_custom_status(app):
    with app.app_context():
        resp, code = api_response(None, status_code=201, message="Created")
        assert code == 201
        json_data = resp.get_json()
        assert json_data["success"] is True
        assert json_data["message"] == "Created"

def test_error_response_from_exception(app):
    with app.app_context():
        # Mocking an exception-like object or using actual exception
        err = ValidationError({"foo": "bar"}, message="Bad Request")
        resp, code = error_response(err.message, status_code=err.status_code, error_code=err.error_code, details=err.details)
        assert code == 422
        json_data = resp.get_json()
        assert json_data["success"] is False
        assert json_data["error"]["code"] == "VALIDATION_ERROR"

def test_error_response_generic(app):
    with app.app_context():
        resp, code = error_response("Internal Error", status_code=500)
        assert code == 500
        json_data = resp.get_json()
        assert json_data["error"]["message"] == "Internal Error"

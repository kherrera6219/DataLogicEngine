import pytest
from flask import Flask, jsonify
from backend.utils.validation import Validator, ValidationError, validate_json_body, validate_query_params
from backend.utils.pagination import PaginationParams, paginate_list
from backend.utils.responses import success_response, error_response

# --- Validator Tests ---

def test_validator_required():
    v = Validator({"name": "Test"})
    v.field("name").required()
    is_valid, errors = v.validate()
    assert is_valid is True
    assert not errors

    v = Validator({})
    v.field("name").required()
    is_valid, errors = v.validate()
    assert is_valid is False
    assert "name is required" in errors["name"]

def test_validator_string_constraints():
    v = Validator({"name": "abc"})
    v.field("name").string(min_length=5)
    is_valid, errors = v.validate()
    assert is_valid is False
    assert "at least 5 characters" in errors["name"][0]

    v = Validator({"name": "toolong"})
    v.field("name").string(max_length=3)
    is_valid, errors = v.validate()
    assert is_valid is False
    assert "at most 3 characters" in errors["name"][0]

def test_validator_integer_constraints():
    v = Validator({"age": 15})
    v.field("age").integer(min_value=18)
    is_valid, errors = v.validate()
    assert is_valid is False
    assert "at least 18" in errors["age"][0]

def test_validator_comprehensive():
    data = {
        "type": "regulatory",
        "active": True,
        "score": 10
    }
    v = Validator(data)
    v.field("type").required().string().one_of({"regulatory", "internal"})
    v.field("active").required().boolean()
    v.field("score").integer(min_value=0, max_value=100)
    
    is_valid, errors = v.validate()
    assert is_valid is True
    assert not errors

def test_validator_one_of_fail():
    v = Validator({"type": "invalid"})
    v.field("type").one_of({"a", "b"})
    is_valid, errors = v.validate()
    assert is_valid is False
    assert "must be one of" in errors["type"][0]

def test_validator_boolean_fail():
    v = Validator({"active": "yes"})
    v.field("active").boolean()
    assert v.validate()[0] is False

def test_validator_custom():
    v = Validator({"val": 10})
    v.field("val").custom(lambda x: x % 2 == 0, "Must be even")
    assert v.validate()[0] is True
    
    v.field("val").custom(lambda x: x > 100, "Too small")
    assert v.validate()[0] is False

def test_validator_raise():
    v = Validator({"name": None})
    v.field("name").required()
    with pytest.raises(ValidationError):
        v.validate_or_raise()

# --- Email Tests ---

def test_pagination_params_defaults(mock_flask_app):
    app = Flask(__name__)
    with app.test_request_context('/?page=1&per_page=10'):
        params = PaginationParams.from_request()
        assert params.page == 1
        assert params.per_page == 10

def test_pagination_params_custom(mock_flask_app):
    app = Flask(__name__)
    with app.test_request_context('/?page=2&per_page=50'):
        params = PaginationParams.from_request()
        assert params.page == 2
        assert params.per_page == 50

def test_paginate_list():
    items = list(range(100))
    params = PaginationParams(page=2, per_page=10)
    result = paginate_list(items, params)
    
    assert len(result['items']) == 10
    assert result['items'][0] == 10
    assert result['pagination']['total'] == 100
    assert result['pagination']['total_pages'] == 10
    assert result['pagination']['has_next'] is True
    assert result['pagination']['has_prev'] is True

# --- Responses Tests ---

def test_standard_responses(mock_flask_app):
    # success_response(data, message, status_code)
    app = Flask(__name__)
    with app.app_context():
        resp, code = success_response({"id": 1}, "Created", 201)
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['id'] == 1
        assert data['message'] == "Created"
        assert code == 201

        resp, code = error_response("Item missing", 404, "NOT_FOUND", {"uid": "123"})
        data = resp.get_json()
        assert data['success'] is False
        assert data['error']['code'] == "NOT_FOUND"
        assert data['error']['details']['uid'] == "123"
        assert code == 404

# --- Decorator Tests ---

def test_validate_json_body_success(mock_flask_app):
    app = Flask(__name__)
    
    @app.route('/test', methods=['POST'])
    @validate_json_body(['field1'])
    def handle():
        return jsonify({"success": True}), 200

    with app.test_client() as client:
        resp = client.post('/test', json={"field1": "value"})
        assert resp.status_code == 200

def test_validate_json_body_missing(mock_flask_app):
    app = Flask(__name__)
    
    @app.route('/test', methods=['POST'])
    @validate_json_body(['field1'])
    def handle():
        return jsonify({"success": True}), 200

    with app.test_client() as client:
        resp = client.post('/test', json={"wrong": "field"})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error']['code'] == "MISSING_FIELDS"

def test_validate_query_params(mock_flask_app):
    app = Flask(__name__)
    
    @app.route('/test')
    @validate_query_params(required=['q'])
    def handle():
        return jsonify({"success": True}), 200

    with app.test_client() as client:
        # Success
        resp = client.get('/test?q=search')
        assert resp.status_code == 200
        
        # Missing
        resp = client.get('/test')
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error']['message'] == "Invalid query parameters"
        assert any("Missing required query parameters" in err for err in data['error']['details']['errors'])

# --- Safe Path Tests ---

from backend.utils.safe_path import get_safe_path
import os

def test_get_safe_path():
    base = os.getcwd()
    
    # Safe paths
    path = get_safe_path(base, "file.txt")
    assert path == os.path.join(base, "file.txt")
    
    path = get_safe_path(base, "subdir/file.txt")
    assert path == os.path.join(base, "subdir", "file.txt")
    
    # Unsafe paths
    with pytest.raises(ValueError, match="Security Violation"):
        get_safe_path(base, "../secret.txt")
        
    # Sanitized path (leading slash stripped)
    path = get_safe_path(base, "/etc/passwd")
    assert path == os.path.join(base, "etc", "passwd")

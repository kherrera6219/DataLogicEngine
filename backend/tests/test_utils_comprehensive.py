
import pytest
import unittest.mock
from unittest.mock import MagicMock, patch, mock_open
from flask import Flask, request
from backend.utils.validation import Validator, ValidationError, validate_json_body, validate_query_params
from backend.utils.safe_path import get_safe_path
from backend.utils.pagination import PaginationParams, paginate_list, pagination_meta, paginate_query, settings
from backend.data_loader import UkgDataLoader
import os
import json

# --- Fixtures ---

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app

# --- Tests for validation.py ---

def test_validator_class():
    data = {
        "name": "Alice",
        "age": 30,
        "email": "alice@example.com",
        "role": "admin",
        "is_active": True,
        "optional_field": None
    }
    
    # Happy Path
    v = Validator(data)
    v.field("name").required().string(min_length=2, max_length=10)
    v.field("age").required().integer(min_value=18, max_value=120)
    v.field("email").required().email()
    v.field("role").one_of({"admin", "user"})
    v.field("is_active").boolean()
    v.field("optional_field", optional=True).string()
    
    is_valid, errors = v.validate()
    assert is_valid
    assert errors == {}
    
    # validate_or_raise
    validated = v.validate_or_raise()
    assert validated == data

def test_validator_failures():
    data = {
        "name": "A", # Too short
        "age": "invalid", # Wrong type
        "email": "not-an-email", 
        "role": "supergod", # Not allowed
        "is_active": "yes" # Not boolean
    }
    
    v = Validator(data)
    v.field("name").string(min_length=2)
    v.field("age").integer()
    v.field("email").email()
    v.field("role").one_of({"admin", "user"})
    v.field("is_active").boolean()
    
    is_valid, errors = v.validate()
    assert not is_valid
    assert "name" in errors
    assert "age" in errors
    assert "email" in errors
    assert "role" in errors
    assert "is_active" in errors

    with pytest.raises(ValidationError):
        v.validate_or_raise()
        
def test_validator_required_missing():
    v = Validator({})
    v.field("missing").required()
    assert not v.validate()[0]
    assert "missing" in v.errors[0] if isinstance(v.errors, list) else v.errors["missing"]

def test_validator_custom_and_matches():
    v = Validator({"code": "ABC-123"})
    v.field("code").matches(r"^[A-Z]{3}-\d{3}$")
    v.field("code").custom(lambda x: x.startswith("A"), "Must start with A")
    assert v.validate()[0]
    
    v2 = Validator({"code": "abc"})
    v2.field("code").matches(r"^\d+$", "Must be digits")
    assert not v2.validate()[0]
    assert "Must be digits" in v2.errors["code"]

def test_validate_json_body_decorator(app):
    @app.route("/test_json", methods=["POST"])
    @validate_json_body(required_fields=["foo"])
    def endpoint():
        return "ok"

    with app.test_client() as client:
        # 1. Not JSON
        resp = client.post("/test_json", data="not json")
        assert resp.status_code == 400
        assert resp.json["error"]["code"] == "INVALID_CONTENT_TYPE"

        # 2. Invalid JSON
        resp = client.post("/test_json", data="{invalid", content_type="application/json")
        assert resp.status_code == 400
        assert resp.json["error"]["code"] == "INVALID_JSON"

        # 3. Missing Field
        resp = client.post("/test_json", json={"bar": "baz"})
        assert resp.status_code == 400
        assert resp.json["error"]["code"] == "MISSING_FIELDS"

        # 4. Success
        resp = client.post("/test_json", json={"foo": "bar"})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}. Body: {resp.get_json()}"

def test_validate_query_params_decorator(app):
    @app.route("/test_query", methods=["GET"])
    @validate_query_params(allowed={"page": int}, required=["sort"])
    def endpoint():
        return "ok"
    
    with app.test_client() as client:
        # 1. Missing required
        resp = client.get("/test_query")
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}. Body: {resp.get_json()}"
        assert "Missing required query parameters" in resp.json["error"]["details"]["errors"][0]
        
        # 2. Invalid Type
        resp = client.get("/test_query?sort=asc&page=abc")
        assert resp.status_code == 400
        assert "must be of type int" in resp.json["error"]["details"]["errors"][0]
        
        # 3. Success
        resp = client.get("/test_query?sort=asc&page=1")
        assert resp.status_code == 200

# --- Tests for safe_path.py ---

def test_safe_path_success():
    base = str(os.path.abspath("/tmp/base"))
    path = get_safe_path(base, "files/doc.txt")
    # On windows this might be slightly different separator-wise
    assert "files" in path
    assert "doc.txt" in path

def test_safe_path_traversal_attempt():
    base = os.path.abspath("/tmp/base")
    # Attempt to go up
    with pytest.raises(ValueError, match="Security Violation"):
        get_safe_path(base, "../etc/passwd")

def test_safe_path_absolute_injection():
    base = os.path.abspath("/tmp/base")
    # Should strip leading / and treat as relative
    safe = get_safe_path(base, "/etc/passwd") 
    assert str(safe).startswith(str(base)) # It stays inside

# --- Tests for pagination.py ---

def test_pagination_params_init():
    p = PaginationParams(page=0, per_page=1000)
    assert p.page == 1
    assert p.per_page == settings.MAX_PAGE_SIZE # should cap at max

def test_pagination_from_request(app):
    with app.test_request_context("/?page=2&per_page=5"):
        p = PaginationParams.from_request()
        assert p.page == 2
        assert p.per_page == 5
    
    with app.test_request_context("/?limit=10&offset=20"):
        p = PaginationParams.from_request()
        assert p.per_page == 10
        assert p.page == 3 # (20 // 10) + 1 = 3

def test_paginate_list():
    items = list(range(100))
    p = PaginationParams(page=2, per_page=10)
    result = paginate_list(items, p)
    
    assert len(result["items"]) == 10
    assert result["items"][0] == 10
    assert result["items"][-1] == 19
    assert result["pagination"]["page"] == 2
    assert result["pagination"]["has_next"] is True
    assert result["pagination"]["has_prev"] is True

def test_paginate_query_mock():
    mock_query = MagicMock()
    paginate_query(mock_query, PaginationParams(page=1, per_page=10))
    mock_query.paginate.assert_called_with(page=1, per_page=10, error_out=False)

def test_pagination_meta():
    mock_p = MagicMock()
    mock_p.page = 1
    mock_p.per_page = 20
    mock_p.total = 50
    mock_p.pages = 3
    mock_p.has_next = True
    mock_p.has_prev = False
    
    meta = pagination_meta(mock_p)
    assert meta["total"] == 50
    assert meta["has_next"] is True

# --- Tests for data_loader.py ---

class MockDBManager:
    def __init__(self):
        self.nodes = []
        self.edges = []
    
    def add_node(self, **kwargs):
        self.nodes.append(kwargs)
    
    def add_edge(self, **kwargs):
        self.edges.append(kwargs)
        
    def get_node_by_original_id(self, original_id):
        # Return a dummy node dict
        return {"uid": "mock_uid", "label": f"Mock {original_id}"}


def test_data_loader_init():
    loader = UkgDataLoader(config={'data_directory': '/tmp/data'})
    assert loader.data_dir == '/tmp/data'

def test_load_file_json():
    loader = UkgDataLoader()
    with patch("builtins.open", mock_open(read_data='{"key": "value"}')):
        data = loader._load_file("test.json")
        assert data == {"key": "value"}

def test_load_file_yaml():
    loader = UkgDataLoader()
    # Mock yaml.safe_load
    with patch("builtins.open", mock_open(read_data='key: value')), \
         patch("yaml.safe_load", return_value={"key": "value"}):
        data = loader._load_file("test.yaml")
        assert data == {"key": "value"}

def test_load_file_invalid_ext():
    loader = UkgDataLoader()
    assert loader._load_file("test.txt") is None

def test_load_locations_success():
    db = MockDBManager()
    loader = UkgDataLoader(ukg_db_manager=db)
    
    fake_yaml = {
        "locations": [
            {
                "id": "USA",
                "label": "United States",
                "children": [
                    {"id": "NY", "label": "New York"}
                ]
            }
        ]
    }
    
    with patch("os.path.exists", return_value=True), \
         patch.object(loader, "_load_file", return_value=fake_yaml):
        
        success = loader.load_locations("/mock/path.yaml")
        assert success is True
        assert len(db.nodes) == 2 # USA and NY
        assert len(db.edges) == 1 # USA -> NY

def test_load_regulations_success():
    db = MockDBManager()
    loader = UkgDataLoader(ukg_db_manager=db)
    
    fake_yaml = {
        "regulatory_frameworks": [
            {
                "id": "GDPR",
                "label": "General Data Protection Regulation",
                "attributes": {
                    "associated_location": "EU"
                }
            }
        ]
    }
    
    with patch("os.path.exists", return_value=True), \
         patch.object(loader, "_load_file", return_value=fake_yaml):
        
        success = loader.load_regulatory_frameworks("/mock/rules.yaml")
        assert success is True
        assert len(db.nodes) == 1
        assert len(db.edges) == 1 # Linked to location

def test_load_fail_no_file():
    loader = UkgDataLoader()
    with patch("os.path.exists", return_value=False):
        assert not loader.load_locations("missing.yaml")
        assert not loader.load_regulatory_frameworks("missing.yaml")

def test_process_location_no_db():
    loader = UkgDataLoader(ukg_db_manager=None) # No DB
    assert loader._process_location_recursive({}) is None

import sys
from functools import wraps
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from datetime import datetime


def _passthrough_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@pytest.fixture
def regulatory_app():
    sys.modules.pop("backend.regulatory_api", None)
    with patch("backend.auth.api_decorators.api_login_required", _passthrough_decorator), patch(
        "backend.auth.api_decorators.api_admin_required", _passthrough_decorator
    ):
        import backend.regulatory_api as regulatory_api_module

        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(regulatory_api_module.regulatory_api, url_prefix="/reg")
        return app


@pytest.fixture
def regulatory_client(regulatory_app):
    return regulatory_app.test_client()


def _attach_manager(app, manager):
    app.config["AXIS_SYSTEM"] = SimpleNamespace(axis_managers={6: manager})


def test_regulatory_api_success_paths(regulatory_app, regulatory_client):
    db_manager = MagicMock()
    db_manager.get_nodes_by_properties.return_value = [{"uid": "f1"}]
    regulatory_app.config["DB_MANAGER"] = db_manager

    manager = MagicMock()
    manager.create_mega_framework.return_value = {"status": "success", "uid": "mega-1"}
    manager.create_large_framework.return_value = {"status": "success", "uid": "large-1"}
    manager.create_medium_framework.return_value = {"status": "success", "uid": "medium-1"}
    manager.create_small_framework.return_value = {"status": "success", "uid": "small-1"}
    manager.create_granular_requirement.return_value = {"status": "success", "uid": "req-1"}
    manager.get_octopus_structure.return_value = {"status": "success", "data": {"uid": "mega-1"}}
    manager.create_regulatory_crosswalk.return_value = {"status": "success", "uid": "cw-1"}
    manager.map_jurisdictions.return_value = {"status": "success", "uid": "jur-1"}
    manager.create_compliance_link.return_value = {"status": "success", "uid": "link-1"}
    _attach_manager(regulatory_app, manager)

    resp = regulatory_client.get("/reg/frameworks?node_level=mega&limit=bad")
    assert resp.status_code == 200
    assert resp.json["count"] == 1

    resp = regulatory_client.post("/reg/frameworks", json={"node_level": "mega"})
    assert resp.status_code == 201

    resp = regulatory_client.post("/reg/frameworks", json={"node_level": "large", "parent_uid": "p1"})
    assert resp.status_code == 201

    resp = regulatory_client.post("/reg/frameworks", json={"node_level": "medium", "parent_uid": "p1"})
    assert resp.status_code == 201

    resp = regulatory_client.post("/reg/frameworks", json={"node_level": "small", "parent_uid": "p1"})
    assert resp.status_code == 201

    resp = regulatory_client.post("/reg/requirements", json={"parent_uid": "p1"})
    assert resp.status_code == 201

    resp = regulatory_client.get("/reg/octopus/mega-1")
    assert resp.status_code == 200

    resp = regulatory_client.post(
        "/reg/crosswalk",
        json={"source_uid": "a", "target_uid": "b", "crosswalk_type": "maps_to"},
    )
    assert resp.status_code == 201

    resp = regulatory_client.post(
        "/reg/jurisdiction",
        json={"framework_uid": "f1", "jurisdiction_data": {"region": "eu"}},
    )
    assert resp.status_code == 201

    resp = regulatory_client.post(
        "/reg/compliance_link",
        json={"framework_uid": "f1", "compliance_standard_uid": "soc2"},
    )
    assert resp.status_code == 201

    resp = regulatory_client.get("/reg/standards")
    assert resp.status_code == 200
    assert resp.json["success"] is True


def test_regulatory_api_validation_and_error_paths(regulatory_app, regulatory_client):
    regulatory_app.config["DB_MANAGER"] = None
    resp = regulatory_client.get("/reg/frameworks")
    assert resp.status_code == 500

    regulatory_app.config["DB_MANAGER"] = MagicMock(get_nodes_by_properties=MagicMock(side_effect=RuntimeError("db fail")))
    resp = regulatory_client.get("/reg/frameworks")
    assert resp.status_code == 500

    manager = MagicMock()
    _attach_manager(regulatory_app, manager)

    resp = regulatory_client.post("/reg/frameworks", json={})
    assert resp.status_code == 400

    resp = regulatory_client.post("/reg/frameworks", json={"node_level": "large"})
    assert resp.status_code == 400

    regulatory_app.config["AXIS_SYSTEM"] = None
    resp = regulatory_client.post("/reg/frameworks", json={"node_level": "mega"})
    assert resp.status_code == 500

    _attach_manager(regulatory_app, None)
    resp = regulatory_client.post("/reg/frameworks", json={"node_level": "mega"})
    assert resp.status_code == 500

    _attach_manager(regulatory_app, manager)
    manager.create_mega_framework.return_value = {"status": "error"}
    resp = regulatory_client.post("/reg/frameworks", json={"node_level": "mega"})
    assert resp.status_code == 400

    resp = regulatory_client.post("/reg/requirements", json={})
    assert resp.status_code == 400

    manager.create_granular_requirement.return_value = {"status": "error"}
    resp = regulatory_client.post("/reg/requirements", json={"parent_uid": "p1"})
    assert resp.status_code == 400

    manager.get_octopus_structure.return_value = {"status": "error"}
    resp = regulatory_client.get("/reg/octopus/mega-1")
    assert resp.status_code == 400

    resp = regulatory_client.post("/reg/crosswalk", json={})
    assert resp.status_code == 400
    manager.create_regulatory_crosswalk.return_value = {"status": "error"}
    resp = regulatory_client.post(
        "/reg/crosswalk",
        json={"source_uid": "a", "target_uid": "b", "crosswalk_type": "maps_to"},
    )
    assert resp.status_code == 400

    resp = regulatory_client.post("/reg/jurisdiction", json={})
    assert resp.status_code == 400
    manager.map_jurisdictions.return_value = {"status": "error"}
    resp = regulatory_client.post(
        "/reg/jurisdiction",
        json={"framework_uid": "f1", "jurisdiction_data": {"region": "eu"}},
    )
    assert resp.status_code == 400

    resp = regulatory_client.post("/reg/compliance_link", json={})
    assert resp.status_code == 400
    manager.create_compliance_link.return_value = {"status": "error"}
    resp = regulatory_client.post(
        "/reg/compliance_link",
        json={"framework_uid": "f1", "compliance_standard_uid": "soc2"},
    )
    assert resp.status_code == 400


def test_regulatory_api_exception_path_on_standards(regulatory_app, regulatory_client):
    with patch("backend.regulatory_api.datetime") as mock_datetime:
        mock_datetime.now.side_effect = [RuntimeError("clock fail"), datetime.now()]
        resp = regulatory_client.get("/reg/standards")
        assert resp.status_code == 500

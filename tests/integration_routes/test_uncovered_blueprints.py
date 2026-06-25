from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

import backend.methods_api as methods_api_module
import backend.security_api as security_api_module


@pytest.fixture
def methods_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(methods_api_module.methods_api)
    return app


@pytest.fixture
def methods_client(methods_app):
    return methods_app.test_client()


def _attach_methods_manager(app, manager):
    app.config["AXIS_SYSTEM"] = SimpleNamespace(axis_managers={4: manager})


def test_methods_routes_cover_success_and_error_paths(methods_app, methods_client):
    manager = MagicMock()
    manager.db_manager.get_nodes_by_properties.return_value = [{"node_id": "m-1"}]
    manager.db_manager.get_node_by_id.return_value = {"node_id": "m-1"}
    manager.get_method_hierarchy.return_value = [{"node_id": "m-1"}]
    manager.find_cross_sector_methods.return_value = {"status": "success", "methods": ["m-1"]}
    manager.find_cross_pillar_methods.return_value = {"status": "success", "methods": ["m-2"]}
    manager.register_method_node.return_value = {"status": "success", "node_id": "m-3"}
    manager.establish_node_hierarchy.return_value = {"status": "success", "parent_id": "m-1", "child_id": "m-2"}
    _attach_methods_manager(methods_app, manager)

    resp = methods_client.get("/api/methods?node_type=analysis")
    assert resp.status_code == 200
    assert resp.json["count"] == 1
    manager.db_manager.get_nodes_by_properties.assert_called_once_with({"node_type": "analysis", "axis_number": 4})

    resp = methods_client.get("/api/methods/m-1")
    assert resp.status_code == 200
    assert resp.json["method"]["node_id"] == "m-1"

    resp = methods_client.post("/api/methods/cross-sector", json={"sector_ids": ["s-1", "s-2"]})
    assert resp.status_code == 200
    assert resp.json["status"] == "success"

    resp = methods_client.post("/api/methods/cross-pillar", json={"pillar_ids": ["p-1"]})
    assert resp.status_code == 200
    assert resp.json["status"] == "success"

    resp = methods_client.post(
        "/api/methods",
        json={"label": "Method 3", "node_type": "method", "node_id": "m-3"},
    )
    assert resp.status_code == 201

    resp = methods_client.post("/api/methods/hierarchy", json={"parent_id": "m-1", "child_id": "m-2"})
    assert resp.status_code == 201

    manager.register_method_node.return_value = {"status": "exists"}
    resp = methods_client.post(
        "/api/methods",
        json={"label": "Method 3", "node_type": "method", "node_id": "m-3"},
    )
    assert resp.status_code == 409

    manager.register_method_node.return_value = {"status": "error"}
    resp = methods_client.post(
        "/api/methods",
        json={"label": "Method 3", "node_type": "method", "node_id": "m-3"},
    )
    assert resp.status_code == 400

    manager.establish_node_hierarchy.return_value = {"status": "exists"}
    resp = methods_client.post("/api/methods/hierarchy", json={"parent_id": "m-1", "child_id": "m-2"})
    assert resp.status_code == 409

    manager.establish_node_hierarchy.return_value = {"status": "error"}
    resp = methods_client.post("/api/methods/hierarchy", json={"parent_id": "m-1", "child_id": "m-2"})
    assert resp.status_code == 400


def test_methods_routes_validation_and_missing_manager(methods_app, methods_client):
    methods_app.config["AXIS_SYSTEM"] = SimpleNamespace(axis_managers={})

    resp = methods_client.get("/api/methods")
    assert resp.status_code == 500

    resp = methods_client.post("/api/methods/cross-sector", json={})
    assert resp.status_code == 400

    resp = methods_client.post("/api/methods/cross-sector", json={"sector_ids": []})
    assert resp.status_code == 400

    resp = methods_client.post("/api/methods/cross-pillar", json={})
    assert resp.status_code == 400

    resp = methods_client.post("/api/methods/cross-pillar", json={"pillar_ids": []})
    assert resp.status_code == 400

    resp = methods_client.post("/api/methods", json={})
    assert resp.status_code == 400

    resp = methods_client.post("/api/methods", json={"label": "X"})
    assert resp.status_code == 400

    resp = methods_client.post("/api/methods/hierarchy", json={})
    assert resp.status_code == 400

    resp = methods_client.get("/api/methods/missing")
    assert resp.status_code == 500

    methods_app.config["AXIS_SYSTEM"] = None
    resp = methods_client.get("/api/methods")
    assert resp.status_code == 500


@pytest.fixture
def security_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(security_api_module.security_bp)
    return app


@pytest.fixture
def security_client(security_app):
    return security_app.test_client()


def test_security_api_endpoints(security_client):
    mock_security_manager = MagicMock()
    mock_security_manager.get_security_status.return_value = {"status": "ok"}
    mock_security_manager.last_scan_results = {
        "scan_id": "scan-1",
        "timestamp": "2024-01-01T00:00:00",
        "vulnerabilities": [{"id": 1}],
        "warnings": [{"id": 2}],
    }

    mock_compliance_manager = MagicMock()
    mock_compliance_manager.get_compliance_status.return_value = {"overall_status": "compliant"}
    mock_compliance_manager.get_compliance_events.return_value = [{"id": "c1"}]
    mock_compliance_manager.generate_compliance_report.return_value = {"report_id": "r1"}

    mock_audit_logger = MagicMock()
    mock_audit_logger.get_audit_events.return_value = [{"id": "a1"}]
    mock_audit_logger.verify_audit_log_integrity.return_value = {"valid": True}

    with patch.object(security_api_module, "get_security_manager", return_value=mock_security_manager), patch.object(
        security_api_module, "get_compliance_manager", return_value=mock_compliance_manager
    ), patch.object(security_api_module, "get_audit_logger", return_value=mock_audit_logger):
        resp = security_client.get("/api/security/health")
        assert resp.status_code == 200

        resp = security_client.get("/api/security/status")
        assert resp.status_code == 200
        assert resp.json["status"] == "ok"

        resp = security_client.get("/api/security/compliance/status")
        assert resp.status_code == 200
        assert resp.json["overall_status"] == "compliant"

        resp = security_client.get(
            "/api/security/compliance/events?start_time=2024-01-01T00:00:00&end_time=2024-01-10T00:00:00&limit=bad"
        )
        assert resp.status_code == 200
        assert resp.json["count"] == 1
        _, kwargs = mock_compliance_manager.get_compliance_events.call_args
        assert kwargs["limit"] == 100

        resp = security_client.post(
            "/api/security/compliance/report",
            json={"start_date": "2024-01-01T00:00:00", "end_date": "2024-01-31T00:00:00"},
        )
        assert resp.status_code == 200
        assert resp.json["report_id"] == "r1"

        resp = security_client.get("/api/security/audit/events?user_id=1&limit=10")
        assert resp.status_code == 200
        assert resp.json["count"] == 1

        resp = security_client.post("/api/security/scan")
        assert resp.status_code == 200
        assert resp.json["scan_id"] == "scan-1"

        mock_security_manager.last_scan_results = None
        resp = security_client.post("/api/security/scan")
        assert resp.status_code == 200
        assert "no results" in resp.json["message"]

        resp = security_client.post("/api/security/audit/verify", json={"log_file": "logs/security/audit.jsonl"})
        assert resp.status_code == 200
        assert resp.json["valid"] is True


def test_security_api_error_paths(security_client):
    mock_security_manager = MagicMock()
    mock_security_manager._perform_security_scan.side_effect = RuntimeError("scan failed")
    mock_security_manager.last_scan_results = None

    mock_compliance_manager = MagicMock()
    mock_compliance_manager.get_compliance_events.side_effect = ValueError("bad filter")
    mock_compliance_manager.generate_compliance_report.side_effect = ValueError("bad date")

    mock_audit_logger = MagicMock()
    mock_audit_logger.get_audit_events.side_effect = RuntimeError("audit failed")
    mock_audit_logger.verify_audit_log_integrity.side_effect = RuntimeError("integrity failed")

    with patch.object(security_api_module, "get_security_manager", return_value=mock_security_manager), patch.object(
        security_api_module, "get_compliance_manager", return_value=mock_compliance_manager
    ), patch.object(security_api_module, "get_audit_logger", return_value=mock_audit_logger):
        resp = security_client.get("/api/security/compliance/events?start_time=not-a-date")
        assert resp.status_code == 400

        resp = security_client.post("/api/security/compliance/report", json={"start_date": "not-a-date"})
        assert resp.status_code == 400

        resp = security_client.get("/api/security/audit/events")
        assert resp.status_code == 400

        resp = security_client.post("/api/security/scan")
        assert resp.status_code == 500

        resp = security_client.post("/api/security/audit/verify", json={})
        assert resp.status_code == 500

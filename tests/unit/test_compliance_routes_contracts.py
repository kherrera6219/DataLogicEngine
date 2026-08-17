from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

from flask import Flask


class _Manager:
    def get_compliance_hierarchy(self, standard_type):
        return {"status": "success", "type": standard_type}

    def register_compliance_standard(self, data, parent_id):
        return {"status": "success", "standard": data, "parent_id": parent_id}

    def find_compliance_for_sector(self, sector_id, standard_type):
        return {"status": "success", "sector_id": sector_id, "type": standard_type}

    def map_regulatory_to_compliance(self, *values):
        return {"status": "success", "values": values}


class _DbManager:
    def __init__(self, standards=None):
        self.standards = list(standards or [])

    def get_nodes_by_properties(self, _properties):
        return self.standards

    def get_incoming_edges(self, _uid, _types):
        return [{"source_id": "parent-uid"}]

    def get_outgoing_edges(self, _uid, _types):
        return [{"target_id": "child-uid"}, {"target_id": "missing-child"}]

    def get_node(self, uid):
        if uid == "missing-child":
            return None
        return {"uid": uid}


def _route(function, *args):
    return inspect.unwrap(function)(*args)


def _status(result):
    return result[1] if isinstance(result, tuple) else result.status_code


def test_compliance_manager_lookup_and_standard_reads(monkeypatch):
    import backend.routes.compliance_routes as module

    app = Flask(__name__)
    with app.test_request_context("/standards"):
        assert module._get_compliance_manager() is None
        assert _status(module._compliance_unavailable()) == 503

    app.config["AXIS_SYSTEM"] = SimpleNamespace(axis_managers={7: _Manager()})
    with app.test_request_context("/standards?type=security"):
        assert _route(module.get_compliance_standards).get_json()["type"] == "security"
    with app.test_request_context("/sector/finance?type=regulatory"):
        assert _route(module.get_sector_compliance, "finance").get_json()["sector_id"] == "finance"

    standard = {"uid": "standard-1", "id": "NIST"}
    app.config["DB_MANAGER"] = _DbManager([standard])
    with app.test_request_context("/standards/NIST"):
        body = _route(module.get_compliance_standard, "NIST").get_json()
        assert body["parent"]["uid"] == "parent-uid" and body["child_count"] == 1
    app.config["DB_MANAGER"] = _DbManager([])
    with app.test_request_context("/standards/missing"):
        assert _status(_route(module.get_compliance_standard, "missing")) == 404
    app.config.pop("DB_MANAGER")
    with app.test_request_context("/standards/missing"):
        assert _status(_route(module.get_compliance_standard, "missing")) == 500


def test_compliance_create_and_regulatory_mapping_contracts(monkeypatch):
    import backend.routes.compliance_routes as module

    app = Flask(__name__)
    app.config["AXIS_SYSTEM"] = SimpleNamespace(axis_managers={7: _Manager()})
    create_payload = SimpleNamespace(model_dump=lambda: {"id": "STD", "name": "Standard", "parent_id": "ROOT"})
    monkeypatch.setattr(module, "get_validated_payload", lambda _schema: create_payload)
    with app.test_request_context("/standards", method="POST", json={}):
        result = _route(module.create_compliance_standard)
        assert _status(result) == 201 and result[0].get_json()["parent_id"] == "ROOT"

    map_payload = SimpleNamespace(
        regulatory_uid="reg-1", compliance_uid="std-1",
        relationship_type="maps_to", confidence=0.9,
    )
    monkeypatch.setattr(module, "get_validated_payload", lambda _schema: map_payload)
    with app.test_request_context("/map-regulatory", method="POST", json={}):
        assert _status(_route(module.map_regulatory_to_compliance)) == 201

    monkeypatch.setattr(module, "get_validated_payload", lambda _schema: None)
    with app.test_request_context("/standards", method="POST", json={}):
        assert _status(_route(module.create_compliance_standard)) == 422
    with app.test_request_context("/map-regulatory", method="POST", json={}):
        assert _status(_route(module.map_regulatory_to_compliance)) == 422

    class Failed(_Manager):
        def register_compliance_standard(self, *_values):
            return {"status": "error", "message": "invalid"}

        def map_regulatory_to_compliance(self, *_values):
            return {"status": "error", "message": "invalid"}

    app.config["AXIS_SYSTEM"] = SimpleNamespace(axis_managers={7: Failed()})
    monkeypatch.setattr(module, "get_validated_payload", lambda schema: create_payload if schema is module.ComplianceStandardCreateRequest else map_payload)
    with app.test_request_context("/standards", method="POST", json={}):
        assert _status(_route(module.create_compliance_standard)) == 400
    with app.test_request_context("/map-regulatory", method="POST", json={}):
        assert _status(_route(module.map_regulatory_to_compliance)) == 400


def test_compliance_routes_unavailable_and_exception_boundaries(monkeypatch):
    import backend.routes.compliance_routes as module

    app = Flask(__name__)
    monkeypatch.setattr(module, "get_validated_payload", lambda schema: (
        SimpleNamespace(model_dump=lambda: {"id": "STD"})
        if schema is module.ComplianceStandardCreateRequest
        else SimpleNamespace(regulatory_uid="r", compliance_uid="c", relationship_type="maps", confidence=1)
    ))
    for function, path, args in [
        (module.get_compliance_standards, "/standards", ()),
        (module.create_compliance_standard, "/standards", ()),
        (module.get_sector_compliance, "/sector/s", ("s",)),
        (module.map_regulatory_to_compliance, "/map-regulatory", ()),
    ]:
        with app.test_request_context(path, method="POST"):
            assert _status(_route(function, *args)) == 503

    class BrokenAxis:
        axis_managers = {7: _Manager()}

    app.config["AXIS_SYSTEM"] = BrokenAxis()
    app.config["AXIS_SYSTEM"].axis_managers[7].get_compliance_hierarchy = lambda *_a: (_ for _ in ()).throw(RuntimeError("standards failed"))
    with app.test_request_context("/standards"):
        assert _status(_route(module.get_compliance_standards)) == 500
    app.config["AXIS_SYSTEM"].axis_managers[7].find_compliance_for_sector = lambda *_a: (_ for _ in ()).throw(RuntimeError("sector failed"))
    with app.test_request_context("/sector/s"):
        assert _status(_route(module.get_sector_compliance, "s")) == 500

    class BrokenDb(_DbManager):
        def get_nodes_by_properties(self, _properties):
            raise RuntimeError("db failed")

    app.config["DB_MANAGER"] = BrokenDb()
    with app.test_request_context("/standards/s"):
        assert _status(_route(module.get_compliance_standard, "s")) == 500


def test_audit_csv_and_compliance_pdf_exports(monkeypatch, tmp_path):
    import flask
    import backend.routes.compliance_routes as module
    import backend.reports.compliance as report_module
    import backend.security.audit_logger as audit_module

    app = Flask(__name__)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(flask, "send_file", lambda *_args, **_kwargs: app.json.response({"sent": True}))

    class AuditLogger:
        count = 0

        def export_to_csv(self, filepath, **_values):
            path = Path(filepath)
            path.write_text("event\n", encoding="utf-8")
            return self.count

    monkeypatch.setattr(audit_module, "AuditLogger", AuditLogger)
    with app.test_request_context("/audit/export?days=7"):
        body = _route(module.export_audit_logs_route).get_json()
        assert body["count"] == 0
    AuditLogger.count = 1
    with app.test_request_context("/audit/export"):
        assert _route(module.export_audit_logs_route).status_code == 200

    pdf = tmp_path / "report.pdf"
    pdf.write_bytes(b"%PDF-test")
    monkeypatch.setattr(report_module, "ComplianceFramework", lambda value: value)
    monkeypatch.setattr(report_module.compliance_reporter, "generate_report", lambda **_values: {"pdf_export_path": str(pdf)})
    payload = SimpleNamespace(framework="NIST", data_points=[{"score": 1}])
    monkeypatch.setattr(module, "get_validated_payload", lambda _schema: payload)
    with app.test_request_context("/report/pdf", method="POST", json={}):
        assert _route(module.export_compliance_report).status_code == 200
    monkeypatch.setattr(report_module.compliance_reporter, "generate_report", lambda **_values: {})
    with app.test_request_context("/report/pdf", method="POST", json={}):
        assert _status(_route(module.export_compliance_report)) == 500
    monkeypatch.setattr(module, "get_validated_payload", lambda _schema: None)
    with app.test_request_context("/report/pdf", method="POST", json={}):
        assert _status(_route(module.export_compliance_report)) == 422

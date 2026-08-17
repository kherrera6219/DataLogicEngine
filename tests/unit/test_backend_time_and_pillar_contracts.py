from __future__ import annotations

import inspect
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from flask import Flask


class _Column:
    def __eq__(self, other):
        return ("eq", other)

    def __ge__(self, other):
        return ("ge", other)

    def __le__(self, other):
        return ("le", other)

    def contains(self, other):
        return ("contains", other)

    def in_(self, other):
        return ("in", other)


class _TimeContext:
    time_type = _Column()
    start_date = _Column()
    end_date = _Column()
    parent_time_id = _Column()
    granularity = _Column()
    attributes = _Column()

    def __init__(self, **values):
        self.id = values.pop("id", 1)
        self.uid = values.pop("uid", "time-1")
        for key, value in values.items():
            setattr(self, key, value)

    def to_dict(self):
        return {
            "uid": self.uid,
            "name": getattr(self, "name", "Time"),
            "time_type": getattr(self, "time_type_value", None) or self.__dict__.get("time_type"),
        }


class _Query:
    def __init__(self, *, first=None, rows=None, get=None, error=None):
        self.first_value = first
        self.rows = list(rows or [])
        self.get_value = get
        self.error = error
        self.filters = []

    def filter(self, *expressions):
        if self.error:
            raise self.error
        self.filters.extend(expressions)
        return self

    def filter_by(self, **values):
        if self.error:
            raise self.error
        self.filters.append(values)
        return self

    def order_by(self, *_expressions):
        return self

    def all(self):
        if self.error:
            raise self.error
        return self.rows

    def first(self):
        if self.error:
            raise self.error
        return self.first_value

    def get(self, _value):
        return self.get_value


class _Session:
    def __init__(self, queries=()):
        self.queries = list(queries)
        self.added = []
        self.deleted = []
        self.commits = 0
        self.rollbacks = 0

    def query(self, _model):
        return self.queries.pop(0) if self.queries else _Query()

    def add(self, value):
        self.added.append(value)

    def delete(self, value):
        self.deleted.append(value)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def _json(result):
    response = result[0] if isinstance(result, tuple) else result
    status = result[1] if isinstance(result, tuple) else response.status_code
    return response.get_json(), status


def _install_time(monkeypatch, queries=()):
    import backend.time_api as module

    session = _Session(queries)
    monkeypatch.setattr(module, "TimeContext", _TimeContext)
    monkeypatch.setattr(module, "db", SimpleNamespace(session=session))
    return module, session


def test_time_list_filters_validation_and_failure(monkeypatch):
    module, _session = _install_time(monkeypatch, [_Query(rows=[_TimeContext(uid="one")])])
    app = Flask(__name__)
    with app.test_request_context("/api/time?type=period&parent_id=1&start_date=2026-01-01&end_date=2026-12-31&granularity=day"):
        body, status = _json(module.get_time_contexts())
        assert status == 200 and body["count"] == 1

    module, _ = _install_time(monkeypatch, [_Query()])
    with app.test_request_context("/api/time?start_date=bad"):
        assert _json(module.get_time_contexts())[1] == 400
    module, _ = _install_time(monkeypatch, [_Query()])
    with app.test_request_context("/api/time?end_date=bad"):
        assert _json(module.get_time_contexts())[1] == 400
    module, _ = _install_time(monkeypatch, [_Query(error=RuntimeError("query failed"))])
    with app.test_request_context("/api/time?type=x"):
        assert _json(module.get_time_contexts())[1] == 500


def test_time_get_with_children_parent_missing_and_failure(monkeypatch):
    app = Flask(__name__)
    parent = _TimeContext(uid="parent")
    item = _TimeContext(id=2, uid="child", parent_time_id=1)
    child = _TimeContext(uid="grandchild")
    module, _ = _install_time(monkeypatch, [
        _Query(first=item), _Query(rows=[child]), _Query(get=parent),
    ])
    with app.test_request_context("/api/time/child"):
        body, status = _json(module.get_time_context("child"))
        assert status == 200 and body["time_context"]["parent"]["uid"] == "parent"

    module, _ = _install_time(monkeypatch, [_Query(first=None)])
    with app.test_request_context("/api/time/missing"):
        assert _json(module.get_time_context("missing"))[1] == 404
    module, _ = _install_time(monkeypatch, [_Query(error=RuntimeError("read failed"))])
    with app.test_request_context("/api/time/broken"):
        assert _json(module.get_time_context("broken"))[1] == 500


def test_time_create_success_validation_and_rollback(monkeypatch):
    app = Flask(__name__)
    module, session = _install_time(monkeypatch)
    with app.test_request_context("/api/time", method="POST", json={}):
        assert _json(module.create_time_context())[1] == 400
    with app.test_request_context("/api/time", method="POST", json={"name": "N", "time_type": "period", "start_date": "bad"}):
        assert _json(module.create_time_context())[1] == 400
    payload = {
        "name": "Release", "time_type": "period", "start_date": "2026-01-01",
        "end_date": "2026-02-01", "granularity": "month", "recurring": True,
        "parent_time_id": 3, "attributes": {"kind": "release"},
    }
    with app.test_request_context("/api/time", method="POST", json=payload):
        assert _json(module.create_time_context())[1] == 201
    assert session.added and session.commits == 1

    class BrokenTime:
        def __init__(self, **_values):
            raise RuntimeError("insert failed")

    monkeypatch.setattr(module, "TimeContext", BrokenTime)
    with app.test_request_context("/api/time", method="POST", json={"name": "N", "time_type": "period", "start_date": "2026-01-01"}):
        assert _json(module.create_time_context())[1] == 500
    assert session.rollbacks == 1


def test_time_update_all_fields_dates_missing_and_failure(monkeypatch):
    app = Flask(__name__)
    item = _TimeContext(uid="update")
    module, session = _install_time(monkeypatch, [_Query(first=item)])
    payload = {
        "name": "Updated", "time_type": "era", "start_date": "2026-01-01",
        "end_date": None, "granularity": "year", "recurring": False,
        "parent_time_id": None, "attributes": {"updated": True},
    }
    with app.test_request_context("/api/time/update", method="PUT", json=payload):
        assert _json(module.update_time_context("update"))[1] == 200
    assert item.name == "Updated" and session.commits == 1

    module, _ = _install_time(monkeypatch, [_Query(first=None)])
    with app.test_request_context("/api/time/missing", method="PUT", json={}):
        assert _json(module.update_time_context("missing"))[1] == 404
    for field in ("start_date", "end_date"):
        module, _ = _install_time(monkeypatch, [_Query(first=_TimeContext())])
        with app.test_request_context("/api/time/bad", method="PUT", json={field: "bad"}):
            assert _json(module.update_time_context("bad"))[1] == 400
    module, session = _install_time(monkeypatch, [_Query(error=RuntimeError("update failed"))])
    with app.test_request_context("/api/time/broken", method="PUT", json={}):
        assert _json(module.update_time_context("broken"))[1] == 500
    assert session.rollbacks == 1


def test_time_delete_children_success_missing_and_failure(monkeypatch):
    app = Flask(__name__)
    item = _TimeContext(id=2, name="Delete me")
    module, _ = _install_time(monkeypatch, [_Query(first=item), _Query(rows=[_TimeContext()])])
    with app.test_request_context("/api/time/delete", method="DELETE"):
        assert _json(module.delete_time_context("delete"))[1] == 400

    module, session = _install_time(monkeypatch, [_Query(first=item), _Query(rows=[])])
    with app.test_request_context("/api/time/delete", method="DELETE"):
        assert _json(module.delete_time_context("delete"))[1] == 200
    assert session.deleted == [item]
    module, _ = _install_time(monkeypatch, [_Query(first=None)])
    with app.test_request_context("/api/time/missing", method="DELETE"):
        assert _json(module.delete_time_context("missing"))[1] == 404
    module, session = _install_time(monkeypatch, [_Query(error=RuntimeError("delete failed"))])
    with app.test_request_context("/api/time/broken", method="DELETE"):
        assert _json(module.delete_time_context("broken"))[1] == 500
    assert session.rollbacks == 1


def test_time_career_project_and_historical_views(monkeypatch):
    app = Flask(__name__)
    now = datetime.now(UTC)
    stages = [
        _TimeContext(start_date=now - timedelta(days=365), end_date=now),
        _TimeContext(start_date=now - timedelta(days=730), end_date=None),
        _TimeContext(start_date=None, end_date=None),
    ]
    module, _ = _install_time(monkeypatch, [_Query(rows=stages)])
    with app.test_request_context("/api/time/career/persona"):
        body, status = _json(module.get_career_timeline("persona"))
        assert status == 200 and body["stage_count"] == 3

    project = _TimeContext(id=9, uid="project")
    task_done = _TimeContext(time_type="task", attributes={"status": "completed"})
    task_open = _TimeContext(time_type="task", attributes={})
    milestone = _TimeContext(time_type="milestone", attributes=None)
    module, _ = _install_time(monkeypatch, [_Query(first=project), _Query(rows=[task_done, task_open, milestone])])
    with app.test_request_context("/api/time/project/p1"):
        body, status = _json(module.get_project_timeline("p1"))
        assert status == 200 and body["completion_percentage"] == 50.0
    module, _ = _install_time(monkeypatch, [_Query(first=None)])
    with app.test_request_context("/api/time/project/missing"):
        assert _json(module.get_project_timeline("missing"))[1] == 404

    module, _ = _install_time(monkeypatch, [_Query(rows=[_TimeContext(uid="history")])])
    with app.test_request_context("/api/time/historical?start_year=2020&end_year=2026"):
        body, status = _json(module.get_historical_periods())
        assert status == 200 and body["count"] == 1


class _PillarManager:
    def get_all_pillar_levels(self):
        return {"status": "success", "pillars": ["p1"]}

    def get_pillar_level(self, pillar_id):
        return {"status": "success", "pillar": {"id": pillar_id, "sublevels": ["s1"]}}

    def create_pillar_level(self, data):
        return {"status": "success", "pillar": data}

    def add_sublevel(self, *_args):
        return {"status": "success", "sublevel": {"id": "s1"}}

    def get_sublevel(self, *_args):
        return {"status": "success", "sublevel": {"id": "s1"}}

    def get_dynamic_mappings(self, *_args):
        return {"status": "success", "mappings": ["m1"]}

    def create_dynamic_mapping(self, *_args):
        return {"status": "success", "mapping": {"id": "m1"}}

    def dynamic_sublevel_expansion(self, *_args):
        return {"status": "success", "expansion": ["s2"]}

    def analyze_text_for_pillar_context(self, _text):
        return {"status": "success", "context": {"pillar": "p1"}}

    def export_pillar_levels_to_yaml(self, path):
        return {"status": "success", "message": "exported", "file_path": path}


def _pillar_call(function, *args):
    return inspect.unwrap(function)(*args)


def test_pillar_api_success_contracts():
    import backend.pillar_api as module

    app = Flask(__name__)
    app.config["KNOWLEDGE_MANAGER"] = _PillarManager()
    cases = [
        ("/", "GET", module.get_all_pillars, (), None),
        ("/p1", "GET", module.get_pillar, ("p1",), None),
        ("/", "POST", module.create_pillar, (), {"pillar_id": "p2"}),
        ("/p1/sublevels", "GET", module.get_sublevels, ("p1",), None),
        ("/p1/sublevels", "POST", module.add_sublevel, ("p1",), {"sublevel_id": "s1", "name": "Sub", "description": "D", "parent_sublevel_id": "root"}),
        ("/p1/sublevels/s1", "GET", module.get_sublevel, ("p1", "s1"), None),
        ("/mappings?pillar_id=p1&sublevel_id=s1", "GET", module.get_mappings, (), None),
        ("/mappings", "POST", module.create_mapping, (), {"source_pillar_id": "p1", "source_sublevel_id": "s1", "target_pillar_id": "p2", "target_sublevel_id": "s2", "mapping_type": "depends", "strength": "0.8", "bidirectional": True}),
        ("/p1/expand", "POST", module.expand_pillar, ("p1",), {"context_text": "expand"}),
        ("/analyze-text", "POST", module.analyze_text, (), {"text": "analyze"}),
        ("/export", "POST", module.export_pillars, (), {"file_path": "pillars.yaml"}),
    ]
    for path, method, function, args, payload in cases:
        with app.test_request_context(path, method=method, json=payload):
            result = _pillar_call(function, *args)
            assert not (isinstance(result, tuple) and result[1] >= 400)


def test_pillar_api_unavailable_validation_and_manager_failures():
    import backend.pillar_api as module

    app = Flask(__name__)
    functions = [
        (module.get_all_pillars, ()), (module.get_pillar, ("p",)), (module.create_pillar, ()),
        (module.get_sublevels, ("p",)), (module.add_sublevel, ("p",)), (module.get_sublevel, ("p", "s")),
        (module.get_mappings, ()), (module.create_mapping, ()), (module.expand_pillar, ("p",)),
        (module.analyze_text, ()), (module.export_pillars, ()),
    ]
    for function, args in functions:
        with app.test_request_context("/", method="POST", json={}):
            assert _pillar_call(function, *args)[1] == 500

    app.config["KNOWLEDGE_MANAGER"] = _PillarManager()
    with app.test_request_context("/", method="POST", json={}):
        assert _pillar_call(module.add_sublevel, "p")[1] == 400
        assert _pillar_call(module.create_mapping)[1] == 400
        assert _pillar_call(module.analyze_text)[1] == 400

    class FailedManager(_PillarManager):
        def __getattribute__(self, name):
            if name.startswith(("get_", "create_", "add_", "dynamic_", "analyze_", "export_")):
                return lambda *_args: {"status": "error", "message": "failed"}
            return super().__getattribute__(name)

    app.config["KNOWLEDGE_MANAGER"] = FailedManager()
    failure_cases = [
        (module.get_all_pillars, ()), (module.get_pillar, ("p",)), (module.create_pillar, ()),
        (module.get_sublevels, ("p",)), (module.add_sublevel, ("p",)), (module.get_sublevel, ("p", "s")),
        (module.get_mappings, ()), (module.create_mapping, ()), (module.expand_pillar, ("p",)),
        (module.analyze_text, ()), (module.export_pillars, ()),
    ]
    payload = {
        "sublevel_id": "s", "name": "S", "source_pillar_id": "p1", "source_sublevel_id": "s1",
        "target_pillar_id": "p2", "target_sublevel_id": "s2", "text": "x",
    }
    for function, args in failure_cases:
        with app.test_request_context("/", method="POST", json=payload):
            result = _pillar_call(function, *args)
            assert isinstance(result, tuple) and result[1] in {400, 404}


def test_pillar_registration_and_auth_hook():
    import backend.pillar_api as module

    app = Flask(__name__)
    assert module.require_pillar_api_authentication.__wrapped__() is None
    assert module.register_api(app) is app

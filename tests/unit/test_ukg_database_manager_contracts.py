from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace


class _Column:
    def __eq__(self, other):
        return ("eq", other)

    def in_(self, values):
        return ("in", values)

    def desc(self):
        return self


class _Model:
    uid = _Column()
    id = _Column()
    tenant_id = _Column()
    node_type = _Column()
    edge_type = _Column()
    source_id = _Column()
    target_id = _Column()
    ka_id = _Column()
    status = _Column()
    session_id = _Column()
    entry_type = _Column()
    pass_num = _Column()
    created_at = _Column()
    started_at = _Column()
    _counter = 0

    def __init__(self, **values):
        _Model._counter += 1
        self.id = values.pop("id", _Model._counter)
        self.created_at = values.pop("created_at", datetime(2026, 1, 1, tzinfo=UTC))
        self.updated_at = values.pop("updated_at", None)
        defaults = {
            "uid": f"uid-{self.id}", "node_type": "concept", "label": "Record",
            "description": "Description", "original_id": None, "axis_number": 1,
            "level": 1, "attributes": {}, "tenant_id": "tenant-a", "edge_type": "related",
            "source_id": 1, "target_id": 2, "weight": 1.0, "ka_id": "KA-001",
            "name": "Algorithm", "input_schema": {}, "output_schema": {}, "version": "1",
            "status": "completed", "input_data": {}, "output_data": {}, "error_message": None,
            "execution_time_ms": 10, "started_at": datetime(2026, 1, 1, tzinfo=UTC),
            "completed_at": datetime(2026, 1, 1, tzinfo=UTC), "session_id": "session-1",
            "entry_type": "fact", "pass_num": 1,
        }
        defaults.update(values)
        for key, value in defaults.items():
            setattr(self, key, value)

    def to_dict(self):
        return {
            key: value.isoformat() if isinstance(value, datetime) else value
            for key, value in self.__dict__.items()
        }


class _Query:
    def __init__(self, *, first=None, rows=None):
        self.first_value = first
        self.rows = list(rows or [])

    def filter(self, *_expressions):
        return self

    def filter_by(self, **_values):
        return self

    def offset(self, _value):
        return self

    def limit(self, _value):
        return self

    def order_by(self, *_values):
        return self

    def first(self):
        return self.first_value

    def all(self):
        return self.rows


class _Result:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows

    def __iter__(self):
        return iter(self.rows)


class _Row:
    def __init__(self, **values):
        self._mapping = values


class _Session:
    def __init__(self):
        self.queries = []
        self.execute_result = _Result([])
        self.added = []
        self.deleted = []
        self.commits = 0
        self.rollbacks = 0
        self.flushes = 0

    def query(self, _model):
        return self.queries.pop(0) if self.queries else _Query()

    def execute(self, *_args, **_kwargs):
        return self.execute_result

    def add(self, value):
        self.added.append(value)

    def delete(self, value):
        self.deleted.append(value)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def flush(self):
        self.flushes += 1


class _Cache:
    def __init__(self):
        self.values = {}
        self.deleted = []

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value, timeout=None):
        self.values[key] = value

    def delete(self, key):
        self.deleted.append(key)


def _manager(tenant="tenant-a"):
    from backend.ukg_db import UkgDatabaseManager

    session = _Session()
    models = SimpleNamespace(
        Node=_Model, Edge=_Model, KnowledgeAlgorithm=_Model, KAExecution=_Model,
        UkgSession=_Model, MemoryEntry=_Model,
    )
    manager = UkgDatabaseManager(
        tenant_id=tenant,
        db_session=SimpleNamespace(session=session),
        models_module=models,
        cache_client=_Cache(),
    )
    return manager, session


def test_node_listing_cache_update_and_delete_contracts():
    manager, session = _manager()
    node = _Model(uid="node-1", label="Node 1")
    session.queries = [_Query(rows=[node])]
    assert manager.get_nodes_by_type("concept", limit=2, offset=1)[0]["uid"] == "node-1"

    manager.cache.values["node:cached:tenant-a"] = {"uid": "cached"}
    assert manager.get_node_by_uid("cached") == {"uid": "cached"}
    session.queries = [_Query(first=node)]
    assert manager.get_node_by_uid("node-1")["uid"] == "node-1"

    session.queries = [_Query(first=node)]
    updated = manager.update_node("node-1", {
        "node_type": "axis", "label": "Updated", "description": "New",
        "original_id": "old", "axis_number": 2, "level": 3, "attributes": {"x": 1},
    })
    assert updated["label"] == "Updated"
    session.queries = [_Query(first=node)]
    assert manager.delete_node("node-1") is True
    session.queries = [_Query(first=None)]
    assert manager.delete_node("missing") is False


def test_edge_create_update_listing_traversal_and_delete_contracts():
    manager, session = _manager()
    source = _Model(id=1, uid="source")
    target = _Model(id=2, uid="target")
    edge = _Model(id=10, uid="edge-1", source_id=1, target_id=2)

    session.queries = [_Query(first=source), _Query(first=target)]
    created = manager.create_edge({
        "uid": "edge-new", "edge_type": "related", "source_uid": "source",
        "target_uid": "target", "label": "relates", "weight": 0.7, "attributes": {"a": 1},
    })
    assert created["uid"] == "edge-new"
    session.queries = [_Query(first=None), _Query(first=target)]
    assert manager.create_edge({"source_uid": "missing", "target_uid": "target"}) is None

    session.queries = [_Query(first=edge), _Query(first=source), _Query(first=target)]
    updated = manager.update_edge("edge-1", {
        "edge_type": "supports", "label": "supports", "weight": 0.9,
        "attributes": {"b": 2}, "source_uid": "source", "target_uid": "target",
    })
    assert updated["edge_type"] == "supports"
    manager.cache.values["edge:cached:tenant-a"] = {"uid": "cached"}
    assert manager.get_edge_by_uid("cached") == {"uid": "cached"}
    session.queries = [_Query(first=edge)]
    assert manager.get_edge_by_uid("edge-1")["uid"] == "edge-1"

    session.queries = [_Query(rows=[edge]), _Query(first=source), _Query(first=target)]
    listed = manager.get_edges_by_type("supports")
    assert listed[0]["source_uid"] == "source" and listed[0]["target_uid"] == "target"
    session.queries = [_Query(first=source), _Query(rows=[edge]), _Query(first=target)]
    assert manager.get_outgoing_edges("source")[0]["target_uid"] == "target"
    session.queries = [_Query(first=target), _Query(rows=[edge]), _Query(first=source)]
    assert manager.get_incoming_edges("target")[0]["source_uid"] == "source"
    session.queries = [_Query(first=None)]
    assert manager.get_outgoing_edges("missing") == []
    session.queries = [_Query(first=None)]
    assert manager.get_incoming_edges("missing") == []

    session.queries = [_Query(first=edge)]
    assert manager.delete_edge("edge-1") is True
    session.queries = [_Query(first=None)]
    assert manager.delete_edge("missing") is False


def test_algorithm_execution_helpers_and_queries():
    manager, session = _manager()
    algorithm = _Model(id=7, ka_id="KA-007")
    created = manager.create_knowledge_algorithm({
        "ka_id": "KA-007", "name": "Algorithm", "description": "D",
        "input_schema": {"type": "object"}, "output_schema": {}, "version": "2",
    })
    assert created["ka_id"] == "KA-007"
    session.queries = [_Query(first=algorithm)]
    assert manager.get_knowledge_algorithm("KA-007")["id"] == 7
    session.queries = [_Query(first=None)]
    assert manager.get_knowledge_algorithm("missing") is None

    assert manager._normalize_ka_execution_status("started") == "running"
    assert manager._normalize_ka_execution_status("success") == "completed"
    assert manager._normalize_ka_execution_status("error") == "failed"
    assert manager._normalize_ka_execution_status("blocked") == "blocked"
    assert manager._normalize_ka_execution_status("other") == "pending"
    assert manager._duration_ms({"duration_ms": "12.4"}) == 12
    assert manager._duration_ms({"execution_time": 0.5}) == 500
    assert manager._duration_ms({"duration_ms": "bad"}) is None
    assert manager._coerce_datetime("2026-01-01T00:00:00Z").tzinfo is not None
    assert manager._coerce_datetime("bad") is None
    assert manager._coerce_datetime(3) is None
    assert manager._execution_input_data({"params": {"x": 1}, "session_id": "s"}) == {"x": 1, "session_id": "s"}
    assert manager._execution_input_data({"input_data": "raw", "session_id": "s"}) == {"value": "raw", "session_id": "s"}
    assert manager._execution_input_data({"session_id": "s"}) == {"session_id": "s"}

    session.queries = [_Query(first=None)]
    execution = manager.create_ka_execution({
        "ka_id": "KA-008", "execution_id": "exec-1", "status": "success",
        "params": {"x": 1}, "results": {"ok": True}, "duration_ms": 8,
        "start_time": "2026-01-01T00:00:00Z", "end_time": "2026-01-01T00:00:01Z",
        "session_id": "session-1",
    })
    assert execution["execution_id"] == "exec-1" and session.flushes == 1
    assert manager.create_ka_execution({}) is None

    row = _Model(uid="exec-2", input_data={"session_id": "session-1"})
    session.queries = [_Query(rows=[row, _Model(uid="other", input_data={"session_id": "other"})])]
    rows = manager.get_ka_executions({"ka_id": "KA-001", "status": "completed", "session_id": "session-1"}, limit="bad", offset="bad")
    assert [item["uid"] for item in rows] == ["exec-2"]


def test_session_memory_search_neighbors_and_raw_query_contracts():
    manager, session = _manager()
    created_session = manager.create_session(user_query="question")
    assert created_session["status"] == "active"
    saved_session = _Model(session_id="session-1", status="active")
    session.queries = [_Query(first=saved_session)]
    assert manager.get_session("session-1")["session_id"] == "session-1"
    session.queries = [_Query(first=saved_session)]
    completed = manager.complete_session("session-1", 0.9)
    assert completed["status"] == "completed"

    session.queries = [_Query(first=saved_session)]
    memory = manager.add_memory_entry("session-1", "fact", content={"value": 1})
    assert memory["entry_type"] == "fact"
    session.queries = [_Query(first=None)]
    assert manager.add_memory_entry("missing", "fact") is None
    entry = _Model(entry_type="fact", session_id="session-1")
    session.queries = [_Query(rows=[entry])]
    assert manager.get_memory_entries("session-1", "fact", pass_num=1)[0]["entry_type"] == "fact"

    session.execute_result = _Result([_Row(uid="node-1", created_at=datetime(2026, 1, 1, tzinfo=UTC))])
    searched = manager.search_nodes("record", ["concept"], [1, 2], limit=5)
    assert searched[0]["created_at"].startswith("2026-01-01")

    start = _Model(id=1, uid="start")
    outgoing = _Model(id=10, source_id=1, target_id=2)
    incoming = _Model(id=11, source_id=3, target_id=1)
    nodes = [start, _Model(id=2, uid="two"), _Model(id=3, uid="three")]
    session.queries = [
        _Query(first=start), _Query(rows=[outgoing]), _Query(rows=[incoming]),
        _Query(rows=nodes), _Query(rows=[outgoing, incoming]),
    ]
    neighbors = manager.get_neighbors("start", ["related"], direction="both", max_depth=1)
    assert len(neighbors["nodes"]) == 3 and len(neighbors["edges"]) == 2
    session.queries = [_Query(first=None)]
    assert manager.get_neighbors("missing") == {"nodes": [], "edges": []}

    session.execute_result = _Result([_Row(value=1, at=datetime(2026, 1, 1, tzinfo=UTC))])
    raw = manager.execute_raw_query("SELECT 1")
    assert raw[0]["at"].startswith("2026-01-01")
    assert manager.close() is None

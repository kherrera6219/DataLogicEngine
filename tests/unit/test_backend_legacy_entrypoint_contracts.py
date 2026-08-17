from __future__ import annotations

import inspect
from contextlib import nullcontext
from types import SimpleNamespace

import pytest
from flask import Flask


class _Query:
    def __init__(self, *, first=None, rows=None, count=0):
        self.first_value = first
        self.rows = list(rows or [])
        self.count_value = count
        self.filters = []

    def filter_by(self, **values):
        self.filters.append(values)
        return self

    def first(self):
        return self.first_value

    def all(self):
        return self.rows

    def count(self):
        return self.count_value

    def order_by(self, *_args):
        return self

    def limit(self, _value):
        return self


class _Column:
    def desc(self):
        return self


class _Session:
    def __init__(self):
        self.added = []
        self.commits = 0
        self.flushes = 0

    def add(self, value):
        self.added.append(value)

    def add_all(self, values):
        self.added.extend(values)

    def commit(self):
        self.commits += 1

    def flush(self):
        self.flushes += 1
        for index, value in enumerate(self.added, 1):
            if not getattr(value, "id", None):
                value.id = index


class _Record:
    query = _Query()
    created_at = _Column()
    _next_id = 1

    def __init__(self, **values):
        self.id = _Record._next_id
        _Record._next_id += 1
        for key, value in values.items():
            setattr(self, key, value)

    def set_password(self, value):
        self.password = value

    def to_dict(self):
        return {
            "id": self.id,
            "title": getattr(self, "title", None),
            "role": getattr(self, "role", None),
            "content": getattr(self, "content", None),
        }


def test_init_database_builds_users_samples_and_graph(monkeypatch):
    import backend.init_db as module

    session = _Session()
    fake_db = SimpleNamespace(session=session, create_all=lambda: None)
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "User", _Record)
    monkeypatch.setattr(module, "SimulationSession", _Record)
    monkeypatch.setattr(module, "KnowledgeGraphNode", _Record)
    monkeypatch.setattr(module, "KnowledgeGraphEdge", _Record)
    monkeypatch.setattr(module, "app", SimpleNamespace(app_context=nullcontext))
    monkeypatch.setenv("INIT_ADMIN_PASSWORD", "admin-secret")
    monkeypatch.setenv("INIT_DEMO_PASSWORD", "demo-secret")

    _Record.query = _Query(first=None)
    module.create_admin_user()
    module.create_demo_user()
    assert {item.username for item in session.added if hasattr(item, "username")} == {"admin", "demo"}

    demo = SimpleNamespace(id=42)
    _Record.query = _Query(first=demo, count=0)
    module.create_sample_simulations()
    _Record.query = _Query(count=0)
    module.create_sample_graph_nodes()
    assert any(getattr(item, "status", None) == "completed" for item in session.added)
    assert any(getattr(item, "edge_type", None) == "association" for item in session.added)

    calls = []
    monkeypatch.setattr(module, "create_admin_user", lambda: calls.append("admin"))
    monkeypatch.setattr(module, "create_demo_user", lambda: calls.append("demo"))
    monkeypatch.setattr(module, "create_sample_simulations", lambda: calls.append("simulations"))
    monkeypatch.setattr(module, "create_sample_graph_nodes", lambda: calls.append("graph"))
    module.init_database()
    assert calls == ["admin", "demo", "simulations", "graph"]


def test_init_database_existing_and_password_policy_branches(monkeypatch):
    import backend.init_db as module

    session = _Session()
    monkeypatch.setattr(module, "db", SimpleNamespace(session=session))
    monkeypatch.setattr(module, "User", _Record)
    monkeypatch.setattr(module, "SimulationSession", _Record)
    monkeypatch.setattr(module, "KnowledgeGraphNode", _Record)
    monkeypatch.setattr(module, "KnowledgeGraphEdge", _Record)

    existing = SimpleNamespace(id=1)
    _Record.query = _Query(first=existing, count=1)
    monkeypatch.delenv("INIT_ADMIN_PASSWORD", raising=False)
    monkeypatch.setenv("FLASK_ENV", "production")
    with pytest.raises(RuntimeError, match="INIT_ADMIN_PASSWORD"):
        module.create_admin_user()

    monkeypatch.setenv("FLASK_ENV", "development")
    module.create_admin_user()
    monkeypatch.delenv("INIT_DEMO_PASSWORD", raising=False)
    module.create_demo_user()
    module.create_sample_simulations()
    module.create_sample_graph_nodes()
    assert session.added == []


def test_seed_data_creates_each_reference_family(monkeypatch):
    import backend.seed_data as module

    session = _Session()
    monkeypatch.setattr(module, "db", SimpleNamespace(session=session, create_all=lambda: None))

    class Pillar(_Record):
        query = _Query(first=None)

    class Sector(_Record):
        query = _Query(first=None)

    class Domain(_Record):
        query = _Query(first=None)

    class Node(_Record):
        query = _Query(first=None)

    class Edge(_Record):
        query = _Query(first=None)

    monkeypatch.setattr(module, "PillarLevel", Pillar)
    monkeypatch.setattr(module, "Sector", Sector)
    monkeypatch.setattr(module, "Domain", Domain)
    monkeypatch.setattr(module, "Node", Node)
    monkeypatch.setattr(module, "Edge", Edge)

    assert module.generate_uid("node").startswith("node-")
    assert module.seed_pillars() == 17
    assert module.seed_sectors() == 15
    assert module.seed_domains() == 13
    assert module.seed_nodes() == 25

    Node.query = _Query(rows=[SimpleNamespace(id=1), SimpleNamespace(id=2), SimpleNamespace(id=3)])
    assert module.seed_edges() == 2
    assert session.commits == 5


def test_seed_data_guards_existing_rows_and_orchestrates(monkeypatch):
    import backend.seed_data as module

    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.delenv("ALLOW_SEED", raising=False)
    allowed, reason = module._seeding_allowed()
    assert not allowed and "Refusing to seed" in reason
    monkeypatch.setenv("ALLOW_SEED", "true")
    assert module._seeding_allowed() == (True, "")
    monkeypatch.setenv("FLASK_ENV", "development")
    assert module._seeding_allowed() == (True, "")

    class Existing(_Record):
        query = _Query(first=SimpleNamespace(id=9))

    session = _Session()
    monkeypatch.setattr(module, "db", SimpleNamespace(session=session, create_all=lambda: None))
    monkeypatch.setattr(module, "PillarLevel", Existing)
    monkeypatch.setattr(module, "Sector", Existing)
    monkeypatch.setattr(module, "Domain", Existing)
    monkeypatch.setattr(module, "Node", Existing)
    monkeypatch.setattr(module, "Edge", Existing)
    assert module.seed_pillars() == 0
    assert module.seed_sectors() == 0
    assert module.seed_domains() == 0
    assert module.seed_nodes() == 0
    Existing.query = _Query(rows=[SimpleNamespace(id=1)])
    assert module.seed_edges() == 0

    monkeypatch.setattr(module, "app", SimpleNamespace(app_context=nullcontext))
    monkeypatch.setattr(module, "seed_pillars", lambda: 1)
    monkeypatch.setattr(module, "seed_sectors", lambda: 2)
    monkeypatch.setattr(module, "seed_domains", lambda: 3)
    monkeypatch.setattr(module, "seed_nodes", lambda: 4)
    monkeypatch.setattr(module, "seed_edges", lambda: 5)
    assert module.run_seed() == 15


def test_confidence_calculator_covers_evidence_ka_persona_and_gate_paths():
    from backend.truth_engine.confidence_calculator import ConfidenceCalculator

    calculator = ConfidenceCalculator()
    run = SimpleNamespace(
        evidence_items=[SimpleNamespace(status="verified"), SimpleNamespace(status="failed")],
        ka_invocations=[SimpleNamespace(status="success"), SimpleNamespace(status="failed")],
        personas=[SimpleNamespace(consensus_reached=True), SimpleNamespace(consensus_reached=False)],
        truthgate_decision="allow",
    )
    assert calculator.calculate(run) == pytest.approx(0.533)
    assert calculator._gate_factor(" BLOCK ") == 0.0
    assert calculator._gate_factor("unknown") == 0.8
    assert calculator._ka_consensus(SimpleNamespace(ka_invocations=[]), [{"status": "pass"}, {"status": "fail"}]) == 0.5
    assert calculator._ka_consensus(SimpleNamespace(ka_invocations=[]), None) == 0.5
    assert calculator._evidence_quality(SimpleNamespace(evidence_items=[])) == 0.5
    assert calculator._persona_agreement(SimpleNamespace(personas=[])) == 0.5

    class Broken:
        @property
        def evidence_items(self):
            raise RuntimeError("lazy load failed")

        @property
        def ka_invocations(self):
            raise RuntimeError("lazy load failed")

        @property
        def personas(self):
            raise RuntimeError("lazy load failed")

    broken = Broken()
    assert calculator._evidence_quality(broken) == 0.5
    assert calculator._ka_consensus(broken, None) == 0.5
    assert calculator._persona_agreement(broken) == 0.5

    class BrokenCalculator(ConfidenceCalculator):
        @staticmethod
        def _evidence_quality(_run):
            raise RuntimeError("calculation failed")

    assert BrokenCalculator().calculate(run) == 0.5


def _call_route(function, *args):
    return inspect.unwrap(function)(*args)


def test_legacy_chat_crud_message_and_search_contracts(monkeypatch):
    import backend.chat as module
    import backend.services.rag_service as rag_module

    app = Flask(__name__)
    session = _Session()
    monkeypatch.setattr(module, "db", SimpleNamespace(session=session))
    monkeypatch.setattr(module, "get_jwt_identity", lambda: 7)

    chat = _Record(title="Existing", user_id=7)
    message = _Record(chat_id=chat.id, role="user", content="Earlier")

    class Chat(_Record):
        created_at = _Column()
        query = _Query(first=chat, rows=[chat])

    class Message(_Record):
        created_at = _Column()
        query = _Query(rows=[message])

    monkeypatch.setattr(module, "Chat", Chat)
    monkeypatch.setattr(module, "Message", Message)

    with app.test_request_context("/chats"):
        response, status = _call_route(module.get_chats)
        assert status == 200 and response.get_json()[0]["title"] == "Existing"
    with app.test_request_context("/chats", method="POST", json={}):
        response, status = _call_route(module.create_chat)
        assert status == 201 and response.get_json()["title"] == "New Chat"
    with app.test_request_context(f"/chats/{chat.id}"):
        response, status = _call_route(module.get_chat, chat.id)
        assert status == 200 and response.get_json()["messages"]

    rag = SimpleNamespace(
        store_chat_message=lambda **_values: None,
        search_chat_history=lambda **_values: [{"message_id": "1"}],
    )
    monkeypatch.setattr(rag_module, "get_rag_service", lambda: rag)
    monkeypatch.setattr(module, "_call_llm_gateway", lambda **_values: {
        "content": "Assistant answer", "provider": "openai", "model": "gpt", "run_id": "run-1",
    })
    with app.test_request_context(f"/chats/{chat.id}/messages", method="POST", json={"content": "Question"}):
        response, status = _call_route(module.add_message, chat.id)
        assert status == 201 and response.get_json()["metadata"]["run_id"] == "run-1"
    with app.test_request_context(f"/chats/{chat.id}/search?q=answer"):
        response, status = _call_route(module.search_chat_history, chat.id)
        assert status == 200 and response.get_json()["results"]


def test_legacy_chat_validation_errors_and_gateway_outcomes(monkeypatch):
    import backend.chat as module
    import backend.llm_gateway.gateway as gateway_module
    import backend.services.rag_service as rag_module

    app = Flask(__name__)
    monkeypatch.setattr(module, "get_jwt_identity", lambda: 8)

    class MissingChat(_Record):
        created_at = _Column()
        query = _Query(first=None)

    monkeypatch.setattr(module, "Chat", MissingChat)
    with app.test_request_context("/chats/99"):
        assert _call_route(module.get_chat, 99)[1] == 404
    with app.test_request_context("/chats/99/messages", method="POST", json={}):
        assert _call_route(module.add_message, 99)[1] == 400
    with app.test_request_context("/chats/99/messages", method="POST", json={"content": "x"}):
        assert _call_route(module.add_message, 99)[1] == 404
    with app.test_request_context("/chats/99/search"):
        assert _call_route(module.search_chat_history, 99)[1] == 400
    with app.test_request_context("/chats/99/search?q=x"):
        assert _call_route(module.search_chat_history, 99)[1] == 404

    chat = SimpleNamespace(id=1)
    MissingChat.query = _Query(first=chat)
    monkeypatch.setattr(rag_module, "get_rag_service", lambda: SimpleNamespace(search_chat_history=lambda **_values: (_ for _ in ()).throw(RuntimeError("search failed"))))
    with app.test_request_context("/chats/1/search?q=x"):
        assert _call_route(module.search_chat_history, 1)[1] == 500

    class Gateway:
        def __init__(self, **_values):
            pass

        def process(self, _request):
            return None

    monkeypatch.setattr(gateway_module, "LLMGateway", Gateway)
    monkeypatch.setattr(module, "db", SimpleNamespace(session=object()))
    ok = SimpleNamespace(ok=True, content="answer", provider_used="openai", model_used="gpt", run_id="run-ok")
    monkeypatch.setattr(module, "run_async", lambda _coro: ok)
    messages = [{"role": "user", "content": "hello"}]
    assert module._call_llm_gateway(messages, 8, "1")["content"] == "answer"
    failed = SimpleNamespace(ok=False, error="denied", run_id="run-fail")
    monkeypatch.setattr(module, "run_async", lambda _coro: failed)
    assert module._call_llm_gateway(messages, 8, "1")["error"] == "denied"
    monkeypatch.setattr(module, "run_async", lambda _coro: (_ for _ in ()).throw(RuntimeError("boom")))
    assert module._call_llm_gateway(messages, 8, "1")["error"] == "boom"

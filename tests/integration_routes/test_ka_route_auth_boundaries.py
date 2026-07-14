from types import SimpleNamespace
from datetime import UTC, datetime

from backend.auth import api_decorators
from backend.routes import ka_routes
from extensions import db
from tests.conftest import create_test_user, seed_login_session


def _assert_json_unauthorized(response):
    assert response.status_code == 401
    body = response.get_json()
    assert body["success"] is False
    assert body["code"] == "UNAUTHORIZED"


class _FakeKAController:
    def __init__(self):
        self.algorithms = {
            "KA-001": {
                "metadata": {
                    "KA_ID": "KA-001",
                    "KA_Name": "Algorithm of Thought",
                    "Category": "Reasoning",
                    "Purpose": "Decompose query into ordered tasks and dependencies",
                    "Status": "Active",
                    "Risk_Class": "Low",
                }
            }
        }
        self.last_execution = None

    def get_available_algorithms(self):
        return self.algorithms

    def _normalize_ka_id(self, ka_id):
        return str(ka_id).upper()

    def execute_algorithm(self, ka_id, input_data):
        self.last_execution = (ka_id, input_data)
        return {
            "success": True,
            "output": {"echo": input_data},
            "execution_time": 0.012,
        }


class _FailingKAController(_FakeKAController):
    def execute_algorithm(self, ka_id, input_data):
        raise RuntimeError("<script>alert('secret-stack')</script>")


class _FakeTruthEngine:
    def __init__(self):
        self.created_session = None
        self.processed_session_id = None

    async def create_session(self, query, user_id=None, tenant_id=None, context=None, tier=None):
        self.created_session = {
            "query": query,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "context": context,
            "tier": tier,
        }
        return {"session_id": "truth-session-1"}

    async def process(self, session_id):
        self.processed_session_id = session_id
        return {
            "status": "completed",
            "session_id": session_id,
            "result": {"ok": True, "status": "completed"},
        }

    def get_session_status(self, session_id):
        return {
            "status": "completed",
            "workflow_steps": [{"name": "intent_parsing", "status": "completed"}],
        }


def _install_api_key_user(app, monkeypatch, *, username="ka_api_key_user"):
    with app.app_context():
        user_id = create_test_user(
            username=username,
            email=f"{username}@test.com",
        )

    monkeypatch.setattr(
        api_decorators.ExternalAPIKey,
        "verify_key",
        staticmethod(lambda _key: SimpleNamespace(user_id=user_id, permissions={"read": True})),
    )
    return user_id


def _insert_ka_execution(
    app,
    *,
    uid,
    ka_id="KA-001",
    status="completed",
    input_data=None,
    output_data=None,
    error_message=None,
    execution_time_ms=42,
):
    from models import KAExecution, KnowledgeAlgorithm

    with app.app_context():
        if KnowledgeAlgorithm.query.filter_by(ka_id=ka_id).first() is None:
            db.session.add(
                KnowledgeAlgorithm(
                    uid=f"ka-{ka_id.lower()}",
                    ka_id=ka_id,
                    name=ka_id,
                    description="Test KA",
                )
            )
            db.session.flush()
        execution = KAExecution(
            uid=uid,
            ka_id=ka_id,
            status=status,
            input_data=input_data,
            output_data=output_data,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
            started_at=datetime(2026, 7, 4, 12, 0, tzinfo=UTC),
            completed_at=datetime(2026, 7, 4, 12, 0, 1, tzinfo=UTC),
        )
        db.session.add(execution)
        db.session.commit()
        return execution.id


def test_live_ka_routes_are_registered(app):
    """The active KA blueprint, not backend/api/ka_management.py, owns KA routes."""
    rules = {str(rule.rule) for rule in app.url_map.iter_rules()}

    assert "/api/v1/ka/algorithms" in rules
    assert "/api/ka/algorithms" in rules


def test_ka_algorithm_list_requires_json_auth(client):
    response = client.get("/api/v1/ka/algorithms")
    _assert_json_unauthorized(response)


def test_ka_health_remains_public(app, client, monkeypatch):
    monkeypatch.setattr(ka_routes, "_controller", _FakeKAController())

    response = client.get("/api/v1/ka/health")

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["total_algorithms"] == 1


def test_ka_algorithm_list_accepts_external_api_key(app, client, monkeypatch):
    monkeypatch.setattr(ka_routes, "_controller", _FakeKAController())
    _install_api_key_user(app, monkeypatch)

    response = client.get(
        "/api/v1/ka/algorithms",
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["algorithms"][0]["id"] == "KA-001"
    assert body["algorithms"][0]["purpose"] == "Decompose query into ordered tasks and dependencies"
    assert body["algorithms"][0]["description"] == "Decompose query into ordered tasks and dependencies"


def test_ka_algorithm_list_clamps_invalid_pagination(app, client, monkeypatch):
    monkeypatch.setattr(ka_routes, "_controller", _FakeKAController())
    _install_api_key_user(app, monkeypatch, username="ka_pagination_user")

    response = client.get(
        "/api/v1/ka/algorithms?page=0&per_page=0",
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["pagination"]["page"] == 1
    assert body["pagination"]["per_page"] == 1


def test_ka_algorithm_list_uses_id_as_name_fallback(app, client, monkeypatch):
    controller = _FakeKAController()
    controller.algorithms["KA-001"]["metadata"].pop("KA_Name")
    monkeypatch.setattr(ka_routes, "_controller", controller)
    _install_api_key_user(app, monkeypatch, username="ka_name_fallback_user")

    response = client.get(
        "/api/v1/ka/algorithms",
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["algorithms"][0]["id"] == "KA-001"
    assert body["algorithms"][0]["name"] == "KA-001"


def test_ka_execute_accepts_documented_payload_with_api_key_principal(app, client, monkeypatch):
    controller = _FakeKAController()
    monkeypatch.setattr(ka_routes, "_controller", controller)
    _install_api_key_user(app, monkeypatch, username="ka_execute_user")

    response = client.post(
        "/api/v1/ka/algorithms/KA-001/execute",
        json={"data": {"value": 7}, "context": {"source": "route-test"}},
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert controller.last_execution == (
        "KA-001",
        {"value": 7, "context": {"source": "route-test"}},
    )


def test_ka_invalid_algorithm_id_does_not_reflect_path_input(app, client, monkeypatch):
    monkeypatch.setattr(ka_routes, "_controller", _FakeKAController())
    _install_api_key_user(app, monkeypatch, username="ka_invalid_id_user")

    response = client.get(
        "/api/v1/ka/algorithms/KA-%3Cscript%3E",
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 400
    body = response.get_json()
    assert body["success"] is False
    assert body["error"] == "Invalid algorithm ID"
    assert "<script>" not in response.get_data(as_text=True)


def test_ka_execute_hides_backend_exception_details(app, client, monkeypatch):
    monkeypatch.setattr(ka_routes, "_controller", _FailingKAController())
    _install_api_key_user(app, monkeypatch, username="ka_execute_exception_user")

    response = client.post(
        "/api/v1/ka/algorithms/KA-001/execute",
        json={"input": {"value": 7}},
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 500
    body = response.get_json()
    assert body["success"] is False
    assert body["error"] == "An internal error occurred. Please try again later."
    assert "secret-stack" not in response.get_data(as_text=True)


def test_ka_history_serializes_persisted_execution_for_frontend(app, client, monkeypatch):
    controller = _FakeKAController()
    controller.algorithms["KA-001"]["metadata"]["Risk_Class"] = "High"
    monkeypatch.setattr(ka_routes, "_controller", controller)
    _install_api_key_user(app, monkeypatch, username="ka_history_user")
    execution_id = _insert_ka_execution(app, uid="ka-exec-history-1")

    response = client.get(
        "/api/v1/ka/history?limit=bad",
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["executions"] == [
        {
            "id": str(execution_id),
            "ka_id": "KA-001",
            "ka_name": "Algorithm of Thought",
            "risk_tier": "destructive",
            "status": "success",
            "triggered_by": "user",
            "run_id": None,
            "duration_ms": 42,
            "created_at": "2026-07-04T12:00:00",
            "error": None,
        }
    ]


def test_ka_history_normalizes_case_and_extracts_trace_run_id(app, client, monkeypatch):
    controller = _FakeKAController()
    monkeypatch.setattr(ka_routes, "_controller", controller)
    _install_api_key_user(app, monkeypatch, username="ka_history_trace_user")
    _insert_ka_execution(
        app,
        uid="ka-exec-history-2",
        ka_id="ka-001",
        status="failed",
        input_data={"trace_run_id": "trace-run-1"},
        error_message="boom",
    )

    response = client.get(
        "/api/v1/ka/history",
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["executions"][0]["ka_id"] == "KA-001"
    assert body["executions"][0]["status"] == "failure"
    assert body["executions"][0]["run_id"] == "trace-run-1"
    assert body["executions"][0]["error"] == "boom"


def test_trace_ka_execution_feed_tolerates_invalid_limit(app, client):
    seed_login_session(client, app, username="ka_feed_user")
    _insert_ka_execution(app, uid="ka-feed-exec-1")

    response = client.get("/api/v1/trace/ka-execution-feed?limit=bad")

    assert response.status_code == 200
    body = response.get_json()
    assert body["limit"] == 20
    assert body["items"][0]["uid"] == "ka-feed-exec-1"


def test_ka_execute_rejects_non_object_json(app, client, monkeypatch):
    monkeypatch.setattr(ka_routes, "_controller", _FakeKAController())
    _install_api_key_user(app, monkeypatch, username="ka_execute_bad_body_user")

    response = client.post(
        "/api/v1/ka/algorithms/KA-001/execute",
        json=["not", "an", "object"],
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 400
    body = response.get_json()
    assert body["success"] is False
    assert body["error"] == "JSON body must be an object"


def test_ka_batch_rejects_non_list_algorithm_ids(app, client, monkeypatch):
    monkeypatch.setattr(ka_routes, "_controller", _FakeKAController())
    _install_api_key_user(app, monkeypatch, username="ka_batch_bad_ids_user")

    response = client.post(
        "/api/v1/ka/batch",
        json={"algorithms": "KA-001", "input": {"value": 7}},
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 400
    body = response.get_json()
    assert body["success"] is False
    assert body["error"] == "algorithms must be a list"


def test_ka_batch_accepts_documented_payload_with_context(app, client, monkeypatch):
    controller = _FakeKAController()
    monkeypatch.setattr(ka_routes, "_controller", controller)
    _install_api_key_user(app, monkeypatch, username="ka_batch_payload_user")

    response = client.post(
        "/api/v1/ka/batch",
        json={
            "algorithms": ["KA-001"],
            "data": {"value": 7},
            "context": {"source": "batch-test"},
        },
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["executed_count"] == 1
    assert controller.last_execution == (
        "KA-001",
        {"value": 7, "context": {"source": "batch-test"}},
    )


def test_ka_batch_hides_per_item_exception_details(app, client, monkeypatch):
    monkeypatch.setattr(ka_routes, "_controller", _FailingKAController())
    _install_api_key_user(app, monkeypatch, username="ka_batch_exception_user")

    response = client.post(
        "/api/v1/ka/batch",
        json={"algorithms": ["KA-001"], "input": {"value": 7}},
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["results"][0]["error"] == "Algorithm execution failed"
    assert "secret-stack" not in response.get_data(as_text=True)


def test_ka_high_stakes_workflow_runs_async_engine_with_api_key_principal(
    app,
    client,
    monkeypatch,
):
    user_id = _install_api_key_user(app, monkeypatch, username="ka_workflow_user")
    fake_engine = _FakeTruthEngine()
    monkeypatch.setattr(
        "backend.truth_engine.api.get_truth_core_engine",
        lambda: fake_engine,
    )

    response = client.post(
        "/api/v1/ka/workflow/high-stakes",
        json={"query": "audit this", "context": {"slice": 5}},
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["session_id"] == "truth-session-1"
    assert fake_engine.created_session == {
        "query": "audit this",
        "user_id": user_id,
        "tenant_id": None,
        "context": {"slice": 5},
        "tier": "high_stakes",
    }
    assert fake_engine.processed_session_id == "truth-session-1"


def test_ka_high_stakes_workflow_rejects_non_object_context(app, client, monkeypatch):
    _install_api_key_user(app, monkeypatch, username="ka_workflow_bad_context_user")

    response = client.post(
        "/api/v1/ka/workflow/high-stakes",
        json={"query": "audit this", "context": "bad"},
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 400
    body = response.get_json()
    assert body["success"] is False
    assert body["error"] == "context must be an object"


def test_ka_trace_uses_truth_engine_api_accessor(app, client, monkeypatch):
    _install_api_key_user(app, monkeypatch, username="ka_trace_user")
    fake_engine = _FakeTruthEngine()
    monkeypatch.setattr(
        "backend.truth_engine.api.get_truth_core_engine",
        lambda: fake_engine,
    )

    response = client.get(
        "/api/v1/ka/trace/truth-session-1",
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["status"] == "completed"
    assert body["trace"] == [{"name": "intent_parsing", "status": "completed"}]


def test_ka_layers_accepts_non_numeric_layer_names(app, client, monkeypatch):
    controller = _FakeKAController()
    controller.algorithms["KA-001"]["metadata"]["Primary_Layers"] = "Layer 1;L2"
    monkeypatch.setattr(ka_routes, "_controller", controller)
    _install_api_key_user(app, monkeypatch, username="ka_layers_user")

    response = client.get(
        "/api/v1/ka/layers",
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert set(body["layers"].keys()) == {"L2", "Layer 1"}


def test_legacy_ka_alias_emits_deprecation_headers(app, client, monkeypatch):
    monkeypatch.setattr(ka_routes, "_controller", _FakeKAController())
    _install_api_key_user(app, monkeypatch, username="ka_legacy_alias_user")

    response = client.get(
        "/api/ka/algorithms",
        headers={"X-API-Key": "ukg_valid_ka_key"},
    )

    assert response.status_code == 200
    assert response.headers["Deprecation"] == "true"
    assert response.headers["Link"] == '</api/v1/ka/algorithms>; rel="successor-version"'

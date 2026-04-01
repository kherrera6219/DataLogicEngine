from types import SimpleNamespace

from app import db
from models import SimulationSession, User
import routes.simulation_routes as simulation_routes_module


class _GatewayOk:
    def __init__(self):
        self.requests = []

    async def process(self, request):
        self.requests.append(request)
        return SimpleNamespace(
            ok=True,
            content="gateway answer",
            error=None,
            run_id="run-123",
            provider_used="test-provider",
            model_used="test-model",
            explainability={"confidence_score": 0.91},
            layers=["ingest", "synthesize"],
            warnings=[],
        )


class _GatewayFail:
    async def process(self, request):
        return SimpleNamespace(
            ok=False,
            content="",
            error="No active providers found",
            run_id="run-err",
            provider_used=None,
            model_used=None,
            explainability={},
            layers=[],
            warnings=["provider unavailable"],
        )


def _create_user(app, username: str, email: str) -> int:
    with app.app_context():
        user = User(username=username, active=True)
        user.email = email
        user.set_password("StrongPass789!Aa")
        db.session.add(user)
        db.session.commit()
        return user.id


def _create_simulation(app, *, owner_id: int, session_id: str, status: str = "active") -> SimulationSession:
    with app.app_context():
        simulation = SimulationSession(
            session_id=session_id,
            user_id=owner_id,
            name="Owned Simulation",
            parameters={"query": "Explain retention policy", "context": {"domain": "compliance"}},
            status=status,
            current_step=0,
            results={},
        )
        db.session.add(simulation)
        db.session.commit()
        return simulation


def test_simulation_get_and_stop_are_scoped_to_authenticated_user(app, authenticated_client):
    owner_id = _create_user(app, "owner2", "owner2@example.com")
    _create_simulation(app, owner_id=owner_id, session_id="sim-owner-2")

    get_response = authenticated_client.get("/api/v1/simulations/sim-owner-2")
    stop_response = authenticated_client.post("/api/v1/simulations/sim-owner-2/stop")

    assert get_response.status_code == 404
    assert stop_response.status_code == 404


def test_simulation_run_is_scoped_to_authenticated_user(app, authenticated_client, monkeypatch):
    owner_id = _create_user(app, "owner3", "owner3@example.com")
    _create_simulation(app, owner_id=owner_id, session_id="sim-owner-3")
    monkeypatch.setattr(
        simulation_routes_module.engine,
        "process_query",
        lambda query, context: {"status": "completed", "final_conclusion": "ok"},
    )

    response = authenticated_client.post("/api/v1/simulations/sim-owner-3/run")

    assert response.status_code == 404


def test_simulation_create_accepts_legacy_query_payload(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/simulations",
        json={
            "name": "Legacy Payload",
            "query": "What changed in this policy?",
            "sim_type": "standard",
        },
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["data"]["parameters"]["query"] == "What changed in this policy?"
    assert body["data"]["session_id"]


def test_api_query_uses_gateway_and_persists_result(app, authenticated_client, monkeypatch):
    gateway = _GatewayOk()
    monkeypatch.setattr("backend.llm_gateway.gateway.get_gateway", lambda: gateway)

    response = authenticated_client.post("/api/v1/query", json={"query": "hello gateway"})

    assert response.status_code == 200
    assert response.get_json()["response"] == "gateway answer"
    assert gateway.requests
    assert gateway.requests[0].meta["source"] == "api_v1_query"

    with app.app_context():
        simulation = SimulationSession.query.order_by(SimulationSession.id.desc()).first()
        assert simulation is not None
        assert simulation.status == "completed"
        assert simulation.results["response"] == "gateway answer"


def test_api_query_fails_closed_when_gateway_unavailable(app, authenticated_client, monkeypatch):
    monkeypatch.setattr("backend.llm_gateway.gateway.get_gateway", lambda: _GatewayFail())

    response = authenticated_client.post("/api/v1/query", json={"query": "hello gateway"})

    assert response.status_code == 503

    with app.app_context():
        simulation = SimulationSession.query.order_by(SimulationSession.id.desc()).first()
        assert simulation is not None
        assert simulation.status == "failed"
        assert "providers" in simulation.results["error"].lower()

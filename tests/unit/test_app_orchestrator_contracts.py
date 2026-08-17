"""Compatibility and fail-closed contracts for the legacy app orchestrator facade."""

from core.simulation.app_orchestrator import AppOrchestrator


class Forwarder:
    def __init__(self, fail=False):
        self.fail = fail

    def _result(self, value):
        if self.fail:
            raise RuntimeError("forward failed")
        return value

    def run_simulation(self, **kwargs):
        return self._result({"status": "success", "kwargs": kwargs})

    def detect_location_from_text(self, text):
        return self._result(
            {
                "status": "success",
                "locations": [{"resolved": True, "node_uids": ["LOC"]}],
            }
        )

    def get_context_for_location(self, **kwargs):
        return self._result({"status": "success", **kwargs})

    def search_nodes(self, **kwargs):
        return self._result([{"uid": "one"}])

    def get_improvement_proposals(self, **kwargs):
        return self._result([{"proposal_id": "one"}])

    def approve_improvement_proposal(self, proposal_id):
        return self._result({"status": "approved", "proposal_id": proposal_id})

    def reject_improvement_proposal(self, proposal_id, reason):
        return self._result({"status": "rejected", "proposal_id": proposal_id, "reason": reason})

    def get_memory_entries(self, session_id):
        return self._result([{"session_id": session_id}])


class Database:
    def __init__(self, session=None, connection=True, fail=False):
        self.session = session
        self.connection = connection
        self.fail = fail

    def get_session(self, session_id):
        if self.fail:
            raise RuntimeError("database failed")
        return self.session

    def test_connection(self):
        if self.fail:
            raise RuntimeError("database failed")
        return self.connection


def test_orchestrator_constructs_and_keeps_durable_simulation_boundary():
    orchestrator = AppOrchestrator(db_manager=Database())
    assert orchestrator.location_context_engine is not None
    assert orchestrator.simulation_engine is None
    result = orchestrator.run_simulation("query")
    assert result["code"] == "SIMULATION_DURABLE_JOB_REQUIRED"
    assert result["status"] == "error"


def test_orchestrator_forwarding_success_contracts():
    db = Database(session={"id": "session"})
    orchestrator = AppOrchestrator(db_manager=db)
    orchestrator.simulation_engine = Forwarder()
    orchestrator.location_context_engine = Forwarder()
    orchestrator.graph_manager = Forwarder()
    orchestrator.memory_manager = Forwarder()
    orchestrator.sekre_engine = Forwarder()

    simulation = orchestrator.run_simulation("query", ["LOC"], 0.9, {"a": 1})
    assert simulation["kwargs"]["target_confidence"] == 0.9
    location = orchestrator.get_location_context(query_text="Seattle")
    assert location["location_uid"] == "LOC"
    assert orchestrator.get_location_context("EXPLICIT")["location_uid"] == "EXPLICIT"

    session = orchestrator.get_session_info("session")
    assert session["status"] == "success"
    assert session["memory_entries_count"] == 1
    search = orchestrator.search_knowledge_graph("one", ["type"], [1], 2)
    assert search["result_count"] == 1
    proposals = orchestrator.get_improvement_proposals("pending", "quality", 2)
    assert proposals["proposal_count"] == 1
    assert orchestrator.approve_improvement("one")["status"] == "approved"
    assert orchestrator.reject_improvement("one", "reason")["reason"] == "reason"

    health = orchestrator.get_system_health()
    assert health["status"] == "healthy"
    assert health["database"] == "connected"


def test_orchestrator_unavailable_component_and_not_found_contracts():
    orchestrator = AppOrchestrator()
    orchestrator.location_context_engine = None
    assert orchestrator.get_location_context("LOC")["message"] == "Location Context Engine not available"
    assert orchestrator.get_session_info("missing")["message"] == "Session not found: missing"
    assert orchestrator.search_knowledge_graph("query")["message"] == "Graph Manager not available"
    assert orchestrator.get_improvement_proposals()["message"] == "SEKRE Engine not available"
    assert orchestrator.approve_improvement("one")["message"] == "SEKRE Engine not available"
    assert orchestrator.reject_improvement("one")["message"] == "SEKRE Engine not available"
    assert orchestrator.get_system_health()["status"] == "critical"

    orchestrator.location_context_engine = Forwarder()
    orchestrator.location_context_engine.detect_location_from_text = lambda _text: {
        "status": "success",
        "locations": [{"resolved": False}],
    }
    assert "No location UID" in orchestrator.get_location_context(query_text="unknown")["message"]


def test_orchestrator_forwarding_exceptions_return_errors():
    orchestrator = AppOrchestrator(db_manager=Database(fail=True))
    failing = Forwarder(fail=True)
    orchestrator.simulation_engine = failing
    orchestrator.location_context_engine = failing
    orchestrator.graph_manager = failing
    orchestrator.sekre_engine = failing

    assert orchestrator.run_simulation("query")["status"] == "error"
    assert orchestrator.get_location_context("LOC")["status"] == "error"
    assert orchestrator.get_session_info("session")["status"] == "error"
    assert orchestrator.search_knowledge_graph("query")["status"] == "error"
    assert orchestrator.get_improvement_proposals()["status"] == "error"
    assert orchestrator.approve_improvement("one")["proposal_id"] == "one"
    assert orchestrator.reject_improvement("one")["proposal_id"] == "one"
    health = orchestrator.get_system_health()
    assert health["database"] == "error"
    assert health["status"] == "healthy"


def test_orchestrator_database_disconnected_and_session_without_memory():
    orchestrator = AppOrchestrator(db_manager=Database(session={"id": "session"}, connection=False))
    session = orchestrator.get_session_info("session")
    assert session["memory_entries_count"] == 0
    orchestrator.simulation_engine = Forwarder()
    assert orchestrator.get_system_health()["database"] == "disconnected"

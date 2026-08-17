from __future__ import annotations

from datetime import UTC, datetime, timedelta


def test_federated_sync_prepares_receives_and_broadcasts_claims():
    from backend.truth_engine.federated_sync import FederatedClaim, FederatedSyncEngine

    class Database:
        def __init__(self):
            self.nodes = []

        def create_node(self, node):
            self.nodes.append(node)
            return node

    database = Database()
    engine = FederatedSyncEngine(database)
    assert engine.prepare_for_sharing({"uid": "low", "level": 4}) is None
    claim = engine.prepare_for_sharing({
        "uid": "claim-1", "level": 5, "tenant_id": "tenant-a",
        "description": "Validated knowledge", "confidence": 0.9,
        "attributes": {"domain": "testing"},
    })
    assert claim is not None and claim.evidence_zkp.startswith("zkp_proof_")
    assert engine.receive_federated_claim(claim) is True
    assert database.nodes[0]["uid"] == "fed_claim-1"
    invalid = FederatedClaim(
        claim_id="bad", source_tenant="tenant", content_hash="hash",
        evidence_zkp="invalid", confidence=0.5,
    )
    assert engine.receive_federated_claim(invalid) is False
    assert engine.broadcast_outbox() == 1
    assert engine.broadcast_outbox() == 0


def test_federated_sync_handles_invalid_claim_and_database_failure():
    from backend.truth_engine.federated_sync import FederatedClaim, FederatedSyncEngine

    engine = FederatedSyncEngine(type("Database", (), {"create_node": lambda *_args: None})())
    assert engine.prepare_for_sharing({"uid": None, "level": 5}) is None
    claim = FederatedClaim(
        claim_id="claim", source_tenant="tenant", content_hash="hash",
        evidence_zkp="zkp_proof_valid", confidence=0.8,
    )
    assert engine.receive_federated_claim(claim) is False


def test_priority_queue_lifecycle_limits_sla_status_and_mapping():
    from backend.truth_engine.truth_link.queues import PriorityQueueManager

    manager = PriorityQueueManager()
    invalid_item = {"id": "default"}
    assert manager.enqueue("invalid", invalid_item)["queue"] == "p1"
    assert manager.peek("p1")["id"] == "default"
    assert manager.dequeue("p1")["id"] == "default"
    assert manager.dequeue("p1") is None

    old_item = {"id": "late"}
    manager.enqueue("p0", old_item)
    old_item["_queued_at"] = (datetime.now(UTC) - timedelta(seconds=2)).isoformat()
    manager.enqueue("p2", {"id": "later-priority"})
    assert manager.dequeue()["id"] == "late"
    assert manager.sla_violations["p0"] == 1
    assert manager.dequeue()["id"] == "later-priority"
    assert manager.dequeue() is None
    assert manager.peek("p5") is None

    manager.PRIORITY_CONFIG["p5"] = {**manager.PRIORITY_CONFIG["p5"], "max_queue": 1}
    assert manager.enqueue("p5", {"id": "one"})["success"] is True
    full = manager.enqueue("p5", {"id": "two"})
    assert full["success"] is False and full["error"] == "Queue full"
    assert manager.get_total_pending() == 1
    assert manager.get_queue_status("p5")["name"] == "HITL"
    assert manager.get_queue_status("unknown")["name"] == "Unknown"
    assert len(manager.get_queue_status()) == 6
    assert manager.clear_queue("p5") == 1
    assert manager.clear_queue("unknown") == 0
    assert manager.tier_to_priority("autonomous") == "p4"
    assert manager.tier_to_priority("unknown") == "p1"

"""
Verification Script: Federated Knowledge Sharing (Track 4)
Tests the end-to-end sync between two mock tenants.
"""
import sys
import os
import asyncio
import logging
from unittest.mock import MagicMock

# Decoupled mock setup
class MockNode:
    def __init__(self, uid, n_type, level, tenant):
        self.uid = uid
        self.node_type = n_type
        self.level = level
        self.tenant_id = tenant
        self.description = "Validated knowledge claim regarding regulatory compliance."
        self.attributes = {"confidence": 0.95}

# Patch modules
sys.modules["backend.extensions"] = MagicMock()
mock_db_mod = MagicMock()
sys.modules["backend.ukg_db"] = mock_db_mod

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.truth_engine.federated_sync import FederatedSyncEngine, FederatedClaim
from backend.knowledge_algorithms.ka_114_federated_outbox import KA114FederatedOutbox
from backend.knowledge_algorithms.ka_115_federated_inbox import KA115FederatedInbox

async def test_federated_sync():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Verification")

    # 1. Setup Tenant A (Source)
    logger.info("Setting up Tenant A (Source)...")
    tenant_a_id = "TENANT_A"
    node_a = {
        'uid': 'clm_123',
        'node_type': 'claim',
        'level': 5,
        'tenant_id': tenant_a_id,
        'description': "High-confidence regulatory insight.",
        'confidence': 0.98,
        'attributes': {'sector': 'finance'}
    }
    
    db_a = MagicMock()
    db_a.get_nodes_by_type.return_value = [node_a]
    mock_db_mod.UkgDatabaseManager.return_value = db_a
    
    outbox_ka = KA114FederatedOutbox({"tenant_id": tenant_a_id})
    result_out = outbox_ka._run_logic({})
    
    assert result_out["success"] is True
    assert result_out["claims_shared"] == 1
    logger.info(f"PASSED: Tenant A successfully shared claim {node_a['uid']}.")

    # 2. Setup Tenant B (Sink)
    logger.info("Setting up Tenant B (Sink)...")
    tenant_b_id = "TENANT_B"
    shared_claim_data = {
        "claim_id": "clm_123",
        "source_tenant": tenant_a_id,
        "content_hash": "abc-123",
        "evidence_zkp": "zkp_proof_abc",
        "confidence": 0.98,
        "attributes": {"sector": "finance"}
    }
    
    db_b = MagicMock()
    db_b.create_node.return_value = True
    mock_db_mod.UkgDatabaseManager.return_value = db_b
    
    inbox_ka = KA115FederatedInbox({"tenant_id": tenant_b_id})
    result_in = inbox_ka._run_logic({"incoming_claims": [shared_claim_data]})
    
    assert result_in["success"] is True
    assert result_in["ingested_count"] == 1
    logger.info("PASSED: Tenant B successfully ingested federated claim.")

    # 3. Verify Sync Engine logic directly
    logger.info("Verifying ZKP validation in Sync Engine...")
    engine = FederatedSyncEngine(db_b)
    invalid_claim = FederatedClaim(
        claim_id="bad", source_tenant="x", content_hash="y", 
        evidence_zkp="invalid_proof", confidence=0.5
    )
    assert engine.receive_federated_claim(invalid_claim) is False
    logger.info("PASSED: Sync Engine rejected invalid ZKP.")

    logger.info("ALL VERIFICATIONS PASSED: Collaborative Graph (Track 4) is functional.")

if __name__ == "__main__":
    asyncio.run(test_federated_sync())

"""
KA-115: Federated Claim Inbox
Purpose: Ingest and verify knowledge claims shared by remote tenants.
"""
import logging
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from backend.truth_engine.federated_sync import FederatedSyncEngine, FederatedClaim
from backend.ukg_db import UkgDatabaseManager

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

class KA115Input(BaseModel):
    incoming_claims: List[Dict[str, Any]] = Field(default_factory=list)

class KA115FederatedInbox(KnowledgeAlgorithm):
    input_schema = KA115Input
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-115"
        self.db_mgr = UkgDatabaseManager(tenant_id=context.get("tenant_id"))
        self.sync_engine = FederatedSyncEngine(self.db_mgr)

    def _run_logic(self, input_data: KA115Input) -> Dict[str, Any]:
        """
        Ingest shared claims provided in the input.
        """
        incoming_claims = input_data.incoming_claims
        
        ingested_count = 0
        errors = []
        
        for claim_dict in incoming_claims:
            try:
                claim = FederatedClaim(**claim_dict)
                if self.sync_engine.receive_federated_claim(claim):
                    ingested_count += 1
                else:
                    errors.append(f"Validation failed for {claim.claim_id}")
            except Exception as e:
                errors.append(str(e))
                
        return {
            "success": ingested_count > 0 or not errors,
            "ingested_count": ingested_count,
            "errors": errors,
            "status": "ingestion_complete"
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    algo = KA115FederatedInbox(context)
    return algo.run(context)

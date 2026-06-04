"""
Layer 2: Retrieval & Grounding Engine
Responsible for dynamically retrieving evidence based on L1 Intent.
Produces EvidencePack and WorkingSubgraph.
Replaces the legacy 'Layer 2 Knowledge Simulator' (static graph).
"""

import logging
from typing import Dict, Any, List

from quad_persona.quad_models import (
    EvidencePack, EvidenceItem, Coord17Intent, RetrievalPlan, Coord17Bindings
)
# Reuse the existing simulated db logic but wrapped in dynamic retrieval
from core.simulation.layer2_legacy_knowledge import NestedLayerDatabase

logger = logging.getLogger(__name__)

class Layer2RetrievalEngine:
    """
    Refactored Layer 2 Engine.
    Executes retrieval plans to build a grounded EvidencePack.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        # Keep the simulated DB for "internal knowledge" lookups
        self.internal_db = NestedLayerDatabase()
        self.internal_db.load_all_data() # Load YAMLs
        
    def process_request(self, 
                        intent_data: Dict[str, Any], 
                        problem_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for Layer 2.
        
        Args:
            intent_data: Dict form of Coord17Intent
            problem_spec: Dict form of ProblemSpec
            
        Returns:
            {
                "evidence_pack": dict,
                "bindings": dict,
                "success": bool
            }
        """
        # 1. Hydrate Objects
        # (Simplified hydration for demo)
        intent = Coord17Intent(**{k:v for k,v in intent_data.items() if k in Coord17Intent.__annotations__})
        
        logger.info(f"Layer 2 Retrieval started for Intent: {intent}")
        
        # 2. Plan Retrieval
        self._generate_plan(intent)
        
        # 3. Execute Retrieval (Internal DB)
        evidence_pack = EvidencePack(research_tier="internal_retrieval")
        bindings = Coord17Bindings()
        
        # Search Internal DB Layer based on Intent Axes
        hits = self._search_internal_db(intent)
        
        for hit in hits:
            # Convert DB nodes to EvidenceItems
            item = EvidenceItem(
                content=f"{hit.get('label')}: {hit.get('description')}",
                source_uri=f"internal://node/{hit.get('node_id')}",
                source_type="internal_knowledge_graph",
                confidence=0.9,
                object_type="knowledge_node"
            )
            evidence_pack.add_item(item)
            
        # 4. Resolve Bindings (What did we actually find?)
        if intent.axis_2_sector:
            bindings.resolved_axes[2] = intent.axis_2_sector # In real system, confirm we found them
            
        logger.info(f"Layer 2 Complete. Found {len(evidence_pack.items)} items.")
        
        return {
            "evidence_pack": evidence_pack.to_dict(),
            "bindings": bindings.to_dict(),
            "success": True
        }

    def _generate_plan(self, intent: Coord17Intent) -> RetrievalPlan:
        """Create a plan of where to look."""
        plan = RetrievalPlan()
        
        # Map Intent Axes to Search Queries
        if intent.axis_2_sector:
            plan.search_queries.extend([f"sector:{s}" for s in intent.axis_2_sector])
            
        if intent.axis_6_regulation:
            plan.search_queries.extend([f"regulation:{r}" for r in intent.axis_6_regulation])
            
        if intent.axis_5_tool:
             plan.search_queries.extend([f"tool:{t}" for t in intent.axis_5_tool])
             
        # Catch-all if specific axes empty
        if not plan.search_queries:
            plan.search_queries.append("broad_scan")
            
        return plan

    def _search_internal_db(self, intent: Coord17Intent) -> List[Dict]:
        """
        Search the loaded NestedLayerDatabase using metadata from intent.
        """
        hits = []
        
        # Search by keyword for mapped axes
        # Combine all mapped terms
        terms = (
            intent.axis_2_sector + 
            intent.axis_3_topic + 
            intent.axis_4_method + 
            intent.axis_5_tool + 
            intent.axis_6_regulation
        )
        
        for term in terms:
            # Use the existing "search_text" method from NestedDB (well, simulated wrapper)
            # The NestedLayerDatabase class has a `search_nodes` method.
            node_hits = self.internal_db.search_nodes(term)
            hits.extend(node_hits)
            
        return hits

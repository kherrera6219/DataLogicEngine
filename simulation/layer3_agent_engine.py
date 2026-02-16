"""
Layer 3: Deep Research Agent Engine
Orchestrates the 3-Tier Deep Research process:
- Tier 1: Light (Claim Extraction)
- Tier 2: Analytic (Reasoning - Future)
- Tier 3: Deep Research (External Search)
"""

import logging
from typing import Dict, Any

from quad_persona.quad_models import EvidencePack, EvidenceItem
# Import KA implementations directly or via Registry
from backend.knowledge_algorithms.ka_claim_extraction import KAClaimExtraction
from backend.knowledge_algorithms.ka_29_online_validation import KAResearch

logger = logging.getLogger(__name__)

class Layer3AgentEngine:
    """
    Executes the Deep Research Agent workflows.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize KAs
        self.ka_claim_extractor = KAClaimExtraction(self.config)
        self.ka_research = KAResearch(self.config)
        
    def process_request(self, 
                        intent: Dict[str, Any], 
                        tier_plan: Dict[str, Any],
                        context: Dict[str, Any]) -> EvidencePack:
        """
        Main entry point for Layer 3.
        
        Args:
            intent: Coord17Intent (What does the user want?)
            tier_plan: { "tier": 1|2|3, "k": int, ... }
            context: Previous layer outputs, raw query, etc.
            
        Returns:
            EvidencePack containing gathered facts.
        """
        tier = tier_plan.get("tier", 1)
        query = intent.get("description", context.get("query_text", ""))
        
        logger.info(f"Layer 3 starting execution. Tier: {tier} | Query: {query}")
        
        # Initialize Output Pack
        pack = EvidencePack(
            research_tier=f"tier{tier}",
            agents_involved=["layer3_router"]
        )
        
        # --- Tier 1: Light / Evidence-Grounded ---
        # Goal: Extract existing claims from context/docs without going external.
        if tier >= 1:
            logger.info("Exec Tier 1: Claim Extraction")
            # Pull text from context to extraction
            # Assuming context has some source text or documents
            extraction_result = self.ka_claim_extractor.execute({
                "text": str(context), # Simplification: dump context as text
                "source_uri": "context_dump"
            })
            
            if extraction_result["success"]:
                for item_dict in extraction_result["evidence_items"]:
                    # Convert dict back to object if needed, or structured differently
                    # Our model stores objects, but KAs return dicts.
                    # Ideally KAs return objects, but for serialization dicts are safer.
                    # Let's manual hydrate.
                    item = EvidenceItem(**item_dict)
                    pack.add_item(item)
                    
        # --- Tier 2: Analytic ---
        # Goal: Reasoning / Gap Analysis (Skipped for this MVP iteration)
        if tier >= 2:
            logger.info("Exec Tier 2: Analytic (Skipped in MVP)")
            # In full version: Run KA-AoT to find derived claims
            pass
            
        # --- Tier 3: Deep Research ---
        # Goal: Go external for missing info
        if tier >= 3:
            logger.info("Exec Tier 3: Deep Research")
            pack.agents_involved.append("ka_research")
            
            # Simple Logic: If Tier 3, treat the query as a research query
            research_result = self.ka_research.execute({
                "query": query,
                "domain": intent.get("domain", "general")
            })
            
            if research_result["success"]:
                for item_dict in research_result["evidence_items"]:
                    item = EvidenceItem(**item_dict)
                    pack.add_item(item)
            else:
                pack.gaps.append(f"Research failed for: {query}")

        logger.info(f"Layer 3 Complete. Gathered {len(pack.items)} items.")
        return pack


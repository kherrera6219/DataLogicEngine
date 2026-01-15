"""
KA-ClaimExtraction (Tier 1)
Extracts factual claims from existing context (EvidencePack) without hallucination.
"""

import logging
from typing import Dict, List, Any
import re
from quad_persona.quad_models import EvidenceItem, EvidencePack

logger = logging.getLogger(__name__)

class KAClaimExtraction:
    """
    Tier 1 Algorithm: Claim Extraction.
    
    Purpose:
        Analyze the unstructured text in the context (user query, retrieved docs)
        and extract distinct atomic claims/facts.
    
    Constraints:
        - strictly grounded: only output claims present in the input.
        - no external calls.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute claim extraction.
        
        Args:
            data: {
                "text": str,  # Unstructured text to analyze
                "source_uri": str, # Origin of this text
                "context": dict
            }
            
        Returns:
            {
                "evidence_items": List[EvidenceItem.to_dict()]
            }
        """
        text = data.get("text", "")
        source_uri = data.get("source_uri", "unknown")
        
        logger.info(f"Extracting claims from {source_uri} (len={len(text)})")
        
        claims = self._extract_atomic_claims(text)
        
        evidence_items = []
        for claim_text in claims:
            # Create a formal evidence item
            item = EvidenceItem(
                content=claim_text,
                source_uri=source_uri,
                source_type="document" if "doc" in source_uri else "input_context",
                confidence=0.9, # High confidence because it's extracted directly
                object_type="extracted_claim",
                validation_state="raw"
            )
            evidence_items.append(item.to_dict())
            
        return {
            "success": True,
            "evidence_items": evidence_items,
            "count": len(evidence_items)
        }
        
    def _extract_atomic_claims(self, text: str) -> List[str]:
        """
        Simple heuristic extractor. 
        In a real system, this would use a small NLP model or regex rules 
        to split complex sentences into atomic facts.
        """
        # 1. Split by sentence terminators
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        claims = []
        for sent in sentences:
            clean_sent = sent.strip()
            if len(clean_sent) > 20: # Filter out short noise
                # Assume each substantial sentence is a claim for Tier 1
                claims.append(clean_sent)
                
        return claims

def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for KA Registry."""
    algo = KAClaimExtraction(data.get("config"))
    return algo.execute(data)

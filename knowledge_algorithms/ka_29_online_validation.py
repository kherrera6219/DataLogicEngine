"""
KA-Research (KA-29 Upgrade) - Tier 3
Performs external research to gather new evidence.
Previously 'ka_29_online_validation.py'.
"""

import logging
from typing import Dict, List, Any, Optional
import time
import re
import random
from quad_persona.quad_models import EvidenceItem, EvidencePack

logger = logging.getLogger(__name__)

class KAResearch:
    """
    Tier 3 Algorithm: Deep Research Adapter.
    
    Purpose:
        Perform 'external' searches to fill information gaps.
        In this implementation, it simulates an external search engine 
        returning structured EvidenceItems.
    
    Future Upgrade:
        Replace _simulate_search with actual Google/Bing/Corporate Search API.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.simulated_delay_ms = self.config.get("delay_ms", 200)
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute research query.
        
        Args:
            data: {
                "query": str,   # The research question
                "domain": str,  # e.g., "regulatory", "technical"
            }
            
        Returns:
            {
                "evidence_items": List[EvidenceItem.to_dict()],
                "status": "success",
                "metadata": dict
            }
        """
        query = data.get("query", "")
        domain = data.get("domain", "general")
        
        if not query:
            return {"success": False, "error": "No query provided"}
            
        logger.info(f"KA-Research executing query: '{query}' [Domain: {domain}]")
        
        # Simulate Network Call
        time.sleep(self.simulated_delay_ms / 1000.0)
        
        # Fetch results
        raw_results = self._simulate_search(query, domain)
        
        # Convert to EvidenceItems
        evidence_items = []
        for result in raw_results:
            item = EvidenceItem(
                content=result["snippet"],
                source_uri=result["url"],
                source_type="web",
                confidence=result["score"],
                provenance=result["source_name"],
                object_type="external_fact",
                validation_state="unverified",
                metadata={"search_query": query, "rank": result["rank"]}
            )
            evidence_items.append(item.to_dict())
            
        return {
            "success": True,
            "evidence_items": evidence_items,
            "query": query,
            "count": len(evidence_items)
        }

    def _simulate_search(self, query: str, domain: str) -> List[Dict[str, Any]]:
        """
        Simulate a search engine returning relevant snippets.
        This replaces the old 'random boolean' logic with 'structured mock data'.
        """
        results = []
        
        # Mock Data Database
        mock_db = {
            "far": [
                {"title": "FAR 52.204-21", "url": "https://acquisition.gov/far/52.204-21", "snippet": "Basic Safeguarding of Covered Contractor Information Systems.", "source": "Acquisition.gov"},
                {"title": "FAR Part 15", "url": "https://acquisition.gov/far/part-15", "snippet": "Contracting by Negotiation - Policies and procedures.", "source": "Acquisition.gov"}
            ],
            "f-22": [
                {"title": "F-22 Raptor Overview", "url": "https://af.mil/f-22", "snippet": "The F-22 Raptor is a 5th generation air superiority fighter.", "source": "USAF"},
                {"title": "F-22 Modernization", "url": "https://lockheedmartin.com/f22-mod", "snippet": "Ongoing modernization program includes radar and avionics upgrades.", "source": "Lockheed Martin"}
            ],
            "hipaa": [
                 {"title": "HIPAA Privacy Rule", "url": "https://hhs.gov/hipaa", "snippet": "Protects medical records and other personal health information.", "source": "HHS.gov"}
            ]
        }
        
        # 1. Simple Keyword Match in Mock DB
        query_lower = query.lower()
        matched_key = None
        for key in mock_db:
            if key in query_lower:
                matched_key = key
                break
        
        if matched_key:
            # Return specific mock hits
            for i, hit in enumerate(mock_db[matched_key]):
                results.append({
                    "rank": i + 1,
                    "url": hit["url"],
                    "snippet": hit["snippet"],
                    "source_name": hit["source"],
                    "score": 0.95 - (i * 0.05)
                })
        else:
            # 2. Generic Fallback
            results.append({
                "rank": 1,
                "url": f"https://search.gov/results?q={query.replace(' ', '+')}",
                "snippet": f"Simulated search result for '{query}'. Information would appear here.",
                "source_name": "General Search",
                "score": 0.6
            })
            
        return results

def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for KA Registry."""
    algo = KAResearch(data.get("config"))
    return algo.execute(data)
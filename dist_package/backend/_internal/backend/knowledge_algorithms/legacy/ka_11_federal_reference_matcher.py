"""
KA-11: Federal Reference Matcher

This algorithm identifies and matches relevant federal acquisition regulations,
particularly FAR and DFARS references, based on query content and context.
"""

import logging
import re
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class FederalReferenceMatcher:
    """
    KA-11: Matches queries to federal acquisition regulations and standards.
    
    This algorithm specializes in identifying relevant FAR, DFARS, and
    other federal references based on the query content and domain context.
    """
    
    def __init__(self):
        """Initialize the Federal Reference Matcher."""
        self.far_references = self._initialize_far_references()
        self.dfars_references = self._initialize_dfars_references()
        logger.info("KA-11: Federal Reference Matcher initialized")
    
    def _initialize_far_references(self) -> Dict[str, List[Dict[str, str]]]:
        """Initialize FAR references by category."""
        return {
            "procurement": [
                {"ref": "FAR 2.101", "title": "Definitions", "relevance": "high"},
                {"ref": "FAR 15.305", "title": "Proposal Evaluation", "relevance": "high"},
                {"ref": "FAR 52.212-1", "title": "Instructions to Offerors", "relevance": "medium"}
            ],
            "contracts": [
                {"ref": "FAR 16.301-3", "title": "Cost-Reimbursement Contract Limitations", "relevance": "high"},
                {"ref": "FAR 52.249-2", "title": "Termination for Convenience", "relevance": "medium"},
                {"ref": "FAR 52.249-8", "title": "Default", "relevance": "medium"}
            ],
            "compliance": [
                {"ref": "FAR 52.222-26", "title": "Equal Opportunity", "relevance": "high"},
                {"ref": "FAR 52.203-13", "title": "Contractor Code of Business Ethics", "relevance": "high"},
                {"ref": "FAR 9.405", "title": "Effect of Listing", "relevance": "medium"}
            ],
            "intellectual_property": [
                {"ref": "FAR 52.227-14", "title": "Rights in Data - General", "relevance": "high"},
                {"ref": "FAR 52.227-17", "title": "Rights in Data - Special Works", "relevance": "medium"},
                {"ref": "FAR 52.227-19", "title": "Commercial Computer Software", "relevance": "medium"}
            ]
        }
    
    def _initialize_dfars_references(self) -> Dict[str, List[Dict[str, str]]]:
        """Initialize DFARS references by category."""
        return {
            "military": [
                {"ref": "DFARS 252.227-7013", "title": "Rights in Technical Data", "relevance": "high"},
                {"ref": "DFARS 252.227-7014", "title": "Rights in Noncommercial Software", "relevance": "high"},
                {"ref": "DFARS 215.300", "title": "Scope of Subpart", "relevance": "medium"}
            ],
            "cybersecurity": [
                {"ref": "DFARS 252.204-7012", "title": "Safeguarding Covered Defense Information", "relevance": "high"},
                {"ref": "DFARS 252.204-7020", "title": "NIST SP 800-171 Assessment", "relevance": "high"},
                {"ref": "DFARS 252.239-7001", "title": "Information Assurance Contractor Training", "relevance": "medium"}
            ],
            "foreign_acquisition": [
                {"ref": "DFARS 252.225-7001", "title": "Buy American and Balance of Payments Program", "relevance": "high"},
                {"ref": "DFARS 252.225-7007", "title": "Prohibition on Acquisition from Certain Countries", "relevance": "high"},
                {"ref": "DFARS 252.225-7048", "title": "Export-Controlled Items", "relevance": "medium"}
            ]
        }
    
    def match_references(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Match query to relevant federal references.
        
        Args:
            query: The query text
            context: Optional context information
            
        Returns:
            Dictionary with matched references
        """
        query_lower = query.lower()
        context = context or {}
        domain = context.get("domain", "")
        
        matched_far = self._match_far_references(query_lower)
        matched_dfars = self._match_dfars_references(query_lower)
        
        # Determine relevance score based on domain and matches
        relevance = self._calculate_reference_relevance(domain, matched_far, matched_dfars)
        
        return {
            "algorithm": "KA-11",
            "query": query,
            "far_references": matched_far,
            "dfars_references": matched_dfars,
            "relevance": relevance
        }
    
    def _match_far_references(self, query_text: str) -> List[Dict[str, str]]:
        """
        Match query to FAR references.
        
        Args:
            query_text: The lowercase query text
            
        Returns:
            List of matched FAR references
        """
        matched_references = []
        
        # Check for explicit FAR mentions (e.g., "FAR 52.212-1")
        explicit_mentions = re.findall(r'far\s+(\d+\.\d+(?:-\d+)?)', query_text)
        for mention in explicit_mentions:
            # Look for exact reference matches
            for category, refs in self.far_references.items():
                for ref_data in refs:
                    if mention in ref_data["ref"]:
                        matched_references.append(ref_data)
        
        # Check for category-based matches
        category_keywords = {
            "procurement": ["procurement", "acquisition", "purchase", "buy", "solicitation", "offer", "proposal"],
            "contracts": ["contract", "agreement", "clause", "term", "condition", "termination", "default"],
            "compliance": ["compliance", "regulation", "requirement", "standard", "ethics", "policy"],
            "intellectual_property": ["intellectual property", "ip", "copyright", "patent", "data rights", "software"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in query_text for keyword in keywords):
                # Add high-relevance references from matched category
                matched_references.extend([
                    ref for ref in self.far_references.get(category, [])
                    if ref["relevance"] == "high" and ref not in matched_references
                ])
        
        return matched_references
    
    def _match_dfars_references(self, query_text: str) -> List[Dict[str, str]]:
        """
        Match query to DFARS references.
        
        Args:
            query_text: The lowercase query text
            
        Returns:
            List of matched DFARS references
        """
        matched_references = []
        
        # Check for explicit DFARS mentions (e.g., "DFARS 252.227-7013")
        explicit_mentions = re.findall(r'dfars\s+(\d+\.\d+(?:-\d+)?)', query_text)
        for mention in explicit_mentions:
            # Look for exact reference matches
            for category, refs in self.dfars_references.items():
                for ref_data in refs:
                    if mention in ref_data["ref"]:
                        matched_references.append(ref_data)
        
        # Check for category-based matches
        category_keywords = {
            "military": ["military", "defense", "dod", "armed forces", "army", "navy", "air force", "marine"],
            "cybersecurity": ["cyber", "security", "information assurance", "nist", "cmmc", "hack", "breach"],
            "foreign_acquisition": ["foreign", "import", "export", "international", "overseas", "country", "nation"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in query_text for keyword in keywords):
                # Add high-relevance references from matched category
                matched_references.extend([
                    ref for ref in self.dfars_references.get(category, [])
                    if ref["relevance"] == "high" and ref not in matched_references
                ])
        
        return matched_references
    
    def _calculate_reference_relevance(self, domain: str, far_refs: List[Dict[str, str]], dfars_refs: List[Dict[str, str]]) -> float:
        """
        Calculate the overall relevance of matched references.
        
        Args:
            domain: The domain context
            far_refs: List of matched FAR references
            dfars_refs: List of matched DFARS references
            
        Returns:
            Relevance score between 0 and 1
        """
        # Base relevance
        if not far_refs and not dfars_refs:
            return 0.0
        
        # Calculate relevance based on match count and types
        high_relevance_count = sum(1 for ref in far_refs + dfars_refs if ref["relevance"] == "high")
        total_refs = len(far_refs) + len(dfars_refs)
        
        # Weight high-relevance references more heavily
        weighted_score = (high_relevance_count * 1.5 + (total_refs - high_relevance_count)) / (total_refs * 1.5)
        
        # Domain-specific boosts
        domain_boosts = {
            "government": 0.15,
            "defense": 0.2,
            "aerospace": 0.15,
            "military": 0.2,
            "procurement": 0.1,
            "contracting": 0.1
        }
        
        domain_boost = domain_boosts.get(domain.lower(), 0.0)
        
        # Combined score (capped at 0.95)
        return min(0.95, weighted_score + domain_boost)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Federal Reference Matcher (KA-11) on the provided data.
    
    Args:
        data: A dictionary containing the query and optional context
        
    Returns:
        Dictionary with matched federal references
    """
    query = data.get("query", "")
    context = data.get("context", {})
    
    if not query:
        return {
            "algorithm": "KA-11",
            "error": "No query provided",
            "success": False
        }
    
    matcher = FederalReferenceMatcher()
    result = matcher.match_references(query, context)
    
    return {
        **result,
        "success": True
    }
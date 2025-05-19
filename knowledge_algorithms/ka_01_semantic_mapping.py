"""
KA-01: Semantic Mapping Engine

This algorithm uses natural language processing to match queries to the appropriate
Pillar Levels and axes in the Universal Knowledge Graph system.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import re

logger = logging.getLogger(__name__)

class SemanticMappingEngine:
    """
    KA-01: Maps input queries to relevant UKG coordinates using semantic analysis.
    Uses embeddings or NLP to match queries to Pillar Levels and axes.
    """
    
    def __init__(self, ukg_data: Optional[Dict[str, Any]] = None):
        """
        Initialize the Semantic Mapping Engine.
        
        Args:
            ukg_data: Optional pre-loaded UKG data structure
        """
        self.ukg_data = ukg_data or {}
        self.domain_keywords = self._initialize_domain_keywords()
        self.pillar_level_keywords = self._initialize_pillar_level_keywords()
        logger.info("KA-01: Semantic Mapping Engine initialized")
    
    def _initialize_domain_keywords(self) -> Dict[str, List[str]]:
        """Initialize domain-specific keywords for matching."""
        return {
            "healthcare": [
                "health", "medical", "patient", "clinical", "hospital", 
                "doctor", "nurse", "treatment", "diagnosis", "healthcare",
                "medicine", "pharma", "drug", "therapy", "prescription"
            ],
            "finance": [
                "finance", "financial", "bank", "investment", "money",
                "fund", "stock", "market", "capital", "asset", "trading",
                "transaction", "payment", "loan", "credit", "debt"
            ],
            "technology": [
                "tech", "technology", "software", "hardware", "data",
                "digital", "computer", "network", "internet", "cloud",
                "app", "application", "system", "device", "platform"
            ],
            "legal": [
                "legal", "law", "regulation", "compliance", "policy",
                "contract", "agreement", "statute", "legislation", "court",
                "judge", "attorney", "lawyer", "license", "permit"
            ],
            "education": [
                "education", "school", "university", "college", "student",
                "teacher", "learning", "training", "course", "curriculum",
                "academic", "study", "research", "knowledge", "skill"
            ]
        }
    
    def _initialize_pillar_level_keywords(self) -> Dict[str, List[str]]:
        """Initialize pillar level keywords for matching."""
        return {
            "PL1": ["fundamental", "basic", "foundation", "core", "essential"],
            "PL2": ["concept", "theory", "framework", "principle", "model"],
            "PL3": ["application", "practical", "implement", "use case", "deployment"],
            "PL4": ["advanced", "specialized", "expert", "complex", "sophisticated"],
            "PL5": ["integration", "synthesis", "holistic", "comprehensive", "unified"],
            "PL6": ["innovation", "novel", "cutting-edge", "breakthrough", "pioneering"],
            "PL7": ["governance", "oversight", "management", "control", "supervision"]
        }
    
    def map_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Map a query to relevant UKG coordinates using semantic analysis.
        
        Args:
            query: The query text to map
            context: Optional context information to aid mapping
            
        Returns:
            A dictionary containing the mapping results
        """
        context = context or {}
        query_lower = query.lower()
        
        # Identify primary domain
        domain = context.get("domain")
        if not domain:
            domain = self._identify_domain(query_lower)
        
        # Identify pillar levels
        pillar_levels = self._identify_pillar_levels(query_lower)
        
        # Identify related axes
        axes = self._identify_axes(query_lower, domain)
        
        # Construct UKG coordinates
        coordinates = self._construct_coordinates(domain, pillar_levels, axes)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(domain, pillar_levels, axes, query_lower)
        
        return {
            "algorithm": "KA-01",
            "query": query,
            "domain": domain,
            "pillar_levels": pillar_levels,
            "axes": axes,
            "coordinates": coordinates,
            "confidence": confidence
        }
    
    def _identify_domain(self, query_text: str) -> str:
        """
        Identify the primary domain related to the query.
        
        Args:
            query_text: The lowercase query text
            
        Returns:
            The identified domain
        """
        domain_scores = {}
        
        for domain, keywords in self.domain_keywords.items():
            score = 0
            for keyword in keywords:
                matches = re.findall(r'\b' + re.escape(keyword) + r'\b', query_text)
                score += len(matches)
            domain_scores[domain] = score
        
        # Get the domain with the highest score
        if not domain_scores or max(domain_scores.values()) == 0:
            return "general"
        
        return max(domain_scores.items(), key=lambda x: x[1])[0]
    
    def _identify_pillar_levels(self, query_text: str) -> List[str]:
        """
        Identify relevant pillar levels based on the query.
        
        Args:
            query_text: The lowercase query text
            
        Returns:
            A list of relevant pillar levels
        """
        pl_scores = {}
        
        for pl, keywords in self.pillar_level_keywords.items():
            score = 0
            for keyword in keywords:
                matches = re.findall(r'\b' + re.escape(keyword) + r'\b', query_text)
                score += len(matches)
            pl_scores[pl] = score
        
        # Get pillar levels with non-zero scores, sorted by score
        relevant_pls = [pl for pl, score in sorted(pl_scores.items(), key=lambda x: x[1], reverse=True) if score > 0]
        
        # If no specific pillar levels detected, default to PL1 and PL2
        if not relevant_pls:
            return ["PL1", "PL2"]
        
        return relevant_pls
    
    def _identify_axes(self, query_text: str, domain: str) -> List[int]:
        """
        Identify relevant axes based on the query and domain.
        
        Args:
            query_text: The lowercase query text
            domain: The identified domain
            
        Returns:
            A list of relevant axis numbers
        """
        # Keywords that suggest relevance to specific axes
        axis_keywords = {
            1: ["knowledge", "concept", "theory", "idea", "understanding"],
            2: ["context", "environment", "setting", "situation", "circumstance"],
            3: ["connection", "link", "relationship", "association", "correlation"],
            4: ["structure", "organization", "framework", "system", "arrangement"],
            5: ["node", "point", "intersection", "junction", "crossover"],
            6: ["coordinate", "position", "location", "placement", "orientation"],
            7: ["validation", "verification", "confirmation", "check", "proof"],
            8: ["role", "job", "position", "responsibility", "function"],
            9: ["sector", "industry", "field", "domain", "area"],
            10: ["regulation", "law", "rule", "policy", "directive"],
            11: ["compliance", "adherence", "conformity", "standard", "requirement"],
            12: ["location", "place", "site", "venue", "region"],
            13: ["time", "period", "duration", "interval", "schedule"]
        }
        
        # Domain-specific axis relevance
        domain_axis_mapping = {
            "healthcare": [8, 9, 10, 11],  # Healthcare tends to involve roles, sector, regulations, compliance
            "finance": [9, 10, 11],  # Finance heavily involves sector, regulations, compliance
            "technology": [1, 4, 5],  # Technology often involves knowledge, structure, nodes
            "legal": [7, 10, 11],  # Legal primarily involves validation, regulations, compliance
            "education": [1, 8]  # Education involves knowledge and roles
        }
        
        # Calculate relevance scores for each axis based on keywords
        axis_scores = {}
        for axis_num, keywords in axis_keywords.items():
            score = 0
            for keyword in keywords:
                matches = re.findall(r'\b' + re.escape(keyword) + r'\b', query_text)
                score += len(matches)
            axis_scores[axis_num] = score
        
        # Add domain-specific axes
        domain_axes = domain_axis_mapping.get(domain, [])
        for axis in domain_axes:
            axis_scores[axis] = axis_scores.get(axis, 0) + 1  # Add weight to domain-specific axes
        
        # Get axes with non-zero scores, sorted by score (descending)
        relevant_axes = [axis for axis, score in sorted(axis_scores.items(), key=lambda x: x[1], reverse=True) if score > 0]
        
        # If no specific axes detected, default to Axes 1, 8, 9
        if not relevant_axes:
            return [1, 8, 9]
        
        # Return top 3 axes or all if fewer than 3
        return relevant_axes[:min(3, len(relevant_axes))]
    
    def _construct_coordinates(self, domain: str, pillar_levels: List[str], axes: List[int]) -> List[str]:
        """
        Construct UKG coordinates based on domain, pillar levels, and axes.
        
        Args:
            domain: The identified domain
            pillar_levels: The relevant pillar levels
            axes: The relevant axes
            
        Returns:
            A list of UKG coordinate strings
        """
        coordinates = []
        
        # Example coordinate format: {PL}.{Axis}.{Domain}
        # e.g., "PL2.1.healthcare" for "Pillar Level 2, Axis 1, Healthcare domain"
        for pl in pillar_levels[:2]:  # Use top 2 pillar levels
            for axis in axes[:2]:  # Use top 2 axes
                coordinate = f"{pl}.{axis}.{domain}"
                coordinates.append(coordinate)
        
        return coordinates
    
    def _calculate_confidence(self, domain: str, pillar_levels: List[str], axes: List[int], query_text: str) -> float:
        """
        Calculate confidence score for the mapping.
        
        Args:
            domain: The identified domain
            pillar_levels: The identified pillar levels
            axes: The identified axes
            query_text: The original query text
            
        Returns:
            A confidence score between 0 and 1
        """
        # Base confidence
        confidence = 0.5
        
        # Adjust based on domain confidence
        domain_keywords = self.domain_keywords.get(domain, [])
        domain_match_count = sum(1 for kw in domain_keywords if re.search(r'\b' + re.escape(kw) + r'\b', query_text))
        domain_confidence = min(0.2, domain_match_count * 0.02)
        
        # Adjust based on pillar level confidence
        pl_confidence = min(0.15, len(pillar_levels) * 0.05)
        
        # Adjust based on axes confidence
        axes_confidence = min(0.15, len(axes) * 0.05)
        
        # Overall confidence
        confidence += domain_confidence + pl_confidence + axes_confidence
        
        # Cap at 0.9 since perfect mapping is rare
        return min(0.9, confidence)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Semantic Mapping Engine (KA-01) on the provided data.
    
    Args:
        data: A dictionary containing the query and optional context
        
    Returns:
        The mapping results
    """
    query = data.get("query", "")
    context = data.get("context", {})
    
    if not query:
        return {
            "algorithm": "KA-01",
            "error": "No query provided",
            "success": False
        }
    
    engine = SemanticMappingEngine()
    result = engine.map_query(query, context)
    
    return {
        **result,
        "success": True
    }
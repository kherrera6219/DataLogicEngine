"""
KA-04: Honeycomb Expansion Algorithm

This algorithm expands knowledge queries across sectors and axes using the
Honeycomb System (Axis 3) to identify interconnections and related concepts.
"""

import logging
from typing import Dict, List, Any, Optional, Set
import random

logger = logging.getLogger(__name__)

class HoneycombExpansionAlgorithm:
    """
    KA-04: Crosswalks data across sectors/axes using Axis 3 (Honeycomb System).
    
    The Honeycomb Expansion Algorithm identifies related concepts, domains, and 
    knowledge areas by traversing interconnected nodes in the UKG system.
    """
    
    def __init__(self, ukg_data: Optional[Dict[str, Any]] = None):
        """
        Initialize the Honeycomb Expansion Algorithm.
        
        Args:
            ukg_data: Optional pre-loaded UKG data structure
        """
        self.ukg_data = ukg_data or {}
        self.sector_connections = self._initialize_sector_connections()
        self.concept_connections = self._initialize_concept_connections()
        logger.info("KA-04: Honeycomb Expansion Algorithm initialized")
    
    def _initialize_sector_connections(self) -> Dict[str, List[str]]:
        """Initialize cross-sector connections map."""
        return {
            # Primary sector: [Related sectors]
            "healthcare": ["technology", "legal", "finance", "education", "government"],
            "technology": ["finance", "healthcare", "education", "manufacturing", "retail"],
            "finance": ["legal", "technology", "real_estate", "government", "insurance"],
            "legal": ["finance", "healthcare", "government", "education", "technology"],
            "education": ["healthcare", "technology", "government", "research", "nonprofit"],
            "manufacturing": ["technology", "logistics", "engineering", "energy", "materials"],
            "retail": ["technology", "logistics", "finance", "marketing", "consumer_goods"],
            "government": ["legal", "finance", "healthcare", "education", "defense"],
            "energy": ["technology", "manufacturing", "environmental", "transportation", "utilities"],
            "engineering": ["technology", "manufacturing", "construction", "energy", "materials"],
        }
    
    def _initialize_concept_connections(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize cross-concept connections within and across sectors."""
        return {
            "data": {
                "healthcare": ["patient records", "clinical trials", "medical research", "health analytics"],
                "technology": ["big data", "data science", "data storage", "data mining"],
                "finance": ["financial data", "market data", "transaction records", "risk analytics"],
                "legal": ["case records", "compliance data", "legal documents", "regulatory filings"]
            },
            "security": {
                "healthcare": ["patient privacy", "HIPAA compliance", "medical device security"],
                "technology": ["cybersecurity", "encryption", "network security", "authentication"],
                "finance": ["financial fraud", "transaction security", "identity protection"],
                "legal": ["data protection", "privacy laws", "security regulations"]
            },
            "compliance": {
                "healthcare": ["medical regulations", "clinical standards", "healthcare laws"],
                "technology": ["data protection", "industry standards", "security frameworks"],
                "finance": ["financial regulations", "reporting requirements", "audit standards"],
                "legal": ["regulatory compliance", "legal requirements", "certification standards"]
            },
            "analytics": {
                "healthcare": ["clinical analytics", "patient outcomes", "medical research"],
                "technology": ["data analytics", "predictive models", "machine learning"],
                "finance": ["financial modeling", "risk assessment", "market analysis"],
                "education": ["student performance", "learning analytics", "educational outcomes"]
            }
        }
    
    def expand_query(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expand a query across sectors and concepts using the Honeycomb system.
        
        Args:
            input_data: Dictionary containing the query and related metadata (e.g., coordinates, domain)
            
        Returns:
            Dictionary with expanded connections and honeycomb paths
        """
        query = input_data.get("query", "")
        domain = input_data.get("domain", "general")
        coordinates = input_data.get("coordinates", [])
        concepts = input_data.get("concepts", [])
        
        # Extract key concepts if not provided
        if not concepts:
            concepts = self._extract_key_concepts(query)
        
        # Identify related sectors
        related_sectors = self._get_related_sectors(domain)
        
        # Identify cross-sector concept connections
        concept_connections = self._get_concept_connections(concepts, domain, related_sectors)
        
        # Generate honeycomb paths
        honeycomb_paths = self._generate_honeycomb_paths(domain, related_sectors, concept_connections)
        
        # Calculate expansion confidence
        confidence = self._calculate_expansion_confidence(domain, concepts, related_sectors)
        
        return {
            "algorithm": "KA-04",
            "query": query,
            "original_domain": domain,
            "original_concepts": concepts,
            "related_sectors": related_sectors,
            "concept_connections": concept_connections,
            "honeycomb_paths": honeycomb_paths,
            "confidence": confidence
        }
    
    def _extract_key_concepts(self, query: str) -> List[str]:
        """
        Extract key concepts from the query.
        
        Args:
            query: The query text
            
        Returns:
            List of key concepts
        """
        # In a full implementation, this would use NLP techniques
        # For now, we'll use a simplified approach
        
        # Common general concepts to check for
        concept_keywords = {
            "data": ["data", "information", "records", "documents"],
            "security": ["security", "protection", "privacy", "confidential"],
            "compliance": ["compliance", "regulation", "standard", "requirement"],
            "analytics": ["analytics", "analysis", "insights", "metrics"],
            "governance": ["governance", "oversight", "management", "control"],
            "risk": ["risk", "threat", "vulnerability", "exposure"],
            "strategy": ["strategy", "plan", "approach", "framework"],
            "policy": ["policy", "guideline", "rule", "procedure"]
        }
        
        found_concepts = []
        query_lower = query.lower()
        
        for concept, keywords in concept_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    found_concepts.append(concept)
                    break
        
        # If no concepts found, default to generic ones based on query length
        if not found_concepts:
            # For longer queries, assume they contain multiple concepts
            if len(query.split()) > 10:
                return ["data", "governance", "strategy"]
            else:
                return ["data"]
        
        return list(set(found_concepts))  # Remove duplicates
    
    def _get_related_sectors(self, domain: str) -> List[str]:
        """
        Get sectors related to the primary domain.
        
        Args:
            domain: The primary domain
            
        Returns:
            List of related sectors
        """
        if domain in self.sector_connections:
            return self.sector_connections[domain]
        
        # Default connections for unknown domains
        return ["technology", "finance", "legal"]
    
    def _get_concept_connections(self, concepts: List[str], domain: str, related_sectors: List[str]) -> Dict[str, List[Dict[str, str]]]:
        """
        Get connections between concepts across different sectors.
        
        Args:
            concepts: List of key concepts
            domain: The primary domain
            related_sectors: List of related sectors
            
        Returns:
            Dictionary mapping concepts to their connections across sectors
        """
        connections = {}
        
        for concept in concepts:
            concept_connections = []
            
            # If the concept exists in our predefined connections
            if concept in self.concept_connections:
                # Add connections from the primary domain
                if domain in self.concept_connections[concept]:
                    for related_concept in self.concept_connections[concept][domain]:
                        concept_connections.append({
                            "concept": related_concept,
                            "sector": domain
                        })
                
                # Add connections from related sectors
                for sector in related_sectors:
                    if sector in self.concept_connections[concept]:
                        for related_concept in self.concept_connections[concept][sector]:
                            concept_connections.append({
                                "concept": related_concept,
                                "sector": sector
                            })
            else:
                # Generate some plausible connections for unknown concepts
                example_connections = [
                    {"concept": f"{concept} management", "sector": domain},
                    {"concept": f"{concept} strategy", "sector": domain},
                    {"concept": f"{concept} analysis", "sector": "technology"}
                ]
                concept_connections.extend(example_connections)
            
            connections[concept] = concept_connections
        
        return connections
    
    def _generate_honeycomb_paths(self, domain: str, related_sectors: List[str], 
                                concept_connections: Dict[str, List[Dict[str, str]]]) -> List[Dict[str, Any]]:
        """
        Generate honeycomb paths that connect concepts across sectors.
        
        Args:
            domain: The primary domain
            related_sectors: List of related sectors
            concept_connections: Dictionary of concept connections
            
        Returns:
            List of honeycomb paths
        """
        paths = []
        visited_sectors = set([domain])
        
        # Generate paths through the honeycomb
        for concept, connections in concept_connections.items():
            # Find connections to unvisited sectors
            unvisited_connections = [
                conn for conn in connections 
                if conn["sector"] not in visited_sectors
            ]
            
            if unvisited_connections:
                # Create paths to unvisited sectors
                for connection in unvisited_connections[:2]:  # Limit to 2 paths per concept
                    target_sector = connection["sector"]
                    target_concept = connection["concept"]
                    
                    path = {
                        "source": {
                            "concept": concept,
                            "sector": domain
                        },
                        "target": {
                            "concept": target_concept,
                            "sector": target_sector
                        },
                        "path_type": "direct",
                        "relevance": self._calculate_path_relevance(concept, target_concept, domain, target_sector)
                    }
                    
                    paths.append(path)
                    visited_sectors.add(target_sector)
        
        # If we have multiple concepts, create some cross-concept paths
        concept_list = list(concept_connections.keys())
        if len(concept_list) >= 2:
            for i in range(min(len(concept_list), 3)):
                source_concept = concept_list[i]
                target_concept = concept_list[(i + 1) % len(concept_list)]
                
                # Find a connection for the target concept
                target_connections = concept_connections.get(target_concept, [])
                if target_connections:
                    target_connection = target_connections[0]
                    
                    path = {
                        "source": {
                            "concept": source_concept,
                            "sector": domain
                        },
                        "target": {
                            "concept": target_concept,
                            "sector": target_connection["sector"]
                        },
                        "path_type": "cross_concept",
                        "relevance": self._calculate_path_relevance(source_concept, target_concept, domain, target_connection["sector"])
                    }
                    
                    paths.append(path)
        
        return paths
    
    def _calculate_path_relevance(self, source_concept: str, target_concept: str, 
                                source_sector: str, target_sector: str) -> float:
        """
        Calculate the relevance score for a honeycomb path.
        
        Args:
            source_concept: The source concept
            target_concept: The target concept
            source_sector: The source sector
            target_sector: The target sector
            
        Returns:
            Relevance score between 0 and 1
        """
        # In a full implementation, this would use semantic similarity metrics
        # For now, we'll use a simplified approach
        
        # Base relevance
        relevance = 0.5
        
        # Adjust based on sector closeness
        sector_connections = self.sector_connections.get(source_sector, [])
        if target_sector in sector_connections:
            # Direct connection between sectors
            sector_index = sector_connections.index(target_sector)
            sector_boost = 0.3 * (1 - sector_index / len(sector_connections))
            relevance += sector_boost
        
        # Adjust based on concept similarity (simplified)
        if source_concept in target_concept or target_concept in source_concept:
            # Direct word overlap
            relevance += 0.2
        
        # Cap at 0.95 for paths
        return min(0.95, relevance)
    
    def _calculate_expansion_confidence(self, domain: str, concepts: List[str], related_sectors: List[str]) -> float:
        """
        Calculate confidence score for the honeycomb expansion.
        
        Args:
            domain: The primary domain
            concepts: The key concepts
            related_sectors: The related sectors
            
        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence
        confidence = 0.6
        
        # Adjust based on domain knowledge
        if domain in self.sector_connections:
            confidence += 0.1
        
        # Adjust based on concept coverage
        known_concepts = set(self.concept_connections.keys())
        known_concept_count = sum(1 for c in concepts if c in known_concepts)
        concept_confidence = 0.2 * (known_concept_count / max(1, len(concepts)))
        confidence += concept_confidence
        
        # Adjust based on sector diversity
        sector_diversity = min(0.1, 0.02 * len(related_sectors))
        confidence += sector_diversity
        
        # Cap at 0.95
        return min(0.95, confidence)


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Honeycomb Expansion Algorithm (KA-04) on the provided data.
    
    Args:
        data: A dictionary containing the query and related metadata
        
    Returns:
        The expansion results
    """
    if "query" not in data:
        return {
            "algorithm": "KA-04",
            "error": "No query provided",
            "success": False
        }
    
    engine = HoneycombExpansionAlgorithm()
    result = engine.expand_query(data)
    
    return {
        **result,
        "success": True
    }
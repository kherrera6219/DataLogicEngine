"""
Universal Knowledge Graph (UKG) System - Axis Role Mapper

This module maps between the UKG's 13-axis coordinate system and the quad persona roles,
focusing on axes 8-11 which represent different expert roles.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

from quad_persona.quad_engine import PersonaProfile

logger = logging.getLogger(__name__)

class AxisRoleMapper:
    """
    Maps between the UKG's 13-axis coordinate system and quad persona roles.
    
    This class handles:
    1. Mapping query coordinates to appropriate expert personas
    2. Translating between axis coordinates and persona attributes
    3. Coordinating multi-axis interactions for persona selection
    """
    
    def __init__(self):
        """Initialize the axis role mapper."""
        # Axis-to-persona type mappings
        self.axis_mappings = {
            8: "knowledge",     # Knowledge Expert
            9: "sector",        # Sector Expert
            10: "regulatory",   # Regulatory Expert (Octopus Node)
            11: "compliance"    # Compliance Expert (Spiderweb Node)
        }
        
        # Reverse mapping
        self.persona_to_axis = {v: k for k, v in self.axis_mappings.items()}
        
        # Other axis categories that influence persona selection
        self.influencing_axes = {
            1: "pillar_level",  # Knowledge Pillar Levels
            2: "sector",        # Industry/Field
            3: "domain",        # Knowledge Domain
            4: "method",        # Methodological approach
            5: "temporal",      # Time context
            6: "regulatory",    # Regulatory framework
            7: "compliance"     # Compliance framework
        }
    
    def get_persona_type_for_axis(self, axis_number: int) -> Optional[str]:
        """
        Get the persona type corresponding to a specific axis.
        
        Args:
            axis_number: The axis number (8-11)
            
        Returns:
            The corresponding persona type, or None if not a persona axis
        """
        return self.axis_mappings.get(axis_number)
    
    def get_axis_for_persona_type(self, persona_type: str) -> Optional[int]:
        """
        Get the axis number for a persona type.
        
        Args:
            persona_type: The persona type (knowledge, sector, regulatory, compliance)
            
        Returns:
            The corresponding axis number, or None if not a valid persona type
        """
        return self.persona_to_axis.get(persona_type)
    
    def map_query_to_personas(self, query_context: Dict[str, Any]) -> Dict[str, float]:
        """
        Map a query's contextual information to relevant persona types with weights.
        
        Args:
            query_context: Contextual information about the query
            
        Returns:
            A dictionary mapping persona types to relevance weights (0.0-1.0)
        """
        # Default weights give equal importance to all personas
        relevance_weights = {
            "knowledge": 0.25,
            "sector": 0.25,
            "regulatory": 0.25,
            "compliance": 0.25
        }
        
        # Extract axis information from query context
        axis_coordinates = query_context.get('axis_coordinates', {})
        
        # Adjust weights based on axis emphasis in the query
        if axis_coordinates:
            # Calculate total axis emphasis
            total_emphasis = sum(axis_coordinates.values())
            if total_emphasis > 0:
                # Normalize to ensure weights sum to 1.0
                for axis_num_str, emphasis in axis_coordinates.items():
                    try:
                        axis_num = int(axis_num_str)
                        if axis_num in self.axis_mappings:
                            persona_type = self.axis_mappings[axis_num]
                            relevance_weights[persona_type] = emphasis / total_emphasis
                    except (ValueError, KeyError):
                        continue
        
        # Handle special case of domain-specific queries
        domain = query_context.get('domain')
        if domain:
            domain_focus = query_context.get('domain_focus', 0.5)  # Default moderate focus
            
            # Adjust weights based on domain focus (boost domain and sector)
            # Domain knowledge is handled by the Knowledge Expert
            relevance_weights["knowledge"] = max(0.3, relevance_weights["knowledge"] * (1 + domain_focus))
            
            # Sector relevance depends on the domain's industry context
            if query_context.get('industry_context'):
                relevance_weights["sector"] = max(0.2, relevance_weights["sector"] * (1 + domain_focus * 0.5))
            
            # Balance weights to ensure they sum to 1.0
            total = sum(relevance_weights.values())
            if total > 0:
                relevance_weights = {k: v/total for k, v in relevance_weights.items()}
        
        return relevance_weights
    
    def generate_persona_query_context(self, query_text: str, query_context: Dict[str, Any], 
                                     persona_type: str) -> Dict[str, Any]:
        """
        Generate context for a specific persona type based on query information.
        
        Args:
            query_text: The original query text
            query_context: General query context
            persona_type: The type of persona to generate context for
            
        Returns:
            Persona-specific context for processing the query
        """
        # Base context shared by all personas
        base_context = {
            "query_text": query_text,
            "persona_type": persona_type
        }
        
        # Add persona-relevant portions of the query context
        if persona_type == "knowledge":  # Axis 8
            # Knowledge Expert needs information about the knowledge domain and pillar levels
            base_context.update({
                "pillar_level": query_context.get("pillar_level"),
                "domain": query_context.get("domain"),
                "conceptual_framework": query_context.get("conceptual_framework"),
                "academic_disciplines": query_context.get("academic_disciplines", [])
            })
            
        elif persona_type == "sector":  # Axis 9
            # Sector Expert needs information about industry and market context
            base_context.update({
                "industry": query_context.get("industry"),
                "sector_code": query_context.get("sector_code"),
                "market_context": query_context.get("market_context"),
                "competitive_factors": query_context.get("competitive_factors", [])
            })
            
        elif persona_type == "regulatory":  # Axis 10
            # Regulatory Expert needs information about regulatory frameworks
            base_context.update({
                "regulatory_domains": query_context.get("regulatory_domains", []),
                "jurisdiction": query_context.get("jurisdiction"),
                "governing_bodies": query_context.get("governing_bodies", []),
                "legal_framework": query_context.get("legal_framework")
            })
            
        elif persona_type == "compliance":  # Axis 11
            # Compliance Expert needs information about standards and requirements
            base_context.update({
                "standards": query_context.get("standards", []),
                "compliance_requirements": query_context.get("compliance_requirements", []),
                "audit_framework": query_context.get("audit_framework"),
                "verification_methods": query_context.get("verification_methods", [])
            })
        
        # Add any cross-cutting context that applies to all personas
        if "temporal_context" in query_context:
            base_context["temporal_context"] = query_context["temporal_context"]
            
        if "location_context" in query_context:
            base_context["location_context"] = query_context["location_context"]
        
        return base_context
    
    def map_persona_to_axis_vector(self, persona: PersonaProfile) -> Dict[int, float]:
        """
        Map a persona to a 13-dimensional axis vector.
        
        This represents how the persona influences or relates to each axis
        in the UKG system.
        
        Args:
            persona: The persona profile
            
        Returns:
            A dictionary mapping axis numbers to influence values (0.0-1.0)
        """
        # Initialize with zeros for all 13 axes
        axis_vector = {i: 0.0 for i in range(1, 14)}
        
        # Set primary axis based on persona type
        persona_axis = self.get_axis_for_persona_type(persona.persona_type)
        if persona_axis:
            axis_vector[persona_axis] = 1.0
        
        # Set secondary axes based on persona attributes
        if persona.persona_type == "knowledge":  # Axis 8
            # Knowledge Expert has influence on Pillar Levels (Axis 1) and Domains (Axis 3)
            axis_vector[1] = 0.8  # Strong influence on Pillar Levels
            axis_vector[3] = 0.6  # Moderate influence on Domains
            axis_vector[4] = 0.4  # Some influence on Methods
            
        elif persona.persona_type == "sector":  # Axis 9
            # Sector Expert has influence on Sectors (Axis 2) and Value (Axis 10)
            axis_vector[2] = 0.9  # Very strong influence on Sectors
            axis_vector[10] = 0.5  # Moderate influence on Value
            axis_vector[5] = 0.3  # Some influence on Temporal context (industry trends)
            
        elif persona.persona_type == "regulatory":  # Axis 10
            # Regulatory Expert has influence on Regulatory (Axis 6) and Risk (Axis 9)
            axis_vector[6] = 0.9  # Very strong influence on Regulatory
            axis_vector[9] = 0.7  # Strong influence on Risk
            axis_vector[12] = 0.4  # Some influence on Location (jurisdictions)
            
        elif persona.persona_type == "compliance":  # Axis 11
            # Compliance Expert has influence on Compliance (Axis 7) and Ethical (Axis 8)
            axis_vector[7] = 0.9  # Very strong influence on Compliance
            axis_vector[8] = 0.6  # Moderate influence on Ethical
            axis_vector[6] = 0.5  # Moderate influence on Regulatory
        
        return axis_vector
    
    def adjust_weights_for_memory(self, weights: Dict[str, float], memory_context: Dict[str, Any]) -> Dict[str, float]:
        """
        Adjust persona relevance weights based on memory context.
        
        Args:
            weights: The initial persona relevance weights
            memory_context: Context from the memory system
            
        Returns:
            Adjusted weights
        """
        # Copy the original weights
        adjusted_weights = weights.copy()
        
        # Check for memory hints about persona importance
        if "persona_effectiveness" in memory_context:
            effectiveness = memory_context["persona_effectiveness"]
            for persona_type, effectiveness_score in effectiveness.items():
                if persona_type in adjusted_weights:
                    # Boost or reduce weight based on past effectiveness
                    adjusted_weights[persona_type] *= max(0.5, min(1.5, effectiveness_score))
        
        # Check for topic continuity
        if "topic_focus" in memory_context:
            topic_focus = memory_context["topic_focus"]
            if "knowledge_intensive" in topic_focus and topic_focus["knowledge_intensive"]:
                adjusted_weights["knowledge"] = min(1.0, adjusted_weights["knowledge"] * 1.3)
                
            if "regulatory_focus" in topic_focus and topic_focus["regulatory_focus"]:
                adjusted_weights["regulatory"] = min(1.0, adjusted_weights["regulatory"] * 1.3)
        
        # Normalize to ensure weights sum to 1.0
        total = sum(adjusted_weights.values())
        return {k: v/total for k, v in adjusted_weights.items()}
    
    def generate_pov_vector(self, persona: PersonaProfile, query_result: Dict[str, Any]) -> Dict[str, float]:
        """
        Generate a Point of View (PoV) vector for a persona based on query results.
        
        This represents the persona's stance or perspective on different aspects
        of the query.
        
        Args:
            persona: The persona profile
            query_result: The result of processing the query with this persona
            
        Returns:
            A dictionary mapping dimension names to stance values (-1.0 to 1.0)
        """
        # Initialize PoV dimensions
        pov_vector = {
            "theoretical_practical": 0.0,  # -1.0 = theoretical, 1.0 = practical
            "risk_opportunity": 0.0,       # -1.0 = risk-focused, 1.0 = opportunity-focused
            "conservative_innovative": 0.0, # -1.0 = conservative, 1.0 = innovative
            "short_long_term": 0.0,         # -1.0 = short-term, 1.0 = long-term
            "narrow_broad": 0.0,            # -1.0 = narrow focus, 1.0 = broad perspective
            "certain_uncertain": 0.0        # -1.0 = certainty-seeking, 1.0 = uncertainty-tolerant
        }
        
        # Adjust dimensions based on persona type
        if persona.persona_type == "knowledge":  # Axis 8
            # Knowledge Experts tend toward theoretical, broad, long-term perspectives
            pov_vector["theoretical_practical"] = -0.6
            pov_vector["narrow_broad"] = 0.5
            pov_vector["short_long_term"] = 0.4
            
        elif persona.persona_type == "sector":  # Axis 9
            # Sector Experts tend toward practical, opportunity-focused, innovative perspectives
            pov_vector["theoretical_practical"] = 0.7
            pov_vector["risk_opportunity"] = 0.6
            pov_vector["conservative_innovative"] = 0.5
            
        elif persona.persona_type == "regulatory":  # Axis 10
            # Regulatory Experts tend toward risk-focused, conservative, certain perspectives
            pov_vector["risk_opportunity"] = -0.7
            pov_vector["conservative_innovative"] = -0.6
            pov_vector["certain_uncertain"] = -0.5
            
        elif persona.persona_type == "compliance":  # Axis 11
            # Compliance Experts tend toward practical, risk-focused, narrow perspectives
            pov_vector["theoretical_practical"] = 0.5
            pov_vector["risk_opportunity"] = -0.8
            pov_vector["narrow_broad"] = -0.6
        
        # Adjust based on query result confidence
        confidence = query_result.get("confidence", 0.7)
        certainty_adjustment = (confidence - 0.5) * 2  # maps 0.5-1.0 to 0.0-1.0
        pov_vector["certain_uncertain"] -= certainty_adjustment
        
        # Ensure all values are within -1.0 to 1.0
        pov_vector = {k: max(-1.0, min(1.0, v)) for k, v in pov_vector.items()}
        
        return pov_vector
"""
Universal Knowledge Graph (UKG) System - Quad Persona Engine

Processes a query through four expert personas (Knowledge, Sector, Regulatory,
Compliance) corresponding to axes 8-11 of the UKG system.

NOTE: This module previously contained two concatenated implementations that
each redefined ``QuadPersonaEngine``/``QueryState``; the second shadowed the
first, and the ``create_quad_persona_engine`` factory bound to a no-arg engine
while passing ``config_path`` -> a runtime TypeError. That duplication has been
removed. The data models now live in ``quad_persona/models.py``; this module
keeps the single live engine and its expert hierarchy.

The canonical, documented persona engine for production is ``backend/dsqp/``
(see docs/ARCHITECTURE.md); query-time 7-component persona construction is done
by ``core/system/persona_construction_service.py`` (which seeds PersonaProfile
via DSQPChain). This heuristic keyword-matching engine is NOT on the live query
path — A9 audit (2026-06-12) found its only external importers are the demo
scripts under ``scripts/demos/simulation/`` plus one Phase-5 test. (Its former
legacy consumer ``core/simulation/layer2_legacy_knowledge.py`` was deleted in
A6a, commit ``2afe2d14``.) Retained for the demos; see REPO_AUDIT_LOG.md (A9).

DISTINCT FROM backend/quad_persona/quad_engine.py, which is the gateway-only
async LLM-routing version (mode="quad"). The two coexist intentionally.
"""

import logging
import uuid
from typing import Dict

from core.persona.quad.models import PersonaProfile, QueryState

logger = logging.getLogger(__name__)

__all__ = [
    "PersonaProfile",
    "QueryState",
    "QuadPersona",
    "KnowledgeExpert",
    "SectorExpert",
    "RegulatoryExpert",
    "ComplianceExpert",
    "QuadPersonaEngine",
    "create_quad_persona_engine",
]


class QuadPersona:
    """Base class for a persona in the Quad Persona Engine."""
    
    def __init__(self, persona_id: str, persona_type: str, name: str, description: str):
        """Initialize a persona."""
        self.persona_id = persona_id
        self.persona_type = persona_type
        self.name = name
        self.description = description
        self.specialties = []
    
    def process_query(self, query_state: QueryState) -> Dict:
        """
        Process a query using this persona's expertise.
        
        Args:
            query_state: The query state
            
        Returns:
            Dictionary with the persona's perspective
        """
        # Base implementation - should be overridden by subclasses
        return {
            "persona_id": self.persona_id,
            "persona_type": self.persona_type,
            "name": self.name,
            "perspective": "Generic perspective from base persona class",
            "confidence": 0.5
        }


class KnowledgeExpert(QuadPersona):
    """Implements the Knowledge Expert persona."""
    
    def __init__(self):
        """Initialize the Knowledge Expert persona."""
        super().__init__(
            persona_id="knowledge_expert",
            persona_type="knowledge",
            name="Knowledge Expert",
            description="Domain knowledge specialist with deep theoretical understanding"
        )
        self.specialties = ["theoretical framework", "conceptual models", "research", "academic knowledge"]
    
    def process_query(self, query_state: QueryState) -> Dict:
        """Process a query from the Knowledge Expert perspective."""
        query_text = query_state.query_text.lower()
        context = query_state.context
        
        # Analyze query for knowledge components
        knowledge_relevance = 0.0
        for specialty in self.specialties:
            if specialty in query_text:
                knowledge_relevance += 0.2
        
        # Check for knowledge graph data
        kg_data = context.get("knowledge_graph", {})
        has_kg_data = (kg_data and kg_data.get("count", 0) > 0)
        
        # Simulated confidence based on relevant factors
        confidence = min(0.9, knowledge_relevance + (0.3 if has_kg_data else 0))
        
        # Simulated perspective based on domain knowledge
        perspective = (
            "From a theoretical knowledge perspective, this query relates to fundamental "
            "domain concepts that require structured analysis and academic understanding."
        )
        
        if has_kg_data:
            perspective += (
                " The knowledge graph provides relevant conceptual frameworks that can "
                "be applied to address this query with rigorous theoretical backing."
            )
        
        return {
            "persona_id": self.persona_id,
            "persona_type": self.persona_type,
            "name": self.name,
            "perspective": perspective,
            "confidence": confidence,
            "recommendations": [
                "Consider the theoretical implications",
                "Review relevant academic literature",
                "Apply conceptual models to structure the answer"
            ]
        }


class SectorExpert(QuadPersona):
    """Implements the Sector Expert persona."""
    
    def __init__(self):
        """Initialize the Sector Expert persona."""
        super().__init__(
            persona_id="sector_expert",
            persona_type="sector",
            name="Sector Expert",
            description="Industry specialist with practical sector experience"
        )
        self.specialties = ["industry", "business", "market", "sector", "practical", "implementation"]
        self.sectors = ["technology", "healthcare", "finance", "education", "government", "manufacturing"]
    
    def process_query(self, query_state: QueryState) -> Dict:
        """Process a query from the Sector Expert perspective."""
        query_text = query_state.query_text.lower()
        context = query_state.context
        
        # Analyze query for sector relevance
        sector_relevance = 0.0
        detected_sectors = []
        
        for specialty in self.specialties:
            if specialty in query_text:
                sector_relevance += 0.1
        
        for sector in self.sectors:
            if sector in query_text:
                sector_relevance += 0.2
                detected_sectors.append(sector)
        
        # Determine primary sector if detected
        primary_sector = detected_sectors[0] if detected_sectors else "general industry"
        
        # Simulated confidence based on sector relevance
        confidence = min(0.85, sector_relevance + 0.4)
        
        # Simulated perspective based on sector expertise
        perspective = (
            f"From a {primary_sector} sector perspective, this query relates to practical "
            "industry challenges that require business domain knowledge and real-world experience."
        )
        
        if context.get("domain"):
            perspective += f" The {context['domain']} domain context provides additional "
            "industry-specific considerations that should be factored into the response."
        
        return {
            "persona_id": self.persona_id,
            "persona_type": self.persona_type,
            "name": self.name,
            "perspective": perspective,
            "confidence": confidence,
            "sectors_identified": detected_sectors,
            "recommendations": [
                f"Apply {primary_sector} sector best practices",
                "Consider practical implementation challenges",
                "Align with industry standards and expectations"
            ]
        }


class RegulatoryExpert(QuadPersona):
    """Implements the Regulatory Expert persona."""
    
    def __init__(self):
        """Initialize the Regulatory Expert persona."""
        super().__init__(
            persona_id="regulatory_expert",
            persona_type="regulatory",
            name="Regulatory Expert",
            description="Specialist in regulatory frameworks and legal requirements"
        )
        self.specialties = [
            "regulation", "legal", "law", "compliance", "rules", "framework", 
            "policy", "governance", "statutory"
        ]
        self.frameworks = {
            "gdpr": "General Data Protection Regulation",
            "hipaa": "Health Insurance Portability and Accountability Act",
            "basel": "Basel Accords for banking regulation",
            "ferpa": "Family Educational Rights and Privacy Act",
            "far": "Federal Acquisition Regulation"
        }
    
    def process_query(self, query_state: QueryState) -> Dict:
        """Process a query from the Regulatory Expert perspective."""
        query_text = query_state.query_text.lower()
        
        # Analyze query for regulatory relevance
        regulatory_relevance = 0.0
        detected_frameworks = []
        
        for specialty in self.specialties:
            if specialty in query_text:
                regulatory_relevance += 0.15
        
        for code, framework in self.frameworks.items():
            if code in query_text or framework.lower() in query_text:
                regulatory_relevance += 0.2
                detected_frameworks.append(framework)
        
        # Simulated confidence based on regulatory relevance
        confidence = min(0.9, regulatory_relevance + 0.3)
        
        # Simulated perspective based on regulatory expertise
        perspective = (
            "From a regulatory perspective, this query requires consideration of "
            "legal frameworks and compliance requirements."
        )
        
        if detected_frameworks:
            framework_list = ", ".join(detected_frameworks)
            perspective += f" Specifically, {framework_list} may apply in this context."
        else:
            perspective += (
                " While no specific regulations were explicitly referenced, general "
                "regulatory principles should be considered."
            )
        
        return {
            "persona_id": self.persona_id,
            "persona_type": self.persona_type,
            "name": self.name,
            "perspective": perspective,
            "confidence": confidence,
            "frameworks_identified": detected_frameworks,
            "recommendations": [
                "Ensure alignment with relevant regulations",
                "Consider legal implications of any proposed actions",
                "Document compliance considerations"
            ]
        }


class ComplianceExpert(QuadPersona):
    """Implements the Compliance Expert persona."""
    
    def __init__(self):
        """Initialize the Compliance Expert persona."""
        super().__init__(
            persona_id="compliance_expert",
            persona_type="compliance",
            name="Compliance Expert",
            description="Specialist in implementing compliance measures and standards"
        )
        self.specialties = [
            "compliance", "standard", "audit", "certification", "control", 
            "procedure", "assessment", "verification"
        ]
        self.standards = {
            "iso": "ISO standards (e.g., ISO 27001, ISO 9001)",
            "soc": "Service Organization Control reports (SOC 1, SOC 2)",
            "pci": "Payment Card Industry Data Security Standard (PCI DSS)",
            "nist": "National Institute of Standards and Technology frameworks",
            "cmmc": "Cybersecurity Maturity Model Certification"
        }
    
    def process_query(self, query_state: QueryState) -> Dict:
        """Process a query from the Compliance Expert perspective."""
        query_text = query_state.query_text.lower()
        context = query_state.context
        
        # Analyze query for compliance relevance
        compliance_relevance = 0.0
        detected_standards = []
        
        for specialty in self.specialties:
            if specialty in query_text:
                compliance_relevance += 0.15
        
        for code, standard in self.standards.items():
            if code in query_text or standard.lower() in query_text:
                compliance_relevance += 0.2
                detected_standards.append(standard)
        
        # Simulated confidence based on compliance relevance
        confidence = min(0.9, compliance_relevance + 0.3)
        
        # Simulated perspective based on compliance expertise
        perspective = (
            "From a compliance perspective, this query relates to implementing and "
            "verifying adherence to standards and control frameworks."
        )
        
        if detected_standards:
            standards_list = ", ".join(detected_standards)
            perspective += f" Specifically, {standards_list} are relevant to this context."
        else:
            perspective += (
                " While no specific standards were explicitly referenced, general "
                "compliance best practices should be considered."
            )
        
        # Check for verification requirements in context
        if context.get("require_verification"):
            perspective += (
                " The requirement for verification indicates a need for rigorous "
                "documentation and evidence collection to demonstrate compliance."
            )
        
        return {
            "persona_id": self.persona_id,
            "persona_type": self.persona_type,
            "name": self.name,
            "perspective": perspective,
            "confidence": confidence,
            "standards_identified": detected_standards,
            "recommendations": [
                "Implement appropriate control measures",
                "Establish verification and documentation procedures",
                "Consider audit requirements and evidence collection"
            ]
        }



class QuadPersonaEngine:
    """
    Implements the Quad Persona Engine, which processes queries through
    four expert personas to provide comprehensive perspectives.
    """
    
    def __init__(self):
        """Initialize the Quad Persona Engine."""
        self.personas = {
            "knowledge": KnowledgeExpert(),
            "sector": SectorExpert(),
            "regulatory": RegulatoryExpert(),
            "compliance": ComplianceExpert()
        }
        logger.info("Quad Persona Engine initialized")
    
    def process_query(self, query_text: str, context: Dict = None) -> Dict:
        """
        Process a query through all personas.
        
        Args:
            query_text: The query text
            context: Optional context information
            
        Returns:
            Dictionary with combined perspectives
        """
        # Create a query state
        query_id = f"q_{uuid.uuid4().hex[:8]}"
        query_state = QueryState(query_id=query_id, query_text=query_text, context=context or {})
        
        # Process with all personas
        self._process_with_all_personas(query_state)
        
        # Combine perspectives
        result = self._combine_perspectives(query_state)
        
        return result
    
    def _process_with_all_personas(self, query_state: QueryState):
        """
        Process a query through all personas.
        
        Args:
            query_state: The query state to process
        """
        for persona_id, persona in self.personas.items():
            try:
                result = persona.process_query(query_state)
                query_state.add_persona_result(persona_id, result)
                logger.debug(f"Processed query {query_state.query_id} with {persona_id} persona")
            except Exception as e:
                logger.error(f"Error processing with {persona_id} persona: {str(e)}")
    
    def _combine_perspectives(self, query_state: QueryState) -> Dict:
        """
        Combine perspectives from all personas.
        
        Args:
            query_state: The query state with persona results
            
        Returns:
            Combined result dictionary
        """
        persona_results = query_state.persona_results
        
        if not persona_results:
            logger.warning(f"No persona results for query {query_state.query_id}")
            return {
                "query_id": query_state.query_id,
                "query_text": query_state.query_text,
                "perspectives": [],
                "confidence": 0.0,
                "error": "No persona results available"
            }
        
        # Extract perspectives
        perspectives = []
        confidence_sum = 0.0
        recommendations = []
        
        for persona_id, result in persona_results.items():
            perspectives.append({
                "persona": result["name"],
                "perspective": result["perspective"],
                "confidence": result["confidence"]
            })
            
            confidence_sum += result["confidence"]
            
            if "recommendations" in result:
                recommendations.extend(result["recommendations"])
        
        # Calculate overall confidence (average of persona confidences)
        avg_confidence = confidence_sum / len(persona_results) if persona_results else 0.0
        
        # Create combined result
        combined_result = {
            "query_id": query_state.query_id,
            "query_text": query_state.query_text,
            "perspectives": perspectives,
            "confidence": avg_confidence,
            "recommendations": list(set(recommendations))  # Remove duplicates
        }
        
        # Set as final result
        query_state.set_final_result(combined_result, avg_confidence)
        
        return combined_result


def create_quad_persona_engine(config_path: str = None) -> QuadPersonaEngine:
    """Create and initialize a Quad Persona Engine.

    The engine takes no constructor arguments; ``config_path`` is accepted for
    backwards compatibility with the historical factory signature but is not
    consumed. (Previously this factory passed ``config_path`` positionally to a
    no-arg engine, raising TypeError.)
    """
    if config_path is not None:
        logger.warning(
            "create_quad_persona_engine received config_path=%r, but the engine "
            "does not consume it; ignoring.",
            config_path,
        )
    engine = QuadPersonaEngine()
    logger.info("Created Quad Persona Engine")
    return engine

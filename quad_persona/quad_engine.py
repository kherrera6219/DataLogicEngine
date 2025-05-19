"""
Universal Knowledge Graph (UKG) System - Quad Persona Engine

This module implements the core Quad Persona Simulation Engine that processes
queries through four expert roles (Knowledge, Sector, Regulatory, and Compliance)
corresponding to Axes 8-11 of the UKG system.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import os

logger = logging.getLogger(__name__)

class PersonaProfile:
    """
    Represents a complete persona profile with 7 components:
    job_role, education, certifications, skills, training, career_path, related_jobs
    """
    
    def __init__(self, persona_id: str, axis_number: int, persona_type: str, name: str, description: str = None):
        """Initialize a persona profile."""
        self.persona_id = persona_id
        self.axis_number = axis_number  # 8, 9, 10, or 11
        self.persona_type = persona_type  # knowledge, sector, regulatory, compliance
        self.name = name
        self.description = description or ""
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # The 7 core components of each persona
        self.components = {
            "job_role": {},
            "education": {},
            "certifications": {},
            "skills": {},
            "training": {},
            "career_path": {},
            "related_jobs": {}
        }
        
        # Additional metadata specific to this persona
        self.metadata = {}
        
        # Axis-specific attributes
        if axis_number == 10:  # Regulatory Expert (Octopus Node)
            self.octopus_connections = []  # Connections to different regulatory frameworks
        
        if axis_number == 11:  # Compliance Expert (Spiderweb Node)
            self.spiderweb_connections = []  # Cross-standard compliance connections
    
    def set_component(self, component_type: str, data: Dict[str, Any]) -> bool:
        """Set data for a specific component of the persona."""
        if component_type not in self.components:
            logger.error(f"Invalid component type: {component_type}")
            return False
            
        self.components[component_type] = data
        self.updated_at = datetime.utcnow()
        return True
    
    def get_component(self, component_type: str) -> Dict[str, Any]:
        """Get data for a specific component of the persona."""
        if component_type not in self.components:
            logger.error(f"Invalid component type: {component_type}")
            return {}
            
        return self.components[component_type]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the persona profile to a dictionary."""
        result = {
            "persona_id": self.persona_id,
            "axis_number": self.axis_number,
            "persona_type": self.persona_type,
            "name": self.name,
            "description": self.description,
            "components": self.components,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        
        if self.axis_number == 10:
            result["octopus_connections"] = self.octopus_connections
            
        if self.axis_number == 11:
            result["spiderweb_connections"] = self.spiderweb_connections
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonaProfile':
        """Create a persona profile from a dictionary."""
        profile = cls(
            persona_id=data.get("persona_id", str(uuid.uuid4())),
            axis_number=data.get("axis_number"),
            persona_type=data.get("persona_type"),
            name=data.get("name"),
            description=data.get("description")
        )
        
        # Load components
        for component_type, component_data in data.get("components", {}).items():
            if component_type in profile.components:
                profile.components[component_type] = component_data
        
        # Load metadata
        profile.metadata = data.get("metadata", {})
        
        # Load timestamps
        if "created_at" in data:
            profile.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            profile.updated_at = datetime.fromisoformat(data["updated_at"])
        
        # Load axis-specific attributes
        if profile.axis_number == 10 and "octopus_connections" in data:
            profile.octopus_connections = data["octopus_connections"]
            
        if profile.axis_number == 11 and "spiderweb_connections" in data:
            profile.spiderweb_connections = data["spiderweb_connections"]
            
        return profile


class QueryState:
    """
    Represents the state of a query being processed through the Quad Persona Engine.
    This includes the original query, context, processing state, and results from each persona.
    """
    
    def __init__(self, query_id: str, query_text: str, context: Dict[str, Any] = None):
        """Initialize a query state."""
        self.query_id = query_id
        self.query_text = query_text
        self.context = context or {}
        self.created_at = datetime.utcnow()
        self.completed_at = None
        self.status = "initialized"  # initialized, processing, completed, failed
        
        # Processing metadata
        self.processing_history = []
        self.current_pass = 0
        self.max_passes = 3  # Default: 3 recursive passes through the personas
        
        # Results from each persona
        self.persona_results = {
            "knowledge": None,  # Axis 8
            "sector": None,     # Axis 9
            "regulatory": None, # Axis 10
            "compliance": None  # Axis 11
        }
        
        # Final synthesized result
        self.final_result = None
        
        # Performance metrics
        self.metrics = {
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "duration_ms": None,
            "persona_processing_times": {},
            "confidence_scores": {}
        }
    
    def update_status(self, new_status: str):
        """Update the status of the query processing."""
        self.status = new_status
        if new_status == "completed" or new_status == "failed":
            self.completed_at = datetime.utcnow()
            self.metrics["end_time"] = self.completed_at.isoformat()
            start_time = datetime.fromisoformat(self.metrics["start_time"])
            duration = (self.completed_at - start_time).total_seconds() * 1000
            self.metrics["duration_ms"] = duration
    
    def add_processing_event(self, event_type: str, details: Dict[str, Any]):
        """Add a processing event to the history."""
        self.processing_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details
        })
    
    def set_persona_result(self, persona_type: str, result: Dict[str, Any], processing_time_ms: float = None):
        """Set the result from a specific persona."""
        if persona_type not in self.persona_results:
            logger.error(f"Invalid persona type: {persona_type}")
            return False
            
        self.persona_results[persona_type] = result
        
        if processing_time_ms is not None:
            self.metrics["persona_processing_times"][persona_type] = processing_time_ms
            
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the query state to a dictionary."""
        return {
            "query_id": self.query_id,
            "query_text": self.query_text,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "processing_history": self.processing_history,
            "current_pass": self.current_pass,
            "max_passes": self.max_passes,
            "persona_results": self.persona_results,
            "final_result": self.final_result,
            "metrics": self.metrics
        }


class QuadPersonaEngine:
    """
    The Quad Persona Simulation Engine processes queries through four expert roles
    corresponding to Axes 8-11 of the UKG system, using deep recursive learning
    to produce expert-informed responses.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize the Quad Persona Engine."""
        self.personas = {
            "knowledge": {},   # Axis 8
            "sector": {},      # Axis 9
            "regulatory": {},  # Axis 10
            "compliance": {}   # Axis 11
        }
        
        self.active_queries = {}  # query_id -> QueryState
        self.completed_queries = {}  # query_id -> QueryState (last 100)
        
        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
        else:
            # Use default configuration
            self.config = {
                "max_recursive_passes": 3,
                "min_confidence_threshold": 0.7,
                "enable_memory_integration": True,
                "default_persona_weights": {
                    "knowledge": 1.0,
                    "sector": 1.0,
                    "regulatory": 1.0,
                    "compliance": 1.0
                }
            }
        
        # Initialize default personas if none exist
        if not any(self.personas.values()):
            self._init_default_personas()
    
    def load_config(self, config_path: str):
        """Load configuration from a YAML or JSON file."""
        try:
            with open(config_path, 'r') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    import yaml
                    self.config = yaml.safe_load(f)
                else:
                    self.config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            # Use default configuration
            self.config = {
                "max_recursive_passes": 3,
                "min_confidence_threshold": 0.7,
                "enable_memory_integration": True,
                "default_persona_weights": {
                    "knowledge": 1.0,
                    "sector": 1.0,
                    "regulatory": 1.0,
                    "compliance": 1.0
                }
            }
    
    def _init_default_personas(self):
        """Initialize default personas for each axis."""
        default_personas = {
            "knowledge": {  # Axis 8
                "persona_id": "knowledge_default",
                "axis_number": 8,
                "persona_type": "knowledge",
                "name": "Knowledge Expert",
                "description": "Expert in domain-specific knowledge and academic concepts",
                "components": {
                    "job_role": {
                        "title": "Domain Specialist",
                        "description": "Specialized expertise in specific knowledge domains"
                    },
                    "education": {
                        "level": "Advanced Degree",
                        "description": "PhD or equivalent in specialized field"
                    },
                    "certifications": {
                        "items": ["Domain Certification", "Research Methodology"],
                        "description": "Specialized certifications in knowledge fields"
                    },
                    "skills": {
                        "items": ["Research", "Analysis", "Theory Development"],
                        "description": "Deep technical knowledge and analytical capabilities"
                    },
                    "training": {
                        "programs": ["Continued Education", "Research Methodologies"],
                        "description": "Ongoing training in cutting-edge developments"
                    },
                    "career_path": {
                        "progression": ["Researcher", "Senior Specialist", "Knowledge Lead"],
                        "description": "Career focused on knowledge development and research"
                    },
                    "related_jobs": {
                        "roles": ["Researcher", "Professor", "Subject Matter Expert"],
                        "description": "Similar roles in knowledge-focused domains"
                    }
                }
            },
            "sector": {  # Axis 9
                "persona_id": "sector_default",
                "axis_number": 9,
                "persona_type": "sector",
                "name": "Sector Expert",
                "description": "Expert in industry-specific practices and standards",
                "components": {
                    "job_role": {
                        "title": "Industry Consultant",
                        "description": "Advisory role on industry-specific challenges"
                    },
                    "education": {
                        "level": "Business Background",
                        "description": "MBA or similar with industry focus"
                    },
                    "certifications": {
                        "items": ["Industry Association Membership", "Sector Analysis"],
                        "description": "Industry-specific credentials and qualifications"
                    },
                    "skills": {
                        "items": ["Market Analysis", "Strategic Planning", "Industry Benchmarking"],
                        "description": "Skills in analyzing and navigating industry dynamics"
                    },
                    "training": {
                        "programs": ["Industry Seminars", "Market Updates"],
                        "description": "Specialized training in industry developments"
                    },
                    "career_path": {
                        "progression": ["Analyst", "Manager", "Executive"],
                        "description": "Progression through industry leadership roles"
                    },
                    "related_jobs": {
                        "roles": ["Business Analyst", "Strategy Consultant", "Industry Advisor"],
                        "description": "Similar roles with industry-specific focus"
                    }
                }
            },
            "regulatory": {  # Axis 10 (Octopus Node)
                "persona_id": "regulatory_default",
                "axis_number": 10,
                "persona_type": "regulatory",
                "name": "Regulatory Expert",
                "description": "Expert in legal frameworks, regulations, and policy",
                "components": {
                    "job_role": {
                        "title": "Regulatory Affairs Specialist",
                        "description": "Specializes in regulatory compliance and interpretation"
                    },
                    "education": {
                        "level": "Legal Background",
                        "description": "Law degree or specialized regulatory training"
                    },
                    "certifications": {
                        "items": ["Regulatory Affairs Certification", "Policy Analysis"],
                        "description": "Specialized regulatory and compliance certifications"
                    },
                    "skills": {
                        "items": ["Regulatory Analysis", "Compliance Assessment", "Policy Interpretation"],
                        "description": "Skills in navigating complex regulatory frameworks"
                    },
                    "training": {
                        "programs": ["Regulatory Updates", "Compliance Workshops"],
                        "description": "Ongoing training in regulatory changes"
                    },
                    "career_path": {
                        "progression": ["Compliance Associate", "Regulatory Specialist", "Chief Compliance Officer"],
                        "description": "Career progression in regulatory oversight"
                    },
                    "related_jobs": {
                        "roles": ["Legal Counsel", "Compliance Officer", "Policy Advisor"],
                        "description": "Similar roles focused on regulatory matters"
                    }
                },
                "octopus_connections": [
                    "International Law", "Federal Regulations", "Industry Standards",
                    "State/Local Requirements", "Licensing Bodies"
                ]
            },
            "compliance": {  # Axis 11 (Spiderweb Node)
                "persona_id": "compliance_default",
                "axis_number": 11,
                "persona_type": "compliance",
                "name": "Compliance Expert",
                "description": "Expert in ensuring adherence to standards and requirements",
                "components": {
                    "job_role": {
                        "title": "Compliance Officer",
                        "description": "Ensures organizational adherence to requirements"
                    },
                    "education": {
                        "level": "Compliance Background",
                        "description": "Specialized education in compliance frameworks"
                    },
                    "certifications": {
                        "items": ["Certified Compliance Professional", "Ethics Certification"],
                        "description": "Formal compliance and ethics certifications"
                    },
                    "skills": {
                        "items": ["Risk Assessment", "Audit Procedures", "Compliance Monitoring"],
                        "description": "Skills in ensuring and verifying compliance"
                    },
                    "training": {
                        "programs": ["Compliance Updates", "Audit Techniques"],
                        "description": "Specialized training in compliance verification"
                    },
                    "career_path": {
                        "progression": ["Compliance Analyst", "Compliance Manager", "Head of Compliance"],
                        "description": "Career progression in compliance oversight"
                    },
                    "related_jobs": {
                        "roles": ["Auditor", "Quality Assurance", "Ethics Officer"],
                        "description": "Similar roles in oversight and verification"
                    }
                },
                "spiderweb_connections": [
                    "Cross-Regulatory Overlaps", "Standard Harmonization", 
                    "Compliance Integration", "Unified Reporting"
                ]
            }
        }
        
        # Create and add default personas
        for persona_type, persona_data in default_personas.items():
            profile = PersonaProfile(
                persona_id=persona_data["persona_id"],
                axis_number=persona_data["axis_number"],
                persona_type=persona_data["persona_type"],
                name=persona_data["name"],
                description=persona_data["description"]
            )
            
            # Set components
            for component_type, component_data in persona_data["components"].items():
                profile.set_component(component_type, component_data)
            
            # Set axis-specific attributes
            if persona_type == "regulatory" and "octopus_connections" in persona_data:
                profile.octopus_connections = persona_data["octopus_connections"]
            
            if persona_type == "compliance" and "spiderweb_connections" in persona_data:
                profile.spiderweb_connections = persona_data["spiderweb_connections"]
            
            # Add persona to the engine
            self.add_persona(profile)
    
    def add_persona(self, profile: PersonaProfile) -> bool:
        """Add a persona profile to the engine."""
        if profile.persona_type not in self.personas:
            logger.error(f"Invalid persona type: {profile.persona_type}")
            return False
        
        self.personas[profile.persona_type][profile.persona_id] = profile
        logger.info(f"Added persona {profile.name} (ID: {profile.persona_id}) of type {profile.persona_type}")
        return True
    
    def get_persona(self, persona_type: str, persona_id: str) -> Optional[PersonaProfile]:
        """Get a persona profile by type and ID."""
        if persona_type not in self.personas:
            logger.error(f"Invalid persona type: {persona_type}")
            return None
        
        return self.personas[persona_type].get(persona_id)
    
    def get_personas_by_type(self, persona_type: str) -> Dict[str, PersonaProfile]:
        """Get all personas of a specific type."""
        if persona_type not in self.personas:
            logger.error(f"Invalid persona type: {persona_type}")
            return {}
        
        return self.personas[persona_type]
    
    def process_query(self, query_text: str, context: Dict[str, Any] = None) -> str:
        """
        Process a query through the Quad Persona Engine.
        
        This method:
        1. Initializes a new query state
        2. Runs the query through each persona (Axes 8-11)
        3. Applies recursive refinement
        4. Synthesizes a final response
        
        Args:
            query_text: The text of the query to process
            context: Optional context information for the query
            
        Returns:
            The final synthesized response
        """
        # Initialize query state
        query_id = str(uuid.uuid4())
        query_state = QueryState(query_id, query_text, context)
        self.active_queries[query_id] = query_state
        
        try:
            # Update query status
            query_state.update_status("processing")
            query_state.add_processing_event("processing_started", {
                "query_text": query_text,
                "context_keys": list(context.keys()) if context else []
            })
            
            # Set max passes from config
            query_state.max_passes = self.config.get("max_recursive_passes", 3)
            
            # Process with each persona
            for pass_number in range(query_state.max_passes):
                query_state.current_pass = pass_number + 1
                query_state.add_processing_event("pass_started", {
                    "pass_number": query_state.current_pass,
                    "max_passes": query_state.max_passes
                })
                
                # Process each persona in sequence
                self._process_with_all_personas(query_state)
                
                # Check if confidence threshold is met
                confidence_values = [
                    result.get("confidence", 0) 
                    for result in query_state.persona_results.values() 
                    if result is not None
                ]
                
                if confidence_values:
                    avg_confidence = sum(confidence_values) / len(confidence_values)
                    min_threshold = self.config.get("min_confidence_threshold", 0.7)
                    
                    if avg_confidence >= min_threshold:
                        logger.info(f"Confidence threshold met after pass {query_state.current_pass}: {avg_confidence:.2f} >= {min_threshold:.2f}")
                        break
            
            # Synthesize final response
            final_result = self._synthesize_response(query_state)
            query_state.final_result = final_result
            
            # Update query status
            query_state.update_status("completed")
            query_state.add_processing_event("processing_completed", {
                "passes_completed": query_state.current_pass,
                "final_confidence": final_result.get("confidence", 0)
            })
            
            # Move to completed queries
            self._add_to_completed_queries(query_id)
            
            return final_result.get("response", "")
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            query_state.update_status("failed")
            query_state.add_processing_event("processing_failed", {
                "error": str(e)
            })
            
            # Move to completed queries
            self._add_to_completed_queries(query_id)
            
            return f"Error processing query: {str(e)}"
    
    def _process_with_all_personas(self, query_state: QueryState):
        """Process a query through all personas in sequence."""
        # Process in a specific order to build context
        persona_types = ["knowledge", "sector", "regulatory", "compliance"]
        
        for persona_type in persona_types:
            start_time = datetime.utcnow()
            
            # Get available personas of this type
            personas = self.get_personas_by_type(persona_type)
            if not personas:
                logger.warning(f"No {persona_type} personas available")
                continue
            
            # For simplicity, use the first available persona
            # In a real implementation, select the most appropriate persona based on the query
            persona_id = next(iter(personas.keys()))
            persona = personas[persona_id]
            
            # Process with this persona
            result = self._process_with_persona(query_state, persona)
            
            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Store result
            query_state.set_persona_result(persona_type, result, processing_time_ms)
            
            # Log processing
            query_state.add_processing_event(f"{persona_type}_processing", {
                "persona_id": persona_id,
                "persona_name": persona.name,
                "processing_time_ms": processing_time_ms,
                "confidence": result.get("confidence", 0)
            })
    
    def _process_with_persona(self, query_state: QueryState, persona: PersonaProfile) -> Dict[str, Any]:
        """
        Process a query with a specific persona.
        
        This is where the actual "thinking" from each expert perspective happens.
        In a real implementation, this would involve more sophisticated processing,
        potentially using language models fine-tuned for each persona type.
        """
        # Extract query information
        query_text = query_state.query_text
        context = query_state.context
        current_pass = query_state.current_pass
        
        # Gather information from previous personas if not the first pass
        previous_insights = {}
        if current_pass > 1:
            for persona_type, result in query_state.persona_results.items():
                if result is not None:
                    previous_insights[persona_type] = result.get("response", "")
        
        # Build a response based on the persona's expertise
        # This is a simplified implementation for demonstration
        
        # Base response structure
        response = {
            "persona_type": persona.persona_type,
            "persona_id": persona.persona_id,
            "persona_name": persona.name,
            "confidence": 0.7 + (0.1 * (current_pass - 1)),  # Confidence increases with each pass
            "response": ""
        }
        
        # Generate response based on persona type
        if persona.persona_type == "knowledge":  # Axis 8
            response["response"] = self._generate_knowledge_response(query_text, persona, previous_insights)
        elif persona.persona_type == "sector":  # Axis 9
            response["response"] = self._generate_sector_response(query_text, persona, previous_insights)
        elif persona.persona_type == "regulatory":  # Axis 10
            response["response"] = self._generate_regulatory_response(query_text, persona, previous_insights)
        elif persona.persona_type == "compliance":  # Axis 11
            response["response"] = self._generate_compliance_response(query_text, persona, previous_insights)
        
        return response
    
    def _generate_knowledge_response(self, query: str, persona: PersonaProfile, previous_insights: Dict[str, str]) -> str:
        """Generate a response from the Knowledge Expert perspective (Axis 8)."""
        job_role = persona.get_component("job_role").get("title", "Knowledge Expert")
        skills = ", ".join(persona.get_component("skills").get("items", ["Analysis"]))
        
        # Build response
        response = f"As a {job_role} with expertise in {skills}, I can provide the following insights: "
        
        # Add domain-specific knowledge
        response += "From a knowledge perspective, this query relates to fundamental concepts and theoretical frameworks. "
        response += "The academic literature suggests multiple approaches to understanding this topic, "
        response += "with varying levels of empirical support and theoretical grounding."
        
        # Add previous insights if available
        if previous_insights:
            response += "\n\nBuilding on previous analysis, I would add these knowledge-specific considerations: "
            response += "The conceptual frameworks need to be integrated with practical applications in a cohesive manner."
        
        return response
    
    def _generate_sector_response(self, query: str, persona: PersonaProfile, previous_insights: Dict[str, str]) -> str:
        """Generate a response from the Sector Expert perspective (Axis 9)."""
        job_role = persona.get_component("job_role").get("title", "Sector Expert")
        skills = ", ".join(persona.get_component("skills").get("items", ["Market Analysis"]))
        
        # Build response
        response = f"From a sector perspective as a {job_role} focused on {skills}, I observe that: "
        
        # Add industry-specific insights
        response += "Industry trends indicate evolving practices in this area, with market leaders adopting innovative approaches. "
        response += "Across different sectors, we see varying levels of maturity and implementation, "
        response += "with regulatory and competitive factors driving adoption in certain industries more than others."
        
        # Incorporate knowledge expert insights if available
        if "knowledge" in previous_insights:
            response += "\n\nWhile the theoretical framework is important as noted by the Knowledge Expert, "
            response += "industry implementation requires practical considerations around ROI, operational impacts, and competitive positioning."
        
        return response
    
    def _generate_regulatory_response(self, query: str, persona: PersonaProfile, previous_insights: Dict[str, str]) -> str:
        """Generate a response from the Regulatory Expert perspective (Axis 10)."""
        job_role = persona.get_component("job_role").get("title", "Regulatory Expert")
        octopus_connections = persona.octopus_connections
        
        # Build response
        response = f"As a {job_role} analyzing the regulatory landscape through multiple frameworks, I can state that: "
        
        # Add regulatory insights
        response += "The regulatory environment surrounding this topic is complex and multi-layered. "
        
        if octopus_connections:
            response += f"Considering the {len(octopus_connections)} key regulatory domains "
            response += f"({', '.join(octopus_connections[:3])}{'...' if len(octopus_connections) > 3 else ''}), "
            response += "there are both overlaps and gaps in how this area is governed. "
        
        response += "Compliance requirements vary by jurisdiction, with some regions implementing more stringent standards than others."
        
        # Incorporate previous insights
        if "knowledge" in previous_insights and "sector" in previous_insights:
            response += "\n\nWhile the theoretical frameworks and industry practices noted by other experts are important, "
            response += "regulatory considerations must be integrated early in decision-making to ensure compliance "
            response += "and avoid potential penalties or market access restrictions."
        
        return response
    
    def _generate_compliance_response(self, query: str, persona: PersonaProfile, previous_insights: Dict[str, str]) -> str:
        """Generate a response from the Compliance Expert perspective (Axis 11)."""
        job_role = persona.get_component("job_role").get("title", "Compliance Officer")
        spiderweb_connections = persona.spiderweb_connections
        
        # Build response
        response = f"Speaking as a {job_role} with a focus on interconnected compliance requirements, I recommend: "
        
        # Add compliance insights
        response += "To ensure full compliance across overlapping requirements, a structured approach is necessary. "
        
        if spiderweb_connections:
            response += f"This requires attention to {len(spiderweb_connections)} key integration areas "
            response += f"({', '.join(spiderweb_connections[:2])}{'...' if len(spiderweb_connections) > 2 else ''}). "
        
        response += "Organizations should implement robust documentation, regular audits, and clear accountability frameworks."
        
        # Synthesize all previous insights
        if len(previous_insights) >= 3:
            response += "\n\nSynthesizing all previous expert insights, a comprehensive approach would integrate: "
            response += "the theoretical frameworks from the Knowledge Expert, "
            response += "market-driven considerations from the Sector Expert, "
            response += "and regulatory requirements highlighted by the Regulatory Expert. "
            response += "This creates a compliance framework that is academically sound, practically implementable, and legally defensible."
        
        return response
    
    def _synthesize_response(self, query_state: QueryState) -> Dict[str, Any]:
        """
        Synthesize a final response from all persona results.
        
        This combines the insights from all personas into a coherent,
        comprehensive response that represents the collective expertise.
        """
        # Collect all persona responses
        persona_responses = {}
        for persona_type, result in query_state.persona_results.items():
            if result is not None:
                persona_responses[persona_type] = {
                    "response": result.get("response", ""),
                    "confidence": result.get("confidence", 0),
                    "persona_name": result.get("persona_name", "")
                }
        
        if not persona_responses:
            return {
                "response": "Unable to generate a response due to lack of persona insights.",
                "confidence": 0.0,
                "active_personas": []
            }
        
        # Calculate average confidence
        confidence_values = [data["confidence"] for data in persona_responses.values()]
        avg_confidence = sum(confidence_values) / len(confidence_values)
        
        # Build introduction based on active personas
        active_personas = list(persona_responses.keys())
        
        if len(active_personas) == 1:
            intro = f"Based on analysis from the {persona_responses[active_personas[0]]['persona_name']}:"
        else:
            intro = f"Synthesizing insights from {len(active_personas)} expert perspectives "
            intro += f"({', '.join([persona_responses[p]['persona_name'] for p in active_personas])}):"
        
        # Combine insights with transitions
        combined_insights = ""
        
        # Knowledge insights (if available)
        if "knowledge" in persona_responses:
            combined_insights += "\n\n📚 From a knowledge perspective:\n"
            combined_insights += persona_responses["knowledge"]["response"]
        
        # Sector insights (if available)
        if "sector" in persona_responses:
            combined_insights += "\n\n🏢 From an industry perspective:\n"
            combined_insights += persona_responses["sector"]["response"]
        
        # Regulatory insights (if available)
        if "regulatory" in persona_responses:
            combined_insights += "\n\n⚖️ From a regulatory standpoint:\n"
            combined_insights += persona_responses["regulatory"]["response"]
        
        # Compliance insights (if available)
        if "compliance" in persona_responses:
            combined_insights += "\n\n✓ For ensuring compliance:\n"
            combined_insights += persona_responses["compliance"]["response"]
        
        # Add summary if all four personas contributed
        if len(active_personas) == 4:
            combined_insights += "\n\n🔄 Integrated Summary:\n"
            combined_insights += "When combining all four perspectives, a comprehensive approach emerges that addresses "
            combined_insights += "theoretical foundations, practical industry applications, regulatory requirements, and "
            combined_insights += "compliance frameworks in a cohesive manner. This multi-dimensional analysis provides "
            combined_insights += "a more complete understanding than any single perspective could offer."
        
        # Final synthesized response
        final_response = f"{intro}{combined_insights}"
        
        return {
            "response": final_response,
            "confidence": avg_confidence,
            "active_personas": active_personas
        }
    
    def _add_to_completed_queries(self, query_id: str):
        """Add a query to completed queries and remove from active queries."""
        if query_id in self.active_queries:
            # Add to completed queries
            self.completed_queries[query_id] = self.active_queries[query_id]
            
            # Remove from active queries
            del self.active_queries[query_id]
            
            # Limit completed queries to last 100
            if len(self.completed_queries) > 100:
                oldest_query_id = next(iter(self.completed_queries))
                del self.completed_queries[oldest_query_id]
    
    def get_query_state(self, query_id: str) -> Optional[QueryState]:
        """Get the state of a query by ID."""
        if query_id in self.active_queries:
            return self.active_queries[query_id]
        
        if query_id in self.completed_queries:
            return self.completed_queries[query_id]
        
        return None


def create_quad_persona_engine(config_path: str = None) -> QuadPersonaEngine:
    """Create and initialize a Quad Persona Engine."""
    engine = QuadPersonaEngine(config_path)
    logger.info("Created Quad Persona Engine")
    return engine
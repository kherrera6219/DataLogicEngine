"""
KA-16: Simulation Memory Patch

This algorithm manages the integration of new information into the simulation's
memory system, handling the persistence, update, and retrieval of context data.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import json
import os
import copy

logger = logging.getLogger(__name__)

class SimulationMemoryPatch:
    """
    KA-16: Integrates and consolidates simulation memory with new information.
    
    This algorithm handles the persistence of simulation results, context updates,
    and retrieval of prior knowledge, supporting cross-query memory for simulation layers.
    """
    
    def __init__(self, memory_path: Optional[str] = None):
        """
        Initialize the Simulation Memory Patch algorithm.
        
        Args:
            memory_path: Optional path to the memory storage file
        """
        # Default memory path if not provided
        self.memory_path = memory_path or os.path.join("data", "simulation_memory.json")
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)
        
        # Initialize memory cache
        self.memory_cache = self._load_memory()
        
        logger.info("KA-16: Simulation Memory Patch initialized")
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from storage or initialize if not exists."""
        try:
            if os.path.exists(self.memory_path):
                with open(self.memory_path, 'r') as f:
                    return json.load(f)
            else:
                return self._initialize_memory()
        except Exception as e:
            logger.error(f"Error loading memory: {str(e)}")
            return self._initialize_memory()
    
    def _initialize_memory(self) -> Dict[str, Any]:
        """Initialize an empty memory structure."""
        memory = {
            "sessions": {},
            "entities": {},
            "concepts": {},
            "facts": {},
            "meta": {
                "last_updated": datetime.now().isoformat(),
                "version": "1.0",
                "patch_count": 0
            }
        }
        return memory
    
    def _save_memory(self):
        """Save memory to persistent storage."""
        try:
            # Update metadata
            self.memory_cache["meta"]["last_updated"] = datetime.now().isoformat()
            self.memory_cache["meta"]["patch_count"] += 1
            
            # Save to file
            with open(self.memory_path, 'w') as f:
                json.dump(self.memory_cache, f, indent=2)
            
            logger.info(f"Memory saved successfully. Patch count: {self.memory_cache['meta']['patch_count']}")
        except Exception as e:
            logger.error(f"Error saving memory: {str(e)}")
    
    def patch_memory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Patch simulation memory with new information.
        
        Args:
            data: Dictionary containing data to be patched into memory
            
        Returns:
            Dictionary with patching results
        """
        # Extract key information
        session_id = data.get("session_id", str(int(time.time())))
        query = data.get("query", "")
        domain = data.get("domain", "general")
        result = data.get("result", {})
        
        # Patch session information
        session_patch = self._patch_session(session_id, query, domain, result)
        
        # Extract and patch entities and concepts
        entity_patches = self._extract_and_patch_entities(result, domain)
        concept_patches = self._extract_and_patch_concepts(result, domain)
        
        # Extract and patch facts
        fact_patches = self._extract_and_patch_facts(result, domain)
        
        # Save updated memory
        self._save_memory()
        
        # Prepare result
        patch_result = {
            "algorithm": "KA-16",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "patches_applied": {
                "session": session_patch,
                "entities": entity_patches,
                "concepts": concept_patches,
                "facts": fact_patches
            },
            "memory_status": {
                "total_sessions": len(self.memory_cache["sessions"]),
                "total_entities": len(self.memory_cache["entities"]),
                "total_concepts": len(self.memory_cache["concepts"]),
                "total_facts": len(self.memory_cache["facts"]),
                "patch_count": self.memory_cache["meta"]["patch_count"]
            },
            "success": True
        }
        
        return patch_result
    
    def _patch_session(self, session_id: str, query: str, domain: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Patch session information into memory.
        
        Args:
            session_id: The session identifier
            query: The query text
            domain: The domain context
            result: The simulation result
            
        Returns:
            Dictionary with session patching details
        """
        # Create new session entry if it doesn't exist
        if session_id not in self.memory_cache["sessions"]:
            self.memory_cache["sessions"][session_id] = {
                "queries": [],
                "domain": domain,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
        
        # Update existing session
        session = self.memory_cache["sessions"][session_id]
        session["last_updated"] = datetime.now().isoformat()
        
        # Add query to session history
        query_entry = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "result_summary": self._create_result_summary(result)
        }
        session["queries"].append(query_entry)
        
        # Update domain if provided
        if domain:
            session["domain"] = domain
        
        return {
            "session_id": session_id,
            "query_count": len(session["queries"]),
            "action": "updated"
        }
    
    def _create_result_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a condensed summary of simulation result."""
        # Extract key information for summary
        summary = {}
        
        # Extract algorithm if present
        if "algorithm" in result:
            summary["algorithm"] = result["algorithm"]
        
        # Extract confidence if present
        if "confidence" in result:
            summary["confidence"] = result["confidence"]
        
        # Extract domain if present
        if "domain" in result:
            summary["domain"] = result["domain"]
        
        # Extract pillar levels if present
        if "pillar_levels" in result:
            summary["pillar_levels"] = result["pillar_levels"]
        
        # Extract coordinates if present
        if "coordinates" in result:
            if isinstance(result["coordinates"], list) and len(result["coordinates"]) > 3:
                summary["coordinates"] = result["coordinates"][:3] + ["..."]
            else:
                summary["coordinates"] = result["coordinates"]
        
        # Extract active personas if present
        if "active_personas" in result:
            summary["active_personas"] = result["active_personas"]
        
        return summary
    
    def _extract_and_patch_entities(self, result: Dict[str, Any], domain: str) -> List[Dict[str, Any]]:
        """
        Extract and patch entities from result.
        
        Args:
            result: The simulation result
            domain: The domain context
            
        Returns:
            List of entity patch details
        """
        entity_patches = []
        
        # Look for entity information in result
        entities = []
        
        # Check common fields where entities might be mentioned
        if "entities" in result:
            entities.extend(result["entities"])
        
        if "coordinates" in result and isinstance(result["coordinates"], list):
            # Treat coordinates as entities
            for coord in result["coordinates"]:
                if isinstance(coord, str) and len(coord) > 0:
                    entities.append({
                        "name": coord,
                        "type": "coordinate",
                        "domain": domain
                    })
        
        # Check for persona results
        if "persona_results" in result:
            for persona_type, persona_data in result["persona_results"].items():
                if isinstance(persona_data, dict):
                    entities.append({
                        "name": persona_data.get("name", persona_type),
                        "type": "persona",
                        "domain": domain,
                        "confidence": persona_data.get("confidence", 0.5)
                    })
        
        # Check for regulations in regulatory references
        if "far_references" in result and isinstance(result["far_references"], list):
            for ref in result["far_references"]:
                if isinstance(ref, dict) and "ref" in ref:
                    entities.append({
                        "name": ref["ref"],
                        "type": "regulation",
                        "domain": "legal",
                        "title": ref.get("title", "")
                    })
        
        if "dfars_references" in result and isinstance(result["dfars_references"], list):
            for ref in result["dfars_references"]:
                if isinstance(ref, dict) and "ref" in ref:
                    entities.append({
                        "name": ref["ref"],
                        "type": "regulation",
                        "domain": "defense",
                        "title": ref.get("title", "")
                    })
        
        # Process and patch each entity
        for entity in entities:
            if isinstance(entity, dict) and "name" in entity:
                entity_name = entity["name"]
                
                # Skip if entity name is not a string or too short
                if not isinstance(entity_name, str) or len(entity_name) < 2:
                    continue
                
                # Create or update entity
                if entity_name not in self.memory_cache["entities"]:
                    # New entity
                    self.memory_cache["entities"][entity_name] = {
                        "type": entity.get("type", "generic"),
                        "domain": entity.get("domain", domain),
                        "mentions": 1,
                        "last_seen": datetime.now().isoformat(),
                        "attributes": {}
                    }
                    action = "created"
                else:
                    # Update existing entity
                    existing = self.memory_cache["entities"][entity_name]
                    existing["mentions"] += 1
                    existing["last_seen"] = datetime.now().isoformat()
                    action = "updated"
                
                # Update attributes
                for key, value in entity.items():
                    if key not in ["name", "type", "domain", "mentions", "last_seen"]:
                        self.memory_cache["entities"][entity_name]["attributes"][key] = value
                
                entity_patches.append({
                    "name": entity_name,
                    "type": self.memory_cache["entities"][entity_name]["type"],
                    "action": action,
                    "mentions": self.memory_cache["entities"][entity_name]["mentions"]
                })
        
        return entity_patches
    
    def _extract_and_patch_concepts(self, result: Dict[str, Any], domain: str) -> List[Dict[str, Any]]:
        """
        Extract and patch concepts from result.
        
        Args:
            result: The simulation result
            domain: The domain context
            
        Returns:
            List of concept patch details
        """
        concept_patches = []
        
        # Look for concept information in result
        concepts = []
        
        # Check common fields where concepts might be mentioned
        if "concepts" in result:
            concepts.extend(result["concepts"])
        
        if "original_concepts" in result:
            concepts.extend(result["original_concepts"])
        
        # Check for related sectors as concepts
        if "related_sectors" in result and isinstance(result["related_sectors"], list):
            for sector in result["related_sectors"]:
                if isinstance(sector, str) and len(sector) > 0:
                    concepts.append({
                        "name": sector,
                        "type": "sector",
                        "domain": domain
                    })
        
        # Check for pillar levels as concepts
        if "pillar_levels" in result and isinstance(result["pillar_levels"], list):
            for pl in result["pillar_levels"]:
                if isinstance(pl, str) and len(pl) > 0:
                    concepts.append({
                        "name": pl,
                        "type": "pillar_level",
                        "domain": domain
                    })
        
        # Process and patch each concept
        for concept in concepts:
            if isinstance(concept, dict) and "name" in concept:
                concept_name = concept["name"]
                
                # Skip if concept name is not a string or too short
                if not isinstance(concept_name, str) or len(concept_name) < 2:
                    continue
                
                # Create or update concept
                if concept_name not in self.memory_cache["concepts"]:
                    # New concept
                    self.memory_cache["concepts"][concept_name] = {
                        "type": concept.get("type", "generic"),
                        "domain": concept.get("domain", domain),
                        "mentions": 1,
                        "last_seen": datetime.now().isoformat(),
                        "related_concepts": [],
                        "attributes": {}
                    }
                    action = "created"
                else:
                    # Update existing concept
                    existing = self.memory_cache["concepts"][concept_name]
                    existing["mentions"] += 1
                    existing["last_seen"] = datetime.now().isoformat()
                    action = "updated"
                
                # Update attributes
                for key, value in concept.items():
                    if key not in ["name", "type", "domain", "mentions", "last_seen", "related_concepts"]:
                        self.memory_cache["concepts"][concept_name]["attributes"][key] = value
                
                # Update related concepts
                if "related_concepts" in concept and isinstance(concept["related_concepts"], list):
                    for related in concept["related_concepts"]:
                        if related not in self.memory_cache["concepts"][concept_name]["related_concepts"]:
                            self.memory_cache["concepts"][concept_name]["related_concepts"].append(related)
                
                concept_patches.append({
                    "name": concept_name,
                    "type": self.memory_cache["concepts"][concept_name]["type"],
                    "action": action,
                    "mentions": self.memory_cache["concepts"][concept_name]["mentions"]
                })
        
        return concept_patches
    
    def _extract_and_patch_facts(self, result: Dict[str, Any], domain: str) -> List[Dict[str, Any]]:
        """
        Extract and patch facts from result.
        
        Args:
            result: The simulation result
            domain: The domain context
            
        Returns:
            List of fact patch details
        """
        fact_patches = []
        
        # Look for fact information in result
        facts = []
        
        # Extract facts from integrated response if present
        if "integrated_response" in result and isinstance(result["integrated_response"], str):
            # Simple fact extraction: sentences ending with period that contain certain keywords
            response = result["integrated_response"]
            sentences = response.split(". ")
            
            fact_keywords = ["is", "are", "was", "were", "has", "have", "require", "must", "should"]
            
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in fact_keywords):
                    # Found potential fact
                    facts.append({
                        "statement": sentence.strip() + ".",
                        "type": "extracted",
                        "domain": domain,
                        "confidence": result.get("confidence", 0.5)
                    })
        
        # Check for implications in decision tree as facts
        if "decision_tree" in result:
            for root, options in result["decision_tree"].items():
                if isinstance(options, list):
                    for option in options:
                        if isinstance(option, dict) and "implications" in option:
                            for implication in option["implications"]:
                                if isinstance(implication, dict) and "effect" in implication:
                                    facts.append({
                                        "statement": implication["effect"],
                                        "type": "implication",
                                        "domain": domain,
                                        "impact": implication.get("impact", "neutral"),
                                        "timeframe": implication.get("timeframe", "unknown")
                                    })
        
        # Process and patch each fact
        for fact in facts:
            if isinstance(fact, dict) and "statement" in fact:
                statement = fact["statement"]
                
                # Skip if statement is not a string or too short
                if not isinstance(statement, str) or len(statement) < 5:
                    continue
                
                # Generate a fact ID if not present
                fact_id = fact.get("id", f"{domain}_{hash(statement) % 10000}")
                
                # Create or update fact
                if fact_id not in self.memory_cache["facts"]:
                    # New fact
                    self.memory_cache["facts"][fact_id] = {
                        "statement": statement,
                        "type": fact.get("type", "generic"),
                        "domain": fact.get("domain", domain),
                        "confidence": fact.get("confidence", 0.5),
                        "first_seen": datetime.now().isoformat(),
                        "last_seen": datetime.now().isoformat(),
                        "mentions": 1,
                        "attributes": {}
                    }
                    action = "created"
                else:
                    # Update existing fact
                    existing = self.memory_cache["facts"][fact_id]
                    existing["mentions"] += 1
                    existing["last_seen"] = datetime.now().isoformat()
                    
                    # Update confidence with decay factor
                    old_conf = existing["confidence"]
                    new_conf = fact.get("confidence", 0.5)
                    existing["confidence"] = (old_conf * 0.7) + (new_conf * 0.3)
                    
                    action = "updated"
                
                # Update attributes
                for key, value in fact.items():
                    if key not in ["statement", "type", "domain", "confidence", "first_seen", "last_seen", "mentions", "id"]:
                        self.memory_cache["facts"][fact_id]["attributes"][key] = value
                
                fact_patches.append({
                    "id": fact_id,
                    "statement_preview": statement[:50] + "..." if len(statement) > 50 else statement,
                    "action": action,
                    "confidence": self.memory_cache["facts"][fact_id]["confidence"],
                    "mentions": self.memory_cache["facts"][fact_id]["mentions"]
                })
        
        return fact_patches
    
    def retrieve_context(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve relevant context based on query and session.
        
        Args:
            query: The query text
            session_id: Optional session identifier
            
        Returns:
            Dictionary with relevant context information
        """
        # Initialize context result
        context = {
            "session_history": [],
            "relevant_entities": [],
            "relevant_concepts": [],
            "relevant_facts": []
        }
        
        # Add session history if session_id provided
        if session_id and session_id in self.memory_cache["sessions"]:
            session = self.memory_cache["sessions"][session_id]
            context["session_history"] = session["queries"][-5:]  # Last 5 queries
            context["domain"] = session["domain"]
        
        # Find relevant entities, concepts, and facts
        query_lower = query.lower()
        
        # Look for entity mentions in query
        for entity_name, entity_data in self.memory_cache["entities"].items():
            if entity_name.lower() in query_lower:
                context["relevant_entities"].append({
                    "name": entity_name,
                    "type": entity_data["type"],
                    "domain": entity_data["domain"],
                    "mentions": entity_data["mentions"],
                    "attributes": entity_data["attributes"]
                })
        
        # Look for concept mentions in query
        for concept_name, concept_data in self.memory_cache["concepts"].items():
            if concept_name.lower() in query_lower:
                context["relevant_concepts"].append({
                    "name": concept_name,
                    "type": concept_data["type"],
                    "domain": concept_data["domain"],
                    "mentions": concept_data["mentions"],
                    "related_concepts": concept_data["related_concepts"],
                    "attributes": concept_data["attributes"]
                })
        
        # Find facts that might be relevant (simple keyword matching)
        query_words = query_lower.split()
        significant_words = [w for w in query_words if len(w) > 3]
        
        for fact_id, fact_data in self.memory_cache["facts"].items():
            statement = fact_data["statement"].lower()
            match_count = sum(1 for word in significant_words if word in statement)
            
            if match_count > 0:
                relevance = min(1.0, match_count / len(significant_words))
                
                if relevance >= 0.2:  # Only include somewhat relevant facts
                    context["relevant_facts"].append({
                        "id": fact_id,
                        "statement": fact_data["statement"],
                        "type": fact_data["type"],
                        "domain": fact_data["domain"],
                        "confidence": fact_data["confidence"],
                        "relevance": relevance
                    })
        
        # Sort facts by relevance
        context["relevant_facts"].sort(key=lambda x: x["relevance"], reverse=True)
        
        # Limit to top 5 most relevant facts
        context["relevant_facts"] = context["relevant_facts"][:5]
        
        return {
            "algorithm": "KA-16",
            "query": query,
            "session_id": session_id,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Simulation Memory Patch (KA-16) on the provided data.
    
    Args:
        data: A dictionary containing the result to be patched
        
    Returns:
        Dictionary with memory patching results
    """
    action = data.get("action", "patch")
    
    # Create memory patcher
    memory_path = data.get("memory_path")
    memory_patcher = SimulationMemoryPatch(memory_path)
    
    if action == "retrieve":
        # Retrieve context based on query
        query = data.get("query", "")
        session_id = data.get("session_id")
        
        if not query:
            return {
                "algorithm": "KA-16",
                "error": "No query provided for context retrieval",
                "success": False
            }
        
        return memory_patcher.retrieve_context(query, session_id)
    else:
        # Patch memory with provided data
        if "result" not in data:
            return {
                "algorithm": "KA-16",
                "error": "No result data provided for patching",
                "success": False
            }
        
        return memory_patcher.patch_memory(data)
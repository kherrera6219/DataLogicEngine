
"""
Universal Knowledge Graph (UKG) System - Axis 11: Context Experts

This module implements Axis 11 of the UKG, which represents Context Expert personas.
These experts understand specific contextual applications of knowledge and methodologies.
"""

import logging
import yaml
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class Axis11ContextExperts:
    """
    Axis 11 - Context Experts
    
    Represents the personas specialized in specific contextual applications
    of knowledge, with 7-part expertise model:
    
    A. Role
    B. Formal Education
    C. Industry and Corporate Certifications
    D. Job Training
    E. Skills
    F. Related Tasks
    G. Related Roles
    
    Each expert type has a hierarchy: mega, large, medium, small, granular
    """
    
    def __init__(self, data_path='data/ukg/contextual_experts.yaml'):
        """Initialize Axis 11 with context expert data."""
        self.axis_number = 11
        self.axis_name = "Context Experts"
        self.data_path = data_path
        self.experts_data = {}
        self.load_data()
        logging.info(f"[{datetime.now()}] Axis 11 (Context Experts) initialized")
    
    def load_data(self):
        """Load context experts data from YAML file."""
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r') as f:
                    self.experts_data = yaml.safe_load(f)
                logging.info(f"[{datetime.now()}] Loaded Context Experts data from {self.data_path}")
            else:
                logging.warning(f"[{datetime.now()}] Context Experts data file not found at {self.data_path}")
                self.experts_data = {"ContextExperts": []}
        except Exception as e:
            logging.error(f"[{datetime.now()}] Error loading Context Experts data: {str(e)}")
            self.experts_data = {"ContextExperts": []}
    
    def get_all_experts(self) -> List[Dict[str, Any]]:
        """Return all context experts."""
        return self.experts_data.get("ContextExperts", [])
    
    def get_expert_by_id(self, expert_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific context expert by ID."""
        experts = self.experts_data.get("ContextExperts", [])
        for expert in experts:
            if expert.get("id") == expert_id:
                return expert
            # Check in subtypes
            for level in ["mega", "large", "medium", "small", "granular"]:
                subtypes = expert.get(f"{level}_subtypes", [])
                for subtype in subtypes:
                    if subtype.get("id") == expert_id:
                        return subtype
        return None
    
    def get_experts_by_sector(self, sector_id: str) -> List[Dict[str, Any]]:
        """Get all context experts related to a specific sector."""
        experts = self.experts_data.get("ContextExperts", [])
        result = []
        
        for expert in experts:
            if expert.get("related_sectors") and sector_id in expert.get("related_sectors"):
                result.append(expert)
        
        return result
    
    def get_expertise_model(self, expert_id: str) -> Dict[str, Any]:
        """
        Get the 7-part expertise model for a specific context expert.
        
        Returns:
        {
            'role': str,
            'formal_education': List[str],
            'certifications': List[str],
            'job_training': List[str],
            'skills': List[str],
            'related_tasks': List[str],
            'related_roles': List[str]
        }
        """
        expert = self.get_expert_by_id(expert_id)
        if not expert:
            return {
                'role': '',
                'formal_education': [],
                'certifications': [],
                'job_training': [],
                'skills': [],
                'related_tasks': [],
                'related_roles': []
            }
        
        return {
            'role': expert.get('label', ''),
            'formal_education': expert.get('formal_education', []),
            'certifications': expert.get('certifications', []),
            'job_training': expert.get('job_training', []),
            'skills': expert.get('skills', []),
            'related_tasks': expert.get('related_tasks', []),
            'related_roles': expert.get('related_roles', [])
        }
    
    def process_query(self, query: str) -> str:
        """Process a query using Axis 11 context."""
        # In a more sophisticated implementation, this would analyze the query and return
        # context-specific insights based on the most relevant context expert
        
        # For demonstration, return a simple response
        return f"Axis 11 (Context Experts) analyzing query: {query}"
    
    def get_branch_structure(self, expert_id: str = None) -> Dict[str, Any]:
        """
        Get the branch structure for context experts.
        
        If expert_id is provided, returns the branch structure for that specific expert.
        Otherwise, returns the full hierarchy.
        """
        if expert_id:
            expert = self.get_expert_by_id(expert_id)
            if not expert:
                return {}
            return self._format_branch(expert)
        
        # Return full branch structure
        result = {
            "type": "hierarchy",
            "name": "Context Experts",
            "children": []
        }
        
        experts = self.experts_data.get("ContextExperts", [])
        for expert in experts:
            result["children"].append(self._format_branch(expert))
        
        return result
    
    def _format_branch(self, expert: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to format an expert as a branch in the hierarchy."""
        branch = {
            "name": expert.get("label", ""),
            "id": expert.get("id", ""),
            "description": expert.get("description", ""),
            "children": []
        }
        
        # Add mega subtypes
        for subtype in expert.get("mega_subtypes", []):
            branch["children"].append({
                "name": subtype.get("label", ""),
                "id": subtype.get("id", ""),
                "description": subtype.get("description", ""),
                "children": self._get_large_subtypes(subtype)
            })
        
        return branch
    
    def _get_large_subtypes(self, parent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get large subtypes for a parent node."""
        result = []
        for subtype in parent.get("large_subtypes", []):
            result.append({
                "name": subtype.get("label", ""),
                "id": subtype.get("id", ""),
                "description": subtype.get("description", ""),
                "children": self._get_medium_subtypes(subtype)
            })
        return result
    
    def _get_medium_subtypes(self, parent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get medium subtypes for a parent node."""
        result = []
        for subtype in parent.get("medium_subtypes", []):
            result.append({
                "name": subtype.get("label", ""),
                "id": subtype.get("id", ""),
                "description": subtype.get("description", ""),
                "children": self._get_small_subtypes(subtype)
            })
        return result
    
    def _get_small_subtypes(self, parent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get small subtypes for a parent node."""
        result = []
        for subtype in parent.get("small_subtypes", []):
            result.append({
                "name": subtype.get("label", ""),
                "id": subtype.get("id", ""),
                "description": subtype.get("description", ""),
                "children": self._get_granular_subtypes(subtype)
            })
        return result
    
    def _get_granular_subtypes(self, parent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get granular subtypes for a parent node."""
        result = []
        for subtype in parent.get("granular_subtypes", []):
            result.append({
                "name": subtype.get("label", ""),
                "id": subtype.get("id", ""),
                "description": subtype.get("description", "")
            })
        return result

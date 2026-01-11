import json
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

class WorkflowLoader:
    """
    Workflow Loader
    
    Ingests the enterprise-grade simulation workflow (v2.5) and provides
    a structured step-by-step iterator for the SimulationOrchestrator.
    """
    
    def __init__(self, workflow_path: Optional[str] = None):
        """
        Initialize the Workflow Loader.
        
        Args:
            workflow_path: Path to the simulation workflow JSON file.
        """
        self.workflow_path = workflow_path or os.path.join(
            os.path.dirname(__file__), "workflows", "simulation_v2_5.json"
        )
        self.workflow_data = {}
        self.steps = []
        self._load_workflow()
        
    def _load_workflow(self):
        """Load and parse the workflow JSON file."""
        try:
            if not os.path.exists(self.workflow_path):
                logging.error(f"Workflow file not found at {self.workflow_path}")
                return
                
            with open(self.workflow_path, 'r') as f:
                self.workflow_data = json.load(f)
                
            # Extract steps from the 10-step structure
            # The JSON structure typically has steps named "step1", "step2"...
            self.steps = []
            for i in range(1, 11):
                step_key = f"step{i}"
                if step_key in self.workflow_data:
                    self.steps.append({
                        "step_number": i,
                        "data": self.workflow_data[step_key]
                    })
            
            logging.info(f"Loaded {len(self.steps)} steps from simulation workflow.")
        except Exception as e:
            logging.error(f"Error loading workflow: {str(e)}")

    def get_step(self, step_number: int) -> Optional[Dict]:
        """Get data for a specific step."""
        for step in self.steps:
            if step["step_number"] == step_number:
                return step["data"]
        return None

    def get_ka_sources_for_step(self, step_number: int) -> List[str]:
        """Extract ka_sources for a given step."""
        step_data = self.get_step(step_number)
        if not step_data:
            return []
            
        sources = []
        # Check for ka_sources in the root of the step or in sub-axes
        if "ka_sources" in step_data:
            sources.extend(step_data["ka_sources"])
            
        # Recursive check for axes if they exist
        for key, value in step_data.items():
            if isinstance(value, dict) and "ka_sources" in value:
                sources.extend(value["ka_sources"])
                
        return list(set(sources))

    def validate_workflow(self) -> bool:
        """Simple validation to ensure all 10 steps exist and have sources."""
        if len(self.steps) < 10:
            logging.warning(f"Workflow only contains {len(self.steps)} steps (expected 10).")
            return False
            
        for step in self.steps:
            sources = self.get_ka_sources_for_step(step["step_number"])
            if not sources:
                logging.warning(f"Step {step['step_number']} has no ka_sources.")
                
        return True

"""
KA-118: Sensitive Data Discovery Agent

This Knowledge Algorithm scans Knowledge Graph nodes for sensitive information (PII, PHI, Secrets)
and automatically applies security classification tags to the 'axis_17_security' coordinate.

Input: Node ID or Scan Scope (e.g., "all", "tenant:123")
Output: Scan Report & Updated Coordinates
"""

from typing import Dict, Any, List, Set
import re
from .ka_master_controller import KnowledgeAlgorithm

class KA118SensitiveDataDiscovery(KnowledgeAlgorithm):
    """
    Automated Data Classification Agent.
    """
    
    # Simple regex patterns for simulation (in prod, use Presidio/Macie)
    PATTERNS = {
        "PII:EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "PII:PHONE": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "PII:SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "SECRET:KEY": r"(?i)(api_key|secret|token).{0,20}['\"][a-zA-Z0-9]{20,}['\"]"
    }

    def __init__(self):
        super().__init__(config={})
        self.ka_id = "ka_118_sensitive_data_discovery"
        self.version = "1.0.0"
        self.description = "Scans content for PII/Secrets and tags security axes."
        self.tier = 3

    def _run_logic(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the scan.
        """
        if hasattr(params, 'data'):
            params = params.data
            
        content = params.get("content", "")
        node_id = params.get("node_id")
        
        found_tags = self._scan_text(content)
        
        result = {
            "status": "success",
            "detected_tags": list(found_tags),
            "classification_level": self._determine_level(found_tags)
        }
        
        # In a real run, we would update the Node model here
        if node_id and found_tags:
            # simulated update
            result["action"] = f"Updated node {node_id} axis_17_security with {list(found_tags)}"
            
        return result

    def _scan_text(self, text: str) -> Set[str]:
        """Scan text against patterns."""
        tags = set()
        for tag_name, pattern in self.PATTERNS.items():
            if re.search(pattern, text):
                tags.add(tag_name)
        return tags

    def _determine_level(self, tags: Set[str]) -> str:
        """Map tags to overall classification level."""
        if any("SSN" in t for t in tags) or any("SECRET" in t for t in tags):
            return "CRITICAL"
        if any("PII" in t for t in tags):
            return "CONFIDENTIAL"
        return "PUBLIC"

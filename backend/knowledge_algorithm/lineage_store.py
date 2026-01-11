import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

class LineageStore:
    """
    Knowledge Lineage Store
    
    Tracks the derivation of facts and knowledge across multiple KAs 
    and simulation passes. Supports JSON-LD style lineage graphs (KA-043).
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the Lineage Store.
        
        Args:
            storage_path: Directory where lineage data will be persisted.
        """
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "data", "lineage"
        )
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path, exist_ok=True)
            
        self.lineage_cache = {}
        logging.info(f"[{datetime.now()}] LineageStore initialized at {self.storage_path}")

    def record_derivation(self, target_id: str, source_ids: List[str], ka_id: str, context: Dict) -> Dict:
        """
        Record a fact derivation.
        
        Args:
            target_id: The ID of the derived fact/node.
            source_ids: List of source fact/node IDs used in derivation.
            ka_id: The ID of the Knowledge Algorithm that performed the derivation.
            context: Additional metadata (simulation_id, pass_number, timestamp).
            
        Returns:
            The created lineage entry.
        """
        entry = {
            "@context": "https://ukg.enterprise/lineage/v1",
            "type": "Derivation",
            "target": target_id,
            "sources": source_ids,
            "agent": f"ka:{ka_id}",
            "timestamp": context.get("timestamp", datetime.now().isoformat()),
            "simulation_id": context.get("simulation_id"),
            "pass_number": context.get("pass_number"),
            "metadata": context.get("metadata", {})
        }
        
        # Save to cache and persist
        self.lineage_cache[target_id] = entry
        self._save_entry(target_id, entry)
        
        return entry

    def _save_entry(self, target_id: str, entry: Dict):
        """Persist a derivation entry to disk."""
        try:
            filename = f"lineage_{target_id.replace(':', '_')}.json"
            filepath = os.path.join(self.storage_path, filename)
            with open(filepath, 'w') as f:
                json.dump(entry, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to persist lineage for {target_id}: {str(e)}")

    def get_lineage(self, target_id: str) -> Optional[Dict]:
        """Retrieve lineage for a specific ID."""
        if target_id in self.lineage_cache:
            return self.lineage_cache[target_id]
            
        # Try loading from disk
        filename = f"lineage_{target_id.replace(':', '_')}.json"
        filepath = os.path.join(self.storage_path, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                entry = json.load(f)
                self.lineage_cache[target_id] = entry
                return entry
                
        return None

    def trace_origins(self, target_id: str, max_depth: int = 5) -> List[Dict]:
        """Perform a recursive trace to find original sources."""
        trace = []
        current_id = target_id
        
        for _ in range(max_depth):
            lineage = self.get_lineage(current_id)
            if not lineage or not lineage.get("sources"):
                break
            trace.append(lineage)
            # Simplification: follow the first source for linear trace
            current_id = lineage["sources"][0]
            
        return trace

"""
FROST (Fast Recording of Simulated Transactions) Snapshot & Delta Service

This module provides high-efficiency state management for the USKD.
It enables branching, snapshotting, and delta tracking of simulation states,
allowing for recursive reasoning and multi-path exploration.
"""

import logging
import json
import hashlib
import copy
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional, Tuple

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class FROSTService:
    """
    FROST Service
    
    Responsibilities:
    1. Capture immutable snapshots of the system state.
    2. compute deltas between snapshots.
    3. Branch and merge states for parallel reasoning.
    4. Provide transactional integrity for nested simulations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # In-memory store of snapshots: snapshot_id -> state_dict
        self.snapshots: Dict[str, Dict[str, Any]] = {}
        
        # Delta store: target_id -> {base_id, delta}
        self.deltas: Dict[str, Dict[str, Any]] = {}
        
        # Branching info
        self.branches: Dict[str, str] = {} # branch_name -> last_snapshot_id

    def _generate_id(self, state: Dict[str, Any]) -> str:
        """Generate a deterministic snapshot ID based on state content."""
        state_str = json.dumps(state, sort_keys=True, cls=DateTimeEncoder)
        return f"snap_{hashlib.sha256(state_str.encode()).hexdigest()[:16]}"

    def snapshot(self, state: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Capture a snapshot of the current state.
        """
        snapshot_id = self._generate_id(state)
        
        if snapshot_id not in self.snapshots:
            # Deep copy to ensure immutability
            self.snapshots[snapshot_id] = copy.deepcopy(state)
            self.logger.debug(f"Created snapshot: {snapshot_id}")
            
        return snapshot_id

    def get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a snapshot by ID."""
        return self.snapshots.get(snapshot_id)

    def diff(self, base_id: str, target_id: str) -> Dict[str, Any]:
        """
        Compute the delta between two snapshots.
        (Simple implementation using dict comparison)
        """
        if base_id not in self.snapshots or target_id not in self.snapshots:
            raise ValueError("Both snapshots must exist to compute diff")
            
        base = self.snapshots[base_id]
        target = self.snapshots[target_id]
        
        # Simple key-level diff
        delta = {
            "added": {},
            "modified": {},
            "removed": []
        }
        
        for k, v in target.items():
            if k not in base:
                delta["added"][k] = v
            elif base[k] != v:
                delta["modified"][k] = v
                
        for k in base:
            if k not in target:
                delta["removed"].append(k)
                
        return delta

    def apply(self, base_id: str, delta: Dict[str, Any]) -> str:
        """
        Apply a delta to a base snapshot to create a new one.
        """
        if base_id not in self.snapshots:
            raise ValueError(f"Base snapshot {base_id} not found")
            
        new_state = copy.deepcopy(self.snapshots[base_id])
        
        # Apply additions/modifications
        new_state.update(delta.get("added", {}))
        new_state.update(delta.get("modified", {}))
        
        # Apply removals
        for k in delta.get("removed", []):
            new_state.pop(k, None)
            
        return self.snapshot(new_state)

    def branch(self, snapshot_id: str, branch_name: str) -> str:
        """
        Create a new named branch from a snapshot.
        """
        if snapshot_id not in self.snapshots:
            raise ValueError(f"Snapshot {snapshot_id} not found")
            
        self.branches[branch_name] = snapshot_id
        self.logger.info(f"Created branch '{branch_name}' at {snapshot_id}")
        return snapshot_id

    def merge(self, base_id: str, branch_snapshots: List[str], policy: str = "latest wins") -> str:
        """
        Merge multiple branch snapshots back into a base state.
        """
        current_state = copy.deepcopy(self.snapshots[base_id])
        
        for snap_id in branch_snapshots:
            if snap_id not in self.snapshots:
                continue
            
            branch_state = self.snapshots[snap_id]
            # Simple merge logic based on policy
            if policy == "latest wins":
                current_state.update(branch_state)
            # Future policy: "consensus" or "refinement" would go here
            
        return self.snapshot(current_state)

    def check_health(self) -> Dict[str, Any]:
        """System health check."""
        return {
            "healthy": True,
            "snapshot_count": len(self.snapshots),
            "branch_count": len(self.branches)
        }

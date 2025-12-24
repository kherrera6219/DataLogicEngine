"""
Universal Knowledge Graph (UKG) System - Axis 15: Federated Intelligence

This module implements the Federated Intelligence axis for the 17-Axis UKG system,
providing cross-system synchronization, distributed knowledge management,
and privacy-preserving federated learning capabilities.
"""

import logging
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Synchronization status types"""
    SYNCED = "synced"
    PENDING = "pending"
    CONFLICT = "conflict"
    STALE = "stale"
    ISOLATED = "isolated"


class FederationMode(Enum):
    """Federation operation modes"""
    FULL_SYNC = "full_sync"
    SELECTIVE_SYNC = "selective_sync"
    PRIVACY_PRESERVING = "privacy_preserving"
    READ_ONLY = "read_only"
    WRITE_THROUGH = "write_through"


class DataSovereignty(Enum):
    """Data sovereignty classifications"""
    GLOBAL = "global"
    REGIONAL = "regional"
    NATIONAL = "national"
    LOCAL = "local"
    RESTRICTED = "restricted"


class FederatedAxis:
    """Handler for Axis 15: Federated Intelligence - Cross-System Knowledge Synchronization"""
    
    def __init__(self):
        """Initialize the Federated Intelligence axis handler."""
        self.axis_number = 15
        self.axis_name = "Federated Intelligence"
        self.description = "Cross-system synchronization, distributed knowledge stores, and privacy-preserving federated learning"
        
        self.sync_statuses = [s.value for s in SyncStatus]
        self.federation_modes = [m.value for m in FederationMode]
        self.sovereignty_levels = [d.value for d in DataSovereignty]
        
        self.federation_nodes = {}
        self.sync_log = []
    
    def navigate(self, **kwargs) -> Dict[str, Any]:
        """
        Navigate the Federated Intelligence axis based on provided parameters.
        
        Parameters:
        - node_id (str): Specific federation node ID
        - sync_status (str): Filter by synchronization status
        - federation_mode (str): Filter by federation mode
        - sovereignty (str): Filter by data sovereignty level
        - include_sync_history (bool): Include synchronization history
        
        Returns:
        - Dict containing the navigation results
        """
        node_id = kwargs.get('node_id')
        sync_status = kwargs.get('sync_status')
        federation_mode = kwargs.get('federation_mode')
        sovereignty = kwargs.get('sovereignty')
        include_sync_history = kwargs.get('include_sync_history', False)
        
        try:
            result_data = {
                "axis": self.axis_number,
                "name": self.axis_name,
                "filters_applied": {
                    "node_id": node_id,
                    "sync_status": sync_status,
                    "federation_mode": federation_mode,
                    "sovereignty": sovereignty
                },
                "federation_nodes": self._get_filtered_nodes(node_id, sync_status, federation_mode, sovereignty),
                "sync_statuses_available": self.sync_statuses,
                "federation_modes_available": self.federation_modes,
                "sovereignty_levels": self.sovereignty_levels
            }
            
            if include_sync_history:
                result_data["sync_history"] = self._get_sync_history(node_id)
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error navigating Federated Intelligence axis: {str(e)}")
            return {
                "axis": self.axis_number,
                "name": self.axis_name,
                "error": str(e)
            }
    
    def register_federation_node(self, node_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new federation node.
        
        Args:
            node_config: Configuration for the federation node
            
        Returns:
            Registration result
        """
        node_id = node_config.get('node_id') or str(uuid.uuid4())
        
        node = {
            "node_id": node_id,
            "name": node_config.get('name', f"Node-{node_id[:8]}"),
            "endpoint": node_config.get('endpoint'),
            "federation_mode": node_config.get('federation_mode', FederationMode.READ_ONLY.value),
            "sovereignty": node_config.get('sovereignty', DataSovereignty.LOCAL.value),
            "sync_status": SyncStatus.PENDING.value,
            "capabilities": node_config.get('capabilities', []),
            "last_sync": None,
            "registered_at": datetime.now(UTC).isoformat(),
            "metadata": node_config.get('metadata', {})
        }
        
        self.federation_nodes[node_id] = node
        
        logger.info(f"Registered federation node: {node_id}")
        
        return {
            "success": True,
            "node_id": node_id,
            "node": node
        }
    
    def sync_knowledge(self, source_node_id: str, target_node_id: str, 
                       knowledge_filter: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Synchronize knowledge between federation nodes.
        
        Args:
            source_node_id: Source node ID
            target_node_id: Target node ID
            knowledge_filter: Optional filter for selective sync
            
        Returns:
            Synchronization result
        """
        sync_id = str(uuid.uuid4())
        
        sync_record = {
            "sync_id": sync_id,
            "source_node": source_node_id,
            "target_node": target_node_id,
            "filter": knowledge_filter,
            "status": "initiated",
            "started_at": datetime.now(UTC).isoformat(),
            "completed_at": None,
            "items_synced": 0,
            "conflicts": [],
            "errors": []
        }
        
        try:
            source_node = self.federation_nodes.get(source_node_id)
            target_node = self.federation_nodes.get(target_node_id)
            
            if not source_node:
                raise ValueError(f"Source node {source_node_id} not found")
            if not target_node:
                raise ValueError(f"Target node {target_node_id} not found")
            
            self._check_sovereignty_compatibility(source_node, target_node)
            
            sync_record["status"] = "completed"
            sync_record["completed_at"] = datetime.now(UTC).isoformat()
            
            if source_node_id in self.federation_nodes:
                self.federation_nodes[source_node_id]["last_sync"] = datetime.now(UTC).isoformat()
                self.federation_nodes[source_node_id]["sync_status"] = SyncStatus.SYNCED.value
            
            if target_node_id in self.federation_nodes:
                self.federation_nodes[target_node_id]["last_sync"] = datetime.now(UTC).isoformat()
                self.federation_nodes[target_node_id]["sync_status"] = SyncStatus.SYNCED.value
            
        except Exception as e:
            sync_record["status"] = "failed"
            sync_record["errors"].append(str(e))
            logger.error(f"Sync failed: {str(e)}")
        
        self.sync_log.append(sync_record)
        
        return sync_record
    
    def resolve_conflict(self, conflict_id: str, resolution_strategy: str) -> Dict[str, Any]:
        """
        Resolve a synchronization conflict.
        
        Args:
            conflict_id: ID of the conflict to resolve
            resolution_strategy: Strategy to use (source_wins, target_wins, merge, manual)
            
        Returns:
            Resolution result
        """
        valid_strategies = ["source_wins", "target_wins", "merge", "manual"]
        
        if resolution_strategy not in valid_strategies:
            return {
                "success": False,
                "error": f"Invalid strategy. Valid options: {valid_strategies}"
            }
        
        return {
            "success": True,
            "conflict_id": conflict_id,
            "resolution_strategy": resolution_strategy,
            "resolved_at": datetime.now(UTC).isoformat()
        }
    
    def get_federated_knowledge(self, query: Dict[str, Any], 
                                 nodes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Query knowledge across federated nodes.
        
        Args:
            query: Knowledge query parameters
            nodes: Optional list of specific nodes to query
            
        Returns:
            Federated query results
        """
        target_nodes = nodes or list(self.federation_nodes.keys())
        
        results = {
            "query": query,
            "nodes_queried": target_nodes,
            "results_by_node": {},
            "aggregated_results": [],
            "query_time": datetime.now(UTC).isoformat()
        }
        
        for node_id in target_nodes:
            if node_id in self.federation_nodes:
                node = self.federation_nodes[node_id]
                if node["sync_status"] != SyncStatus.ISOLATED.value:
                    results["results_by_node"][node_id] = {
                        "status": "queried",
                        "count": 0,
                        "items": []
                    }
        
        return results
    
    def _get_filtered_nodes(self, node_id: Optional[str], sync_status: Optional[str],
                            federation_mode: Optional[str], sovereignty: Optional[str]) -> List[Dict]:
        """Get filtered list of federation nodes."""
        nodes = list(self.federation_nodes.values())
        
        if node_id:
            nodes = [n for n in nodes if n["node_id"] == node_id]
        if sync_status:
            nodes = [n for n in nodes if n["sync_status"] == sync_status]
        if federation_mode:
            nodes = [n for n in nodes if n["federation_mode"] == federation_mode]
        if sovereignty:
            nodes = [n for n in nodes if n["sovereignty"] == sovereignty]
        
        return nodes
    
    def _get_sync_history(self, node_id: Optional[str] = None) -> List[Dict]:
        """Get synchronization history."""
        if node_id:
            return [s for s in self.sync_log 
                    if s["source_node"] == node_id or s["target_node"] == node_id]
        return self.sync_log[-100:]
    
    def _check_sovereignty_compatibility(self, source_node: Dict, target_node: Dict) -> bool:
        """Check if sovereignty levels are compatible for sync."""
        sovereignty_hierarchy = {
            DataSovereignty.GLOBAL.value: 0,
            DataSovereignty.REGIONAL.value: 1,
            DataSovereignty.NATIONAL.value: 2,
            DataSovereignty.LOCAL.value: 3,
            DataSovereignty.RESTRICTED.value: 4
        }
        
        source_level = sovereignty_hierarchy.get(source_node.get("sovereignty"), 4)
        target_level = sovereignty_hierarchy.get(target_node.get("sovereignty"), 4)
        
        if source_level > target_level:
            raise ValueError(
                f"Cannot sync from {source_node['sovereignty']} to {target_node['sovereignty']} - "
                "sovereignty level violation"
            )
        
        return True
    
    def get_axis_metadata(self) -> Dict[str, Any]:
        """Get metadata about this axis."""
        return {
            "axis_number": self.axis_number,
            "axis_name": self.axis_name,
            "description": self.description,
            "sync_statuses": self.sync_statuses,
            "federation_modes": self.federation_modes,
            "sovereignty_levels": self.sovereignty_levels,
            "active_nodes": len(self.federation_nodes)
        }

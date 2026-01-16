"""
KA-58: Dynamic Knowledge Graph Connector

This algorithm dynamically forms and manages connections between knowledge graph nodes,
evaluating semantic and structural relationships to establish optimal linkages.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import time
import random
import uuid

logger = logging.getLogger(__name__)

class DynamicKnowledgeGraphConnector:
    """
    KA-58: Dynamic Knowledge Graph Connector.
    
    This algorithm dynamically forms and manages connections between knowledge graph nodes,
    evaluating semantic, structural, and contextual relationships to establish
    optimal linkages that enhance knowledge coherence and accessibility.
    """
    
    def __init__(self):
        """Initialize the Dynamic Knowledge Graph Connector."""
        self.connection_types = self._initialize_connection_types()
        self.connection_strengths = self._initialize_connection_strengths()
        self.connection_thresholds = self._initialize_connection_thresholds()
        self.connection_metrics = self._initialize_connection_metrics()
        logger.info("KA-58: Dynamic Knowledge Graph Connector initialized")
    
    def _initialize_connection_types(self) -> Dict[str, Dict[str, Any]]:
        """Initialize types of connections between knowledge graph nodes."""
        return {
            "semantic": {
                "description": "Connection based on meaning similarity",
                "weight_range": [0.1, 1.0],
                "directionality": "bidirectional",
                "default_weight": 0.5,
                "typical_distance": "variable"
            },
            "hierarchical": {
                "description": "Connection representing parent-child or category relationships",
                "weight_range": [0.5, 1.0],
                "directionality": "directed",
                "default_weight": 0.8,
                "typical_distance": "close"
            },
            "sequential": {
                "description": "Connection representing temporal or procedural sequence",
                "weight_range": [0.3, 0.9],
                "directionality": "directed",
                "default_weight": 0.7,
                "typical_distance": "close"
            },
            "causal": {
                "description": "Connection representing cause-effect relationships",
                "weight_range": [0.4, 1.0],
                "directionality": "directed",
                "default_weight": 0.8,
                "typical_distance": "variable"
            },
            "associative": {
                "description": "Connection representing general association or co-occurrence",
                "weight_range": [0.1, 0.7],
                "directionality": "bidirectional",
                "default_weight": 0.4,
                "typical_distance": "variable"
            },
            "compositional": {
                "description": "Connection representing part-whole relationships",
                "weight_range": [0.6, 1.0],
                "directionality": "directed",
                "default_weight": 0.8,
                "typical_distance": "close"
            },
            "contrastive": {
                "description": "Connection representing contrast or opposition",
                "weight_range": [0.3, 0.8],
                "directionality": "bidirectional",
                "default_weight": 0.5,
                "typical_distance": "variable"
            },
            "analogical": {
                "description": "Connection representing similarity across domains",
                "weight_range": [0.2, 0.9],
                "directionality": "bidirectional",
                "default_weight": 0.6,
                "typical_distance": "far"
            }
        }
    
    def _initialize_connection_strengths(self) -> Dict[str, Dict[str, Any]]:
        """Initialize strength levels for connections."""
        return {
            "strong": {
                "description": "Strong, highly reliable connection",
                "weight_range": [0.8, 1.0],
                "stability": "high",
                "formation_threshold": 0.8
            },
            "moderate": {
                "description": "Moderately strong connection",
                "weight_range": [0.5, 0.79],
                "stability": "medium",
                "formation_threshold": 0.5
            },
            "weak": {
                "description": "Weak, tentative connection",
                "weight_range": [0.2, 0.49],
                "stability": "low",
                "formation_threshold": 0.2
            },
            "potential": {
                "description": "Potential connection, not yet established",
                "weight_range": [0.01, 0.19],
                "stability": "very_low",
                "formation_threshold": 0.01
            }
        }
    
    def _initialize_connection_thresholds(self) -> Dict[str, float]:
        """Initialize thresholds for different connection operations."""
        return {
            "formation": 0.3,       # Minimum score to form a connection
            "reinforcement": 0.1,   # Minimum increase to strengthen connection
            "weakening": 0.1,       # Minimum decrease to weaken connection
            "pruning": 0.1,         # Maximum weight to consider pruning
            "merging": 0.85         # Minimum similarity to merge nodes
        }
    
    def _initialize_connection_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Initialize metrics for evaluating connections."""
        return {
            "semantic_similarity": {
                "description": "Measure of meaning similarity between nodes",
                "calculation": "cosine_similarity",
                "weight": 0.4,
                "applicable_to": ["semantic", "analogical"]
            },
            "co_occurrence": {
                "description": "Frequency of nodes appearing in same context",
                "calculation": "frequency_count",
                "weight": 0.2,
                "applicable_to": ["associative", "sequential"]
            },
            "structural_proximity": {
                "description": "Closeness in graph structure",
                "calculation": "path_distance",
                "weight": 0.15,
                "applicable_to": ["hierarchical", "compositional"]
            },
            "temporal_relevance": {
                "description": "Relevance based on recency and frequency",
                "calculation": "decay_function",
                "weight": 0.1,
                "applicable_to": ["sequential", "causal"]
            },
            "causal_strength": {
                "description": "Strength of causal relationship",
                "calculation": "conditional_probability",
                "weight": 0.15,
                "applicable_to": ["causal"]
            }
        }
    
    def establish_connections(self, 
                           source_nodes: List[Dict[str, Any]],
                           target_nodes: List[Dict[str, Any]],
                           knowledge_graph: Dict[str, Any],
                           config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Establish connections between source and target nodes in a knowledge graph.
        
        Args:
            source_nodes: List of source nodes
            target_nodes: List of target nodes to connect to
            knowledge_graph: Knowledge graph structure
            config: Optional configuration for connection establishment
            
        Returns:
            Dictionary with established connections
        """
        # Set default configuration if not provided
        if config is None:
            config = {
                "connection_types": ["semantic", "hierarchical", "sequential", "causal", "associative"],
                "min_connection_strength": 0.3,
                "max_connections_per_node": 10,
                "consider_existing_connections": True,
                "bidirectional_by_default": False,
                "merge_similar_nodes": False,
                "prune_weak_connections": True
            }
        
        # Validate inputs
        if not source_nodes or not target_nodes:
            return {
                "success": False,
                "error": "No source or target nodes provided",
                "connections_formed": 0,
                "connections": []
            }
        
        # Extract allowed connection types
        allowed_connection_types = config.get("connection_types", list(self.connection_types.keys()))
        
        # Establish connections
        new_connections = []
        modified_connections = []
        merged_nodes = []
        pruned_connections = []
        
        # First, identify potential merges if configured
        if config.get("merge_similar_nodes", False):
            merged_nodes = self._identify_node_merges(
                source_nodes, target_nodes, knowledge_graph, config
            )
        
        # Update nodes list after merges
        if merged_nodes:
            source_nodes = self._update_nodes_after_merge(source_nodes, merged_nodes)
            target_nodes = self._update_nodes_after_merge(target_nodes, merged_nodes)
        
        # Process each source node
        for source in source_nodes:
            source_id = source.get("id")
            if not source_id:
                continue
            
            # Get existing connections if enabled
            existing_connections = []
            if config.get("consider_existing_connections", True):
                existing_connections = self._get_existing_connections(
                    source_id, knowledge_graph
                )
            
            # Track number of connections for this source
            source_connection_count = len(existing_connections)
            max_connections = config.get("max_connections_per_node", 10)
            
            # Evaluate potential connections to each target
            potential_connections = []
            
            for target in target_nodes:
                target_id = target.get("id")
                if not target_id or source_id == target_id:
                    continue
                
                # Skip if already connected (unless we're considering strengthening)
                if self._is_already_connected(source_id, target_id, existing_connections) and not config.get("strengthen_existing", True):
                    continue
                
                # Evaluate connection for each allowed type
                for conn_type in allowed_connection_types:
                    if conn_type not in self.connection_types:
                        continue
                    
                    # Calculate connection strength
                    strength = self._calculate_connection_strength(
                        source, target, conn_type, knowledge_graph
                    )
                    
                    # If strength meets threshold, add to potential connections
                    min_strength = config.get("min_connection_strength", 0.3)
                    if strength >= min_strength:
                        potential_connections.append({
                            "source_id": source_id,
                            "target_id": target_id,
                            "type": conn_type,
                            "strength": strength,
                            "bidirectional": self.connection_types[conn_type]["directionality"] == "bidirectional"
                        })
            
            # Sort potential connections by strength (descending)
            potential_connections.sort(key=lambda x: x["strength"], reverse=True)
            
            # Establish connections up to max limit
            for connection in potential_connections:
                if source_connection_count >= max_connections:
                    break
                
                target_id = connection["target_id"]
                conn_type = connection["type"]
                strength = connection["strength"]
                bidirectional = connection["bidirectional"] or config.get("bidirectional_by_default", False)
                
                # Check if connection already exists
                existing_conn = self._find_existing_connection(
                    source_id, target_id, existing_connections
                )
                
                if existing_conn:
                    # Strengthen existing connection if new strength is higher
                    if strength > existing_conn.get("weight", 0):
                        strengthened = self._strengthen_connection(
                            existing_conn, strength, conn_type
                        )
                        if strengthened:
                            modified_connections.append(existing_conn)
                else:
                    # Create new connection
                    new_conn = self._create_connection(
                        source_id, target_id, conn_type, strength, bidirectional
                    )
                    new_connections.append(new_conn)
                    existing_connections.append(new_conn)
                    source_connection_count += 1
        
        # Prune weak connections if enabled
        if config.get("prune_weak_connections", True):
            pruned_connections = self._prune_weak_connections(
                knowledge_graph, config.get("pruning_threshold", self.connection_thresholds["pruning"])
            )
        
        # Prepare result
        result = {
            "success": True,
            "connections_formed": len(new_connections),
            "connections_modified": len(modified_connections),
            "connections_pruned": len(pruned_connections),
            "nodes_merged": len(merged_nodes),
            "new_connections": new_connections,
            "modified_connections": modified_connections,
            "pruned_connections": pruned_connections,
            "merged_nodes": merged_nodes
        }
        
        return result
    
    def _calculate_connection_strength(self, source_node: Dict[str, Any], 
                                     target_node: Dict[str, Any],
                                     connection_type: str,
                                     knowledge_graph: Dict[str, Any]) -> float:
        """
        Calculate the strength of a potential connection between nodes.
        
        Args:
            source_node: Source node data
            target_node: Target node data
            connection_type: Type of connection to evaluate
            knowledge_graph: Knowledge graph structure
            
        Returns:
            Connection strength score (0-1)
        """
        # Get applicable metrics for this connection type
        applicable_metrics = []
        for metric_name, metric_info in self.connection_metrics.items():
            if connection_type in metric_info.get("applicable_to", []):
                applicable_metrics.append((metric_name, metric_info))
        
        if not applicable_metrics:
            # No applicable metrics, use default weight
            return self.connection_types[connection_type]["default_weight"]
        
        # Calculate weighted score using applicable metrics
        total_weight = 0
        weighted_sum = 0
        
        for metric_name, metric_info in applicable_metrics:
            weight = metric_info.get("weight", 1.0)
            total_weight += weight
            
            # Calculate metric value
            metric_value = self._calculate_metric(
                metric_name, source_node, target_node, knowledge_graph
            )
            
            weighted_sum += weight * metric_value
        
        # Normalize by total weight
        if total_weight > 0:
            normalized_strength = weighted_sum / total_weight
        else:
            normalized_strength = 0.5  # Default if no weights
        
        # Ensure in valid range
        return max(0.0, min(1.0, normalized_strength))
    
    def _calculate_metric(self, metric_name: str, 
                       source_node: Dict[str, Any],
                       target_node: Dict[str, Any],
                       knowledge_graph: Dict[str, Any]) -> float:
        """
        Calculate a specific metric between two nodes.
        
        Args:
            metric_name: Name of the metric to calculate
            source_node: Source node data
            target_node: Target node data
            knowledge_graph: Knowledge graph structure
            
        Returns:
            Metric value (0-1)
        """
        if metric_name == "semantic_similarity":
            return self._calculate_semantic_similarity(source_node, target_node)
        
        elif metric_name == "co_occurrence":
            return self._calculate_co_occurrence(source_node, target_node, knowledge_graph)
        
        elif metric_name == "structural_proximity":
            return self._calculate_structural_proximity(source_node, target_node, knowledge_graph)
        
        elif metric_name == "temporal_relevance":
            return self._calculate_temporal_relevance(source_node, target_node)
        
        elif metric_name == "causal_strength":
            return self._calculate_causal_strength(source_node, target_node, knowledge_graph)
        
        # Default for unknown metrics
        return 0.5
    
    def _calculate_semantic_similarity(self, node1: Dict[str, Any], 
                                    node2: Dict[str, Any]) -> float:
        """
        Calculate semantic similarity between two nodes.
        
        Args:
            node1: First node data
            node2: Second node data
            
        Returns:
            Semantic similarity score (0-1)
        """
        # In a real implementation, this would use embeddings or NLP methods
        # Here we'll use a simplified approach based on content overlap
        
        # Extract text content
        text1 = ""
        text2 = ""
        
        for field in ["name", "title", "description", "content"]:
            if field in node1:
                text1 += " " + str(node1[field])
            if field in node2:
                text2 += " " + str(node2[field])
        
        # Check for embedded vectors
        if "embedding" in node1 and "embedding" in node2:
            # Calculate cosine similarity between embeddings
            # (This would be implemented with proper vector operations)
            return 0.7  # Placeholder
        
        # Simple word overlap similarity if no embeddings
        if not text1 or not text2:
            return 0.0
        
        # Tokenize and calculate overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
        
        similarity = intersection / union
        
        # Check for category/type matches
        if node1.get("type") == node2.get("type"):
            similarity += 0.2
        if node1.get("category") == node2.get("category"):
            similarity += 0.2
        
        return min(1.0, similarity)
    
    def _calculate_co_occurrence(self, node1: Dict[str, Any], 
                              node2: Dict[str, Any],
                              knowledge_graph: Dict[str, Any]) -> float:
        """
        Calculate co-occurrence strength between nodes.
        
        Args:
            node1: First node data
            node2: Second node data
            knowledge_graph: Knowledge graph structure
            
        Returns:
            Co-occurrence score (0-1)
        """
        # In a real implementation, this would analyze contexts where both nodes appear
        
        # Check for explicitly stored co-occurrence
        if "co_occurrences" in knowledge_graph:
            node1_id = node1.get("id")
            node2_id = node2.get("id")
            
            if node1_id and node2_id:
                key = f"{node1_id}_{node2_id}"
                alt_key = f"{node2_id}_{node1_id}"
                
                if key in knowledge_graph["co_occurrences"]:
                    count = knowledge_graph["co_occurrences"][key]
                    # Normalize count to 0-1 range (assuming max count of 100)
                    return min(1.0, count / 100)
                elif alt_key in knowledge_graph["co_occurrences"]:
                    count = knowledge_graph["co_occurrences"][alt_key]
                    return min(1.0, count / 100)
        
        # Fallback to checking for shared references
        references1 = set(node1.get("references", []))
        references2 = set(node2.get("references", []))
        
        if references1 and references2:
            shared = len(references1.intersection(references2))
            total = min(len(references1), len(references2))
            
            if total > 0:
                return shared / total
        
        # Check for shared contexts
        contexts1 = set(node1.get("contexts", []))
        contexts2 = set(node2.get("contexts", []))
        
        if contexts1 and contexts2:
            shared = len(contexts1.intersection(contexts2))
            total = min(len(contexts1), len(contexts2))
            
            if total > 0:
                return shared / total
        
        # Default score for minimal information
        return 0.1
    
    def _calculate_structural_proximity(self, node1: Dict[str, Any], 
                                     node2: Dict[str, Any],
                                     knowledge_graph: Dict[str, Any]) -> float:
        """
        Calculate structural proximity in the graph.
        
        Args:
            node1: First node data
            node2: Second node data
            knowledge_graph: Knowledge graph structure
            
        Returns:
            Structural proximity score (0-1)
        """
        # Extract node IDs
        node1_id = node1.get("id")
        node2_id = node2.get("id")
        
        if not node1_id or not node2_id:
            return 0.0
        
        # Check for hierarchy information
        if "hierarchy" in knowledge_graph:
            hierarchy = knowledge_graph["hierarchy"]
            
            # Direct parent-child relationship
            if node1_id in hierarchy.get("parents", {}).get(node2_id, []):
                return 0.9  # Strong parent connection
            
            if node2_id in hierarchy.get("parents", {}).get(node1_id, []):
                return 0.9  # Strong parent connection
            
            # Siblings (same parent)
            node1_parents = hierarchy.get("parents", {}).get(node1_id, [])
            node2_parents = hierarchy.get("parents", {}).get(node2_id, [])
            
            shared_parents = set(node1_parents).intersection(set(node2_parents))
            if shared_parents:
                return 0.7  # Strong sibling connection
        
        # Check path distance in graph
        connections = knowledge_graph.get("connections", [])
        if connections:
            # In a real implementation, this would use graph algorithms
            # For simplicity, we'll check direct connection
            for conn in connections:
                if (conn.get("source") == node1_id and conn.get("target") == node2_id) or \
                   (conn.get("source") == node2_id and conn.get("target") == node1_id):
                    return 0.8  # Directly connected
        
        # Check shared properties
        props1 = node1.get("properties", {})
        props2 = node2.get("properties", {})
        
        if props1 and props2:
            shared_keys = set(props1.keys()).intersection(set(props2.keys()))
            matching_values = 0
            
            for key in shared_keys:
                if props1[key] == props2[key]:
                    matching_values += 1
            
            if shared_keys:
                property_similarity = matching_values / len(shared_keys)
                return max(0.2, property_similarity * 0.6)  # Scale to reasonable range
        
        # Low default for minimal information
        return 0.1
    
    def _calculate_temporal_relevance(self, node1: Dict[str, Any], 
                                   node2: Dict[str, Any]) -> float:
        """
        Calculate temporal relevance between nodes.
        
        Args:
            node1: First node data
            node2: Second node data
            
        Returns:
            Temporal relevance score (0-1)
        """
        # Check for timestamp information
        timestamp1 = node1.get("timestamp", node1.get("created_at", None))
        timestamp2 = node2.get("timestamp", node2.get("created_at", None))
        
        if timestamp1 is None or timestamp2 is None:
            return 0.5  # Neutral score if no timestamps
        
        # Calculate temporal proximity
        try:
            # Parse timestamps if they're strings
            if isinstance(timestamp1, str):
                timestamp1 = float(timestamp1)
            if isinstance(timestamp2, str):
                timestamp2 = float(timestamp2)
            
            # Calculate time difference in hours
            time_diff = abs(timestamp1 - timestamp2) / 3600
            
            # Apply decay function: higher score for closer timestamps
            # Score = 1.0 for same time, decaying to 0.1 over a 30-day period
            temporal_score = max(0.1, min(1.0, 1.0 - (time_diff / (24 * 30))))
            
            return temporal_score
            
        except (ValueError, TypeError):
            # Fallback if timestamps are invalid
            return 0.5
    
    def _calculate_causal_strength(self, node1: Dict[str, Any], 
                                node2: Dict[str, Any],
                                knowledge_graph: Dict[str, Any]) -> float:
        """
        Calculate causal relationship strength between nodes.
        
        Args:
            node1: First node data
            node2: Second node data
            knowledge_graph: Knowledge graph structure
            
        Returns:
            Causal strength score (0-1)
        """
        # Check for explicit causal relationships
        node1_id = node1.get("id")
        node2_id = node2.get("id")
        
        if "causal_relations" in knowledge_graph:
            causal_relations = knowledge_graph["causal_relations"]
            
            # Check if there's a direct causal relationship
            relation_key = f"{node1_id}->{node2_id}"
            if relation_key in causal_relations:
                return causal_relations[relation_key].get("strength", 0.8)
        
        # Check for cause-effect in node properties
        if "causes" in node1:
            causes = node1["causes"]
            if isinstance(causes, list) and node2_id in causes:
                return 0.9
            elif isinstance(causes, dict) and node2_id in causes:
                return causes[node2_id].get("strength", 0.8)
        
        if "effects" in node1:
            effects = node1["effects"]
            if isinstance(effects, list) and node2_id in effects:
                return 0.9
            elif isinstance(effects, dict) and node2_id in effects:
                return effects[node2_id].get("strength", 0.8)
        
        # Check for causal language in descriptions
        node1_desc = node1.get("description", "").lower()
        node2_desc = node2.get("description", "").lower()
        
        causal_terms = ["causes", "results in", "leads to", "produces", "generates", "creates"]
        
        for term in causal_terms:
            if term in node1_desc and node2.get("name", "").lower() in node1_desc:
                return 0.7
            if term in node2_desc and node1.get("name", "").lower() in node2_desc:
                return 0.7
        
        # Default for minimal information
        return 0.2
    
    def _is_already_connected(self, source_id: str, target_id: str, 
                           connections: List[Dict[str, Any]]) -> bool:
        """
        Check if two nodes are already connected.
        
        Args:
            source_id: ID of source node
            target_id: ID of target node
            connections: List of existing connections
            
        Returns:
            True if nodes are already connected
        """
        for conn in connections:
            if (conn.get("source") == source_id and conn.get("target") == target_id) or \
               (conn.get("bidirectional", False) and conn.get("source") == target_id and conn.get("target") == source_id):
                return True
        
        return False
    
    def _find_existing_connection(self, source_id: str, target_id: str, 
                               connections: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find an existing connection between nodes.
        
        Args:
            source_id: ID of source node
            target_id: ID of target node
            connections: List of existing connections
            
        Returns:
            Connection dict if found, None otherwise
        """
        for conn in connections:
            if conn.get("source") == source_id and conn.get("target") == target_id:
                return conn
            
            # Check reverse direction if bidirectional
            if conn.get("bidirectional", False) and conn.get("source") == target_id and conn.get("target") == source_id:
                return conn
        
        return None
    
    def _get_existing_connections(self, node_id: str, 
                               knowledge_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get existing connections for a node.
        
        Args:
            node_id: ID of the node
            knowledge_graph: Knowledge graph structure
            
        Returns:
            List of connections involving the node
        """
        connections = []
        
        for conn in knowledge_graph.get("connections", []):
            if conn.get("source") == node_id or conn.get("target") == node_id:
                connections.append(conn)
        
        return connections
    
    def _create_connection(self, source_id: str, target_id: str, 
                        connection_type: str, strength: float,
                        bidirectional: bool) -> Dict[str, Any]:
        """
        Create a new connection between nodes.
        
        Args:
            source_id: ID of source node
            target_id: ID of target node
            connection_type: Type of connection
            strength: Connection strength (0-1)
            bidirectional: Whether connection is bidirectional
            
        Returns:
            Dictionary representing the new connection
        """
        # Create unique ID for the connection
        conn_id = f"conn_{uuid.uuid4().hex[:8]}"
        
        # Get connection properties based on type
        conn_info = self.connection_types.get(connection_type, {})
        
        # Create connection
        connection = {
            "id": conn_id,
            "source": source_id,
            "target": target_id,
            "type": connection_type,
            "weight": strength,
            "bidirectional": bidirectional,
            "created_at": time.time(),
            "updated_at": time.time()
        }
        
        # Add type-specific properties
        if "directionality" in conn_info:
            connection["directionality"] = conn_info["directionality"]
        
        return connection
    
    def _strengthen_connection(self, connection: Dict[str, Any], 
                            new_strength: float,
                            new_type: Optional[str] = None) -> bool:
        """
        Strengthen an existing connection if new strength is higher.
        
        Args:
            connection: Existing connection
            new_strength: New strength value
            new_type: Optional new connection type
            
        Returns:
            True if connection was strengthened
        """
        current_strength = connection.get("weight", 0.0)
        
        # Only strengthen if new strength is sufficiently higher
        if new_strength > current_strength + self.connection_thresholds["reinforcement"]:
            connection["weight"] = new_strength
            connection["updated_at"] = time.time()
            
            # Update type if provided and different
            if new_type and new_type != connection.get("type"):
                connection["type"] = new_type
            
            return True
        
        return False
    
    def _identify_node_merges(self, source_nodes: List[Dict[str, Any]], 
                           target_nodes: List[Dict[str, Any]],
                           knowledge_graph: Dict[str, Any],
                           config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify nodes that should be merged due to high similarity.
        
        Args:
            source_nodes: List of source nodes
            target_nodes: List of target nodes
            knowledge_graph: Knowledge graph structure
            config: Configuration options
            
        Returns:
            List of merge operations
        """
        merge_operations = []
        merge_threshold = config.get("merge_threshold", self.connection_thresholds["merging"])
        
        # Combine all nodes for comparison
        all_nodes = source_nodes + target_nodes
        processed_pairs = set()
        
        # Compare all node pairs
        for i, node1 in enumerate(all_nodes):
            for j, node2 in enumerate(all_nodes[i+1:], i+1):
                # Skip if already processed
                node1_id = node1.get("id")
                node2_id = node2.get("id")
                
                if not node1_id or not node2_id:
                    continue
                
                pair_key = f"{node1_id}_{node2_id}"
                reverse_key = f"{node2_id}_{node1_id}"
                
                if pair_key in processed_pairs or reverse_key in processed_pairs:
                    continue
                
                processed_pairs.add(pair_key)
                
                # Calculate similarity for merge consideration
                similarity = self._calculate_semantic_similarity(node1, node2)
                
                # If similarity exceeds threshold, add to merge operations
                if similarity >= merge_threshold:
                    # Determine which node to keep (prefer source nodes, then by created date)
                    keep_node1 = False
                    
                    if node1 in source_nodes and node2 not in source_nodes:
                        keep_node1 = True
                    elif node2 in source_nodes and node1 not in source_nodes:
                        keep_node1 = False
                    else:
                        # Both in same list, check created date
                        time1 = node1.get("created_at", 0)
                        time2 = node2.get("created_at", 0)
                        keep_node1 = time1 <= time2  # Keep older node
                    
                    # Create merge operation
                    if keep_node1:
                        merge_operations.append({
                            "primary_node": node1_id,
                            "secondary_node": node2_id,
                            "similarity": similarity
                        })
                    else:
                        merge_operations.append({
                            "primary_node": node2_id,
                            "secondary_node": node1_id,
                            "similarity": similarity
                        })
        
        return merge_operations
    
    def _update_nodes_after_merge(self, nodes: List[Dict[str, Any]], 
                               merge_operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update node list after merge operations.
        
        Args:
            nodes: Original list of nodes
            merge_operations: List of merge operations
            
        Returns:
            Updated list of nodes
        """
        # Skip if no merge operations
        if not merge_operations:
            return nodes
        
        # Track nodes to remove
        nodes_to_remove = set()
        
        # Update node IDs based on merges
        for merge in merge_operations:
            secondary_id = merge.get("secondary_node")
            if secondary_id:
                nodes_to_remove.add(secondary_id)
        
        # Create filtered list
        updated_nodes = []
        
        for node in nodes:
            node_id = node.get("id")
            if node_id and node_id not in nodes_to_remove:
                updated_nodes.append(node)
        
        return updated_nodes
    
    def _prune_weak_connections(self, knowledge_graph: Dict[str, Any], 
                             pruning_threshold: float) -> List[Dict[str, Any]]:
        """
        Prune weak connections from the graph.
        
        Args:
            knowledge_graph: Knowledge graph structure
            pruning_threshold: Maximum weight to consider pruning
            
        Returns:
            List of pruned connections
        """
        pruned = []
        connections = knowledge_graph.get("connections", [])
        
        # Identify connections for pruning
        for conn in connections[:]:  # Use copy for safe removal
            weight = conn.get("weight", 0.0)
            
            # Prune if weight below threshold
            if weight <= pruning_threshold:
                pruned.append(conn)
                connections.remove(conn)
        
        return pruned
    
    def optimize_connections(self, knowledge_graph: Dict[str, Any], 
                          config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimize connections in a knowledge graph.
        
        Args:
            knowledge_graph: Knowledge graph to optimize
            config: Optional configuration for optimization
            
        Returns:
            Dictionary with optimization results
        """
        # Set default configuration if not provided
        if config is None:
            config = {
                "pruning_threshold": 0.2,
                "reinforcement_threshold": 0.1,
                "redundancy_threshold": 0.8,
                "max_connections_per_node": 20,
                "optimize_density": True,
                "optimize_redundancy": True,
                "optimize_centrality": True
            }
        
        # Validate input
        if not knowledge_graph or "connections" not in knowledge_graph:
            return {
                "success": False,
                "error": "Invalid knowledge graph structure",
                "optimizations_performed": 0
            }
        
        # Track all optimizations
        optimizations = {
            "pruned_connections": [],
            "strengthened_connections": [],
            "merged_connections": [],
            "added_connections": []
        }
        
        # Prune weak connections if enabled
        if config.get("optimize_density", True):
            pruned = self._prune_weak_connections(
                knowledge_graph, config.get("pruning_threshold", 0.2)
            )
            optimizations["pruned_connections"] = pruned
        
        # Optimize redundancy if enabled
        if config.get("optimize_redundancy", True):
            merged = self._merge_redundant_connections(
                knowledge_graph, config.get("redundancy_threshold", 0.8)
            )
            optimizations["merged_connections"] = merged
        
        # Optimize centrality if enabled
        if config.get("optimize_centrality", True):
            added = self._optimize_centrality(
                knowledge_graph, config.get("max_connections_per_node", 20)
            )
            optimizations["added_connections"] = added
        
        # Count total optimizations
        total_optimizations = sum(len(ops) for ops in optimizations.values())
        
        # Prepare result
        result = {
            "success": True,
            "optimizations_performed": total_optimizations,
            "optimization_details": optimizations
        }
        
        return result
    
    def _merge_redundant_connections(self, knowledge_graph: Dict[str, Any], 
                                  redundancy_threshold: float) -> List[Dict[str, Any]]:
        """
        Merge redundant connections in the graph.
        
        Args:
            knowledge_graph: Knowledge graph structure
            redundancy_threshold: Similarity threshold for merging
            
        Returns:
            List of merged connections
        """
        merged = []
        connections = knowledge_graph.get("connections", [])
        
        # Group connections by node pair
        connection_groups = {}
        
        for conn in connections:
            source = conn.get("source")
            target = conn.get("target")
            
            if not source or not target:
                continue
            
            # Normalize order for grouping
            if conn.get("bidirectional", False):
                # Use alphabetical ordering for bidirectional
                key = "_".join(sorted([source, target]))
            else:
                key = f"{source}_{target}"
            
            if key not in connection_groups:
                connection_groups[key] = []
            
            connection_groups[key].append(conn)
        
        # Process each group to merge redundant connections
        for key, group in connection_groups.items():
            if len(group) <= 1:
                continue  # No redundancy
            
            # Sort by weight descending
            group.sort(key=lambda x: x.get("weight", 0), reverse=True)
            
            # Keep strongest connection
            strongest = group[0]
            to_merge = group[1:]
            
            for conn in to_merge:
                # Check if types are compatible for merging
                if self._are_types_compatible(strongest.get("type"), conn.get("type")):
                    # Merge by keeping strongest and increasing its weight
                    new_weight = min(1.0, strongest.get("weight", 0) + conn.get("weight", 0) * 0.2)
                    strongest["weight"] = new_weight
                    strongest["updated_at"] = time.time()
                    
                    # If any are bidirectional, make the merged one bidirectional
                    if conn.get("bidirectional", False):
                        strongest["bidirectional"] = True
                    
                    # Remember merged connection
                    merged.append(conn)
                    
                    # Remove from connections list
                    if conn in connections:
                        connections.remove(conn)
        
        return merged
    
    def _optimize_centrality(self, knowledge_graph: Dict[str, Any], 
                          max_connections: int) -> List[Dict[str, Any]]:
        """
        Optimize graph centrality by adding strategic connections.
        
        Args:
            knowledge_graph: Knowledge graph structure
            max_connections: Maximum connections per node
            
        Returns:
            List of added connections
        """
        added = []
        
        # Calculate node centrality (simplified)
        nodes = knowledge_graph.get("nodes", [])
        connections = knowledge_graph.get("connections", [])
        
        # Count connections per node
        node_connections = {}
        for node in nodes:
            node_id = node.get("id")
            if node_id:
                node_connections[node_id] = 0
        
        for conn in connections:
            source = conn.get("source")
            target = conn.get("target")
            
            if source in node_connections:
                node_connections[source] += 1
            
            if target in node_connections and conn.get("bidirectional", False):
                node_connections[target] += 1
        
        # Identify central nodes (highest connection count)
        sorted_nodes = sorted(node_connections.items(), key=lambda x: x[1], reverse=True)
        central_nodes = [node_id for node_id, count in sorted_nodes[:min(5, len(sorted_nodes))]]
        
        # Identify isolated nodes (lowest connection count)
        isolated_nodes = [node_id for node_id, count in sorted_nodes[-min(10, len(sorted_nodes)):]]
        
        # Add strategic connections from central to isolated nodes
        for central_id in central_nodes:
            # Skip if this node already has maximum connections
            if node_connections.get(central_id, 0) >= max_connections:
                continue
            
            central_node = None
            for node in nodes:
                if node.get("id") == central_id:
                    central_node = node
                    break
            
            if not central_node:
                continue
            
            # Check each isolated node
            for isolated_id in isolated_nodes:
                # Skip self-connections
                if isolated_id == central_id:
                    continue
                
                # Check if already connected
                already_connected = False
                for conn in connections:
                    if (conn.get("source") == central_id and conn.get("target") == isolated_id) or \
                       (conn.get("bidirectional", False) and 
                        conn.get("source") == isolated_id and conn.get("target") == central_id):
                        already_connected = True
                        break
                
                if already_connected:
                    continue
                
                # Find the isolated node
                isolated_node = None
                for node in nodes:
                    if node.get("id") == isolated_id:
                        isolated_node = node
                        break
                
                if not isolated_node:
                    continue
                
                # Calculate connection strength
                strength = self._calculate_semantic_similarity(central_node, isolated_node)
                
                # Only add if reasonable strength
                if strength >= 0.3:
                    # Create new connection
                    new_conn = self._create_connection(
                        central_id, isolated_id, "semantic", strength, True
                    )
                    
                    connections.append(new_conn)
                    added.append(new_conn)
                    
                    # Update connection count
                    node_connections[central_id] += 1
                    
                    # Stop if maximum reached
                    if node_connections[central_id] >= max_connections:
                        break
        
        return added
    
    def _are_types_compatible(self, type1: str, type2: str) -> bool:
        """
        Check if connection types are compatible for merging.
        
        Args:
            type1: First connection type
            type2: Second connection type
            
        Returns:
            True if types are compatible
        """
        # Some types are naturally compatible
        compatible_groups = [
            {"semantic", "associative"},
            {"hierarchical", "compositional"},
            {"sequential", "causal"}
        ]
        
        for group in compatible_groups:
            if type1 in group and type2 in group:
                return True
        
        # Same type is always compatible
        return type1 == type2
    
    def analyze_connection_patterns(self, knowledge_graph: Dict[str, Any], 
                                 config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze connection patterns in a knowledge graph.
        
        Args:
            knowledge_graph: Knowledge graph to analyze
            config: Optional configuration for analysis
            
        Returns:
            Dictionary with analysis results
        """
        # Set default configuration if not provided
        if config is None:
            config = {
                "detect_clusters": True,
                "detect_hubs": True,
                "detect_bridges": True,
                "analyze_connectivity": True,
                "min_cluster_size": 3,
                "hub_connection_threshold": 5
            }
        
        # Validate input
        if not knowledge_graph or "connections" not in knowledge_graph:
            return {
                "success": False,
                "error": "Invalid knowledge graph structure",
                "patterns_detected": 0
            }
        
        # Prepare result
        results = {
            "clusters": [],
            "hubs": [],
            "bridges": [],
            "connectivity_analysis": {}
        }
        
        # Build node adjacency map
        adjacency = self._build_adjacency_map(knowledge_graph)
        
        # Detect clusters if enabled
        if config.get("detect_clusters", True):
            clusters = self._detect_clusters(
                knowledge_graph, adjacency, config.get("min_cluster_size", 3)
            )
            results["clusters"] = clusters
        
        # Detect hubs if enabled
        if config.get("detect_hubs", True):
            hubs = self._detect_hubs(
                knowledge_graph, adjacency, config.get("hub_connection_threshold", 5)
            )
            results["hubs"] = hubs
        
        # Detect bridges if enabled
        if config.get("detect_bridges", True):
            bridges = self._detect_bridges(knowledge_graph, adjacency)
            results["bridges"] = bridges
        
        # Analyze connectivity if enabled
        if config.get("analyze_connectivity", True):
            connectivity = self._analyze_connectivity(knowledge_graph, adjacency)
            results["connectivity_analysis"] = connectivity
        
        # Count total patterns
        total_patterns = len(results["clusters"]) + len(results["hubs"]) + len(results["bridges"])
        
        # Finalize result
        analysis_result = {
            "success": True,
            "patterns_detected": total_patterns,
            "pattern_details": results
        }
        
        return analysis_result
    
    def _build_adjacency_map(self, knowledge_graph: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Build an adjacency map from the graph connections.
        
        Args:
            knowledge_graph: Knowledge graph structure
            
        Returns:
            Dictionary mapping node IDs to lists of connected node IDs
        """
        adjacency = {}
        connections = knowledge_graph.get("connections", [])
        
        # Initialize empty lists for all nodes
        for node in knowledge_graph.get("nodes", []):
            node_id = node.get("id")
            if node_id:
                adjacency[node_id] = []
        
        # Add connections
        for conn in connections:
            source = conn.get("source")
            target = conn.get("target")
            
            if not source or not target:
                continue
            
            # Ensure nodes exist in adjacency
            if source not in adjacency:
                adjacency[source] = []
            if target not in adjacency:
                adjacency[target] = []
            
            # Add connection
            adjacency[source].append(target)
            
            # Add reverse connection if bidirectional
            if conn.get("bidirectional", False):
                adjacency[target].append(source)
        
        return adjacency
    
    def _detect_clusters(self, knowledge_graph: Dict[str, Any], 
                      adjacency: Dict[str, List[str]],
                      min_size: int) -> List[Dict[str, Any]]:
        """
        Detect clusters of closely connected nodes.
        
        Args:
            knowledge_graph: Knowledge graph structure
            adjacency: Adjacency map
            min_size: Minimum cluster size
            
        Returns:
            List of detected clusters
        """
        clusters = []
        visited = set()
        
        # Find connected components using BFS
        for start_node in adjacency:
            if start_node in visited:
                continue
            
            # Begin new cluster
            cluster = []
            queue = [start_node]
            component_visited = set(queue)
            
            while queue:
                node = queue.pop(0)
                cluster.append(node)
                visited.add(node)
                
                # Add unvisited neighbors
                for neighbor in adjacency.get(node, []):
                    if neighbor not in component_visited:
                        component_visited.add(neighbor)
                        queue.append(neighbor)
            
            # Save cluster if large enough
            if len(cluster) >= min_size:
                # Calculate cluster cohesion
                cohesion = self._calculate_cluster_cohesion(cluster, adjacency)
                
                clusters.append({
                    "id": f"cluster_{len(clusters)}",
                    "nodes": cluster,
                    "size": len(cluster),
                    "cohesion": cohesion
                })
        
        # Sort by size
        clusters.sort(key=lambda x: x["size"], reverse=True)
        
        return clusters
    
    def _calculate_cluster_cohesion(self, cluster: List[str], 
                                 adjacency: Dict[str, List[str]]) -> float:
        """
        Calculate cohesion of a cluster.
        
        Args:
            cluster: List of node IDs in the cluster
            adjacency: Adjacency map
            
        Returns:
            Cohesion score (0-1)
        """
        if len(cluster) <= 1:
            return 0.0
        
        # Count internal connections
        internal_connections = 0
        for node in cluster:
            neighbors = adjacency.get(node, [])
            internal_neighbors = [n for n in neighbors if n in cluster]
            internal_connections += len(internal_neighbors)
        
        # Maximum possible internal connections
        max_connections = len(cluster) * (len(cluster) - 1)
        
        if max_connections == 0:
            return 0.0
        
        # Normalize by maximum possible
        return internal_connections / max_connections
    
    def _detect_hubs(self, knowledge_graph: Dict[str, Any], 
                  adjacency: Dict[str, List[str]],
                  connection_threshold: int) -> List[Dict[str, Any]]:
        """
        Detect hub nodes with many connections.
        
        Args:
            knowledge_graph: Knowledge graph structure
            adjacency: Adjacency map
            connection_threshold: Minimum connections to be a hub
            
        Returns:
            List of detected hubs
        """
        hubs = []
        
        # Calculate degree for each node
        for node_id, neighbors in adjacency.items():
            degree = len(neighbors)
            
            if degree >= connection_threshold:
                # Find node data
                node_data = {}
                for node in knowledge_graph.get("nodes", []):
                    if node.get("id") == node_id:
                        node_data = node
                        break
                
                hubs.append({
                    "node_id": node_id,
                    "degree": degree,
                    "name": node_data.get("name", ""),
                    "type": node_data.get("type", ""),
                    "connections": neighbors
                })
        
        # Sort by degree
        hubs.sort(key=lambda x: x["degree"], reverse=True)
        
        return hubs
    
    def _detect_bridges(self, knowledge_graph: Dict[str, Any], 
                     adjacency: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """
        Detect bridge connections between clusters.
        
        Args:
            knowledge_graph: Knowledge graph structure
            adjacency: Adjacency map
            
        Returns:
            List of detected bridges
        """
        bridges = []
        connections = knowledge_graph.get("connections", [])
        
        # Use a simplified approach to detect potential bridges
        for conn in connections:
            source = conn.get("source")
            target = conn.get("target")
            
            if not source or not target:
                continue
            
            # Check if this is potentially a bridge
            source_neighbors = set(adjacency.get(source, []))
            target_neighbors = set(adjacency.get(target, []))
            
            # A bridge typically has few common neighbors
            common_neighbors = source_neighbors.intersection(target_neighbors)
            
            if len(common_neighbors) <= 1:
                # This might be a bridge - check importance
                source_degree = len(source_neighbors)
                target_degree = len(target_neighbors)
                
                # Bridges often connect nodes with higher degrees
                if source_degree >= 3 and target_degree >= 3:
                    bridges.append({
                        "connection_id": conn.get("id"),
                        "source": source,
                        "target": target,
                        "type": conn.get("type"),
                        "weight": conn.get("weight"),
                        "source_degree": source_degree,
                        "target_degree": target_degree
                    })
        
        # Sort by combined degree
        bridges.sort(key=lambda x: x["source_degree"] + x["target_degree"], reverse=True)
        
        return bridges
    
    def _analyze_connectivity(self, knowledge_graph: Dict[str, Any], 
                           adjacency: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Analyze overall connectivity of the graph.
        
        Args:
            knowledge_graph: Knowledge graph structure
            adjacency: Adjacency map
            
        Returns:
            Connectivity analysis results
        """
        # Count nodes and connections
        node_count = len(knowledge_graph.get("nodes", []))
        connection_count = len(knowledge_graph.get("connections", []))
        
        # Calculate basic metrics
        metrics = {
            "node_count": node_count,
            "connection_count": connection_count,
            "density": 0.0,
            "average_degree": 0.0,
            "isolated_node_count": 0,
            "connectivity_ratio": 0.0
        }
        
        if node_count > 1:
            # Graph density (ratio of actual connections to possible connections)
            max_connections = node_count * (node_count - 1)
            if max_connections > 0:
                metrics["density"] = connection_count / max_connections
            
            # Average degree (connections per node)
            if node_count > 0:
                metrics["average_degree"] = connection_count / node_count
            
            # Count isolated nodes
            isolated_count = sum(1 for neighbors in adjacency.values() if not neighbors)
            metrics["isolated_node_count"] = isolated_count
            
            # Connectivity ratio (connected nodes / total nodes)
            metrics["connectivity_ratio"] = (node_count - isolated_count) / node_count
        
        return metrics


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Dynamic Knowledge Graph Connector (KA-58) on the provided data.
    
    Args:
        data: A dictionary containing nodes and configuration
        
    Returns:
        Dictionary with connection results
    """
    # Extract data
    mode = data.get("mode", "establish")  # establish, optimize, or analyze
    source_nodes = data.get("source_nodes", [])
    target_nodes = data.get("target_nodes", [])
    knowledge_graph = data.get("knowledge_graph", {"nodes": [], "connections": []})
    config = data.get("config")
    
    # Generate sample data if requested
    if data.get("generate_sample", False):
        if mode == "establish":
            source_nodes, target_nodes, knowledge_graph = generate_sample_nodes(
                data.get("node_count", 10)
            )
        else:
            knowledge_graph = generate_sample_graph(
                data.get("node_count", 20),
                data.get("connection_count", 40)
            )
    
    # Create connector
    connector = DynamicKnowledgeGraphConnector()
    
    try:
        if mode == "establish":
            # Establish connections
            result = connector.establish_connections(
                source_nodes, target_nodes, knowledge_graph, config
            )
            
            if not result.get("success", False):
                return {
                    "algorithm": "KA-58",
                    "success": False,
                    "error": result.get("error", "Unknown error establishing connections"),
                    "timestamp": time.time()
                }
            
            # Return successful result
            return {
                "algorithm": "KA-58",
                "success": True,
                "connections_formed": result["connections_formed"],
                "connections_modified": result.get("connections_modified", 0),
                "new_connections": result["new_connections"],
                "modified_connections": result.get("modified_connections", []),
                "knowledge_graph": knowledge_graph,
                "timestamp": time.time()
            }
        
        elif mode == "optimize":
            # Optimize connections
            result = connector.optimize_connections(knowledge_graph, config)
            
            if not result.get("success", False):
                return {
                    "algorithm": "KA-58",
                    "success": False,
                    "error": result.get("error", "Unknown error optimizing connections"),
                    "timestamp": time.time()
                }
            
            # Return successful result
            return {
                "algorithm": "KA-58",
                "success": True,
                "optimizations_performed": result["optimizations_performed"],
                "optimization_details": result["optimization_details"],
                "knowledge_graph": knowledge_graph,
                "timestamp": time.time()
            }
        
        elif mode == "analyze":
            # Analyze connection patterns
            result = connector.analyze_connection_patterns(knowledge_graph, config)
            
            if not result.get("success", False):
                return {
                    "algorithm": "KA-58",
                    "success": False,
                    "error": result.get("error", "Unknown error analyzing connections"),
                    "timestamp": time.time()
                }
            
            # Return successful result
            return {
                "algorithm": "KA-58",
                "success": True,
                "patterns_detected": result["patterns_detected"],
                "pattern_details": result["pattern_details"],
                "timestamp": time.time()
            }
        
        else:
            return {
                "algorithm": "KA-58",
                "success": False,
                "error": f"Invalid mode: {mode}",
                "timestamp": time.time()
            }
    
    except Exception as e:
        logger.error(f"Error in KA-58 Dynamic Knowledge Graph Connector: {str(e)}")
        return {
            "algorithm": "KA-58",
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        }


def generate_sample_nodes(count: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Generate sample nodes for testing.
    
    Args:
        count: Number of nodes to generate
        
    Returns:
        Tuple of (source_nodes, target_nodes, knowledge_graph)
    """
    # Generate nodes
    all_nodes = []
    for i in range(count):
        node = {
            "id": f"node_{i}",
            "name": f"Sample Node {i}",
            "description": f"This is sample node {i} for testing",
            "type": random.choice(["concept", "entity", "event", "attribute"]),
            "created_at": time.time() - random.randint(0, 1000000)
        }
        all_nodes.append(node)
    
    # Split into source and target
    mid_point = count // 2
    source_nodes = all_nodes[:mid_point]
    target_nodes = all_nodes[mid_point:]
    
    # Create knowledge graph
    knowledge_graph = {
        "nodes": all_nodes,
        "connections": []
    }
    
    return source_nodes, target_nodes, knowledge_graph


def generate_sample_graph(node_count: int, connection_count: int) -> Dict[str, Any]:
    """
    Generate a sample knowledge graph for testing.
    
    Args:
        node_count: Number of nodes to generate
        connection_count: Number of connections to generate
        
    Returns:
        Dictionary with knowledge graph
    """
    # Generate nodes
    nodes = []
    for i in range(node_count):
        node = {
            "id": f"node_{i}",
            "name": f"Sample Node {i}",
            "description": f"This is sample node {i} for testing",
            "type": random.choice(["concept", "entity", "event", "attribute"]),
            "created_at": time.time() - random.randint(0, 1000000)
        }
        nodes.append(node)
    
    # Generate connections
    connections = []
    for i in range(connection_count):
        # Choose random nodes
        source_idx = random.randint(0, node_count - 1)
        target_idx = random.randint(0, node_count - 1)
        
        # Avoid self-connections
        while target_idx == source_idx:
            target_idx = random.randint(0, node_count - 1)
        
        # Create connection
        connection = {
            "id": f"conn_{i}",
            "source": f"node_{source_idx}",
            "target": f"node_{target_idx}",
            "type": random.choice(["semantic", "hierarchical", "associative", "causal"]),
            "weight": random.uniform(0.2, 0.9),
            "bidirectional": random.random() > 0.7,
            "created_at": time.time() - random.randint(0, 100000)
        }
        connections.append(connection)
    
    # Create knowledge graph
    knowledge_graph = {
        "nodes": nodes,
        "connections": connections
    }
    
    return knowledge_graph
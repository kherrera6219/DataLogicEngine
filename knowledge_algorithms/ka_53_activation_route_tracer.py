"""
KA-53: Activation Route Tracer

This algorithm traces activation routes through neural pathways,
mapping how information flows through the network and identifying
critical activation pathways for key concepts.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
import time
import math
import random
import uuid
import heapq
import copy

logger = logging.getLogger(__name__)

class ActivationRouteTracer:
    """
    KA-53: Traces activation routes through neural networks.
    
    This algorithm maps how information and activation signals propagate
    through simulated neural networks, identifying critical pathways,
    bottlenecks, and activation patterns for different concepts.
    """
    
    def __init__(self):
        """Initialize the Activation Route Tracer."""
        self.route_types = self._initialize_route_types()
        self.analysis_methods = self._initialize_analysis_methods()
        self.pathway_templates = self._initialize_pathway_templates()
        logger.info("KA-53: Activation Route Tracer initialized")
    
    def _initialize_route_types(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the types of activation routes."""
        return {
            "direct": {
                "description": "Straight-line activation path between source and target",
                "characteristics": ["fast propagation", "minimal branching", "high fidelity"],
                "optimal_use": "Core concept transmission",
                "complexity": "low"
            },
            "branching": {
                "description": "Pathway that splits into multiple sub-paths",
                "characteristics": ["concept expansion", "parallel processing", "association generation"],
                "optimal_use": "Idea exploration and expansion",
                "complexity": "medium"
            },
            "convergent": {
                "description": "Multiple input pathways converging to a single output",
                "characteristics": ["concept synthesis", "information integration", "multi-source fusion"],
                "optimal_use": "Combining related information",
                "complexity": "medium"
            },
            "recursive": {
                "description": "Pathway that loops back on itself for iterative processing",
                "characteristics": ["refinement", "iteration", "self-improvement"],
                "optimal_use": "Deep thinking and refinement",
                "complexity": "high"
            },
            "distributed": {
                "description": "Activation spread across wide network areas",
                "characteristics": ["redundancy", "fault tolerance", "holistic processing"],
                "optimal_use": "Complex concept representation",
                "complexity": "very high"
            },
            "inhibitory": {
                "description": "Pathway that reduces activation in connected areas",
                "characteristics": ["focus enhancement", "noise reduction", "contrast amplification"],
                "optimal_use": "Attention focusing",
                "complexity": "medium"
            }
        }
    
    def _initialize_analysis_methods(self) -> Dict[str, Dict[str, Any]]:
        """Initialize methods for analyzing activation routes."""
        return {
            "path_tracing": {
                "description": "Direct tracing of activation from source to targets",
                "applicable_to": ["direct", "branching", "convergent"],
                "computational_cost": "low",
                "accuracy": 0.9
            },
            "activation_flow": {
                "description": "Mapping the flow of activation strength through the network",
                "applicable_to": ["direct", "branching", "convergent", "distributed"],
                "computational_cost": "medium",
                "accuracy": 0.85
            },
            "recursive_analysis": {
                "description": "Analysis of recursive and cyclic activation patterns",
                "applicable_to": ["recursive"],
                "computational_cost": "high",
                "accuracy": 0.8
            },
            "inhibition_mapping": {
                "description": "Mapping of inhibitory connections and their effects",
                "applicable_to": ["inhibitory"],
                "computational_cost": "medium",
                "accuracy": 0.75
            },
            "pathway_comparison": {
                "description": "Comparing activation routes across different inputs",
                "applicable_to": ["all"],
                "computational_cost": "high",
                "accuracy": 0.85
            },
            "bottleneck_identification": {
                "description": "Finding critical junction points in activation pathways",
                "applicable_to": ["branching", "convergent", "distributed"],
                "computational_cost": "medium",
                "accuracy": 0.9
            }
        }
    
    def _initialize_pathway_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize templates for common neural pathway patterns."""
        return {
            "sequential_chain": {
                "description": "Linear chain of activations with minimal branching",
                "structure": [
                    {"layer": 1, "nodes": 1, "pattern": "single"},
                    {"layer": 2, "nodes": 1, "pattern": "single"},
                    {"layer": 3, "nodes": 1, "pattern": "single"}
                ],
                "transmission_fidelity": 0.95
            },
            "fan_out": {
                "description": "Single input spreading to multiple outputs",
                "structure": [
                    {"layer": 1, "nodes": 1, "pattern": "single"},
                    {"layer": 2, "nodes": 3, "pattern": "divergent"},
                    {"layer": 3, "nodes": 5, "pattern": "divergent"}
                ],
                "transmission_fidelity": 0.85
            },
            "fan_in": {
                "description": "Multiple inputs converging to single output",
                "structure": [
                    {"layer": 1, "nodes": 5, "pattern": "distributed"},
                    {"layer": 2, "nodes": 3, "pattern": "convergent"},
                    {"layer": 3, "nodes": 1, "pattern": "single"}
                ],
                "transmission_fidelity": 0.8
            },
            "recursive_loop": {
                "description": "Activation pathway with feedback loops",
                "structure": [
                    {"layer": 1, "nodes": 2, "pattern": "recursive"},
                    {"layer": 2, "nodes": 3, "pattern": "recursive"},
                    {"layer": 3, "nodes": 2, "pattern": "recursive"}
                ],
                "transmission_fidelity": 0.75
            },
            "parallel_pathways": {
                "description": "Multiple parallel activation streams",
                "structure": [
                    {"layer": 1, "nodes": 2, "pattern": "split"},
                    {"layer": 2, "nodes": 4, "pattern": "parallel"},
                    {"layer": 3, "nodes": 4, "pattern": "parallel"},
                    {"layer": 4, "nodes": 2, "pattern": "merge"}
                ],
                "transmission_fidelity": 0.9
            },
            "cross_connected": {
                "description": "Dense cross-connections between parallel paths",
                "structure": [
                    {"layer": 1, "nodes": 3, "pattern": "split"},
                    {"layer": 2, "nodes": 5, "pattern": "cross_connected"},
                    {"layer": 3, "nodes": 5, "pattern": "cross_connected"},
                    {"layer": 4, "nodes": 3, "pattern": "merge"}
                ],
                "transmission_fidelity": 0.85
            }
        }
    
    def trace_activation_routes(self, network: Dict[str, Any], 
                             inputs: List[Dict[str, Any]],
                             targets: Optional[List[Dict[str, Any]]] = None,
                             config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Trace activation routes through a neural network.
        
        Args:
            network: Network structure with nodes and connections
            inputs: Input activations to trace from
            targets: Optional target nodes to trace to
            config: Optional configuration parameters
            
        Returns:
            Dictionary with traced activation routes
        """
        # Set default configuration if not provided
        if config is None:
            config = {
                "trace_depth": 5,
                "trace_method": "path_tracing",
                "activation_threshold": 0.2,
                "include_weak_paths": False,
                "max_paths_per_input": 3,
                "include_path_metrics": True
            }
        
        # Validate inputs
        if not inputs:
            return {
                "success": False,
                "error": "No input activations provided",
                "routes": []
            }
        
        if not network or "nodes" not in network or "connections" not in network:
            return {
                "success": False,
                "error": "Invalid network structure",
                "routes": []
            }
        
        # Prepare network for tracing
        processed_network = self._preprocess_network(network)
        
        # Select tracing method
        trace_method = config.get("trace_method", "path_tracing")
        if trace_method not in self.analysis_methods:
            trace_method = "path_tracing"  # Default to basic path tracing
        
        # Trace routes for each input
        all_routes = []
        
        for input_idx, input_activation in enumerate(inputs):
            input_id = input_activation.get("id", f"input_{input_idx}")
            
            # Find the corresponding node in the network
            input_node = None
            for node in processed_network["nodes"]:
                if node.get("id") == input_id:
                    input_node = node
                    break
            
            # If input node not found, try matching by other criteria
            if input_node is None:
                # Try matching by layer and position if available
                if "layer" in input_activation and "position" in input_activation:
                    for node in processed_network["nodes"]:
                        if (node.get("layer") == input_activation["layer"] and 
                            node.get("position") == input_activation["position"]):
                            input_node = node
                            break
            
            # If still not found, create a virtual input node
            if input_node is None:
                input_node = {
                    "id": input_id,
                    "type": "input",
                    "layer": 0,
                    "position": input_idx,
                    "virtual": True
                }
                processed_network["nodes"].append(input_node)
                
                # Connect to first layer nodes as fallback
                first_layer_nodes = [n for n in processed_network["nodes"] if n.get("layer") == 1]
                for target_node in first_layer_nodes:
                    processed_network["connections"].append({
                        "source": input_node["id"],
                        "target": target_node["id"],
                        "weight": 0.5,
                        "virtual": True
                    })
            
            # Set the initial activation
            activation = input_activation.get("activation", 1.0)
            input_node["initial_activation"] = activation
            
            # Trace from this input
            if trace_method == "path_tracing":
                routes = self._trace_direct_paths(
                    input_node, 
                    processed_network, 
                    targets, 
                    config["trace_depth"],
                    config["activation_threshold"],
                    config["max_paths_per_input"]
                )
            elif trace_method == "activation_flow":
                routes = self._trace_activation_flow(
                    input_node, 
                    processed_network, 
                    targets, 
                    config["trace_depth"],
                    config["activation_threshold"]
                )
            elif trace_method == "recursive_analysis":
                routes = self._trace_recursive_patterns(
                    input_node, 
                    processed_network, 
                    config["trace_depth"],
                    config["activation_threshold"]
                )
            else:
                # Fallback to direct path tracing
                routes = self._trace_direct_paths(
                    input_node, 
                    processed_network, 
                    targets, 
                    config["trace_depth"],
                    config["activation_threshold"],
                    config["max_paths_per_input"]
                )
            
            # Calculate path metrics if requested
            if config["include_path_metrics"]:
                for route in routes:
                    route["metrics"] = self._calculate_path_metrics(route, processed_network)
            
            # Add to all routes
            all_routes.extend(routes)
        
        # Analyze the collective routes
        collective_analysis = self._analyze_collective_routes(all_routes, processed_network)
        
        return {
            "success": True,
            "routes": all_routes,
            "route_count": len(all_routes),
            "trace_method": trace_method,
            "analysis": collective_analysis
        }
    
    def _preprocess_network(self, network: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess the network for tracing.
        
        Args:
            network: Original network structure
            
        Returns:
            Processed network ready for tracing
        """
        processed = copy.deepcopy(network)
        
        # Ensure all nodes have unique IDs
        for i, node in enumerate(processed["nodes"]):
            if "id" not in node:
                node["id"] = f"node_{i}"
        
        # Ensure all connections have source and target
        valid_connections = []
        for conn in processed["connections"]:
            if "source" in conn and "target" in conn:
                valid_connections.append(conn)
        
        processed["connections"] = valid_connections
        
        # Create adjacency list for faster lookup
        processed["adjacency"] = {}
        
        for node in processed["nodes"]:
            node_id = node["id"]
            processed["adjacency"][node_id] = []
        
        for conn in processed["connections"]:
            source = conn["source"]
            target = conn["target"]
            weight = conn.get("weight", 0.5)
            
            if source in processed["adjacency"]:
                processed["adjacency"][source].append({
                    "target": target,
                    "weight": weight,
                    "connection": conn
                })
        
        return processed
    
    def _trace_direct_paths(self, input_node: Dict[str, Any], 
                         network: Dict[str, Any],
                         targets: Optional[List[Dict[str, Any]]],
                         max_depth: int,
                         activation_threshold: float,
                         max_paths: int) -> List[Dict[str, Any]]:
        """
        Trace direct paths from input node using modified Dijkstra's algorithm.
        
        Args:
            input_node: Starting node for tracing
            network: Processed network structure
            targets: Optional target nodes to trace to
            max_depth: Maximum depth of tracing
            activation_threshold: Minimum activation to continue tracing
            max_paths: Maximum number of paths to return per input
            
        Returns:
            List of traced paths
        """
        source_id = input_node["id"]
        initial_activation = input_node.get("initial_activation", 1.0)
        
        # Convert targets to IDs if provided
        target_ids = None
        if targets:
            target_ids = set()
            for target in targets:
                target_id = target.get("id")
                if target_id:
                    target_ids.add(target_id)
        
        # Use a priority queue to find strongest paths first
        # Format: (negative activation strength, current depth, current node, path, activations)
        queue = [(0, 0, source_id, [source_id], {source_id: initial_activation})]
        visited = set()  # Track visited node pairs to avoid cycles
        paths_found = []
        
        while queue and len(paths_found) < max_paths:
            # Get path with highest activation
            neg_strength, depth, current, path, activations = heapq.heappop(queue)
            strength = -neg_strength  # Convert back to positive
            
            # Check if we've reached a target (if targets are specified)
            if target_ids and current in target_ids:
                # Create path record
                path_record = {
                    "id": str(uuid.uuid4())[:8],
                    "source": source_id,
                    "target": current,
                    "path": path,
                    "activation_strength": strength,
                    "activations": dict(activations),
                    "depth": depth,
                    "route_type": self._determine_route_type(path, network)
                }
                
                paths_found.append(path_record)
                continue
            
            # Stop if max depth reached
            if depth >= max_depth:
                # If no specific targets, return this path
                if target_ids is None:
                    path_record = {
                        "id": str(uuid.uuid4())[:8],
                        "source": source_id,
                        "target": current,
                        "path": path,
                        "activation_strength": strength,
                        "activations": dict(activations),
                        "depth": depth,
                        "route_type": self._determine_route_type(path, network)
                    }
                    
                    paths_found.append(path_record)
                continue
            
            # Get outgoing connections
            if current in network["adjacency"]:
                for edge in network["adjacency"][current]:
                    next_node = edge["target"]
                    weight = edge["weight"]
                    
                    # Calculate activation for next node
                    next_activation = strength * weight
                    
                    # Skip if below threshold
                    if next_activation < activation_threshold:
                        continue
                    
                    # Skip if creates a cycle
                    edge_key = (current, next_node)
                    if edge_key in visited:
                        continue
                    
                    # Skip if node already in path (avoid loops)
                    if next_node in path:
                        continue
                    
                    visited.add(edge_key)
                    
                    # Create new path and activations
                    new_path = path + [next_node]
                    new_activations = dict(activations)
                    new_activations[next_node] = next_activation
                    
                    # Push to queue, using negative strength for min-heap as max-heap
                    heapq.heappush(
                        queue, 
                        (-next_activation, depth + 1, next_node, new_path, new_activations)
                    )
        
        # If no specific targets were given and we have no paths yet,
        # collect the deepest paths we found
        if target_ids is None and not paths_found and queue:
            # Sort remaining queue by depth (secondary key) and activation (primary key)
            sorted_queue = sorted(queue, key=lambda x: (x[1], -x[0]), reverse=True)
            
            # Take the top paths
            for i in range(min(max_paths, len(sorted_queue))):
                neg_strength, depth, current, path, activations = sorted_queue[i]
                strength = -neg_strength
                
                path_record = {
                    "id": str(uuid.uuid4())[:8],
                    "source": source_id,
                    "target": current,
                    "path": path,
                    "activation_strength": strength,
                    "activations": dict(activations),
                    "depth": depth,
                    "route_type": self._determine_route_type(path, network)
                }
                
                paths_found.append(path_record)
        
        return paths_found
    
    def _trace_activation_flow(self, input_node: Dict[str, Any], 
                            network: Dict[str, Any],
                            targets: Optional[List[Dict[str, Any]]],
                            max_depth: int,
                            activation_threshold: float) -> List[Dict[str, Any]]:
        """
        Trace activation flow through the network using breadth-first traversal.
        
        Args:
            input_node: Starting node for tracing
            network: Processed network structure
            targets: Optional target nodes to trace to
            max_depth: Maximum depth of tracing
            activation_threshold: Minimum activation to continue tracing
            
        Returns:
            List of activation flows
        """
        source_id = input_node["id"]
        initial_activation = input_node.get("initial_activation", 1.0)
        
        # Initialize activation state
        activation_state = {source_id: initial_activation}
        activation_history = [{source_id: initial_activation}]
        
        # Convert targets to IDs if provided
        target_ids = None
        if targets:
            target_ids = set()
            for target in targets:
                target_id = target.get("id")
                if target_id:
                    target_ids.add(target_id)
        
        # Propagate activation for max_depth steps
        for depth in range(max_depth):
            # Calculate new activation state
            new_state = {}
            
            # For each currently active node
            for node_id, activation in activation_state.items():
                # Skip if activation below threshold
                if activation < activation_threshold:
                    continue
                
                # Propagate to connected nodes
                if node_id in network["adjacency"]:
                    for edge in network["adjacency"][node_id]:
                        target_id = edge["target"]
                        weight = edge["weight"]
                        
                        # Calculate new activation
                        new_activation = activation * weight
                        
                        # Add to new state (combining if already present)
                        if target_id in new_state:
                            new_state[target_id] = max(new_state[target_id], new_activation)
                        else:
                            new_state[target_id] = new_activation
            
            # Update state for next iteration
            activation_state = new_state
            activation_history.append(dict(new_state))
            
            # Stop if no active nodes remain
            if not activation_state:
                break
        
        # Extract significant flows
        flows = []
        
        # If specific targets, extract flows to those targets
        if target_ids:
            for target_id in target_ids:
                # Find the highest activation for this target
                max_activation = 0
                max_depth = -1
                
                for depth, state in enumerate(activation_history):
                    if target_id in state and state[target_id] > max_activation:
                        max_activation = state[target_id]
                        max_depth = depth
                
                if max_activation >= activation_threshold:
                    # Create flow record
                    flow_record = {
                        "id": str(uuid.uuid4())[:8],
                        "source": source_id,
                        "target": target_id,
                        "path": self._reconstruct_path(
                            source_id, target_id, network, activation_history
                        ),
                        "activation_strength": max_activation,
                        "depth": max_depth,
                        "activation_history": self._extract_path_activations(
                            activation_history, target_id
                        ),
                        "route_type": "activation_flow"
                    }
                    
                    flows.append(flow_record)
        else:
            # Extract flows to all significant endpoints
            final_state = activation_history[-1]
            
            # Sort by activation strength
            significant_targets = [
                (node_id, activation) for node_id, activation in final_state.items()
                if activation >= activation_threshold
            ]
            significant_targets.sort(key=lambda x: x[1], reverse=True)
            
            # Take top 5 targets
            for target_id, activation in significant_targets[:5]:
                flow_record = {
                    "id": str(uuid.uuid4())[:8],
                    "source": source_id,
                    "target": target_id,
                    "path": self._reconstruct_path(
                        source_id, target_id, network, activation_history
                    ),
                    "activation_strength": activation,
                    "depth": len(activation_history) - 1,
                    "activation_history": self._extract_path_activations(
                        activation_history, target_id
                    ),
                    "route_type": "activation_flow"
                }
                
                flows.append(flow_record)
        
        return flows
    
    def _extract_path_activations(self, activation_history: List[Dict[str, float]], 
                               target_id: str) -> List[float]:
        """
        Extract activation values for a specific node across time steps.
        
        Args:
            activation_history: History of activation states
            target_id: ID of the target node
            
        Returns:
            List of activation values
        """
        activations = []
        
        for state in activation_history:
            activations.append(state.get(target_id, 0.0))
        
        return activations
    
    def _reconstruct_path(self, source_id: str, target_id: str, 
                       network: Dict[str, Any], 
                       activation_history: List[Dict[str, float]]) -> List[str]:
        """
        Reconstruct the most likely path from source to target.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            network: Network structure
            activation_history: History of activation states
            
        Returns:
            List of node IDs representing the path
        """
        # Simple case - direct connection
        if len(activation_history) <= 2:
            return [source_id, target_id]
        
        # Start with source and target
        path = [source_id]
        current = source_id
        target_found = False
        
        # For each time step (except the first)
        for t in range(1, len(activation_history)):
            state = activation_history[t]
            
            # If we've reached the target
            if current == target_id:
                target_found = True
                break
            
            # Find the strongest connection from current
            strongest_next = None
            strongest_activation = 0
            
            if current in network["adjacency"]:
                for edge in network["adjacency"][current]:
                    next_id = edge["target"]
                    
                    # Skip if not in current state
                    if next_id not in state:
                        continue
                    
                    # Skip if already in path (avoid loops)
                    if next_id in path:
                        continue
                    
                    activation = state[next_id]
                    
                    if activation > strongest_activation:
                        strongest_activation = activation
                        strongest_next = next_id
            
            # If no strong connection found, try to find any active node
            if strongest_next is None:
                # Find the strongest activated node in this state
                candidates = [(node_id, activation) for node_id, activation in state.items()
                             if node_id not in path]
                candidates.sort(key=lambda x: x[1], reverse=True)
                
                if candidates:
                    strongest_next = candidates[0][0]
            
            # Add to path if found
            if strongest_next:
                path.append(strongest_next)
                current = strongest_next
            else:
                # No valid next node found
                break
        
        # If target not in path yet, add it
        if not target_found:
            path.append(target_id)
        
        return path
    
    def _trace_recursive_patterns(self, input_node: Dict[str, Any], 
                               network: Dict[str, Any],
                               max_depth: int,
                               activation_threshold: float) -> List[Dict[str, Any]]:
        """
        Trace recursive activation patterns.
        
        Args:
            input_node: Starting node for tracing
            network: Processed network structure
            max_depth: Maximum depth of tracing
            activation_threshold: Minimum activation to continue tracing
            
        Returns:
            List of recursive patterns
        """
        source_id = input_node["id"]
        initial_activation = input_node.get("initial_activation", 1.0)
        
        # Initialize structures for tracking recursion
        paths = []
        visited = set()
        loops_found = set()
        
        # For recursive detection, we need to track paths that include the same node multiple times
        # Use a modified DFS approach
        def dfs(node_id, current_path, activations, depth, visited_edges):
            if depth >= max_depth:
                return
            
            # Check for loops in current path
            if node_id in current_path:
                # Found a loop
                loop_start_idx = current_path.index(node_id)
                loop = tuple(current_path[loop_start_idx:])
                
                # Skip if we've already found this loop
                if loop in loops_found:
                    return
                
                loops_found.add(loop)
                
                # Create loop record
                loop_record = {
                    "id": str(uuid.uuid4())[:8],
                    "source": source_id,
                    "pattern": "recursive_loop",
                    "loop": list(loop),
                    "loop_nodes": len(loop),
                    "full_path": list(current_path),
                    "activation_strength": activations[node_id],
                    "activations": dict(activations),
                    "depth": depth,
                    "route_type": "recursive"
                }
                
                paths.append(loop_record)
                return
            
            # Continue DFS exploration
            if node_id in network["adjacency"]:
                for edge in network["adjacency"][node_id]:
                    next_id = edge["target"]
                    weight = edge["weight"]
                    
                    # Calculate next activation
                    if node_id in activations:
                        next_activation = activations[node_id] * weight
                    else:
                        next_activation = initial_activation * weight
                    
                    # Skip if below threshold
                    if next_activation < activation_threshold:
                        continue
                    
                    # Skip if we've visited this edge too many times
                    edge_key = (node_id, next_id)
                    if edge_key in visited_edges and visited_edges[edge_key] >= 2:
                        continue
                    
                    # Update edge visit count
                    new_visited_edges = dict(visited_edges)
                    new_visited_edges[edge_key] = new_visited_edges.get(edge_key, 0) + 1
                    
                    # Update path and activations
                    new_path = current_path + (next_id,)
                    new_activations = dict(activations)
                    new_activations[next_id] = next_activation
                    
                    # Continue DFS
                    dfs(next_id, new_path, new_activations, depth + 1, new_visited_edges)
        
        # Start DFS from input node
        dfs(source_id, (source_id,), {source_id: initial_activation}, 0, {})
        
        # If no loops found, return empty list
        if not paths:
            # Try finding potential loops based on network structure
            potential_loops = self._find_potential_loops(network, source_id, max_depth)
            
            if potential_loops:
                for loop in potential_loops:
                    loop_record = {
                        "id": str(uuid.uuid4())[:8],
                        "source": source_id,
                        "pattern": "potential_recursive_loop",
                        "loop": loop,
                        "loop_nodes": len(loop),
                        "activation_strength": 0.5,  # Estimated
                        "depth": len(loop),
                        "route_type": "potentially_recursive",
                        "comment": "Potential loop inferred from network structure"
                    }
                    
                    paths.append(loop_record)
        
        return paths
    
    def _find_potential_loops(self, network: Dict[str, Any], 
                           start_node: str, 
                           max_depth: int) -> List[List[str]]:
        """
        Find potential loops in the network structure.
        
        Args:
            network: Network structure
            start_node: Starting node ID
            max_depth: Maximum depth to search
            
        Returns:
            List of potential loops
        """
        loops = []
        visited = set()
        
        def dfs(node_id, current_path, depth):
            if depth >= max_depth:
                return
            
            if node_id in current_path:
                # Found a loop
                loop_start_idx = current_path.index(node_id)
                loop = current_path[loop_start_idx:]
                loops.append(loop)
                return
            
            if node_id in network["adjacency"]:
                for edge in network["adjacency"][node_id]:
                    next_id = edge["target"]
                    edge_key = (node_id, next_id)
                    
                    if edge_key in visited:
                        continue
                    
                    visited.add(edge_key)
                    dfs(next_id, current_path + [next_id], depth + 1)
        
        dfs(start_node, [start_node], 0)
        return loops
    
    def _determine_route_type(self, path: List[str], network: Dict[str, Any]) -> str:
        """
        Determine the type of route based on path characteristics.
        
        Args:
            path: Node IDs in the path
            network: Network structure
            
        Returns:
            Route type classification
        """
        if not path or len(path) <= 1:
            return "unknown"
        
        # Check for loops (recursive pattern)
        unique_nodes = set(path)
        if len(unique_nodes) < len(path):
            return "recursive"
        
        # Check for branching pattern
        branching_nodes = []
        for node_id in path:
            if node_id in network["adjacency"]:
                outgoing_count = len(network["adjacency"][node_id])
                if outgoing_count > 1:
                    branching_nodes.append(node_id)
        
        if len(branching_nodes) > 1:
            return "branching"
        
        # Check for convergent pattern (need to look at whole network)
        convergent_nodes = []
        for node_id in path:
            # Count incoming connections
            incoming_count = 0
            for src, edges in network["adjacency"].items():
                for edge in edges:
                    if edge["target"] == node_id:
                        incoming_count += 1
            
            if incoming_count > 1:
                convergent_nodes.append(node_id)
        
        if len(convergent_nodes) > 1:
            return "convergent"
        
        # Check for inhibitory pattern
        inhibitory_edges = 0
        for i in range(len(path) - 1):
            source = path[i]
            target = path[i + 1]
            
            # Find the connection
            for edge in network["adjacency"].get(source, []):
                if edge["target"] == target:
                    if edge.get("type") == "inhibitory" or edge.get("weight", 0) < 0:
                        inhibitory_edges += 1
        
        if inhibitory_edges > 0:
            return "inhibitory"
        
        # Default to direct route
        return "direct"
    
    def _calculate_path_metrics(self, route: Dict[str, Any], network: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate metrics for an activation route.
        
        Args:
            route: Traced activation route
            network: Network structure
            
        Returns:
            Dictionary with path metrics
        """
        metrics = {}
        
        # Extract path
        path = route.get("path", [])
        
        if len(path) <= 1:
            return {
                "path_length": 0,
                "avg_activation": 0,
                "activation_decay": 0,
                "activation_stability": 0
            }
        
        # Path length (count edges)
        metrics["path_length"] = len(path) - 1
        
        # Average activation along path
        activations = route.get("activations", {})
        path_activations = [activations.get(node_id, 0) for node_id in path]
        
        if path_activations:
            metrics["avg_activation"] = sum(path_activations) / len(path_activations)
        else:
            metrics["avg_activation"] = 0
        
        # Activation decay (ratio of end to start activation)
        if len(path_activations) >= 2 and path_activations[0] > 0:
            metrics["activation_decay"] = path_activations[-1] / path_activations[0]
        else:
            metrics["activation_decay"] = 0
        
        # Activation stability (standard deviation of activation changes)
        if len(path_activations) >= 2:
            changes = []
            for i in range(1, len(path_activations)):
                if path_activations[i-1] > 0:
                    change = path_activations[i] / path_activations[i-1]
                    changes.append(change)
            
            if changes:
                avg_change = sum(changes) / len(changes)
                variance = sum((change - avg_change) ** 2 for change in changes) / len(changes)
                stability = 1 / (1 + variance)  # Transform variance to stability (0-1)
                metrics["activation_stability"] = stability
            else:
                metrics["activation_stability"] = 0
        else:
            metrics["activation_stability"] = 0
        
        # Bottleneck identification
        if len(path) > 2:
            # Find the minimum activation in interior nodes
            interior_activations = path_activations[1:-1]
            if interior_activations:
                min_activation = min(interior_activations)
                min_index = path_activations.index(min_activation)
                bottleneck_node = path[min_index]
                
                metrics["bottleneck"] = {
                    "node_id": bottleneck_node,
                    "position": min_index,
                    "activation": min_activation
                }
        
        return metrics
    
    def _analyze_collective_routes(self, routes: List[Dict[str, Any]], 
                                network: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the collective properties of all traced routes.
        
        Args:
            routes: List of traced routes
            network: Network structure
            
        Returns:
            Dictionary with collective analysis
        """
        if not routes:
            return {
                "route_count": 0,
                "dominant_route_type": "none",
                "critical_nodes": [],
                "pathway_patterns": []
            }
        
        # Count route types
        route_types = {}
        for route in routes:
            route_type = route.get("route_type", "unknown")
            route_types[route_type] = route_types.get(route_type, 0) + 1
        
        # Identify dominant route type
        dominant_type = max(route_types.items(), key=lambda x: x[1])[0] if route_types else "unknown"
        
        # Identify critical nodes (appear in multiple paths)
        node_counts = {}
        for route in routes:
            path = route.get("path", [])
            for node_id in path:
                node_counts[node_id] = node_counts.get(node_id, 0) + 1
        
        # Nodes appearing in more than half the routes are critical
        threshold = len(routes) / 2
        critical_nodes = []
        
        for node_id, count in node_counts.items():
            if count >= threshold:
                # Find node info
                node_info = {"id": node_id, "occurrence_count": count}
                
                # Add additional info if available
                for node in network["nodes"]:
                    if node.get("id") == node_id:
                        node_info["layer"] = node.get("layer")
                        node_info["position"] = node.get("position")
                        node_info["type"] = node.get("type")
                        break
                
                critical_nodes.append(node_info)
        
        # Sort by occurrence count
        critical_nodes.sort(key=lambda x: x["occurrence_count"], reverse=True)
        
        # Identify common pathway patterns
        pathway_patterns = []
        
        # Look for sequential chains
        sequential_chains = [r for r in routes if r.get("route_type") == "direct"]
        if sequential_chains and len(sequential_chains) >= len(routes) * 0.3:
            pathway_patterns.append({
                "pattern": "sequential_chain",
                "occurrence": len(sequential_chains),
                "description": "Direct sequential activation chains",
                "examples": [r["id"] for r in sequential_chains[:3]]
            })
        
        # Look for branching patterns
        branching_routes = [r for r in routes if r.get("route_type") == "branching"]
        if branching_routes and len(branching_routes) >= len(routes) * 0.2:
            pathway_patterns.append({
                "pattern": "fan_out",
                "occurrence": len(branching_routes),
                "description": "Branching activation paths",
                "examples": [r["id"] for r in branching_routes[:3]]
            })
        
        # Look for convergent patterns
        convergent_routes = [r for r in routes if r.get("route_type") == "convergent"]
        if convergent_routes and len(convergent_routes) >= len(routes) * 0.2:
            pathway_patterns.append({
                "pattern": "fan_in",
                "occurrence": len(convergent_routes),
                "description": "Converging activation paths",
                "examples": [r["id"] for r in convergent_routes[:3]]
            })
        
        # Look for recursive patterns
        recursive_routes = [r for r in routes if r.get("route_type") == "recursive"]
        if recursive_routes:
            pathway_patterns.append({
                "pattern": "recursive_loop",
                "occurrence": len(recursive_routes),
                "description": "Recursive activation loops",
                "examples": [r["id"] for r in recursive_routes[:3]]
            })
        
        return {
            "route_count": len(routes),
            "route_type_distribution": route_types,
            "dominant_route_type": dominant_type,
            "critical_nodes": critical_nodes,
            "pathway_patterns": pathway_patterns
        }


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Activation Route Tracer (KA-53) on the provided data.
    
    Args:
        data: A dictionary containing network structure, inputs, and optional configuration
        
    Returns:
        Dictionary with traced activation routes
    """
    network = data.get("network", {})
    inputs = data.get("inputs", [])
    targets = data.get("targets", None)
    config = data.get("config", None)
    
    # Generate sample data if requested
    if not network and data.get("generate_sample", False):
        # Generate a sample network based on template
        template = data.get("template", "sequential_chain")
        network = generate_sample_network(template, data.get("size", "medium"))
        
        # Generate sample inputs if not provided
        if not inputs:
            inputs = [{
                "id": network["nodes"][0]["id"],
                "activation": 1.0
            }]
        
        # Generate sample targets if requested
        if not targets and data.get("generate_targets", False):
            # Use last node as target
            targets = [{
                "id": network["nodes"][-1]["id"]
            }]
    
    # Validate inputs
    if not network:
        return {
            "algorithm": "KA-53",
            "success": False,
            "error": "No network structure provided",
            "timestamp": time.time()
        }
    
    if not inputs:
        return {
            "algorithm": "KA-53",
            "success": False,
            "error": "No input activations provided",
            "timestamp": time.time()
        }
    
    tracer = ActivationRouteTracer()
    
    try:
        result = tracer.trace_activation_routes(network, inputs, targets, config)
        
        if not result.get("success", False):
            return {
                "algorithm": "KA-53",
                "success": False,
                "error": result.get("error", "Unknown error"),
                "timestamp": time.time()
            }
        
        return {
            "algorithm": "KA-53",
            "routes": result["routes"],
            "route_count": result["route_count"],
            "trace_method": result["trace_method"],
            "analysis": result["analysis"],
            "timestamp": time.time(),
            "success": True
        }
    
    except Exception as e:
        logger.error(f"Error in KA-53 Activation Route Tracer: {str(e)}")
        return {
            "algorithm": "KA-53",
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        }


def generate_sample_network(template: str, size: str) -> Dict[str, Any]:
    """
    Generate a sample network for testing.
    
    Args:
        template: Network template to use
        size: Size of the network (small, medium, large)
        
    Returns:
        Dictionary with network structure
    """
    if template not in ["sequential_chain", "fan_out", "fan_in", "recursive_loop", "parallel_pathways", "cross_connected"]:
        template = "sequential_chain"
    
    if size not in ["small", "medium", "large"]:
        size = "medium"
    
    # Determine network dimensions based on size
    if size == "small":
        layers = 3
        width = 3
    elif size == "medium":
        layers = 5
        width = 5
    else:  # large
        layers = 8
        width = 8
    
    nodes = []
    connections = []
    
    # Generate nodes based on template
    if template == "sequential_chain":
        # Simple chain of nodes
        for layer in range(layers):
            nodes.append({
                "id": f"node_{layer}_0",
                "layer": layer,
                "position": 0,
                "type": "normal"
            })
        
        # Connect sequentially
        for layer in range(layers - 1):
            connections.append({
                "source": f"node_{layer}_0",
                "target": f"node_{layer+1}_0",
                "weight": 0.9
            })
    
    elif template == "fan_out":
        # First layer single node
        nodes.append({
            "id": f"node_0_0",
            "layer": 0,
            "position": 0,
            "type": "input"
        })
        
        # Middle layers - expanding width
        for layer in range(1, layers):
            layer_width = min(layer * 2, width)
            for pos in range(layer_width):
                nodes.append({
                    "id": f"node_{layer}_{pos}",
                    "layer": layer,
                    "position": pos,
                    "type": "normal"
                })
            
            # Connect to previous layer
            if layer == 1:
                # First expansion connects to input
                for pos in range(layer_width):
                    connections.append({
                        "source": "node_0_0",
                        "target": f"node_{layer}_{pos}",
                        "weight": 0.8
                    })
            else:
                prev_width = min((layer - 1) * 2, width)
                # Each node connects to 1-2 nodes in next layer
                for prev_pos in range(prev_width):
                    for pos in range(max(0, prev_pos - 1), min(layer_width, prev_pos + 2)):
                        connections.append({
                            "source": f"node_{layer-1}_{prev_pos}",
                            "target": f"node_{layer}_{pos}",
                            "weight": 0.7
                        })
    
    elif template == "fan_in":
        # First layer - multiple inputs
        first_width = min(width, 5)
        for pos in range(first_width):
            nodes.append({
                "id": f"node_0_{pos}",
                "layer": 0,
                "position": pos,
                "type": "input"
            })
        
        # Middle layers - converging width
        for layer in range(1, layers):
            layer_width = max(1, width - layer)
            for pos in range(layer_width):
                nodes.append({
                    "id": f"node_{layer}_{pos}",
                    "layer": layer,
                    "position": pos,
                    "type": "normal"
                })
            
            # Connect to previous layer
            prev_width = max(1, width - (layer - 1)) if layer > 1 else first_width
            
            for prev_pos in range(prev_width):
                for pos in range(layer_width):
                    # Ensure good coverage
                    if abs(prev_pos - pos) <= 2:
                        connections.append({
                            "source": f"node_{layer-1}_{prev_pos}",
                            "target": f"node_{layer}_{pos}",
                            "weight": 0.75
                        })
    
    elif template == "recursive_loop":
        # Create layers
        for layer in range(layers):
            layer_width = min(3, width)
            for pos in range(layer_width):
                nodes.append({
                    "id": f"node_{layer}_{pos}",
                    "layer": layer,
                    "position": pos,
                    "type": "normal" if layer > 0 else "input"
                })
        
        # Forward connections
        for layer in range(layers - 1):
            layer_width = min(3, width)
            next_width = min(3, width)
            
            for pos in range(layer_width):
                for next_pos in range(next_width):
                    if random.random() < 0.7:
                        connections.append({
                            "source": f"node_{layer}_{pos}",
                            "target": f"node_{layer+1}_{next_pos}",
                            "weight": 0.8
                        })
        
        # Add backward connections for recursion
        num_loops = layers // 2
        for _ in range(num_loops):
            from_layer = random.randint(2, layers - 1)
            to_layer = random.randint(0, from_layer - 2)
            
            from_pos = random.randint(0, min(3, width) - 1)
            to_pos = random.randint(0, min(3, width) - 1)
            
            connections.append({
                "source": f"node_{from_layer}_{from_pos}",
                "target": f"node_{to_layer}_{to_pos}",
                "weight": 0.5,
                "recursive": True
            })
    
    elif template == "parallel_pathways":
        # Create two parallel pathways
        for layer in range(layers):
            for pathway in range(2):
                nodes.append({
                    "id": f"node_{layer}_{pathway}",
                    "layer": layer,
                    "position": pathway,
                    "type": "normal" if layer > 0 else "input",
                    "pathway": pathway
                })
        
        # Connect pathways internally
        for layer in range(layers - 1):
            for pathway in range(2):
                connections.append({
                    "source": f"node_{layer}_{pathway}",
                    "target": f"node_{layer+1}_{pathway}",
                    "weight": 0.9
                })
        
        # Add occasional cross-connections
        num_crosses = layers // 3
        for _ in range(num_crosses):
            layer = random.randint(1, layers - 2)
            connections.append({
                "source": f"node_{layer}_0",
                "target": f"node_{layer+1}_1",
                "weight": 0.4,
                "cross": True
            })
            connections.append({
                "source": f"node_{layer}_1",
                "target": f"node_{layer+1}_0",
                "weight": 0.4,
                "cross": True
            })
    
    elif template == "cross_connected":
        # Create a densely connected network
        width = min(width, 4)  # Limit width for cross-connected
        
        # Create node grid
        for layer in range(layers):
            for pos in range(width):
                nodes.append({
                    "id": f"node_{layer}_{pos}",
                    "layer": layer,
                    "position": pos,
                    "type": "normal" if layer > 0 else "input"
                })
        
        # Create dense connections
        for layer in range(layers - 1):
            for pos in range(width):
                # Connect to all nodes in next layer
                for next_pos in range(width):
                    connection_strength = 0.9 if pos == next_pos else 0.4
                    connections.append({
                        "source": f"node_{layer}_{pos}",
                        "target": f"node_{layer+1}_{next_pos}",
                        "weight": connection_strength
                    })
    
    return {
        "nodes": nodes,
        "connections": connections,
        "template": template,
        "size": size
    }
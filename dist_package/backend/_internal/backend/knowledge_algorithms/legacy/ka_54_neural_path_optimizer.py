"""
KA-54: Neural Path Optimizer

This algorithm optimizes neural activation pathways for efficiency, strengthening
important connections while pruning unnecessary ones to improve signal clarity
and processing effectiveness.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
import time
import math
import random
import copy

logger = logging.getLogger(__name__)

class NeuralPathOptimizer:
    """
    KA-54: Optimizes neural activation pathways.
    
    This algorithm identifies and optimizes the efficiency of neural pathways
    by strengthening important connections, eliminating unnecessary ones, and
    reconfiguring network topology to improve information flow.
    """
    
    def __init__(self):
        """Initialize the Neural Path Optimizer."""
        self.optimization_strategies = self._initialize_optimization_strategies()
        self.connection_types = self._initialize_connection_types()
        self.evaluation_metrics = self._initialize_evaluation_metrics()
        logger.info("KA-54: Neural Path Optimizer initialized")
    
    def _initialize_optimization_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize optimization strategies for neural pathways."""
        return {
            "pruning": {
                "description": "Remove low-value connections to reduce noise and increase clarity",
                "suitable_for": ["noisy_networks", "redundant_pathways", "overconnected_nodes"],
                "impact_on_efficiency": "high",
                "impact_on_accuracy": "medium",
                "computational_cost": "low"
            },
            "strengthening": {
                "description": "Increase weights of high-value connections to enhance signal propagation",
                "suitable_for": ["weak_signals", "critical_pathways", "precision_tasks"],
                "impact_on_efficiency": "medium",
                "impact_on_accuracy": "high",
                "computational_cost": "low"
            },
            "rerouting": {
                "description": "Redirect signals through more optimal pathways",
                "suitable_for": ["bottlenecks", "high_latency_paths", "suboptimal_routing"],
                "impact_on_efficiency": "very high",
                "impact_on_accuracy": "medium",
                "computational_cost": "high"
            },
            "consolidation": {
                "description": "Merge similar pathways to reduce redundancy and improve coherence",
                "suitable_for": ["parallel_duplicates", "similar_pathways", "resource_constraints"],
                "impact_on_efficiency": "high",
                "impact_on_accuracy": "medium",
                "computational_cost": "medium"
            },
            "expansion": {
                "description": "Add new connections to provide alternative pathways for critical information",
                "suitable_for": ["single_point_failures", "limited_connectivity", "critical_concepts"],
                "impact_on_efficiency": "medium",
                "impact_on_accuracy": "high",
                "computational_cost": "high"
            },
            "balancing": {
                "description": "Redistribute connection weights to maintain equilibrium and prevent domination",
                "suitable_for": ["uneven_activations", "attention_imbalance", "concept_bias"],
                "impact_on_efficiency": "medium",
                "impact_on_accuracy": "high",
                "computational_cost": "medium"
            }
        }
    
    def _initialize_connection_types(self) -> Dict[str, Dict[str, Any]]:
        """Initialize types of neural connections for optimization."""
        return {
            "critical": {
                "description": "Essential connections that form the backbone of the pathway",
                "optimization_priority": "very high",
                "pruning_threshold": 0.05,  # Very low threshold - rarely prune
                "strengthening_factor": 1.5  # High strengthening
            },
            "supporting": {
                "description": "Secondary connections that enhance primary pathways",
                "optimization_priority": "high",
                "pruning_threshold": 0.2,
                "strengthening_factor": 1.2
            },
            "complementary": {
                "description": "Additional connections that provide context or nuance",
                "optimization_priority": "medium",
                "pruning_threshold": 0.3,
                "strengthening_factor": 1.1
            },
            "redundant": {
                "description": "Duplicate connections that provide minimal additional value",
                "optimization_priority": "low",
                "pruning_threshold": 0.6,  # High threshold - often prune
                "strengthening_factor": 0.9  # May actually weaken
            },
            "noise": {
                "description": "Connections that introduce distraction or confusion",
                "optimization_priority": "very low",
                "pruning_threshold": 0.8,  # Very high threshold - almost always prune
                "strengthening_factor": 0.7  # Significantly weaken
            }
        }
    
    def _initialize_evaluation_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Initialize metrics for evaluating pathway optimization."""
        return {
            "throughput": {
                "description": "Rate at which signals can propagate through the pathway",
                "calculation": "sum of effective weights / path length",
                "optimal_range": [0.7, 0.95]
            },
            "signal_clarity": {
                "description": "How clearly the intended signal stands out from noise",
                "calculation": "primary signal strength / average noise level",
                "optimal_range": [3.0, 10.0]
            },
            "pattern_stability": {
                "description": "Consistency of activation patterns for similar inputs",
                "calculation": "1 - (variance of activation patterns)",
                "optimal_range": [0.7, 0.9]
            },
            "energy_efficiency": {
                "description": "Computational efficiency of the pathway",
                "calculation": "output value / total activation cost",
                "optimal_range": [0.5, 0.8]
            },
            "robustness": {
                "description": "Ability to maintain performance despite perturbations",
                "calculation": "performance after noise / baseline performance",
                "optimal_range": [0.8, 0.95]
            },
            "integration_level": {
                "description": "How well the pathway connects to the broader network",
                "calculation": "count of useful cross-connections / pathway length",
                "optimal_range": [0.3, 0.6]
            }
        }
    
    def optimize_neural_pathways(self, network: Dict[str, Any], 
                              pathways: List[Dict[str, Any]],
                              optimization_goals: Optional[Dict[str, float]] = None,
                              config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimize neural pathways for improved efficiency and effectiveness.
        
        Args:
            network: Network structure with nodes and connections
            pathways: List of neural pathways to optimize
            optimization_goals: Optional goals for specific metrics
            config: Optional configuration parameters
            
        Returns:
            Dictionary with optimization results
        """
        # Set default configuration if not provided
        if config is None:
            config = {
                "optimization_intensity": 0.7,  # How aggressive the optimization should be (0-1)
                "allowed_strategies": ["pruning", "strengthening", "rerouting", "consolidation", "expansion", "balancing"],
                "max_iterations": 5,
                "evaluation_threshold": 0.8,  # Target metric score for success
                "preserve_critical_paths": True,
                "allow_topology_changes": True
            }
        
        # Set default optimization goals if not provided
        if optimization_goals is None:
            optimization_goals = {
                "throughput": 0.8,
                "signal_clarity": 5.0,
                "pattern_stability": 0.8,
                "energy_efficiency": 0.7,
                "robustness": 0.85,
                "integration_level": 0.4
            }
        
        # Validate inputs
        if not network or "nodes" not in network or "connections" not in network:
            return {
                "success": False,
                "error": "Invalid network structure",
                "optimized_pathways": [],
                "metrics": {}
            }
        
        if not pathways:
            return {
                "success": False,
                "error": "No pathways provided for optimization",
                "optimized_pathways": [],
                "metrics": {}
            }
        
        # Prepare network for optimization
        working_network = self._preprocess_network(network)
        
        # Analyze initial pathways and network
        initial_analysis = self._analyze_pathways(working_network, pathways)
        
        # Determine optimization approach for each pathway
        optimization_plans = self._create_optimization_plans(
            working_network, 
            pathways, 
            initial_analysis, 
            optimization_goals, 
            config
        )
        
        # Apply optimizations
        optimized_network, optimized_pathways, optimization_history = self._apply_optimizations(
            working_network, 
            pathways, 
            optimization_plans, 
            config
        )
        
        # Evaluate results
        final_analysis = self._analyze_pathways(optimized_network, optimized_pathways)
        improvement_analysis = self._calculate_improvements(initial_analysis, final_analysis)
        
        # Prepare result
        result = {
            "success": True,
            "optimized_network": optimized_network,
            "optimized_pathways": optimized_pathways,
            "initial_analysis": initial_analysis,
            "final_analysis": final_analysis,
            "improvement": improvement_analysis,
            "optimization_history": optimization_history
        }
        
        return result
    
    def _preprocess_network(self, network: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess the network for optimization.
        
        Args:
            network: Original network structure
            
        Returns:
            Processed network ready for optimization
        """
        processed = copy.deepcopy(network)
        
        # Ensure all nodes have unique IDs
        for i, node in enumerate(processed["nodes"]):
            if "id" not in node:
                node["id"] = f"node_{i}"
        
        # Ensure all connections have source and target
        valid_connections = []
        for i, conn in enumerate(processed["connections"]):
            if "source" in conn and "target" in conn:
                # Ensure connection has an ID
                if "id" not in conn:
                    conn["id"] = f"conn_{i}"
                
                # Ensure connection has a weight
                if "weight" not in conn:
                    conn["weight"] = 0.5
                
                valid_connections.append(conn)
        
        processed["connections"] = valid_connections
        
        # Create adjacency list for faster lookup
        processed["adjacency"] = {}
        
        for node in processed["nodes"]:
            node_id = node["id"]
            processed["adjacency"][node_id] = {
                "outgoing": [],
                "incoming": []
            }
        
        for conn in processed["connections"]:
            source = conn["source"]
            target = conn["target"]
            
            if source in processed["adjacency"]:
                processed["adjacency"][source]["outgoing"].append({
                    "target": target,
                    "connection": conn
                })
            
            if target in processed["adjacency"]:
                processed["adjacency"][target]["incoming"].append({
                    "source": source,
                    "connection": conn
                })
        
        return processed
    
    def _analyze_pathways(self, network: Dict[str, Any], 
                        pathways: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze neural pathways for optimization opportunities.
        
        Args:
            network: Processed network structure
            pathways: List of neural pathways to analyze
            
        Returns:
            Dictionary with pathway analysis
        """
        # Overall metrics
        overall_metrics = {
            "throughput": 0,
            "signal_clarity": 0,
            "pattern_stability": 0,
            "energy_efficiency": 0,
            "robustness": 0,
            "integration_level": 0
        }
        
        # Per-pathway analysis
        pathway_analyses = []
        
        for pathway in pathways:
            path_nodes = pathway.get("path", [])
            
            # Skip invalid pathways
            if len(path_nodes) < 2:
                continue
            
            # Extract connections along the pathway
            path_connections = []
            
            for i in range(len(path_nodes) - 1):
                source = path_nodes[i]
                target = path_nodes[i + 1]
                
                # Find the connection between these nodes
                connection = None
                if source in network["adjacency"]:
                    for edge in network["adjacency"][source]["outgoing"]:
                        if edge["target"] == target:
                            connection = edge["connection"]
                            break
                
                if connection:
                    path_connections.append(connection)
            
            # Calculate pathway metrics
            pathway_metrics = self._calculate_pathway_metrics(network, path_nodes, path_connections)
            
            # Identify bottlenecks
            bottlenecks = self._identify_bottlenecks(network, path_nodes, path_connections, pathway_metrics)
            
            # Classify connections
            connection_classifications = self._classify_connections(network, path_connections, pathway_metrics)
            
            # Identify optimization opportunities
            optimization_opportunities = self._identify_optimization_opportunities(
                network, path_nodes, path_connections, pathway_metrics, bottlenecks
            )
            
            # Add to pathway analyses
            pathway_analyses.append({
                "pathway_id": pathway.get("id", f"pathway_{len(pathway_analyses)}"),
                "metrics": pathway_metrics,
                "bottlenecks": bottlenecks,
                "connection_classifications": connection_classifications,
                "optimization_opportunities": optimization_opportunities
            })
            
            # Update overall metrics (weighted by pathway importance)
            pathway_importance = pathway.get("importance", 1.0)
            for metric, value in pathway_metrics.items():
                overall_metrics[metric] += value * pathway_importance
        
        # Normalize overall metrics
        if pathways:
            total_importance = sum(p.get("importance", 1.0) for p in pathways if len(p.get("path", [])) >= 2)
            if total_importance > 0:
                overall_metrics = {k: v / total_importance for k, v in overall_metrics.items()}
        
        # Calculate network-level metrics
        network_metrics = self._calculate_network_metrics(network, pathways)
        
        return {
            "overall_metrics": overall_metrics,
            "pathway_analyses": pathway_analyses,
            "network_metrics": network_metrics
        }
    
    def _calculate_pathway_metrics(self, network: Dict[str, Any], 
                                path_nodes: List[str], 
                                path_connections: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate metrics for a neural pathway.
        
        Args:
            network: Processed network structure
            path_nodes: List of node IDs in the pathway
            path_connections: List of connections along the pathway
            
        Returns:
            Dictionary with pathway metrics
        """
        metrics = {}
        
        # Initialize default metric values
        for metric in self.evaluation_metrics:
            metrics[metric] = 0.0
        
        # Return defaults for invalid pathways
        if len(path_nodes) < 2 or not path_connections:
            return metrics
        
        # Throughput (rate at which signals can propagate)
        connection_weights = [conn.get("weight", 0.5) for conn in path_connections]
        if connection_weights:
            # Throughput is the geometric mean of connection weights
            throughput = 1.0
            for weight in connection_weights:
                throughput *= max(0.001, weight)  # Avoid zero
            throughput = throughput ** (1.0 / len(connection_weights))
            metrics["throughput"] = throughput
        
        # Signal clarity (signal-to-noise ratio)
        # Calculate based on connection weights vs noise connections
        if path_connections:
            signal_strength = sum(conn.get("weight", 0.5) for conn in path_connections)
            
            # Calculate noise from irrelevant connections to pathway nodes
            noise_level = 0
            noise_count = 0
            
            for node_id in path_nodes:
                if node_id in network["adjacency"]:
                    # Count outgoing connections not in pathway
                    for edge in network["adjacency"][node_id]["outgoing"]:
                        target = edge["target"]
                        if target not in path_nodes or path_nodes.index(target) != path_nodes.index(node_id) + 1:
                            noise_level += edge["connection"].get("weight", 0.5)
                            noise_count += 1
                    
                    # Count incoming connections not in pathway
                    for edge in network["adjacency"][node_id]["incoming"]:
                        source = edge["source"]
                        if source not in path_nodes or path_nodes.index(source) != path_nodes.index(node_id) - 1:
                            noise_level += edge["connection"].get("weight", 0.5)
                            noise_count += 1
            
            # Calculate signal clarity
            avg_noise = noise_level / max(1, noise_count)
            avg_signal = signal_strength / len(path_connections)
            if avg_noise > 0:
                metrics["signal_clarity"] = avg_signal / avg_noise
            else:
                metrics["signal_clarity"] = 10.0  # Max value if no noise
        
        # Pattern stability (estimated)
        # Higher weights and fewer alternative paths = more stable
        weight_variance = 0
        if len(connection_weights) > 1:
            mean_weight = sum(connection_weights) / len(connection_weights)
            weight_variance = sum((w - mean_weight) ** 2 for w in connection_weights) / len(connection_weights)
        
        metrics["pattern_stability"] = max(0, 1.0 - min(1.0, weight_variance * 2))
        
        # Energy efficiency
        # More efficient pathways have higher weights with fewer connections
        path_length = len(path_connections)
        if path_length > 0:
            effective_strength = sum(connection_weights) / path_length
            
            # Penalize longer paths
            length_penalty = math.log(path_length + 1) / 10
            metrics["energy_efficiency"] = effective_strength / (1 + length_penalty)
        
        # Robustness
        # Higher robustness if the pathway has alternative parallel connections
        robustness_score = 0
        for i, node_id in enumerate(path_nodes):
            if i == 0 or i == len(path_nodes) - 1:
                continue  # Skip start and end nodes
            
            # Check for alternative paths around this node
            if i > 0 and i < len(path_nodes) - 1:
                prev_node = path_nodes[i - 1]
                next_node = path_nodes[i + 1]
                
                # Check if there's a direct connection from prev to next
                has_bypass = False
                if prev_node in network["adjacency"]:
                    for edge in network["adjacency"][prev_node]["outgoing"]:
                        if edge["target"] == next_node:
                            has_bypass = True
                            break
                
                if has_bypass:
                    robustness_score += 1
        
        if len(path_nodes) > 2:
            metrics["robustness"] = 0.5 + (robustness_score / (len(path_nodes) - 2)) * 0.5
        else:
            metrics["robustness"] = 0.5  # Default for short paths
        
        # Integration level
        # Measures how well the pathway connects to the broader network
        cross_connections = 0
        
        for node_id in path_nodes:
            if node_id in network["adjacency"]:
                # Count connections to nodes outside the pathway
                for edge in network["adjacency"][node_id]["outgoing"]:
                    if edge["target"] not in path_nodes:
                        cross_connections += 1
                
                for edge in network["adjacency"][node_id]["incoming"]:
                    if edge["source"] not in path_nodes:
                        cross_connections += 1
        
        if len(path_nodes) > 0:
            metrics["integration_level"] = min(1.0, cross_connections / (len(path_nodes) * 2))
        
        return metrics
    
    def _identify_bottlenecks(self, network: Dict[str, Any], 
                           path_nodes: List[str], 
                           path_connections: List[Dict[str, Any]],
                           metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Identify bottlenecks in a neural pathway.
        
        Args:
            network: Processed network structure
            path_nodes: List of node IDs in the pathway
            path_connections: List of connections along the pathway
            metrics: Calculated pathway metrics
            
        Returns:
            List of identified bottlenecks
        """
        bottlenecks = []
        
        # Return empty list for invalid pathways
        if len(path_nodes) < 3 or len(path_connections) < 2:
            return bottlenecks
        
        # Check for weak connections (bottlenecks)
        for i, connection in enumerate(path_connections):
            weight = connection.get("weight", 0.5)
            
            # Connection is a bottleneck if its weight is significantly lower than others
            if i > 0 and i < len(path_connections) - 1:
                prev_weight = path_connections[i - 1].get("weight", 0.5)
                next_weight = path_connections[i + 1].get("weight", 0.5)
                
                avg_adjacent_weight = (prev_weight + next_weight) / 2
                
                if weight < avg_adjacent_weight * 0.7:  # Significantly weaker
                    bottlenecks.append({
                        "type": "weak_connection",
                        "connection_id": connection.get("id"),
                        "position": i,
                        "weight": weight,
                        "severity": (avg_adjacent_weight - weight) / avg_adjacent_weight,
                        "source": connection.get("source"),
                        "target": connection.get("target")
                    })
        
        # Check for overloaded nodes (high fan-in or fan-out)
        for i, node_id in enumerate(path_nodes):
            if i == 0 or i == len(path_nodes) - 1:
                continue  # Skip start and end nodes
            
            # Count incoming and outgoing connections
            if node_id in network["adjacency"]:
                incoming_count = len(network["adjacency"][node_id]["incoming"])
                outgoing_count = len(network["adjacency"][node_id]["outgoing"])
                
                # Node is a bottleneck if it has many incoming but few outgoing connections
                if incoming_count > 3 and outgoing_count < incoming_count / 2:
                    bottlenecks.append({
                        "type": "convergence_bottleneck",
                        "node_id": node_id,
                        "position": i,
                        "incoming_count": incoming_count,
                        "outgoing_count": outgoing_count,
                        "severity": min(1.0, (incoming_count - outgoing_count) / incoming_count)
                    })
                
                # Node is also a bottleneck if it has few incoming but many outgoing connections
                if outgoing_count > 3 and incoming_count < outgoing_count / 2:
                    bottlenecks.append({
                        "type": "divergence_bottleneck",
                        "node_id": node_id,
                        "position": i,
                        "incoming_count": incoming_count,
                        "outgoing_count": outgoing_count,
                        "severity": min(1.0, (outgoing_count - incoming_count) / outgoing_count)
                    })
        
        # Sort bottlenecks by severity
        bottlenecks.sort(key=lambda x: x["severity"], reverse=True)
        
        return bottlenecks
    
    def _classify_connections(self, network: Dict[str, Any], 
                           path_connections: List[Dict[str, Any]],
                           metrics: Dict[str, float]) -> Dict[str, List[str]]:
        """
        Classify connections in a neural pathway by their role and importance.
        
        Args:
            network: Processed network structure
            path_connections: List of connections along the pathway
            metrics: Calculated pathway metrics
            
        Returns:
            Dictionary mapping connection types to lists of connection IDs
        """
        classification = {
            "critical": [],
            "supporting": [],
            "complementary": [],
            "redundant": [],
            "noise": []
        }
        
        # Return empty classifications for invalid pathways
        if not path_connections:
            return classification
        
        # Get connection weights
        weights = [conn.get("weight", 0.5) for conn in path_connections]
        _avg_weight = sum(weights) / len(weights)  # noqa: F841 - For future analysis
        max_weight = max(weights)
        _min_weight = min(weights)  # noqa: F841 - For future analysis
        
        # Classify each connection
        for i, connection in enumerate(path_connections):
            conn_id = connection.get("id")
            weight = connection.get("weight", 0.5)
            
            # Initial classification based on weight percentile
            if weight > 0.8 * max_weight:
                category = "critical"
            elif weight > 0.6 * max_weight:
                category = "supporting"
            elif weight > 0.4 * max_weight:
                category = "complementary"
            elif weight > 0.2 * max_weight:
                category = "redundant"
            else:
                category = "noise"
            
            # Adjust classification based on position
            if i == 0 or i == len(path_connections) - 1:
                # First and last connections are usually more important
                if category == "redundant":
                    category = "complementary"
                elif category == "complementary":
                    category = "supporting"
                elif category == "supporting":
                    category = "critical"
            
            # Adjust classification based on structure
            is_bottleneck = False
            if i > 0 and i < len(path_connections) - 1:
                prev_weight = path_connections[i - 1].get("weight", 0.5)
                next_weight = path_connections[i + 1].get("weight", 0.5)
                
                if weight < min(prev_weight, next_weight) * 0.7:
                    is_bottleneck = True
            
            if is_bottleneck:
                # Bottlenecks are critical (they need improvement)
                category = "critical"
            
            # Add to classification
            classification[category].append(conn_id)
        
        return classification
    
    def _identify_optimization_opportunities(self, network: Dict[str, Any], 
                                          path_nodes: List[str], 
                                          path_connections: List[Dict[str, Any]],
                                          metrics: Dict[str, float],
                                          bottlenecks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify optimization opportunities for a neural pathway.
        
        Args:
            network: Processed network structure
            path_nodes: List of node IDs in the pathway
            path_connections: List of connections along the pathway
            metrics: Calculated pathway metrics
            bottlenecks: Identified bottlenecks
            
        Returns:
            Dictionary mapping optimization strategies to lists of opportunities
        """
        opportunities = {
            "pruning": [],
            "strengthening": [],
            "rerouting": [],
            "consolidation": [],
            "expansion": [],
            "balancing": []
        }
        
        # Return empty opportunities for invalid pathways
        if len(path_nodes) < 2 or not path_connections:
            return opportunities
        
        # 1. Pruning opportunities
        
        # Identify low-value connections to nodes in the pathway
        for node_id in path_nodes:
            if node_id in network["adjacency"]:
                # Look for incoming connections not in the primary path
                for edge in network["adjacency"][node_id]["incoming"]:
                    source = edge["source"]
                    conn = edge["connection"]
                    
                    # Skip if the connection is part of the primary path
                    is_in_path = False
                    for path_conn in path_connections:
                        if conn.get("id") == path_conn.get("id"):
                            is_in_path = True
                            break
                    
                    if not is_in_path and conn.get("weight", 0.5) < 0.3:
                        opportunities["pruning"].append({
                            "connection_id": conn.get("id"),
                            "source": source,
                            "target": node_id,
                            "weight": conn.get("weight", 0.5),
                            "reason": "low_value_connection"
                        })
        
        # 2. Strengthening opportunities
        
        # Strengthen critical connections, especially bottlenecks
        for bottleneck in bottlenecks:
            if bottleneck["type"] == "weak_connection":
                opportunities["strengthening"].append({
                    "connection_id": bottleneck.get("connection_id"),
                    "source": bottleneck.get("source"),
                    "target": bottleneck.get("target"),
                    "current_weight": bottleneck.get("weight", 0),
                    "suggested_weight": min(1.0, bottleneck.get("weight", 0) * 1.5),
                    "reason": "bottleneck_connection"
                })
        
        # Strengthen important connections with moderate weights
        for i, connection in enumerate(path_connections):
            weight = connection.get("weight", 0.5)
            
            # Consider strengthening if in the middle range
            if 0.4 <= weight <= 0.7:
                # Check importance based on position
                is_important = False
                
                if i == 0 or i == len(path_connections) - 1:
                    # First and last connections are important
                    is_important = True
                elif i > 0 and i < len(path_connections) - 1:
                    # Check if it's in an important segment
                    prev_weight = path_connections[i - 1].get("weight", 0.5)
                    next_weight = path_connections[i + 1].get("weight", 0.5)
                    
                    if prev_weight > 0.7 and next_weight > 0.7:
                        # Connection between two strong connections
                        is_important = True
                
                if is_important:
                    opportunities["strengthening"].append({
                        "connection_id": connection.get("id"),
                        "source": connection.get("source"),
                        "target": connection.get("target"),
                        "current_weight": weight,
                        "suggested_weight": min(1.0, weight * 1.3),
                        "reason": "important_connection"
                    })
        
        # 3. Rerouting opportunities
        
        # Find alternative routes around bottlenecks
        for bottleneck in bottlenecks:
            if bottleneck["type"] == "weak_connection":
                source = bottleneck.get("source")
                target = bottleneck.get("target")
                
                # Look for existing alternative routes
                alt_routes = []
                
                if source in network["adjacency"] and target in network:
                    # Try to find a two-step path (source -> intermediate -> target)
                    for out_edge in network["adjacency"][source]["outgoing"]:
                        intermediate = out_edge["target"]
                        
                        # Skip if intermediate is the direct target
                        if intermediate == target:
                            continue
                        
                        # Check if intermediate connects to target
                        if intermediate in network["adjacency"]:
                            for next_edge in network["adjacency"][intermediate]["outgoing"]:
                                if next_edge["target"] == target:
                                    # Found an alternative route
                                    alt_routes.append({
                                        "path": [source, intermediate, target],
                                        "connections": [
                                            out_edge["connection"],
                                            next_edge["connection"]
                                        ],
                                        "total_weight": (
                                            out_edge["connection"].get("weight", 0.5) * 
                                            next_edge["connection"].get("weight", 0.5)
                                        )
                                    })
                
                # Suggest rerouting if viable alternatives exist
                if alt_routes:
                    # Sort by total weight
                    alt_routes.sort(key=lambda x: x["total_weight"], reverse=True)
                    best_route = alt_routes[0]
                    
                    if best_route["total_weight"] > bottleneck.get("weight", 0):
                        opportunities["rerouting"].append({
                            "bottleneck_id": bottleneck.get("connection_id"),
                            "alternative_path": best_route["path"],
                            "alternative_connections": [conn.get("id") for conn in best_route["connections"]],
                            "current_weight": bottleneck.get("weight", 0),
                            "alternative_weight": best_route["total_weight"],
                            "improvement_ratio": best_route["total_weight"] / max(0.001, bottleneck.get("weight", 0)),
                            "reason": "better_alternative_exists"
                        })
        
        # 4. Consolidation opportunities
        
        # Find parallel paths that could be consolidated
        # This is complex - we'll implement a simplified version
        visited_paths = set()
        
        for i, node1 in enumerate(path_nodes):
            for j in range(i + 2, min(i + 4, len(path_nodes))):
                node2 = path_nodes[j]
                path_key = f"{node1}_{node2}"
                
                if path_key in visited_paths:
                    continue
                
                visited_paths.add(path_key)
                
                # Check for multiple paths between node1 and node2
                paths = []
                self._find_paths_between(network, node1, node2, [], set(), paths, max_depth=3)
                
                if len(paths) > 1:
                    # Multiple paths exist - potential consolidation
                    opportunities["consolidation"].append({
                        "start_node": node1,
                        "end_node": node2,
                        "num_paths": len(paths),
                        "paths": paths[:3],  # Limit to top 3 for simplicity
                        "reason": "parallel_paths_exist"
                    })
        
        # 5. Expansion opportunities
        
        # Look for critical nodes with no alternative paths
        critical_nodes = []
        
        for i, node_id in enumerate(path_nodes):
            if i == 0 or i == len(path_nodes) - 1:
                continue  # Skip start and end nodes
            
            # Check if there's an alternative path around this node
            if i > 0 and i < len(path_nodes) - 1:
                prev_node = path_nodes[i - 1]
                next_node = path_nodes[i + 1]
                
                # Try to find any path from prev to next that doesn't include this node
                alt_paths = []
                self._find_paths_between(
                    network, prev_node, next_node, [], set([node_id]), alt_paths, max_depth=3
                )
                
                if not alt_paths:
                    # No alternative exists - this is a critical node
                    critical_nodes.append({
                        "node_id": node_id,
                        "position": i,
                        "prev_node": prev_node,
                        "next_node": next_node
                    })
        
        # Suggest expansion for critical nodes
        for critical in critical_nodes:
            opportunities["expansion"].append({
                "node_id": critical["node_id"],
                "prev_node": critical["prev_node"],
                "next_node": critical["next_node"],
                "suggestion": "create_bypass_connection",
                "reason": "single_point_of_failure"
            })
        
        # 6. Balancing opportunities
        
        # Check for uneven distribution of weights
        weights = [conn.get("weight", 0.5) for conn in path_connections]
        if len(weights) > 2:
            weight_variance = self._calculate_variance(weights)
            
            if weight_variance > 0.04:  # Significant variance
                opportunities["balancing"].append({
                    "path_range": [0, len(path_connections) - 1],
                    "weight_variance": weight_variance,
                    "min_weight": min(weights),
                    "max_weight": max(weights),
                    "suggestion": "equalize_weights",
                    "reason": "uneven_signal_propagation"
                })
        
        return opportunities
    
    def _calculate_variance(self, values: List[float]) -> float:
        """
        Calculate variance of a list of values.
        
        Args:
            values: List of values
            
        Returns:
            Variance
        """
        if not values:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def _find_paths_between(self, network: Dict[str, Any], 
                          start: str, end: str, 
                          current_path: List[str],
                          excluded_nodes: Set[str],
                          result_paths: List[List[str]],
                          max_depth: int) -> None:
        """
        Find all paths between two nodes using DFS.
        
        Args:
            network: Processed network
            start: Starting node ID
            end: Ending node ID
            current_path: Current path being explored
            excluded_nodes: Nodes to exclude from search
            result_paths: List to collect found paths
            max_depth: Maximum recursion depth
            
        Returns:
            None (modifies result_paths in place)
        """
        # Add current node to path
        new_path = current_path + [start]
        
        # Check if we've reached the end
        if start == end:
            result_paths.append(new_path)
            return
        
        # Stop if max depth reached
        if len(new_path) > max_depth:
            return
        
        # Explore outgoing connections
        if start in network["adjacency"]:
            for edge in network["adjacency"][start]["outgoing"]:
                next_node = edge["target"]
                
                # Skip if next node is excluded or already in path
                if next_node in excluded_nodes or next_node in new_path:
                    continue
                
                # Continue DFS
                self._find_paths_between(
                    network, next_node, end, new_path, excluded_nodes, result_paths, max_depth
                )
    
    def _calculate_network_metrics(self, network: Dict[str, Any], 
                                pathways: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate network-level metrics.
        
        Args:
            network: Processed network structure
            pathways: List of neural pathways
            
        Returns:
            Dictionary with network metrics
        """
        metrics = {}
        
        # Count nodes and connections
        num_nodes = len(network["nodes"])
        num_connections = len(network["connections"])
        
        # Network density
        if num_nodes > 1:
            max_possible_connections = num_nodes * (num_nodes - 1)
            metrics["network_density"] = num_connections / max_possible_connections
        else:
            metrics["network_density"] = 0
        
        # Average node degree
        total_degree = 0
        for node_id in network["adjacency"]:
            in_degree = len(network["adjacency"][node_id]["incoming"])
            out_degree = len(network["adjacency"][node_id]["outgoing"])
            total_degree += in_degree + out_degree
        
        if num_nodes > 0:
            metrics["avg_node_degree"] = total_degree / num_nodes
        else:
            metrics["avg_node_degree"] = 0
        
        # Average connection weight
        total_weight = sum(conn.get("weight", 0.5) for conn in network["connections"])
        if num_connections > 0:
            metrics["avg_connection_weight"] = total_weight / num_connections
        else:
            metrics["avg_connection_weight"] = 0
        
        # Pathway coverage
        # What percentage of nodes are included in pathways
        pathway_nodes = set()
        for pathway in pathways:
            path = pathway.get("path", [])
            for node_id in path:
                pathway_nodes.add(node_id)
        
        metrics["pathway_coverage"] = len(pathway_nodes) / max(1, num_nodes)
        
        # Average pathway overlap
        # Measure how much pathways share nodes
        if len(pathways) > 1:
            overlap_sum = 0
            comparison_count = 0
            
            for i, p1 in enumerate(pathways):
                path1 = set(p1.get("path", []))
                if not path1:
                    continue
                    
                for j in range(i+1, len(pathways)):
                    p2 = pathways[j]
                    path2 = set(p2.get("path", []))
                    if not path2:
                        continue
                    
                    # Calculate Jaccard similarity
                    intersection = len(path1.intersection(path2))
                    union = len(path1.union(path2))
                    
                    if union > 0:
                        overlap_sum += intersection / union
                        comparison_count += 1
            
            if comparison_count > 0:
                metrics["avg_pathway_overlap"] = overlap_sum / comparison_count
            else:
                metrics["avg_pathway_overlap"] = 0
        else:
            metrics["avg_pathway_overlap"] = 0
        
        return metrics
    
    def _create_optimization_plans(self, network: Dict[str, Any], 
                                pathways: List[Dict[str, Any]],
                                analysis: Dict[str, Any],
                                optimization_goals: Dict[str, float],
                                config: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Create optimization plans for each pathway.
        
        Args:
            network: Processed network structure
            pathways: List of neural pathways
            analysis: Pathway analysis results
            optimization_goals: Target metrics
            config: Configuration parameters
            
        Returns:
            Dictionary with optimization plans
        """
        allowed_strategies = config.get("allowed_strategies", [])
        optimization_intensity = config.get("optimization_intensity", 0.7)
        
        # Overall plans
        plans = {
            "pruning": [],
            "strengthening": [],
            "rerouting": [],
            "consolidation": [],
            "expansion": [],
            "balancing": []
        }
        
        # Process each pathway
        for pathway_analysis in analysis.get("pathway_analyses", []):
            pathway_id = pathway_analysis["pathway_id"]
            
            # Find the corresponding pathway
            pathway = None
            for p in pathways:
                if p.get("id") == pathway_id:
                    pathway = p
                    break
            
            if not pathway:
                continue
            
            # Check which metrics need improvement
            metrics_to_improve = {}
            
            for metric, value in pathway_analysis["metrics"].items():
                if metric in optimization_goals:
                    target = optimization_goals[metric]
                    
                    # Check if current value is significantly below target
                    if metric in ["throughput", "pattern_stability", "energy_efficiency", "robustness", "integration_level"]:
                        if value < target * 0.9:
                            metrics_to_improve[metric] = (target - value) / target
                    elif metric == "signal_clarity":
                        if value < target * 0.8:
                            metrics_to_improve[metric] = (target - value) / target
            
            # Prioritize metrics to improve
            if not metrics_to_improve:
                continue  # No improvements needed
            
            prioritized_metrics = sorted(
                metrics_to_improve.items(), key=lambda x: x[1], reverse=True
            )
            
            # Map metrics to strategies
            for metric, importance in prioritized_metrics:
                if metric == "throughput":
                    strategies = ["strengthening", "rerouting"]
                elif metric == "signal_clarity":
                    strategies = ["pruning", "strengthening"]
                elif metric == "pattern_stability":
                    strategies = ["balancing", "strengthening"]
                elif metric == "energy_efficiency":
                    strategies = ["pruning", "consolidation"]
                elif metric == "robustness":
                    strategies = ["expansion", "rerouting"]
                elif metric == "integration_level":
                    strategies = ["expansion", "balancing"]
                else:
                    strategies = []
                
                # Filter by allowed strategies
                if allowed_strategies:
                    strategies = [s for s in strategies if s in allowed_strategies]
                
                # Add plans based on opportunities
                for strategy in strategies:
                    opportunities = pathway_analysis["optimization_opportunities"].get(strategy, [])
                    
                    for opportunity in opportunities:
                        # Create plan
                        plan = {
                            "pathway_id": pathway_id,
                            "metric_to_improve": metric,
                            "importance": importance,
                            "opportunity": opportunity,
                            "intensity": optimization_intensity
                        }
                        
                        plans[strategy].append(plan)
        
        # Sort plans by importance
        for strategy in plans:
            plans[strategy].sort(key=lambda x: x["importance"], reverse=True)
        
        return plans
    
    def _apply_optimizations(self, network: Dict[str, Any], 
                          pathways: List[Dict[str, Any]],
                          optimization_plans: Dict[str, List[Dict[str, Any]]],
                          config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Apply optimizations to the network and pathways.
        
        Args:
            network: Processed network structure
            pathways: List of neural pathways
            optimization_plans: Optimization plans
            config: Configuration parameters
            
        Returns:
            Tuple of (optimized_network, optimized_pathways, optimization_history)
        """
        # Create deep copies to avoid modifying originals
        optimized_network = copy.deepcopy(network)
        optimized_pathways = copy.deepcopy(pathways)
        
        # Track optimization history
        optimization_history = []
        
        # Track which connections have been modified
        modified_connections = set()
        
        # Apply optimizations by strategy
        max_iterations = config.get("max_iterations", 5)
        allow_topology_changes = config.get("allow_topology_changes", True)
        preserve_critical_paths = config.get("preserve_critical_paths", True)
        
        # Limit number of optimizations per strategy
        strategy_limits = {
            "pruning": min(5, max_iterations),
            "strengthening": min(10, max_iterations * 2),
            "rerouting": min(3, max_iterations),
            "consolidation": min(2, max_iterations // 2),
            "expansion": min(3, max_iterations),
            "balancing": min(5, max_iterations)
        }
        
        # Apply strategies in specific order for best results
        strategy_order = [
            "pruning",        # First remove noise
            "strengthening",  # Then strengthen important connections
            "rerouting",      # Then reroute through better paths
            "expansion",      # Then add new connections where needed
            "consolidation",  # Then consolidate similar pathways
            "balancing"       # Finally balance the weights
        ]
        
        # Apply each strategy
        for strategy in strategy_order:
            plans = optimization_plans.get(strategy, [])
            applied_count = 0
            
            for plan in plans:
                if applied_count >= strategy_limits[strategy]:
                    break
                
                # Extract plan details
                pathway_id = plan["pathway_id"]
                metric = plan["metric_to_improve"]
                intensity = plan["intensity"]
                opportunity = plan["opportunity"]
                
                # Apply the optimization based on strategy
                result = None
                
                if strategy == "pruning":
                    result = self._apply_pruning(
                        optimized_network, pathway_id, opportunity, intensity, 
                        preserve_critical_paths
                    )
                
                elif strategy == "strengthening":
                    result = self._apply_strengthening(
                        optimized_network, pathway_id, opportunity, intensity
                    )
                
                elif strategy == "rerouting":
                    if allow_topology_changes:
                        result = self._apply_rerouting(
                            optimized_network, optimized_pathways, pathway_id, 
                            opportunity, intensity
                        )
                
                elif strategy == "expansion":
                    if allow_topology_changes:
                        result = self._apply_expansion(
                            optimized_network, optimized_pathways, pathway_id, 
                            opportunity, intensity
                        )
                
                elif strategy == "consolidation":
                    if allow_topology_changes:
                        result = self._apply_consolidation(
                            optimized_network, optimized_pathways, pathway_id, 
                            opportunity, intensity
                        )
                
                elif strategy == "balancing":
                    result = self._apply_balancing(
                        optimized_network, pathway_id, opportunity, intensity
                    )
                
                # Record the optimization if successful
                if result and result.get("success", False):
                    # Check if this modifies already modified connections
                    conn_ids = result.get("modified_connections", [])
                    skip = False
                    
                    for conn_id in conn_ids:
                        if conn_id in modified_connections:
                            # Skip if we've already modified this connection a lot
                            modifications = sum(
                                1 for hist in optimization_history 
                                if conn_id in hist.get("modified_connections", [])
                            )
                            
                            if modifications >= 2:  # Limit modifications per connection
                                skip = True
                                break
                    
                    if not skip:
                        # Record the optimization
                        history_entry = {
                            "strategy": strategy,
                            "pathway_id": pathway_id,
                            "metric": metric,
                            "details": result,
                            "modified_connections": conn_ids
                        }
                        
                        optimization_history.append(history_entry)
                        applied_count += 1
                        
                        # Add to modified connections
                        for conn_id in conn_ids:
                            modified_connections.add(conn_id)
        
        # Finalize the network (rebuild adjacency list)
        optimized_network = self._rebuild_network(optimized_network)
        
        # Update pathway connections if needed
        if allow_topology_changes:
            optimized_pathways = self._update_pathways(optimized_network, optimized_pathways)
        
        return optimized_network, optimized_pathways, optimization_history
    
    def _apply_pruning(self, network: Dict[str, Any], 
                    pathway_id: str, 
                    opportunity: Dict[str, Any],
                    intensity: float,
                    preserve_critical: bool) -> Dict[str, Any]:
        """
        Apply pruning optimization.
        
        Args:
            network: Network to optimize
            pathway_id: ID of the pathway being optimized
            opportunity: Pruning opportunity details
            intensity: Optimization intensity (0-1)
            preserve_critical: Whether to preserve critical paths
            
        Returns:
            Dictionary with results of the optimization
        """
        conn_id = opportunity.get("connection_id")
        
        # Find the connection
        connection = None
        for conn in network["connections"]:
            if conn.get("id") == conn_id:
                connection = conn
                break
        
        if not connection:
            return {"success": False, "reason": "connection_not_found"}
        
        # Check if this is a critical connection (part of a critical path)
        if preserve_critical:
            source = connection.get("source")
            target = connection.get("target")
            
            # Check if there's an alternative path
            if source in network["adjacency"] and target in network["adjacency"]:
                alt_paths = []
                self._find_paths_between(
                    network, source, target, [], set(), alt_paths, max_depth=3
                )
                
                # Remove the direct path
                alt_paths = [p for p in alt_paths if len(p) > 2 or (len(p) == 2 and p[0] != source and p[1] != target)]
                
                if not alt_paths:
                    # No alternative path, this might be critical
                    return {"success": False, "reason": "critical_connection"}
        
        # Apply pruning based on intensity
        original_weight = connection.get("weight", 0.5)
        
        if intensity > 0.8:
            # High intensity - remove the connection
            network["connections"].remove(connection)
            
            return {
                "success": True,
                "action": "removed_connection",
                "connection_id": conn_id,
                "original_weight": original_weight,
                "modified_connections": [conn_id]
            }
        else:
            # Lower intensity - reduce the weight
            reduction_factor = 0.5 + (intensity * 0.5)  # 0.5 to 1.0
            new_weight = original_weight * (1 - reduction_factor)
            connection["weight"] = max(0.1, new_weight)  # Ensure minimum weight
            
            return {
                "success": True,
                "action": "reduced_weight",
                "connection_id": conn_id,
                "original_weight": original_weight,
                "new_weight": connection["weight"],
                "modified_connections": [conn_id]
            }
    
    def _apply_strengthening(self, network: Dict[str, Any], 
                          pathway_id: str, 
                          opportunity: Dict[str, Any],
                          intensity: float) -> Dict[str, Any]:
        """
        Apply strengthening optimization.
        
        Args:
            network: Network to optimize
            pathway_id: ID of the pathway being optimized
            opportunity: Strengthening opportunity details
            intensity: Optimization intensity (0-1)
            
        Returns:
            Dictionary with results of the optimization
        """
        conn_id = opportunity.get("connection_id")
        
        # Find the connection
        connection = None
        for conn in network["connections"]:
            if conn.get("id") == conn_id:
                connection = conn
                break
        
        if not connection:
            return {"success": False, "reason": "connection_not_found"}
        
        # Apply strengthening based on intensity and suggestion
        original_weight = connection.get("weight", 0.5)
        suggested_weight = opportunity.get("suggested_weight", min(1.0, original_weight * 1.5))
        
        # Calculate new weight
        weight_increase = (suggested_weight - original_weight) * intensity
        new_weight = min(1.0, original_weight + weight_increase)
        
        # Update connection
        connection["weight"] = new_weight
        
        return {
            "success": True,
            "action": "increased_weight",
            "connection_id": conn_id,
            "original_weight": original_weight,
            "new_weight": new_weight,
            "modified_connections": [conn_id]
        }
    
    def _apply_rerouting(self, network: Dict[str, Any], 
                      pathways: List[Dict[str, Any]],
                      pathway_id: str, 
                      opportunity: Dict[str, Any],
                      intensity: float) -> Dict[str, Any]:
        """
        Apply rerouting optimization.
        
        Args:
            network: Network to optimize
            pathways: Pathways to update
            pathway_id: ID of the pathway being optimized
            opportunity: Rerouting opportunity details
            intensity: Optimization intensity (0-1)
            
        Returns:
            Dictionary with results of the optimization
        """
        bottleneck_id = opportunity.get("bottleneck_id")
        alternative_path = opportunity.get("alternative_path", [])
        alternative_connections = opportunity.get("alternative_connections", [])
        
        if len(alternative_path) < 3 or not alternative_connections:
            return {"success": False, "reason": "invalid_alternative"}
        
        # Find the bottleneck connection
        bottleneck = None
        for conn in network["connections"]:
            if conn.get("id") == bottleneck_id:
                bottleneck = conn
                break
        
        if not bottleneck:
            return {"success": False, "reason": "bottleneck_not_found"}
        
        # Find the alternative connections
        alt_conns = []
        for conn_id in alternative_connections:
            for conn in network["connections"]:
                if conn.get("id") == conn_id:
                    alt_conns.append(conn)
                    break
        
        if len(alt_conns) != len(alternative_connections):
            return {"success": False, "reason": "alternative_connections_not_found"}
        
        # Modify weights based on intensity
        original_weights = {}
        new_weights = {}
        
        # Reduce bottleneck weight
        original_weights[bottleneck_id] = bottleneck.get("weight", 0.5)
        
        if intensity > 0.8:
            # High intensity - significantly reduce bottleneck
            new_weights[bottleneck_id] = max(0.1, original_weights[bottleneck_id] * 0.5)
        else:
            # Lower intensity - moderately reduce bottleneck
            reduction = 0.2 + (intensity * 0.3)  # 0.2 to 0.5
            new_weights[bottleneck_id] = max(0.2, original_weights[bottleneck_id] * (1 - reduction))
        
        bottleneck["weight"] = new_weights[bottleneck_id]
        
        # Strengthen alternative connections
        for conn in alt_conns:
            conn_id = conn.get("id")
            original_weights[conn_id] = conn.get("weight", 0.5)
            
            # Increase based on intensity
            increase = 0.1 + (intensity * 0.4)  # 0.1 to 0.5
            new_weights[conn_id] = min(1.0, original_weights[conn_id] * (1 + increase))
            
            conn["weight"] = new_weights[conn_id]
        
        # Update pathway if found
        pathway = None
        for p in pathways:
            if p.get("id") == pathway_id:
                pathway = p
                break
        
        if pathway:
            # Check if we need to update the path
            path = pathway.get("path", [])
            
            # Only update if the bottleneck was significantly weakened
            if new_weights[bottleneck_id] < 0.3 and intensity > 0.7:
                # Find bottleneck position
                src = bottleneck.get("source")
                tgt = bottleneck.get("target")
                
                if src in path and tgt in path:
                    src_idx = path.index(src)
                    tgt_idx = path.index(tgt)
                    
                    if src_idx + 1 == tgt_idx:
                        # Replace with alternative path
                        alt_path = alternative_path
                        if alt_path[0] != src:
                            alt_path = alt_path[::-1]  # Reverse if needed
                        
                        # Replace the segment
                        new_path = path[:src_idx + 1] + alt_path[1:-1] + path[tgt_idx:]
                        pathway["path"] = new_path
        
        return {
            "success": True,
            "action": "rerouted_pathway",
            "bottleneck_id": bottleneck_id,
            "alternative_path": alternative_path,
            "original_weights": original_weights,
            "new_weights": new_weights,
            "modified_connections": list(original_weights.keys())
        }
    
    def _apply_expansion(self, network: Dict[str, Any], 
                      pathways: List[Dict[str, Any]],
                      pathway_id: str, 
                      opportunity: Dict[str, Any],
                      intensity: float) -> Dict[str, Any]:
        """
        Apply expansion optimization.
        
        Args:
            network: Network to optimize
            pathways: Pathways to update
            pathway_id: ID of the pathway being optimized
            opportunity: Expansion opportunity details
            intensity: Optimization intensity (0-1)
            
        Returns:
            Dictionary with results of the optimization
        """
        node_id = opportunity.get("node_id")
        prev_node = opportunity.get("prev_node")
        next_node = opportunity.get("next_node")
        suggestion = opportunity.get("suggestion")
        
        if suggestion != "create_bypass_connection" or not prev_node or not next_node:
            return {"success": False, "reason": "unsupported_suggestion"}
        
        # Check if bypass already exists
        bypass_exists = False
        for conn in network["connections"]:
            if conn.get("source") == prev_node and conn.get("target") == next_node:
                bypass_exists = True
                break
        
        if bypass_exists:
            return {"success": False, "reason": "bypass_already_exists"}
        
        # Create a new connection ID
        new_conn_id = f"conn_{len(network['connections'])}"
        
        # Create the bypass connection
        # Weight depends on intensity - higher intensity = stronger bypass
        bypass_weight = 0.3 + (intensity * 0.3)  # 0.3 to 0.6
        
        new_connection = {
            "id": new_conn_id,
            "source": prev_node,
            "target": next_node,
            "weight": bypass_weight,
            "type": "bypass",
            "created_by": "optimizer"
        }
        
        # Add to network
        network["connections"].append(new_connection)
        
        return {
            "success": True,
            "action": "added_bypass",
            "node_bypassed": node_id,
            "new_connection_id": new_conn_id,
            "source": prev_node,
            "target": next_node,
            "weight": bypass_weight,
            "modified_connections": [new_conn_id]
        }
    
    def _apply_consolidation(self, network: Dict[str, Any], 
                          pathways: List[Dict[str, Any]],
                          pathway_id: str, 
                          opportunity: Dict[str, Any],
                          intensity: float) -> Dict[str, Any]:
        """
        Apply consolidation optimization.
        
        Args:
            network: Network to optimize
            pathways: Pathways to update
            pathway_id: ID of the pathway being optimized
            opportunity: Consolidation opportunity details
            intensity: Optimization intensity (0-1)
            
        Returns:
            Dictionary with results of the optimization
        """
        start_node = opportunity.get("start_node")
        end_node = opportunity.get("end_node")
        paths = opportunity.get("paths", [])
        
        if not start_node or not end_node or len(paths) < 2:
            return {"success": False, "reason": "invalid_opportunity"}
        
        # Find the strongest path
        strongest_path = None
        strongest_score = 0
        
        for path in paths:
            # Calculate path strength
            strength = 1.0
            path_connections = []
            
            for i in range(len(path) - 1):
                src = path[i]
                tgt = path[i + 1]
                
                # Find connection
                conn = None
                for c in network["connections"]:
                    if c.get("source") == src and c.get("target") == tgt:
                        conn = c
                        break
                
                if conn:
                    path_connections.append(conn)
                    strength *= conn.get("weight", 0.5)
            
            # Check if this is the strongest
            if strength > strongest_score:
                strongest_score = strength
                strongest_path = {"path": path, "connections": path_connections}
        
        if not strongest_path:
            return {"success": False, "reason": "no_valid_paths"}
        
        # Apply consolidation based on intensity
        # Strengthen the strongest path
        modified_connections = []
        
        for conn in strongest_path["connections"]:
            conn_id = conn.get("id")
            original_weight = conn.get("weight", 0.5)
            
            # Increase weight based on intensity
            increase = 0.1 + (intensity * 0.3)  # 0.1 to 0.4
            new_weight = min(1.0, original_weight * (1 + increase))
            
            conn["weight"] = new_weight
            modified_connections.append(conn_id)
        
        # Weaken alternative paths if intensity is high
        if intensity > 0.6:
            for path in paths:
                if path == strongest_path["path"]:
                    continue  # Skip the strongest path
                
                # Weaken connections in this path
                for i in range(len(path) - 1):
                    src = path[i]
                    tgt = path[i + 1]
                    
                    # Find connection
                    for conn in network["connections"]:
                        if conn.get("source") == src and conn.get("target") == tgt:
                            conn_id = conn.get("id")
                            
                            # Skip if already modified
                            if conn_id in modified_connections:
                                continue
                            
                            original_weight = conn.get("weight", 0.5)
                            
                            # Decrease weight based on intensity
                            decrease = 0.1 + (intensity * 0.3)  # 0.1 to 0.4
                            new_weight = max(0.2, original_weight * (1 - decrease))
                            
                            conn["weight"] = new_weight
                            modified_connections.append(conn_id)
        
        return {
            "success": True,
            "action": "consolidated_pathways",
            "start_node": start_node,
            "end_node": end_node,
            "strongest_path": strongest_path["path"],
            "modified_connections": modified_connections
        }
    
    def _apply_balancing(self, network: Dict[str, Any], 
                      pathway_id: str, 
                      opportunity: Dict[str, Any],
                      intensity: float) -> Dict[str, Any]:
        """
        Apply balancing optimization.
        
        Args:
            network: Network to optimize
            pathway_id: ID of the pathway being optimized
            opportunity: Balancing opportunity details
            intensity: Optimization intensity (0-1)
            
        Returns:
            Dictionary with results of the optimization
        """
        # Find the pathway
        pathway = None
        for p in network.get("pathways", []):
            if p.get("id") == pathway_id:
                pathway = p
                break
        
        if not pathway:
            # Try the original pathways list if available
            return {"success": False, "reason": "pathway_not_found"}
        
        path_range = opportunity.get("path_range", [0, 0])
        if path_range[1] <= path_range[0]:
            return {"success": False, "reason": "invalid_range"}
        
        # Get the connections in the range
        path = pathway.get("path", [])
        if len(path) < 2:
            return {"success": False, "reason": "invalid_path"}
        
        start_idx = max(0, min(path_range[0], len(path) - 2))
        end_idx = max(start_idx + 1, min(path_range[1], len(path) - 1))
        
        connections_to_balance = []
        for i in range(start_idx, end_idx):
            src = path[i]
            tgt = path[i + 1]
            
            # Find connection
            for conn in network["connections"]:
                if conn.get("source") == src and conn.get("target") == tgt:
                    connections_to_balance.append(conn)
                    break
        
        if not connections_to_balance:
            return {"success": False, "reason": "no_connections_in_range"}
        
        # Calculate target weight (weighted average based on intensity)
        weights = [conn.get("weight", 0.5) for conn in connections_to_balance]
        avg_weight = sum(weights) / len(weights)
        
        # Higher intensity = more uniform balancing
        modified_connections = []
        original_weights = {}
        new_weights = {}
        
        for conn in connections_to_balance:
            conn_id = conn.get("id")
            original_weight = conn.get("weight", 0.5)
            original_weights[conn_id] = original_weight
            
            # Calculate new weight (blend original with average)
            blend_factor = 0.3 + (intensity * 0.6)  # 0.3 to 0.9
            new_weight = (original_weight * (1 - blend_factor)) + (avg_weight * blend_factor)
            
            conn["weight"] = new_weight
            new_weights[conn_id] = new_weight
            modified_connections.append(conn_id)
        
        return {
            "success": True,
            "action": "balanced_weights",
            "path_range": path_range,
            "average_weight": avg_weight,
            "original_weights": original_weights,
            "new_weights": new_weights,
            "modified_connections": modified_connections
        }
    
    def _rebuild_network(self, network: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rebuild the network adjacency structure after modifications.
        
        Args:
            network: Modified network structure
            
        Returns:
            Updated network with rebuilt adjacency list
        """
        # Create new adjacency list
        adjacency = {}
        
        for node in network["nodes"]:
            node_id = node["id"]
            adjacency[node_id] = {
                "outgoing": [],
                "incoming": []
            }
        
        for conn in network["connections"]:
            source = conn.get("source")
            target = conn.get("target")
            
            if source in adjacency:
                adjacency[source]["outgoing"].append({
                    "target": target,
                    "connection": conn
                })
            
            if target in adjacency:
                adjacency[target]["incoming"].append({
                    "source": source,
                    "connection": conn
                })
        
        network["adjacency"] = adjacency
        return network
    
    def _update_pathways(self, network: Dict[str, Any], 
                      pathways: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update pathways based on network modifications.
        
        Args:
            network: Updated network structure
            pathways: Original pathways
            
        Returns:
            Updated pathways
        """
        updated_pathways = []
        
        for pathway in pathways:
            path = pathway.get("path", [])
            
            if len(path) < 2:
                updated_pathways.append(pathway)
                continue
            
            # Check if path connections still exist
            need_update = False
            
            for i in range(len(path) - 1):
                src = path[i]
                tgt = path[i + 1]
                
                # Check if connection exists
                connection_exists = False
                if src in network["adjacency"]:
                    for edge in network["adjacency"][src]["outgoing"]:
                        if edge["target"] == tgt:
                            connection_exists = True
                            break
                
                if not connection_exists:
                    need_update = True
                    break
            
            if need_update:
                # Try to find an alternative path
                start = path[0]
                end = path[-1]
                
                alt_paths = []
                self._find_paths_between(network, start, end, [], set(), alt_paths, max_depth=len(path) + 1)
                
                if alt_paths:
                    # Use the shortest path
                    alt_paths.sort(key=len)
                    new_pathway = dict(pathway)
                    new_pathway["path"] = alt_paths[0]
                    updated_pathways.append(new_pathway)
                else:
                    # Keep original if no alternative
                    updated_pathways.append(pathway)
            else:
                # Keep original
                updated_pathways.append(pathway)
        
        return updated_pathways


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Neural Path Optimizer (KA-54) on the provided data.
    
    Args:
        data: A dictionary containing network structure, pathways, and optional configuration
        
    Returns:
        Dictionary with optimization results
    """
    network = data.get("network", {})
    pathways = data.get("pathways", [])
    optimization_goals = data.get("optimization_goals")
    config = data.get("config")
    
    # Generate sample data if requested
    if not network and data.get("generate_sample", False):
        network, pathways = generate_sample_data(
            data.get("template", "basic"),
            data.get("size", "medium")
        )
    
    # Validate inputs
    if not network:
        return {
            "algorithm": "KA-54",
            "success": False,
            "error": "No network structure provided",
            "timestamp": time.time()
        }
    
    if not pathways:
        return {
            "algorithm": "KA-54",
            "success": False,
            "error": "No pathways provided for optimization",
            "timestamp": time.time()
        }
    
    optimizer = NeuralPathOptimizer()
    
    try:
        result = optimizer.optimize_neural_pathways(network, pathways, optimization_goals, config)
        
        if not result.get("success", False):
            return {
                "algorithm": "KA-54",
                "success": False,
                "error": result.get("error", "Unknown error"),
                "timestamp": time.time()
            }
        
        # Prepare output (limit size for very large networks)
        output = {
            "algorithm": "KA-54",
            "success": True,
            "improvement": result["improvement"],
            "optimization_count": len(result["optimization_history"]),
            "initial_metrics": result["initial_analysis"]["overall_metrics"],
            "final_metrics": result["final_analysis"]["overall_metrics"],
            "timestamp": time.time()
        }
        
        # Include optimized network if not too large
        if len(result["optimized_network"]["nodes"]) <= 100:
            output["optimized_network"] = result["optimized_network"]
            output["optimized_pathways"] = result["optimized_pathways"]
        else:
            output["network_size"] = {
                "nodes": len(result["optimized_network"]["nodes"]),
                "connections": len(result["optimized_network"]["connections"])
            }
            output["message"] = "Network too large to include in response. Access specific elements if needed."
        
        # Include optimization history
        output["optimization_history"] = result["optimization_history"]
        
        return output
    
    except Exception as e:
        logger.error(f"Error in KA-54 Neural Path Optimizer: {str(e)}")
        return {
            "algorithm": "KA-54",
            "success": False,
            "error": str(e),
            "timestamp": time.time()
        }


def generate_sample_data(template: str, size: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Generate sample data for testing.
    
    Args:
        template: Network template to use
        size: Size of the network (small, medium, large)
        
    Returns:
        Tuple of (network, pathways)
    """
    if template not in ["basic", "densely_connected", "bottlenecked", "unbalanced"]:
        template = "basic"
    
    if size not in ["small", "medium", "large"]:
        size = "medium"
    
    # Determine network dimensions based on size
    if size == "small":
        width = 3
        depth = 4
    elif size == "medium":
        width = 5
        depth = 6
    else:  # large
        width = 8
        depth = 10
    
    # Generate nodes in layers
    nodes = []
    node_id_map = {}
    
    for layer in range(depth):
        layer_width = width
        
        # Adjust width for specific templates
        if template == "bottlenecked" and layer == depth // 2:
            layer_width = max(1, width // 2)  # Create bottleneck
        
        for pos in range(layer_width):
            node_id = f"node_{layer}_{pos}"
            node = {
                "id": node_id,
                "layer": layer,
                "position": pos,
                "type": "input" if layer == 0 else "output" if layer == depth - 1 else "hidden"
            }
            nodes.append(node)
            node_id_map[(layer, pos)] = node_id
    
    # Generate connections
    connections = []
    conn_id = 0
    
    for layer in range(depth - 1):
        source_width = width
        target_width = width
        
        # Adjust for bottleneck template
        if template == "bottlenecked" and layer == depth // 2 - 1:
            target_width = max(1, width // 2)
        elif template == "bottlenecked" and layer == depth // 2:
            source_width = max(1, width // 2)
        
        for source_pos in range(min(source_width, len([n for n in nodes if n["layer"] == layer]))):
            source_id = node_id_map.get((layer, source_pos))
            if not source_id:
                continue
                
            # Determine connection targets based on template
            if template == "basic":
                # Each node connects to 1-2 nodes in the next layer
                for target_pos in range(max(0, source_pos - 1), min(target_width, source_pos + 2)):
                    target_id = node_id_map.get((layer + 1, target_pos))
                    if not target_id:
                        continue
                    
                    # Create connection with random weight
                    weight = random.uniform(0.4, 0.8)
                    connections.append({
                        "id": f"conn_{conn_id}",
                        "source": source_id,
                        "target": target_id,
                        "weight": weight
                    })
                    conn_id += 1
            
            elif template == "densely_connected":
                # Each node connects to all nodes in the next layer
                for target_pos in range(target_width):
                    target_id = node_id_map.get((layer + 1, target_pos))
                    if not target_id:
                        continue
                    
                    # Create connection with random weight
                    weight = random.uniform(0.3, 0.7)
                    connections.append({
                        "id": f"conn_{conn_id}",
                        "source": source_id,
                        "target": target_id,
                        "weight": weight
                    })
                    conn_id += 1
            
            elif template == "bottlenecked":
                # Connect to nodes in bottleneck layer or from bottleneck layer
                if layer == depth // 2 - 1:
                    # Many-to-few connections into bottleneck
                    for target_pos in range(target_width):
                        target_id = node_id_map.get((layer + 1, target_pos))
                        if not target_id:
                            continue
                        
                        # Create connection with random weight
                        weight = random.uniform(0.3, 0.6)  # Lower weights into bottleneck
                        connections.append({
                            "id": f"conn_{conn_id}",
                            "source": source_id,
                            "target": target_id,
                            "weight": weight
                        })
                        conn_id += 1
                elif layer == depth // 2:
                    # Few-to-many connections out of bottleneck
                    for target_pos in range(target_width):
                        target_id = node_id_map.get((layer + 1, target_pos))
                        if not target_id:
                            continue
                        
                        # Create connection with random weight
                        weight = random.uniform(0.3, 0.6)  # Lower weights out of bottleneck
                        connections.append({
                            "id": f"conn_{conn_id}",
                            "source": source_id,
                            "target": target_id,
                            "weight": weight
                        })
                        conn_id += 1
                else:
                    # Normal connections elsewhere
                    for target_pos in range(max(0, source_pos - 1), min(target_width, source_pos + 2)):
                        target_id = node_id_map.get((layer + 1, target_pos))
                        if not target_id:
                            continue
                        
                        # Create connection with random weight
                        weight = random.uniform(0.5, 0.9)
                        connections.append({
                            "id": f"conn_{conn_id}",
                            "source": source_id,
                            "target": target_id,
                            "weight": weight
                        })
                        conn_id += 1
            
            elif template == "unbalanced":
                # Create unbalanced weights within pathways
                for target_pos in range(max(0, source_pos - 1), min(target_width, source_pos + 2)):
                    target_id = node_id_map.get((layer + 1, target_pos))
                    if not target_id:
                        continue
                    
                    # Create connection with highly variable weight
                    if layer % 2 == 0:
                        # Even layers get high weights
                        weight = random.uniform(0.7, 0.9)
                    else:
                        # Odd layers get low weights
                        weight = random.uniform(0.2, 0.4)
                    
                    connections.append({
                        "id": f"conn_{conn_id}",
                        "source": source_id,
                        "target": target_id,
                        "weight": weight
                    })
                    conn_id += 1
    
    # Create network
    network = {
        "nodes": nodes,
        "connections": connections,
        "template": template,
        "size": size
    }
    
    # Generate sample pathways
    pathways = []
    
    # Create a few pathways through the network
    num_pathways = 3 if size == "small" else 5 if size == "medium" else 8
    
    for i in range(num_pathways):
        # Start with a random input node
        input_nodes = [n for n in nodes if n["layer"] == 0]
        if not input_nodes:
            continue
        
        start_node = random.choice(input_nodes)
        path = [start_node["id"]]
        
        # Build path layer by layer
        current_layer = 0
        current_id = start_node["id"]
        
        while current_layer < depth - 1:
            # Find outgoing connections from current node
            next_nodes = []
            for conn in connections:
                if conn["source"] == current_id:
                    next_nodes.append({
                        "id": conn["target"],
                        "weight": conn["weight"]
                    })
            
            if not next_nodes:
                break
            
            # Choose next node (weighted by connection strength)
            weights = [n["weight"] for n in next_nodes]
            total_weight = sum(weights)
            
            if total_weight > 0:
                # Weighted selection
                r = random.uniform(0, total_weight)
                cumulative = 0
                selected = next_nodes[0]["id"]  # Default
                
                for n, w in zip(next_nodes, weights):
                    cumulative += w
                    if r <= cumulative:
                        selected = n["id"]
                        break
            else:
                # Random selection if no weights
                selected = random.choice(next_nodes)["id"]
            
            # Add to path
            path.append(selected)
            current_id = selected
            
            # Update layer
            for node in nodes:
                if node["id"] == current_id:
                    current_layer = node["layer"]
                    break
        
        # Add pathway
        pathways.append({
            "id": f"pathway_{i}",
            "path": path,
            "importance": random.uniform(0.5, 1.0)
        })
    
    return network, pathways
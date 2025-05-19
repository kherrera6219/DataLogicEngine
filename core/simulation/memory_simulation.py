"""
UKG Memory Simulation Engine

This module implements an in-memory nested layered simulation engine for the
Universal Knowledge Graph (UKG) system, focusing on layers 1-3.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import networkx as nx
import json

class MemorySimulationEngine:
    """
    In-memory simulation engine for UKG layers 1-3
    
    This engine provides a lightweight, fast simulation of the UKG system
    for the top 3 layers: Knowledge (Pillar Levels), Sectors, and Domains.
    It creates an in-memory graph representation that can be queried and
    manipulated without requiring database access.
    """
    
    def __init__(self):
        """Initialize the Memory Simulation Engine."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize the graph
        self.graph = nx.DiGraph()
        
        # Initialize layer stores
        self.pillar_levels = {}  # Axis 1: Knowledge (PL01-PL100)
        self.sectors = {}        # Axis 2: Sectors
        self.domains = {}        # Axis 3: Domains
        
        # Layer connections
        self.pillar_to_sector = {}  # PL -> Sector mappings
        self.sector_to_domain = {}  # Sector -> Domain mappings
        self.domain_to_pillar = {}  # Domain -> PL mappings (cross-connections)
        
        # Initialize simulation state
        self.simulation_active = False
        self.simulation_step = 0
        self.simulation_context = {}
        
        self.logger.info(f"[{datetime.now()}] Memory Simulation Engine initialized")
    
    def load_pillar_levels(self, pillar_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Load pillar level data into the simulation engine.
        
        Args:
            pillar_data: List of pillar level data dictionaries
            
        Returns:
            Dict containing load result
        """
        self.logger.info(f"[{datetime.now()}] Loading {len(pillar_data)} pillar levels")
        
        # Clear existing pillar data
        self.pillar_levels = {}
        
        # Process each pillar level
        for pillar in pillar_data:
            pillar_id = pillar.get('pillar_id')
            if not pillar_id:
                continue
                
            # Add to internal dictionary
            self.pillar_levels[pillar_id] = pillar
            
            # Add node to graph
            node_attrs = {
                'type': 'pillar_level',
                'axis': 1,
                'name': pillar.get('name', ''),
                'data': pillar
            }
            self.graph.add_node(pillar_id, **node_attrs)
            
            # Process sublevels if available
            sublevels = pillar.get('sublevels', {})
            for sublevel_id, sublevel_name in sublevels.items():
                sublevel_node_id = f"{pillar_id}_{sublevel_id}"
                sublevel_attrs = {
                    'type': 'pillar_sublevel',
                    'axis': 1,
                    'name': sublevel_name,
                    'pillar_id': pillar_id,
                    'sublevel_id': sublevel_id
                }
                self.graph.add_node(sublevel_node_id, **sublevel_attrs)
                self.graph.add_edge(pillar_id, sublevel_node_id, edge_type='has_sublevel')
        
        self.logger.info(f"[{datetime.now()}] Loaded {len(self.pillar_levels)} pillar levels")
        return {
            'status': 'success',
            'pillar_count': len(self.pillar_levels),
            'timestamp': datetime.now().isoformat()
        }
    
    def load_sectors(self, sector_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Load sector data into the simulation engine.
        
        Args:
            sector_data: List of sector data dictionaries
            
        Returns:
            Dict containing load result
        """
        self.logger.info(f"[{datetime.now()}] Loading {len(sector_data)} sectors")
        
        # Clear existing sector data
        self.sectors = {}
        
        # First pass: Add all sectors
        for sector in sector_data:
            sector_id = sector.get('sector_code')
            if not sector_id:
                continue
                
            # Add to internal dictionary
            self.sectors[sector_id] = sector
            
            # Add node to graph
            node_attrs = {
                'type': 'sector',
                'axis': 2,
                'name': sector.get('name', ''),
                'data': sector
            }
            self.graph.add_node(sector_id, **node_attrs)
        
        # Second pass: Connect parent-child relationships
        for sector in sector_data:
            sector_id = sector.get('sector_code')
            parent_id = sector.get('parent_sector_code')
            
            if sector_id and parent_id and parent_id in self.sectors:
                self.graph.add_edge(parent_id, sector_id, edge_type='has_subsector')
        
        self.logger.info(f"[{datetime.now()}] Loaded {len(self.sectors)} sectors")
        return {
            'status': 'success',
            'sector_count': len(self.sectors),
            'timestamp': datetime.now().isoformat()
        }
    
    def load_domains(self, domain_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Load domain data into the simulation engine.
        
        Args:
            domain_data: List of domain data dictionaries
            
        Returns:
            Dict containing load result
        """
        self.logger.info(f"[{datetime.now()}] Loading {len(domain_data)} domains")
        
        # Clear existing domain data
        self.domains = {}
        
        # First pass: Add all domains
        for domain in domain_data:
            domain_id = domain.get('domain_code')
            if not domain_id:
                continue
                
            # Add to internal dictionary
            self.domains[domain_id] = domain
            
            # Add node to graph
            node_attrs = {
                'type': 'domain',
                'axis': 3,
                'name': domain.get('name', ''),
                'data': domain
            }
            self.graph.add_node(domain_id, **node_attrs)
            
            # Connect to sector if available
            sector_id = domain.get('sector_code')
            if sector_id and sector_id in self.sectors:
                self.graph.add_edge(sector_id, domain_id, edge_type='has_domain')
                self.sector_to_domain.setdefault(sector_id, []).append(domain_id)
        
        # Second pass: Connect parent-child relationships
        for domain in domain_data:
            domain_id = domain.get('domain_code')
            parent_id = domain.get('parent_domain_code')
            
            if domain_id and parent_id and parent_id in self.domains:
                self.graph.add_edge(parent_id, domain_id, edge_type='has_subdomain')
        
        self.logger.info(f"[{datetime.now()}] Loaded {len(self.domains)} domains")
        return {
            'status': 'success',
            'domain_count': len(self.domains),
            'timestamp': datetime.now().isoformat()
        }
    
    def connect_pillars_to_sectors(self, connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Connect pillar levels to sectors.
        
        Args:
            connections: List of connection data dictionaries
            
        Returns:
            Dict containing connection result
        """
        self.logger.info(f"[{datetime.now()}] Connecting pillars to sectors: {len(connections)} connections")
        
        # Clear existing connections
        self.pillar_to_sector = {}
        
        # Process each connection
        connection_count = 0
        for conn in connections:
            pillar_id = conn.get('pillar_id')
            sector_id = conn.get('sector_id')
            
            if not pillar_id or not sector_id:
                continue
            
            if pillar_id not in self.pillar_levels or sector_id not in self.sectors:
                continue
            
            # Add to internal dictionary
            self.pillar_to_sector.setdefault(pillar_id, []).append(sector_id)
            
            # Add edge to graph
            edge_attrs = {
                'edge_type': 'pillar_to_sector',
                'weight': conn.get('weight', 1.0),
                'data': conn
            }
            self.graph.add_edge(pillar_id, sector_id, **edge_attrs)
            connection_count += 1
        
        self.logger.info(f"[{datetime.now()}] Connected {connection_count} pillar-sector pairs")
        return {
            'status': 'success',
            'connection_count': connection_count,
            'timestamp': datetime.now().isoformat()
        }
    
    def connect_domains_to_pillars(self, connections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Connect domains to pillar levels (cross-connections).
        
        Args:
            connections: List of connection data dictionaries
            
        Returns:
            Dict containing connection result
        """
        self.logger.info(f"[{datetime.now()}] Connecting domains to pillars: {len(connections)} connections")
        
        # Clear existing connections
        self.domain_to_pillar = {}
        
        # Process each connection
        connection_count = 0
        for conn in connections:
            domain_id = conn.get('domain_id')
            pillar_id = conn.get('pillar_id')
            
            if not domain_id or not pillar_id:
                continue
            
            if domain_id not in self.domains or pillar_id not in self.pillar_levels:
                continue
            
            # Add to internal dictionary
            self.domain_to_pillar.setdefault(domain_id, []).append(pillar_id)
            
            # Add edge to graph
            edge_attrs = {
                'edge_type': 'domain_to_pillar',
                'weight': conn.get('weight', 1.0),
                'data': conn
            }
            self.graph.add_edge(domain_id, pillar_id, **edge_attrs)
            connection_count += 1
        
        self.logger.info(f"[{datetime.now()}] Connected {connection_count} domain-pillar pairs")
        return {
            'status': 'success',
            'connection_count': connection_count,
            'timestamp': datetime.now().isoformat()
        }
    
    def start_simulation(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Start a simulation run.
        
        Args:
            context: Optional simulation context
            
        Returns:
            Dict containing simulation start result
        """
        self.logger.info(f"[{datetime.now()}] Starting simulation")
        
        # Initialize simulation state
        self.simulation_active = True
        self.simulation_step = 0
        self.simulation_context = context or {}
        
        # Create a simulation ID
        simulation_id = f"sim_{uuid.uuid4().hex[:16]}"
        self.simulation_context['simulation_id'] = simulation_id
        self.simulation_context['start_time'] = datetime.now().isoformat()
        
        # Calculate initial graph stats
        node_count = self.graph.number_of_nodes()
        edge_count = self.graph.number_of_edges()
        
        # Calculate layer counts
        pillar_count = len([n for n, attrs in self.graph.nodes(data=True) if attrs.get('type') == 'pillar_level'])
        sector_count = len([n for n, attrs in self.graph.nodes(data=True) if attrs.get('type') == 'sector'])
        domain_count = len([n for n, attrs in self.graph.nodes(data=True) if attrs.get('type') == 'domain'])
        
        self.logger.info(f"[{datetime.now()}] Simulation {simulation_id} started with {node_count} nodes and {edge_count} edges")
        
        return {
            'status': 'success',
            'simulation_id': simulation_id,
            'simulation_step': self.simulation_step,
            'graph_stats': {
                'node_count': node_count,
                'edge_count': edge_count,
                'pillar_count': pillar_count,
                'sector_count': sector_count,
                'domain_count': domain_count
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def run_simulation_step(self) -> Dict[str, Any]:
        """
        Run a single simulation step.
        
        Returns:
            Dict containing simulation step result
        """
        if not self.simulation_active:
            return {
                'status': 'error',
                'message': 'Simulation not active',
                'timestamp': datetime.now().isoformat()
            }
        
        self.logger.info(f"[{datetime.now()}] Running simulation step {self.simulation_step}")
        
        # Increment step counter
        self.simulation_step += 1
        
        # Simulation layer 1: Knowledge diffusion
        # Spread activation through pillar levels
        pillar_activations = self._run_knowledge_diffusion()
        
        # Simulation layer 2: Sector influence
        # Propagate sector-based knowledge adaptations
        sector_activities = self._run_sector_influence(pillar_activations)
        
        # Simulation layer 3: Domain specialization
        # Apply domain-specific transformations to knowledge
        domain_activities = self._run_domain_specialization(sector_activities)
        
        # Record step results
        step_results = {
            'step': self.simulation_step,
            'pillar_activations': pillar_activations,
            'sector_activities': sector_activities,
            'domain_activities': domain_activities,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add to simulation context
        self.simulation_context.setdefault('steps', []).append(step_results)
        
        self.logger.info(f"[{datetime.now()}] Completed simulation step {self.simulation_step}")
        
        return {
            'status': 'success',
            'simulation_id': self.simulation_context['simulation_id'],
            'simulation_step': self.simulation_step,
            'results': step_results,
            'timestamp': datetime.now().isoformat()
        }
    
    def _run_knowledge_diffusion(self) -> Dict[str, float]:
        """
        Run the knowledge diffusion simulation layer.
        
        Returns:
            Dict mapping pillar IDs to activation levels
        """
        # Initialize activations
        # Start with random or provided seed activations
        activations = {}
        
        # Get seed activations from context if available
        seed_activations = self.simulation_context.get('seed_activations', {})
        
        # Process each pillar level
        for pillar_id in self.pillar_levels:
            # Start with seed value or default
            activation = seed_activations.get(pillar_id, 0.1)
            
            # Get all connected pillars
            neighbors = list(self.graph.neighbors(pillar_id))
            
            # Simulate knowledge diffusion - more connections = higher activation
            diffusion_factor = 0.05 * len(neighbors)
            activation += diffusion_factor
            
            # Normalize activation to 0.0-1.0 range
            activation = min(1.0, max(0.0, activation))
            
            # Store activation level
            activations[pillar_id] = activation
        
        return activations
    
    def _run_sector_influence(self, pillar_activations: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        """
        Run the sector influence simulation layer.
        
        Args:
            pillar_activations: Dict mapping pillar IDs to activation levels
            
        Returns:
            Dict containing sector activities
        """
        # Initialize sector activities
        sector_activities = {}
        
        # Process each sector
        for sector_id in self.sectors:
            # Get connected pillars (incoming edges)
            connected_pillars = [
                src for src, tgt, attrs in self.graph.in_edges(sector_id, data=True)
                if attrs.get('edge_type') == 'pillar_to_sector'
            ]
            
            # Calculate sector influence based on connected pillar activations
            influence = 0.0
            knowledge_sources = []
            
            for pillar_id in connected_pillars:
                if pillar_id in pillar_activations:
                    pillar_weight = self.graph.get_edge_data(pillar_id, sector_id).get('weight', 1.0)
                    pillar_contribution = pillar_activations[pillar_id] * pillar_weight
                    influence += pillar_contribution
                    
                    knowledge_sources.append({
                        'pillar_id': pillar_id,
                        'name': self.pillar_levels[pillar_id].get('name', ''),
                        'activation': pillar_activations[pillar_id],
                        'weight': pillar_weight,
                        'contribution': pillar_contribution
                    })
            
            # Normalize influence
            if connected_pillars:
                influence /= len(connected_pillars)
            
            # Store sector activity
            sector_activities[sector_id] = {
                'sector_id': sector_id,
                'name': self.sectors[sector_id].get('name', ''),
                'influence': influence,
                'knowledge_sources': knowledge_sources
            }
        
        return sector_activities
    
    def _run_domain_specialization(self, sector_activities: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Run the domain specialization simulation layer.
        
        Args:
            sector_activities: Dict containing sector activities
            
        Returns:
            Dict containing domain activities
        """
        # Initialize domain activities
        domain_activities = {}
        
        # Process each domain
        for domain_id in self.domains:
            # Get connected sectors
            domain_data = self.domains[domain_id]
            sector_id = domain_data.get('sector_code')
            
            # Get connected pillars (direct connections)
            directly_connected_pillars = [
                tgt for src, tgt, attrs in self.graph.out_edges(domain_id, data=True)
                if attrs.get('edge_type') == 'domain_to_pillar'
            ]
            
            # Calculate domain specialization
            specialization = 0.0
            knowledge_adaptations = []
            
            # Factor 1: Sector influence
            if sector_id and sector_id in sector_activities:
                sector_influence = sector_activities[sector_id]['influence']
                specialization += sector_influence * 0.6  # 60% weight to sector influence
                
                knowledge_adaptations.append({
                    'type': 'sector_influence',
                    'sector_id': sector_id,
                    'name': self.sectors[sector_id].get('name', ''),
                    'influence': sector_influence,
                    'contribution': sector_influence * 0.6
                })
            
            # Factor 2: Direct pillar connections
            pillar_factor = 0.0
            if directly_connected_pillars:
                for pillar_id in directly_connected_pillars:
                    pillar_data = self.pillar_levels.get(pillar_id, {})
                    pillar_name = pillar_data.get('name', '')
                    
                    edge_data = self.graph.get_edge_data(domain_id, pillar_id)
                    if edge_data:
                        weight = edge_data.get('weight', 1.0)
                        pillar_factor += weight
                        
                        knowledge_adaptations.append({
                            'type': 'direct_pillar_connection',
                            'pillar_id': pillar_id,
                            'name': pillar_name,
                            'weight': weight,
                            'contribution': weight * 0.4 / len(directly_connected_pillars)
                        })
                
                # Normalize and add contribution (40% weight to direct connections)
                pillar_factor = pillar_factor / len(directly_connected_pillars)
                specialization += pillar_factor * 0.4
            
            # Store domain activity
            domain_activities[domain_id] = {
                'domain_id': domain_id,
                'name': domain_data.get('name', ''),
                'specialization': specialization,
                'knowledge_adaptations': knowledge_adaptations
            }
        
        return domain_activities
    
    def stop_simulation(self) -> Dict[str, Any]:
        """
        Stop the current simulation run.
        
        Returns:
            Dict containing simulation stop result
        """
        if not self.simulation_active:
            return {
                'status': 'error',
                'message': 'No active simulation to stop',
                'timestamp': datetime.now().isoformat()
            }
        
        self.logger.info(f"[{datetime.now()}] Stopping simulation {self.simulation_context.get('simulation_id')}")
        
        # Mark simulation as inactive
        self.simulation_active = False
        
        # Add stop time to context
        self.simulation_context['stop_time'] = datetime.now().isoformat()
        
        # Calculate simulation duration
        start_time = datetime.fromisoformat(self.simulation_context['start_time'])
        stop_time = datetime.fromisoformat(self.simulation_context['stop_time'])
        duration = (stop_time - start_time).total_seconds()
        
        self.logger.info(f"[{datetime.now()}] Simulation {self.simulation_context.get('simulation_id')} stopped after {self.simulation_step} steps and {duration:.2f} seconds")
        
        return {
            'status': 'success',
            'simulation_id': self.simulation_context.get('simulation_id'),
            'steps_completed': self.simulation_step,
            'duration_seconds': duration,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_simulation_results(self) -> Dict[str, Any]:
        """
        Get the results of the most recent simulation run.
        
        Returns:
            Dict containing simulation results
        """
        if not self.simulation_context.get('simulation_id'):
            return {
                'status': 'error',
                'message': 'No simulation has been run',
                'timestamp': datetime.now().isoformat()
            }
        
        self.logger.info(f"[{datetime.now()}] Getting results for simulation {self.simulation_context.get('simulation_id')}")
        
        # Return the simulation context
        return {
            'status': 'success',
            'simulation_id': self.simulation_context.get('simulation_id'),
            'steps_completed': self.simulation_step,
            'context': self.simulation_context,
            'timestamp': datetime.now().isoformat()
        }
    
    def export_graph(self, format: str = 'json') -> Dict[str, Any]:
        """
        Export the current simulation graph.
        
        Args:
            format: Export format ('json' or 'gexf')
            
        Returns:
            Dict containing export result
        """
        self.logger.info(f"[{datetime.now()}] Exporting graph in {format} format")
        
        if format == 'json':
            # Convert graph to JSON format
            nodes = [{'id': n, **self.graph.nodes[n]} for n in self.graph.nodes()]
            edges = [{'source': u, 'target': v, **d} for u, v, d in self.graph.edges(data=True)]
            
            graph_data = {
                'nodes': nodes,
                'edges': edges,
                'metadata': {
                    'node_count': len(nodes),
                    'edge_count': len(edges),
                    'timestamp': datetime.now().isoformat(),
                    'simulation_id': self.simulation_context.get('simulation_id')
                }
            }
            
            return {
                'status': 'success',
                'format': 'json',
                'graph': graph_data,
                'timestamp': datetime.now().isoformat()
            }
            
        elif format == 'gexf':
            try:
                import networkx as nx
                from io import StringIO
                
                # Convert to GEXF format
                sio = StringIO()
                nx.write_gexf(self.graph, sio)
                gexf_data = sio.getvalue()
                
                return {
                    'status': 'success',
                    'format': 'gexf',
                    'graph': gexf_data,
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f"Error exporting to GEXF: {str(e)}",
                    'timestamp': datetime.now().isoformat()
                }
        
        else:
            return {
                'status': 'error',
                'message': f"Unsupported export format: {format}",
                'timestamp': datetime.now().isoformat()
            }
    
    def get_path_between(self, source_id: str, target_id: str) -> Dict[str, Any]:
        """
        Find the shortest path between two nodes in the graph.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            
        Returns:
            Dict containing path result
        """
        self.logger.info(f"[{datetime.now()}] Finding path between {source_id} and {target_id}")
        
        if source_id not in self.graph or target_id not in self.graph:
            return {
                'status': 'error',
                'message': 'Source or target node not found',
                'source_id': source_id,
                'target_id': target_id,
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Find shortest path
            path = nx.shortest_path(self.graph, source_id, target_id)
            
            # Get path details
            path_details = []
            for i in range(len(path) - 1):
                source = path[i]
                target = path[i + 1]
                edge_data = self.graph.get_edge_data(source, target)
                
                path_details.append({
                    'source': source,
                    'source_type': self.graph.nodes[source]['type'],
                    'source_name': self.graph.nodes[source]['name'],
                    'target': target,
                    'target_type': self.graph.nodes[target]['type'],
                    'target_name': self.graph.nodes[target]['name'],
                    'edge_type': edge_data.get('edge_type', 'unknown'),
                    'weight': edge_data.get('weight', 1.0)
                })
            
            return {
                'status': 'success',
                'path': path,
                'path_details': path_details,
                'path_length': len(path) - 1,
                'timestamp': datetime.now().isoformat()
            }
            
        except nx.NetworkXNoPath:
            return {
                'status': 'no_path',
                'message': 'No path exists between the specified nodes',
                'source_id': source_id,
                'target_id': target_id,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Error finding path: {str(e)}",
                'source_id': source_id,
                'target_id': target_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def search_graph(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search the graph for nodes matching the specified criteria.
        
        Args:
            query: Search query dictionary
            
        Returns:
            Dict containing search results
        """
        self.logger.info(f"[{datetime.now()}] Searching graph with query: {query}")
        
        # Extract query parameters
        node_type = query.get('node_type')
        axis = query.get('axis')
        name_contains = query.get('name_contains')
        
        # Build filter function
        def node_matches(node_data):
            if node_type and node_data.get('type') != node_type:
                return False
            
            if axis and node_data.get('axis') != axis:
                return False
            
            if name_contains and name_contains.lower() not in node_data.get('name', '').lower():
                return False
            
            return True
        
        # Apply filter
        matching_nodes = []
        for node_id, node_data in self.graph.nodes(data=True):
            if node_matches(node_data):
                matching_nodes.append({
                    'id': node_id,
                    **node_data
                })
        
        return {
            'status': 'success',
            'nodes': matching_nodes,
            'count': len(matching_nodes),
            'query': query,
            'timestamp': datetime.now().isoformat()
        }


# Example usage

def create_sample_simulation():
    """Create a sample simulation with test data."""
    logging.basicConfig(level=logging.INFO)
    
    # Create engine
    engine = MemorySimulationEngine()
    
    # Sample pillar levels
    pillar_levels = [
        {
            "pillar_id": "PL01",
            "name": "U.S. Government Regulatory Systems",
            "description": "Core government regulatory frameworks and legal systems",
            "sublevels": {
                "1": "Federal Regulations",
                "2": "State Regulations",
                "3": "Local Government Codes"
            }
        },
        {
            "pillar_id": "PL04",
            "name": "Contracting & Procurement Sciences",
            "description": "Government and private sector acquisition methodologies",
            "sublevels": {
                "1": "Contract Types",
                "2": "Procurement Procedures"
            }
        },
        {
            "pillar_id": "PL07",
            "name": "Data Privacy & Security",
            "description": "Information security, privacy frameworks, and protection methods",
            "sublevels": {
                "1": "Data Protection Frameworks",
                "2": "Information Security"
            }
        }
    ]
    
    # Sample sectors
    sectors = [
        {
            "sector_code": "GOV",
            "name": "Government",
            "description": "Public sector, government agencies, and regulatory bodies"
        },
        {
            "sector_code": "TECH",
            "name": "Technology",
            "description": "Information technology, software, hardware, and digital services"
        },
        {
            "sector_code": "FIN",
            "name": "Finance",
            "description": "Financial services, banking, and investment"
        }
    ]
    
    # Sample domains
    domains = [
        {
            "domain_code": "FEDGOV",
            "name": "Federal Government",
            "description": "U.S. Federal Government operations and processes",
            "sector_code": "GOV"
        },
        {
            "domain_code": "CSEC",
            "name": "Cybersecurity",
            "description": "Computer and network security, defense against cyber threats",
            "sector_code": "TECH"
        },
        {
            "domain_code": "FINTECH",
            "name": "Financial Technology",
            "description": "Technology applications in finance and banking",
            "sector_code": "FIN"
        }
    ]
    
    # Load data
    engine.load_pillar_levels(pillar_levels)
    engine.load_sectors(sectors)
    engine.load_domains(domains)
    
    # Create connections
    pillar_sector_connections = [
        {"pillar_id": "PL01", "sector_id": "GOV", "weight": 0.9},
        {"pillar_id": "PL01", "sector_id": "FIN", "weight": 0.4},
        {"pillar_id": "PL04", "sector_id": "GOV", "weight": 0.8},
        {"pillar_id": "PL07", "sector_id": "TECH", "weight": 0.9},
        {"pillar_id": "PL07", "sector_id": "FIN", "weight": 0.6}
    ]
    
    domain_pillar_connections = [
        {"domain_id": "FEDGOV", "pillar_id": "PL01", "weight": 0.9},
        {"domain_id": "CSEC", "pillar_id": "PL07", "weight": 0.9},
        {"domain_id": "FINTECH", "pillar_id": "PL07", "weight": 0.7},
        {"domain_id": "FINTECH", "pillar_id": "PL01", "weight": 0.4}
    ]
    
    engine.connect_pillars_to_sectors(pillar_sector_connections)
    engine.connect_domains_to_pillars(domain_pillar_connections)
    
    # Return the initialized engine
    return engine


if __name__ == "__main__":
    # Create sample simulation
    engine = create_sample_simulation()
    
    # Start simulation
    engine.start_simulation()
    
    # Run simulation steps
    for i in range(3):
        result = engine.run_simulation_step()
        print(f"Step {i+1} complete")
    
    # Get results
    results = engine.get_simulation_results()
    print(f"Simulation complete with {results['steps_completed']} steps")
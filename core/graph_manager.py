import os
import yaml
import logging
import networkx as nx
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

class GraphManager:
    """
    Graph Manager for the Universal Knowledge Graph (UKG).

    Manages the 13-axis knowledge graph, including:
    - Pillar Levels (Axis 1)
    - Sectors (Axis 2)
    - Honeycomb System (Axis 3)
    - Branch System (Axis 4)
    - Node System (Axis 5)
    - Octopus Node (Axis 6)
    - Spiderweb Node (Axis 7)
    - Knowledge Role (Axis 8)
    - Sector Expert (Axis 9)
    - Regulatory Expert (Axis 10)
    - Compliance Expert (Axis 11)
    - Location (Axis 12)
    - Temporal (Axis 13)
    """

    def __init__(self, config, united_system_manager=None):
        """
        Initialize the Graph Manager.

        Args:
            config: Application configuration
            united_system_manager: Optional UnitedSystemManager instance
        """
        self.config = config
        self.usm = united_system_manager
        self.logger = logging.getLogger(__name__)

        # Initialize main graph
        self.graph = nx.DiGraph()

        # Load axis definitions
        self.axis_definitions_data = self._load_yaml_file(config.axis_definitions_path, "Axis Definitions")

        # Load pillar levels
        self.pillar_levels_data = self._load_yaml_file(config.pillar_levels_path, "Pillar Levels")

        # Load regulatory frameworks
        self.regulatory_frameworks_data = self._load_yaml_file(config.regulatory_frameworks_path, "Regulatory Frameworks")

        # Load locations gazetteer
        self.locations_gazetteer_data = self._load_yaml_file(config.locations_gazetteer_path, "Locations Gazetteer")

        # Initialize the graph structure
        self._build_initial_graph_structure()

        self.logger.info(f"GraphManager initialized with {len(self.graph.nodes)} nodes and {len(self.graph.edges)} edges")

    def _load_yaml_file(self, file_path: str, data_name: str) -> Dict:
        """
        Load data from a YAML file.

        Args:
            file_path: Path to the YAML file
            data_name: Human-readable name for the data

        Returns:
            Dict containing the loaded data or empty dict if not found
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                self.logger.info(f"Loaded {data_name} from {file_path}")
                return data if data else {}
            else:
                self.logger.warning(f"{data_name} file not found at {file_path}")
                return {}
        except Exception as e:
            self.logger.error(f"Error loading {data_name} from {file_path}: {str(e)}")
            return {}

    def _build_initial_graph_structure(self):
        """
        Build the initial UKG graph structure from loaded data.
        """
        self.logger.info("Building initial UKG graph structure...")

        # Create Axis nodes (1-13)
        for i in range(1, 14):
            axis_id = f"Axis{i}"
            axis_data = self.axis_definitions_data.get(axis_id, {})
            axis_name = axis_data.get("name", f"Axis {i}")

            # Generate UID if United System Manager is available
            if self.usm:
                axis_uid_pkg = self.usm.create_unified_id(
                    entity_label=axis_name,
                    entity_type="AxisNode",
                    ukg_coords={"AxisNumber": i},
                    specific_id_part=axis_id
                )
                axis_uid = axis_uid_pkg["uid_string"]
                axis_data["uid_string"] = axis_uid
            else:
                # Fallback if USM not available
                axis_uid = f"UID_AXIS_{i}"
                axis_data["uid_string"] = axis_uid

            # Add to graph
            self.graph.add_node(
                axis_uid,
                name=axis_name,
                type="AxisNode",
                axis_number=i,
                original_id=axis_id,
                **axis_data
            )

            self.logger.info(f"Added Axis {i} node: {axis_name}")

        # Build Pillar Levels from Axis 1
        self._build_pillar_structure()

        # Build other axis structures
        # TODO: Implement other axis builders

        self.logger.info(f"Initial UKG graph structure built with {len(self.graph.nodes)} nodes")

    def _build_pillar_structure(self):
        """
        Build the Pillar Level structure (Axis 1).
        """
        self.logger.info("Building Pillar Level structure (Axis 1)...")

        axis1_uid = self._get_axis_uid_by_number(1)
        if not axis1_uid:
            self.logger.warning("Axis 1 UID not found, cannot build Pillar structure")
            return

        # Process pillar levels
        pillars = self.pillar_levels_data.get("PillarLevels", [])
        for pillar in pillars:
            pl_id = pillar.get("id")
            pl_label = pillar.get("label", "Unknown Pillar")
            pl_description = pillar.get("description", "")

            # Generate UID
            if self.usm:
                pl_uid_pkg = self.usm.create_unified_id(
                    entity_label=pl_label,
                    entity_type="PillarLevelNode",
                    ukg_coords={"Axis1": pl_id},
                    specific_id_part=pl_id
                )
                pl_uid = pl_uid_pkg["uid_string"]
            else:
                pl_uid = f"UID_PL_{pl_id}"

            # Add pillar node
            self.graph.add_node(
                pl_uid,
                name=pl_label,
                description=pl_description,
                type="PillarLevelNode",
                original_id=pl_id,
                axis_number=1
            )

            # Connect to Axis 1
            self.graph.add_edge(axis1_uid, pl_uid, relationship="has_pillar_level")

            # Process sublevels if available
            sublevels = pillar.get("sublevels", [])
            for sublevel in sublevels:
                self._add_pillar_sublevel(pl_uid, sublevel)

            self.logger.info(f"Added Pillar Level: {pl_label}")

    def _add_pillar_sublevel(self, parent_uid: str, sublevel_data: Dict, level: int = 1):
        """
        Add a sublevel to a pillar level node.

        Args:
            parent_uid: UID of the parent node
            sublevel_data: Data for the sublevel
            level: Current sublevel depth
        """
        sl_id = sublevel_data.get("id")
        sl_label = sublevel_data.get("label", "Unknown Sublevel")
        sl_description = sublevel_data.get("description", "")

        # Generate UID
        if self.usm:
            sl_uid_pkg = self.usm.create_unified_id(
                entity_label=sl_label,
                entity_type="PillarSublevelNode",
                ukg_coords={"Axis1": sl_id, "ParentUID": parent_uid, "Level": level},
                specific_id_part=sl_id
            )
            sl_uid = sl_uid_pkg["uid_string"]
        else:
            sl_uid = f"UID_SL_{sl_id}"

        # Add sublevel node
        self.graph.add_node(
            sl_uid,
            name=sl_label,
            description=sl_description,
            type="PillarSublevelNode",
            original_id=sl_id,
            level=level,
            axis_number=1
        )

        # Connect to parent
        self.graph.add_edge(parent_uid, sl_uid, relationship="has_sublevel")

        # Process nested sublevels
        nested_sublevels = sublevel_data.get("sublevels", [])
        for nested in nested_sublevels:
            self._add_pillar_sublevel(sl_uid, nested, level + 1)

    def _get_axis_uid_by_number(self, axis_number: int) -> Optional[str]:
        """
        Get the UID for a specific axis by its number.

        Args:
            axis_number: The axis number (1-13)

        Returns:
            The axis UID or None if not found
        """
        for node, data in self.graph.nodes(data=True):
            if data.get("type") == "AxisNode" and data.get("axis_number") == axis_number:
                return node
        return None

    def get_node_data_by_uid(self, uid: str) -> Optional[Dict]:
        """
        Get node data by UID.

        Args:
            uid: Node's unique identifier

        Returns:
            Dict containing the node data or None if not found
        """
        if uid in self.graph:
            return dict(self.graph.nodes[uid])
        return None

    def get_node_data_by_attribute(self, attr_name: str, attr_value: Any, node_type: Optional[str] = None) -> Optional[str]:
        """
        Get node UID by a specific attribute value.

        Args:
            attr_name: Attribute name to search
            attr_value: Value to match
            node_type: Optional node type to filter on

        Returns:
            The matching node UID or None if not found
        """
        for node, data in self.graph.nodes(data=True):
            if attr_name in data and data[attr_name] == attr_value:
                if node_type is None or data.get("type") == node_type:
                    return node
        return None

    def get_pillar_level_uid(self, pillar_id: str) -> Optional[str]:
        """
        Get the UID for a specific Pillar Level by its ID.

        Args:
            pillar_id: The Pillar Level ID (e.g., 'PL01')

        Returns:
            The UID of the Pillar Level or None if not found
        """
        return self.get_node_data_by_attribute("original_id", pillar_id, "PillarLevelNode")

    def get_connected_nodes(self, node_uid: str, relationship_type: Optional[str] = None, direction: str = "outgoing") -> List[Dict]:
        """
        Get nodes connected to a specific node.

        Args:
            node_uid: The UID of the node
            relationship_type: Optional relationship type filter
            direction: 'outgoing', 'incoming', or 'both'

        Returns:
            List of connected node data dictionaries
        """
        if node_uid not in self.graph:
            return []

        result = []

        if direction in ["outgoing", "both"]:
            for _, target in self.graph.out_edges(node_uid):
                edge_data = self.graph.get_edge_data(node_uid, target)
                if relationship_type is None or edge_data.get("relationship") == relationship_type:
                    node_data = self.get_node_data_by_uid(target)
                    if node_data:
                        result.append({
                            "node": node_data,
                            "relationship": edge_data.get("relationship", "unknown"),
                            "direction": "outgoing"
                        })

        if direction in ["incoming", "both"]:
            for source, _ in self.graph.in_edges(node_uid):
                edge_data = self.graph.get_edge_data(source, node_uid)
                if relationship_type is None or edge_data.get("relationship") == relationship_type:
                    node_data = self.get_node_data_by_uid(source)
                    if node_data:
                        result.append({
                            "node": node_data,
                            "relationship": edge_data.get("relationship", "unknown"),
                            "direction": "incoming"
                        })

        return result

    def get_axis_uid(self, axis_id: str) -> Optional[str]:
        """
        Get the UID for a specific axis by its ID.

        Args:
            axis_id: The axis ID (e.g., 'Axis1')

        Returns:
            The axis UID or None if not found
        """
        return self.get_node_data_by_attribute("original_id", axis_id, "AxisNode")

    def search_nodes(self, query: str, node_types: Optional[List[str]] = None, limit: int = 10) -> List[Dict]:
        """
        Search for nodes matching a query string.

        Args:
            query: Search query string
            node_types: Optional list of node types to filter on
            limit: Maximum number of results to return

        Returns:
            List of matching node data dictionaries
        """
        query = query.lower()
        results = []

        for node, data in self.graph.nodes(data=True):
            if node_types and data.get("type") not in node_types:
                continue

            # Search in name, description, and other text fields
            name = str(data.get("name", "")).lower()
            description = str(data.get("description", "")).lower()

            if query in name or query in description:
                results.append(dict(data))

            if len(results) >= limit:
                break

        return results
    
    def find_location_uids_from_text(self, text):
        """
        Find location UIDs based on text references.
        
        Args:
            text (str): The text to analyze
            
        Returns:
            list: List of matching location UIDs
        """
        # This would use more sophisticated NLP in a real implementation
        # For simplicity, just do basic substring matching
        text_lower = text.lower()
        locations = []
        
        for node, attrs in self.graph.nodes(data=True):
            if attrs.get('entity_type', '').lower() in ['country', 'state', 'city', 'region']:
                label = attrs.get('label', '').lower()
                if label and label in text_lower:
                    locations.append(node)
        
        return locations
    
    def get_graph_statistics(self):
        """
        Get statistics about the UKG graph.
        
        Returns:
            dict: Various statistics about the graph
        """
        node_count = len(self.graph.nodes)
        edge_count = len(self.graph.edges)
        
        # Count nodes by type
        node_types = {}
        for _, attrs in self.graph.nodes(data=True):
            entity_type = attrs.get('entity_type', 'Unknown')
            node_types[entity_type] = node_types.get(entity_type, 0) + 1
        
        # Count edges by relationship type
        edge_types = {}
        for _, _, attrs in self.graph.edges(data=True):
            rel_type = attrs.get('relationship', 'Unknown')
            edge_types[rel_type] = edge_types.get(rel_type, 0) + 1
        
        return {
            'total_nodes': node_count,
            'total_edges': edge_count,
            'node_types': node_types,
            'edge_types': edge_types
        }
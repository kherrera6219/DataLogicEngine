import networkx as nx
import yaml
import os
import logging
from datetime import datetime
from pathlib import Path

class GraphManager:
    """
    The GraphManager is responsible for creating and managing the Universal Knowledge Graph (UKG).
    It handles loading data from YAML files, building the graph structure, and providing
    methods to query and manipulate the graph.
    """
    
    def __init__(self, config, united_system_manager):
        """
        Initialize the GraphManager.
        
        Args:
            config (dict): Configuration dictionary containing paths to data files
            united_system_manager (UnitedSystemManager): Reference to the UnitedSystemManager
        """
        self.config = config
        self.united_system_manager = united_system_manager
        self.graph = nx.DiGraph()  # Use a directed graph to represent relationships
        self.axis_definitions_data = {}
        self.pillar_levels_data = {}
        self.sector_data = {}
        self.topics_data = {}
        self.methods_data = {}
        self.tools_data = {}
        self.regulatory_frameworks_data = {}
        self.compliance_standards_data = {}
        self.personas_data = {}
        self.time_periods_data = {}
        self.config_or_default_path_for_locations = config.get('ukg_paths', {}).get('locations', 'data/ukg/locations_gazetteer.yaml')
        
        logging.info(f"[{datetime.now()}] GraphManager initialized")
    
    def initialize_graph(self):
        """Initialize the graph by loading data and building the initial structure."""
        logging.info(f"[{datetime.now()}] GM: Initializing UKG graph structure")
        
        # Load definitions and data
        self._load_definitions()
        
        # Build the initial graph structure
        self._build_initial_graph_structure()
        
        # Build connections between nodes
        self._build_graph_connections()
        
        logging.info(f"[{datetime.now()}] GM: UKG initialization complete. Nodes: {len(self.graph.nodes)}, Edges: {len(self.graph.edges)}")
    
    def _load_definitions(self):
        """Load all definition files for the UKG."""
        self.axis_definitions_data = self._load_yaml_file(
            self.config.get('ukg_paths', {}).get('axis_definitions', 'data/ukg/axis_definitions.yaml'),
            "Axis Definitions"
        )
        
        self.pillar_levels_data = self._load_yaml_file(
            self.config.get('ukg_paths', {}).get('pillar_levels', 'data/ukg/pillar_levels.yaml'),
            "Pillar Levels"
        )
        
        self.sector_data = self._load_yaml_file(
            self.config.get('ukg_paths', {}).get('sectors', 'data/ukg/sectors.yaml'),
            "Sectors"
        )
        
        self.topics_data = self._load_yaml_file(
            self.config.get('ukg_paths', {}).get('topics', 'data/ukg/topics.yaml'),
            "Topics"
        )
        
        self.methods_data = self._load_yaml_file(
            self.config.get('ukg_paths', {}).get('methods', 'data/ukg/methods.yaml'),
            "Methods"
        )
        
        self.tools_data = self._load_yaml_file(
            self.config.get('ukg_paths', {}).get('tools', 'data/ukg/tools.yaml'),
            "Tools"
        )
        
        self.regulatory_frameworks_data = self._load_yaml_file(
            self.config.get('ukg_paths', {}).get('regulatory_frameworks', 'data/ukg/regulatory_frameworks.yaml'),
            "Regulatory Frameworks"
        )
        
        self.compliance_standards_data = self._load_yaml_file(
            self.config.get('ukg_paths', {}).get('compliance_standards', 'data/ukg/compliance_standards.yaml'),
            "Compliance Standards"
        )
        
        self.personas_data = self._load_yaml_file(
            self.config.get('ukg_paths', {}).get('personas', 'data/ukg/personas.yaml'),
            "Personas"
        )
        
        self.time_periods_data = self._load_yaml_file(
            self.config.get('ukg_paths', {}).get('time_periods', 'data/ukg/time_periods.yaml'),
            "Time Periods"
        )
    
    def _load_yaml_file(self, file_path, description):
        """
        Load data from a YAML file.
        
        Args:
            file_path (str): Path to the YAML file
            description (str): Description of the file for logging
            
        Returns:
            dict: The loaded data, or an empty dict if loading failed
        """
        try:
            if not os.path.exists(file_path):
                logging.warning(f"[{datetime.now()}] GM: {description} file not found: {file_path}")
                return {}
            
            with open(file_path, 'r') as file:
                data = yaml.safe_load(file)
                logging.info(f"[{datetime.now()}] GM: Loaded {description} from {file_path}")
                return data
        except Exception as e:
            logging.error(f"[{datetime.now()}] GM: Error loading {description} from {file_path}: {str(e)}")
            return {}
    
    def _build_initial_graph_structure(self):
        """Build the initial graph structure from loaded definitions."""
        # Create root node for the UKG
        ukg_root_uid_pkg = self.united_system_manager.create_unified_id(
            entity_label="UKG_Root",
            entity_type="RootNode"
        )
        ukg_root_uid = ukg_root_uid_pkg["uid_string"]
        self.graph.add_node(ukg_root_uid, **ukg_root_uid_pkg)
        
        # Create nodes for the 13 axes
        self._create_axis_nodes(ukg_root_uid)
        
        # Create nodes for Pillar Levels (Axis 1)
        self._create_pillar_level_nodes()
        
        # Create nodes for Sectors (Axis 2)
        self._create_sector_nodes()
        
        # Create nodes for Topics (Axis 3)
        self._create_topic_nodes()
        
        # Create nodes for Methods (Axis 4)
        # (Placeholder - can be implemented later)
        
        # Create nodes for Tools (Axis 5)
        # (Placeholder - can be implemented later)
        
        # Create nodes for Regulatory Frameworks (Axis 6)
        self._create_regulatory_framework_nodes()
        
        # Create nodes for Compliance Standards (Axis 7)
        self._create_compliance_standard_nodes()
        
        # Create nodes for Personas (Axis 8-11)
        self._create_persona_nodes()
        
        # Create nodes for Locations (Axis 12)
        self._create_location_nodes()
        
        # Create nodes for Time (Axis 13)
        # (Placeholder - can be implemented later)
    
    def _create_axis_nodes(self, ukg_root_uid):
        """
        Create nodes for the 13 axes of the UKG.
        
        Args:
            ukg_root_uid (str): UID of the UKG root node
        """
        logging.info(f"[{datetime.now()}] GM: Creating Axis nodes")
        
        if 'Axes' not in self.axis_definitions_data:
            logging.warning(f"[{datetime.now()}] GM: No Axes defined in axis_definitions.yaml")
            return
        
        for axis_def in self.axis_definitions_data['Axes']:
            axis_label = axis_def.get('label', 'Unknown Axis')
            axis_number = axis_def.get('number', 0)
            axis_description = axis_def.get('description', '')
            axis_original_id = axis_def.get('original_id', f"Axis{axis_number}")
            
            axis_uid_pkg = self.united_system_manager.create_unified_id(
                entity_label=axis_label,
                entity_type="Axis",
                ukg_coords={"AxisNumber": axis_number},
                specific_id_part=axis_original_id
            )
            
            axis_uid = axis_uid_pkg["uid_string"]
            
            # Store the UID string in the axis definition for later reference
            axis_def['uid_string'] = axis_uid
            
            # Add axis node to the graph
            self.graph.add_node(
                axis_uid,
                label=axis_label,
                number=axis_number,
                description=axis_description,
                original_id=axis_original_id,
                **axis_uid_pkg
            )
            
            # Connect axis to UKG root
            self.graph.add_edge(ukg_root_uid, axis_uid, relationship="has_axis")
            
            logging.info(f"[{datetime.now()}] GM: Added Axis {axis_number}: {axis_label} (UID: {axis_uid[:10]}...)")
    
    def _create_pillar_level_nodes(self):
        """Create nodes for Pillar Levels (Axis 1)."""
        logging.info(f"[{datetime.now()}] GM: Creating Pillar Level nodes")
        
        axis1_uid_str = self._get_axis_uid_by_number(1)
        if not axis1_uid_str:
            logging.warning(f"[{datetime.now()}] GM: Axis 1 UID not found, cannot create Pillar Level nodes")
            return
        
        if 'PillarLevels' not in self.pillar_levels_data:
            logging.warning(f"[{datetime.now()}] GM: No Pillar Levels defined in pillar_levels.yaml")
            return
        
        for pl_def in self.pillar_levels_data['PillarLevels']:
            pl_original_id = pl_def.get('id', 'Unknown_PL')
            pl_label = pl_def.get('label', 'Unknown Pillar Level')
            pl_description = pl_def.get('description', '')
            
            # Create UID for Pillar Level
            pl_uid_pkg = self.united_system_manager.create_unified_id(
                entity_label=pl_label,
                entity_type="PillarLevel",
                ukg_coords={"Axis1": pl_original_id},
                specific_id_part=pl_original_id
            )
            
            pl_uid = pl_uid_pkg["uid_string"]
            
            # Store UID in definition for later reference
            pl_def['uid_string'] = pl_uid
            
            # Add node to graph
            self.graph.add_node(
                pl_uid,
                label=pl_label,
                description=pl_description,
                original_id=pl_original_id,
                **pl_uid_pkg
            )
            
            # Connect to Axis 1
            self.graph.add_edge(axis1_uid_str, pl_uid, relationship="has_pillar_level")
            
            # Create nodes for PL members if defined
            if 'members' in pl_def and isinstance(pl_def['members'], list):
                for member_def in pl_def['members']:
                    member_label = member_def.get('label', 'Unknown Member')
                    member_id = member_def.get('id', 'Unknown_Member')
                    
                    member_uid_pkg = self.united_system_manager.create_unified_id(
                        entity_label=member_label,
                        entity_type="PillarLevelMember",
                        ukg_coords={"Axis1": pl_original_id, "MemberID": member_id},
                        specific_id_part=member_id
                    )
                    
                    member_uid = member_uid_pkg["uid_string"]
                    
                    # Add member node
                    self.graph.add_node(
                        member_uid,
                        label=member_label,
                        original_id=member_id,
                        **member_uid_pkg
                    )
                    
                    # Connect member to Pillar Level
                    self.graph.add_edge(pl_uid, member_uid, relationship="has_member")
            
            logging.info(f"[{datetime.now()}] GM: Added Pillar Level: {pl_label} (UID: {pl_uid[:10]}...)")
    
    def _create_sector_nodes(self):
        """Create nodes for Sectors (Axis 2)."""
        logging.info(f"[{datetime.now()}] GM: Creating Sector nodes")
        
        axis2_uid_str = self._get_axis_uid_by_number(2)
        if not axis2_uid_str:
            logging.warning(f"[{datetime.now()}] GM: Axis 2 UID not found, cannot create Sector nodes")
            return
        
        if 'Sectors' not in self.sector_data:
            logging.warning(f"[{datetime.now()}] GM: No Sectors defined in sectors.yaml")
            return
        
        for sector_def in self.sector_data['Sectors']:
            sector_original_id = sector_def.get('id', 'Unknown_Sector')
            sector_label = sector_def.get('label', 'Unknown Sector')
            sector_description = sector_def.get('description', '')
            sector_code = sector_def.get('code', '')
            
            # Create UID for Sector
            sector_uid_pkg = self.united_system_manager.create_unified_id(
                entity_label=sector_label,
                entity_type="Sector",
                ukg_coords={"Axis2": sector_original_id, "SectorCode": sector_code},
                specific_id_part=sector_original_id
            )
            
            sector_uid = sector_uid_pkg["uid_string"]
            
            # Store UID in definition for later reference
            sector_def['uid_string'] = sector_uid
            
            # Add node to graph
            self.graph.add_node(
                sector_uid,
                label=sector_label,
                description=sector_description,
                code=sector_code,
                original_id=sector_original_id,
                **sector_uid_pkg
            )
            
            # Connect to Axis 2
            self.graph.add_edge(axis2_uid_str, sector_uid, relationship="has_sector")
            
            # Create subsector nodes if defined
            if 'subsectors' in sector_def and isinstance(sector_def['subsectors'], list):
                for subsector_def in sector_def['subsectors']:
                    subsector_label = subsector_def.get('label', 'Unknown Subsector')
                    subsector_id = subsector_def.get('id', 'Unknown_Subsector')
                    subsector_code = subsector_def.get('code', '')
                    
                    subsector_uid_pkg = self.united_system_manager.create_unified_id(
                        entity_label=subsector_label,
                        entity_type="Subsector",
                        ukg_coords={"Axis2": sector_original_id, "SubsectorID": subsector_id, "SubsectorCode": subsector_code},
                        specific_id_part=subsector_id
                    )
                    
                    subsector_uid = subsector_uid_pkg["uid_string"]
                    
                    # Add subsector node
                    self.graph.add_node(
                        subsector_uid,
                        label=subsector_label,
                        code=subsector_code,
                        original_id=subsector_id,
                        **subsector_uid_pkg
                    )
                    
                    # Connect subsector to Sector
                    self.graph.add_edge(sector_uid, subsector_uid, relationship="has_subsector")
            
            logging.info(f"[{datetime.now()}] GM: Added Sector: {sector_label} (UID: {sector_uid[:10]}...)")
    
    def _create_topic_nodes(self):
        """Create nodes for Topics (Axis 3)."""
        logging.info(f"[{datetime.now()}] GM: Creating Topic nodes")
        
        axis3_uid_str = self._get_axis_uid_by_number(3)
        if not axis3_uid_str:
            logging.warning(f"[{datetime.now()}] GM: Axis 3 UID not found, cannot create Topic nodes")
            return
        
        if 'Topics' not in self.topics_data:
            logging.warning(f"[{datetime.now()}] GM: No Topics defined in topics.yaml")
            return
        
        for topic_def in self.topics_data['Topics']:
            topic_original_id = topic_def.get('id', 'Unknown_Topic')
            topic_label = topic_def.get('label', 'Unknown Topic')
            topic_description = topic_def.get('description', '')
            
            # Create UID for Topic
            topic_uid_pkg = self.united_system_manager.create_unified_id(
                entity_label=topic_label,
                entity_type="Topic",
                ukg_coords={"Axis3": topic_original_id},
                specific_id_part=topic_original_id
            )
            
            topic_uid = topic_uid_pkg["uid_string"]
            
            # Store UID in definition for later reference
            topic_def['uid_string'] = topic_uid
            
            # Add node to graph
            self.graph.add_node(
                topic_uid,
                label=topic_label,
                description=topic_description,
                original_id=topic_original_id,
                **topic_uid_pkg
            )
            
            # Connect to Axis 3
            self.graph.add_edge(axis3_uid_str, topic_uid, relationship="has_topic")
            
            # Create subtopic nodes if defined
            if 'subtopics' in topic_def and isinstance(topic_def['subtopics'], list):
                for subtopic_def in topic_def['subtopics']:
                    subtopic_label = subtopic_def.get('label', 'Unknown Subtopic')
                    subtopic_id = subtopic_def.get('id', 'Unknown_Subtopic')
                    
                    subtopic_uid_pkg = self.united_system_manager.create_unified_id(
                        entity_label=subtopic_label,
                        entity_type="Subtopic",
                        ukg_coords={"Axis3": topic_original_id, "SubtopicID": subtopic_id},
                        specific_id_part=subtopic_id
                    )
                    
                    subtopic_uid = subtopic_uid_pkg["uid_string"]
                    
                    # Add subtopic node
                    self.graph.add_node(
                        subtopic_uid,
                        label=subtopic_label,
                        original_id=subtopic_id,
                        **subtopic_uid_pkg
                    )
                    
                    # Connect subtopic to Topic
                    self.graph.add_edge(topic_uid, subtopic_uid, relationship="has_subtopic")
            
            logging.info(f"[{datetime.now()}] GM: Added Topic: {topic_label} (UID: {topic_uid[:10]}...)")
    
    def _create_regulatory_framework_nodes(self):
        """Create nodes for Regulatory Frameworks (Axis 6)."""
        logging.info(f"[{datetime.now()}] GM: Creating Regulatory Framework nodes")
        
        axis6_uid_str = self._get_axis_uid_by_number(6)
        if not axis6_uid_str:
            logging.warning(f"[{datetime.now()}] GM: Axis 6 UID not found, cannot create Regulatory Framework nodes")
            return
        
        if 'RegulatoryFrameworks' not in self.regulatory_frameworks_data:
            logging.warning(f"[{datetime.now()}] GM: No Regulatory Frameworks defined in regulatory_frameworks.yaml")
            return
        
        for reg_def in self.regulatory_frameworks_data['RegulatoryFrameworks']:
            reg_original_id = reg_def.get('id', 'Unknown_Regulation')
            reg_label = reg_def.get('label', 'Unknown Regulatory Framework')
            reg_description = reg_def.get('description', '')
            reg_jurisdiction = reg_def.get('jurisdiction', 'Unknown')
            
            # Create UID for Regulatory Framework
            reg_uid_pkg = self.united_system_manager.create_unified_id(
                entity_label=reg_label,
                entity_type="RegulatoryFramework",
                ukg_coords={"Axis6": reg_original_id, "Jurisdiction": reg_jurisdiction},
                specific_id_part=reg_original_id
            )
            
            reg_uid = reg_uid_pkg["uid_string"]
            
            # Store UID in definition for later reference
            reg_def['uid_string'] = reg_uid
            
            # Add node to graph
            self.graph.add_node(
                reg_uid,
                label=reg_label,
                description=reg_description,
                jurisdiction=reg_jurisdiction,
                original_id=reg_original_id,
                **reg_uid_pkg
            )
            
            # Connect to Axis 6
            self.graph.add_edge(axis6_uid_str, reg_uid, relationship="has_regulatory_framework")
            
            # Create regulation sections if defined
            if 'sections' in reg_def and isinstance(reg_def['sections'], list):
                for section_def in reg_def['sections']:
                    section_label = section_def.get('label', 'Unknown Section')
                    section_id = section_def.get('id', 'Unknown_Section')
                    section_number = section_def.get('number', '')
                    
                    section_uid_pkg = self.united_system_manager.create_unified_id(
                        entity_label=section_label,
                        entity_type="RegulationSection",
                        ukg_coords={"Axis6": reg_original_id, "SectionID": section_id, "SectionNumber": section_number},
                        specific_id_part=section_id
                    )
                    
                    section_uid = section_uid_pkg["uid_string"]
                    
                    # Add section node
                    self.graph.add_node(
                        section_uid,
                        label=section_label,
                        number=section_number,
                        original_id=section_id,
                        **section_uid_pkg
                    )
                    
                    # Connect section to Regulatory Framework
                    self.graph.add_edge(reg_uid, section_uid, relationship="has_section")
            
            logging.info(f"[{datetime.now()}] GM: Added Regulatory Framework: {reg_label} (UID: {reg_uid[:10]}...)")
    
    def _create_compliance_standard_nodes(self):
        """Create nodes for Compliance Standards (Axis 7)."""
        logging.info(f"[{datetime.now()}] GM: Creating Compliance Standard nodes")
        
        axis7_uid_str = self._get_axis_uid_by_number(7)
        if not axis7_uid_str:
            logging.warning(f"[{datetime.now()}] GM: Axis 7 UID not found, cannot create Compliance Standard nodes")
            return
        
        if 'ComplianceStandards' not in self.compliance_standards_data:
            logging.warning(f"[{datetime.now()}] GM: No Compliance Standards defined in compliance_standards.yaml")
            return
        
        for std_def in self.compliance_standards_data['ComplianceStandards']:
            std_original_id = std_def.get('id', 'Unknown_Standard')
            std_label = std_def.get('label', 'Unknown Compliance Standard')
            std_description = std_def.get('description', '')
            std_version = std_def.get('version', '')
            
            # Create UID for Compliance Standard
            std_uid_pkg = self.united_system_manager.create_unified_id(
                entity_label=std_label,
                entity_type="ComplianceStandard",
                ukg_coords={"Axis7": std_original_id, "Version": std_version},
                specific_id_part=std_original_id
            )
            
            std_uid = std_uid_pkg["uid_string"]
            
            # Store UID in definition for later reference
            std_def['uid_string'] = std_uid
            
            # Add node to graph
            self.graph.add_node(
                std_uid,
                label=std_label,
                description=std_description,
                version=std_version,
                original_id=std_original_id,
                **std_uid_pkg
            )
            
            # Connect to Axis 7
            self.graph.add_edge(axis7_uid_str, std_uid, relationship="has_compliance_standard")
            
            # Create control nodes if defined
            if 'controls' in std_def and isinstance(std_def['controls'], list):
                for control_def in std_def['controls']:
                    control_label = control_def.get('label', 'Unknown Control')
                    control_id = control_def.get('id', 'Unknown_Control')
                    control_number = control_def.get('number', '')
                    
                    control_uid_pkg = self.united_system_manager.create_unified_id(
                        entity_label=control_label,
                        entity_type="ComplianceControl",
                        ukg_coords={"Axis7": std_original_id, "ControlID": control_id, "ControlNumber": control_number},
                        specific_id_part=control_id
                    )
                    
                    control_uid = control_uid_pkg["uid_string"]
                    
                    # Add control node
                    self.graph.add_node(
                        control_uid,
                        label=control_label,
                        number=control_number,
                        original_id=control_id,
                        **control_uid_pkg
                    )
                    
                    # Connect control to Compliance Standard
                    self.graph.add_edge(std_uid, control_uid, relationship="has_control")
            
            logging.info(f"[{datetime.now()}] GM: Added Compliance Standard: {std_label} (UID: {std_uid[:10]}...)")
    
    def _create_persona_nodes(self):
        """Create nodes for Personas (Axis 8-11)."""
        logging.info(f"[{datetime.now()}] GM: Creating Persona nodes")
        
        # Map persona types to axis numbers
        persona_axis_map = {
            "KnowledgeExpert": 8,
            "SkillExpert": 9,
            "RoleExpert": 10,
            "ContextExpert": 11
        }
        
        if 'Personas' not in self.personas_data:
            logging.warning(f"[{datetime.now()}] GM: No Personas defined in personas.yaml")
            return
        
        for persona_def in self.personas_data['Personas']:
            persona_type = persona_def.get('type', '')
            if persona_type not in persona_axis_map:
                logging.warning(f"[{datetime.now()}] GM: Unknown persona type: {persona_type}")
                continue
            
            axis_number = persona_axis_map[persona_type]
            axis_uid_str = self._get_axis_uid_by_number(axis_number)
            if not axis_uid_str:
                logging.warning(f"[{datetime.now()}] GM: Axis {axis_number} UID not found, cannot create {persona_type} nodes")
                continue
            
            persona_original_id = persona_def.get('id', f'Unknown_{persona_type}')
            persona_label = persona_def.get('label', f'Unknown {persona_type}')
            persona_description = persona_def.get('description', '')
            
            # Create UID for Persona
            persona_uid_pkg = self.united_system_manager.create_unified_id(
                entity_label=persona_label,
                entity_type=persona_type,
                ukg_coords={f"Axis{axis_number}": persona_original_id},
                specific_id_part=persona_original_id
            )
            
            persona_uid = persona_uid_pkg["uid_string"]
            
            # Store UID in definition for later reference
            persona_def['uid_string'] = persona_uid
            
            # Add node to graph
            self.graph.add_node(
                persona_uid,
                label=persona_label,
                description=persona_description,
                type=persona_type,
                original_id=persona_original_id,
                **persona_uid_pkg
            )
            
            # Connect to appropriate Axis
            self.graph.add_edge(axis_uid_str, persona_uid, relationship=f"has_{persona_type.lower()}")
            
            # Create subtypes if defined
            if 'subtypes' in persona_def and isinstance(persona_def['subtypes'], list):
                for subtype_def in persona_def['subtypes']:
                    subtype_label = subtype_def.get('label', f'Unknown {persona_type} Subtype')
                    subtype_id = subtype_def.get('id', f'Unknown_{persona_type}_Subtype')
                    
                    subtype_uid_pkg = self.united_system_manager.create_unified_id(
                        entity_label=subtype_label,
                        entity_type=f"{persona_type}Subtype",
                        ukg_coords={f"Axis{axis_number}": persona_original_id, "SubtypeID": subtype_id},
                        specific_id_part=subtype_id
                    )
                    
                    subtype_uid = subtype_uid_pkg["uid_string"]
                    
                    # Add subtype node
                    self.graph.add_node(
                        subtype_uid,
                        label=subtype_label,
                        original_id=subtype_id,
                        **subtype_uid_pkg
                    )
                    
                    # Connect subtype to Persona
                    self.graph.add_edge(persona_uid, subtype_uid, relationship="has_subtype")
            
            logging.info(f"[{datetime.now()}] GM: Added {persona_type}: {persona_label} (UID: {persona_uid[:10]}...)")
    
    def _create_location_nodes(self):
        """Create nodes for Locations (Axis 12)."""
        logging.info(f"[{datetime.now()}] GM: Creating Location nodes")
        
        axis12_uid_str = self._get_axis_uid_by_number(12)
        if not axis12_uid_str:
            logging.warning(f"[{datetime.now()}] GM: Axis 12 UID not found, cannot create Location nodes")
            return
            
        location_data_path = self.config_or_default_path_for_locations
        raw_location_data = self._load_yaml_file(location_data_path, "Locations Gazetteer")
            
        if raw_location_data and 'Locations' in raw_location_data:
            # Process top-level locations first
            for loc_def in raw_location_data['Locations']:
                self._add_location_node_recursive(loc_def, axis12_uid_str, parent_loc_uid=None)
        else:
            logging.warning(f"[{datetime.now()}] GM: Location gazetteer data not found or invalid at {location_data_path}")
    
    def _add_location_node_recursive(self, loc_def, axis12_uid, parent_loc_uid=None):
        """
        Recursively adds location nodes and their children to the graph.
        
        Args:
            loc_def (dict): Location definition 
            axis12_uid (str): UID of Axis 12
            parent_loc_uid (str, optional): UID of parent location
        """
        loc_original_id = loc_def["loc_id"]
        loc_label = loc_def["loc_label"]
        
        loc_uid_pkg = self.united_system_manager.create_unified_id(
            entity_label=loc_label,
            entity_type=loc_def.get("type", "Location"),  # Specific type like "Country", "City"
            ukg_coords={"Axis12": loc_original_id, "ISO": loc_def.get("iso_code","N/A")},  # Main Axis 12 context
            specific_id_part=loc_original_id
        )
        loc_uid = loc_uid_pkg["uid_string"]
        
        node_attributes = {
            "label": loc_label, "type": loc_def.get("type", "Location"), 
            "original_id": loc_original_id,
            "iso_code": loc_def.get("iso_code"),
            "latitude": loc_def.get("latitude"),  # For precise points
            "longitude": loc_def.get("longitude"),
            "linked_regulatory_framework_uids": loc_def.get("linked_regulatory_framework_uids", []),
            **loc_uid_pkg
        }
        # Remove None values from attributes before adding node
        node_attributes = {k:v for k,v in node_attributes.items() if v is not None}
        self.graph.add_node(loc_uid, **node_attributes)
        
        if parent_loc_uid:  # Link to parent location
            self.graph.add_edge(parent_loc_uid, loc_uid, relationship="contains_sub_location")
        else:  # Link top-level location to Axis12 node
            self.graph.add_edge(axis12_uid, loc_uid, relationship="has_location_entry")
        
        logging.debug(f"    GM_Axis12: Added Location Node '{loc_label}' (UID {loc_uid[:10]}...)")
        
        # Process children
        for child_loc_def in loc_def.get("children", []):
            self._add_location_node_recursive(child_loc_def, axis12_uid, parent_loc_uid=loc_uid)
        # Process precise points if any (not hierarchical children, but associated points)
        for precise_point_def in loc_def.get("precise_locations", []):
            self._add_location_node_recursive(precise_point_def, axis12_uid, parent_loc_uid=loc_uid)  # Points are children of their city/region
    
    def _build_graph_connections(self):
        """Build connections between nodes across different axes."""
        logging.info(f"[{datetime.now()}] GM: Building cross-axis connections")
        
        # Build connections from Pillar Levels to Topics
        self._connect_pillar_levels_to_topics()
        
        # Build connections from Sectors to Regulatory Frameworks
        self._connect_sectors_to_regulatory_frameworks()
        
        # Build connections from Regulatory Frameworks to Compliance Standards
        self._connect_regulatory_to_compliance()
        
        # Build connections from Locations to Regulatory Frameworks
        self._connect_locations_to_regulatory_frameworks()
    
    def _connect_pillar_levels_to_topics(self):
        """Connect Pillar Level nodes to relevant Topic nodes."""
        # This would be implemented based on relationships defined in YAML files
        # For simplicity, not fully implemented in this example
        pass
    
    def _connect_sectors_to_regulatory_frameworks(self):
        """Connect Sector nodes to relevant Regulatory Framework nodes."""
        # This would be implemented based on relationships defined in YAML files
        # For simplicity, not fully implemented in this example
        pass
    
    def _connect_regulatory_to_compliance(self):
        """Connect Regulatory Framework nodes to relevant Compliance Standard nodes."""
        # This would be implemented based on relationships defined in YAML files
        # For simplicity, not fully implemented in this example
        pass
    
    def _connect_locations_to_regulatory_frameworks(self):
        """Connect Location nodes to relevant Regulatory Framework nodes."""
        # Iterate through all location nodes
        location_nodes = [node for node, attr in self.graph.nodes(data=True) 
                         if attr.get('entity_type', '').lower() in ['country', 'state', 'city', 'region', 'supranationalregion']]
        
        for loc_uid in location_nodes:
            # Get linked regulatory framework UIDs
            linked_reg_uids = self.graph.nodes[loc_uid].get('linked_regulatory_framework_uids', [])
            
            # Connect each location to its linked regulatory frameworks
            for reg_uid in linked_reg_uids:
                if self.graph.has_node(reg_uid):
                    self.graph.add_edge(loc_uid, reg_uid, relationship="subject_to_regulation")
                    logging.debug(f"    GM: Connected Location {self.graph.nodes[loc_uid].get('label')} to Regulatory Framework {reg_uid[:10]}...")
    
    def _get_axis_uid_by_number(self, axis_number):
        """
        Get the UID for an axis by its number.
        
        Args:
            axis_number (int): The axis number
            
        Returns:
            str: The axis UID or None if not found
        """
        for axis_def in self.axis_definitions_data.get('Axes', []):
            if axis_def.get('number') == axis_number and 'uid_string' in axis_def:
                return axis_def['uid_string']
        return None
    
    def get_node_data_by_uid(self, uid):
        """
        Get all data for a node with the given UID.
        
        Args:
            uid (str): The UID of the node
            
        Returns:
            dict: Node attributes or None if not found
        """
        if self.graph.has_node(uid):
            return dict(self.graph.nodes[uid])
        return None
    
    def get_node_data_by_attribute(self, attribute_name, attribute_value, node_type=None):
        """
        Get a node UID that matches the specified attribute.
        
        Args:
            attribute_name (str): The name of the attribute
            attribute_value (str): The value to match
            node_type (str, optional): Filter by node type
            
        Returns:
            str: The UID of the first matching node, or None if not found
        """
        for node, attrs in self.graph.nodes(data=True):
            if attribute_name in attrs and attrs[attribute_name] == attribute_value:
                if node_type is None or attrs.get('entity_type') == node_type:
                    return node
        return None
    
    def get_pillar_level_uid(self, pl_original_id):
        """
        Get the UID for a Pillar Level by its original ID.
        
        Args:
            pl_original_id (str): The original ID of the Pillar Level
            
        Returns:
            str: The UID or None if not found
        """
        return self.get_node_data_by_attribute('original_id', pl_original_id, 'PillarLevel')
    
    def get_axis_uid(self, axis_original_id):
        """
        Get the UID for an Axis by its original ID.
        
        Args:
            axis_original_id (str): The original ID of the axis
            
        Returns:
            str: The UID or None if not found
        """
        return self.get_node_data_by_attribute('original_id', axis_original_id, 'Axis')
    
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

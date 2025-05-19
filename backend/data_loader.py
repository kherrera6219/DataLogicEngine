import os
import yaml
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

class UkgDataLoader:
    """
    Utility class for loading data into the UKG database from YAML or JSON files.
    This is used to populate the database with initial data like locations,
    regulatory frameworks, etc.
    """
    
    def __init__(self, config=None, ukg_db_manager=None):
        """
        Initialize the data loader.
        
        Args:
            config (dict, optional): Configuration dictionary
            ukg_db_manager (UkgDatabaseManager, optional): Database manager for UKG operations
        """
        self.config = config or {}
        self.db_manager = ukg_db_manager
        self.data_dir = self.config.get('data_directory', './data')
        
        # Default file paths
        self.locations_file = os.path.join(self.data_dir, 'locations_gazetteer.yaml')
        self.regulations_file = os.path.join(self.data_dir, 'regulatory_frameworks.yaml')
        
        logging.info(f"[{datetime.now()}] UkgDataLoader initialized with data directory: {self.data_dir}")
    
    def load_locations(self, file_path=None):
        """
        Load location data from a YAML or JSON file.
        
        Args:
            file_path (str, optional): Path to the locations file
                
        Returns:
            bool: True if loading succeeded, False otherwise
        """
        path = file_path or self.locations_file
        logging.info(f"[{datetime.now()}] Loading locations from {path}")
        
        if not os.path.exists(path):
            logging.error(f"[{datetime.now()}] Location file not found at {path}")
            return False
        
        try:
            # Load data
            data = self._load_file(path)
            if not data or 'locations' not in data:
                logging.error(f"[{datetime.now()}] No 'locations' key found in {path}")
                return False
            
            # Process locations recursively
            location_count = 0
            for location in data['locations']:
                self._process_location_recursive(location)
                location_count += 1
                
            logging.info(f"[{datetime.now()}] Successfully loaded {location_count} top-level locations")
            return True
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] Error loading locations: {str(e)}")
            return False
    
    def _process_location_recursive(self, loc_def, parent_uid=None):
        """
        Process a location definition and all its children recursively.
        
        Args:
            loc_def (dict): Location definition dictionary
            parent_uid (str, optional): Parent location UID
            
        Returns:
            str: The UID of the created location node
        """
        if not self.db_manager:
            logging.warning(f"[{datetime.now()}] No DB manager available, skipping location: {loc_def.get('id', 'unknown')}")
            return None
            
        # Create a unique ID for this location
        node_uid = str(uuid.uuid4())
        
        # Extract basic node properties
        loc_id = loc_def.get('id')
        loc_type = loc_def.get('type', 'Location')
        loc_label = loc_def.get('label', f"Location {loc_id}")
        loc_desc = loc_def.get('description', '')
        
        # Extract attributes
        attributes = loc_def.get('attributes', {})
        
        # If there are regulatory frameworks linked to this location, add them
        if 'regulatory_frameworks' in attributes:
            pass  # We'll handle these when processing regulatory frameworks
        
        # Add the node to the database
        try:
            # Create the location node
            self.db_manager.add_node(
                uid=node_uid,
                node_type=f"Location{loc_type}",
                label=loc_label,
                description=loc_desc,
                original_id=loc_id,
                axis_number=12,  # Axis 12 is for locations
                attributes=attributes
            )
            
            logging.debug(f"[{datetime.now()}] Added location node: {loc_label} (ID: {loc_id})")
            
            # Link to parent if exists
            if parent_uid:
                self.db_manager.add_edge(
                    source_uid=parent_uid,
                    target_uid=node_uid,
                    edge_type="contains_sub_location",
                    label=f"Contains {loc_label}",
                    attributes={"relationship_type": "hierarchical"}
                )
                
                logging.debug(f"[{datetime.now()}] Linked location {loc_id} to parent")
            
            # Process children recursively
            if 'children' in loc_def and isinstance(loc_def['children'], list):
                for child in loc_def['children']:
                    self._process_location_recursive(child, node_uid)
            
            return node_uid
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] Error adding location node {loc_id}: {str(e)}")
            return None
    
    def load_regulatory_frameworks(self, file_path=None):
        """
        Load regulatory framework data from a YAML or JSON file.
        
        Args:
            file_path (str, optional): Path to the regulatory frameworks file
                
        Returns:
            bool: True if loading succeeded, False otherwise
        """
        path = file_path or self.regulations_file
        logging.info(f"[{datetime.now()}] Loading regulatory frameworks from {path}")
        
        if not os.path.exists(path):
            logging.error(f"[{datetime.now()}] Regulatory frameworks file not found at {path}")
            return False
        
        try:
            # Load data
            data = self._load_file(path)
            if not data or 'regulatory_frameworks' not in data:
                logging.error(f"[{datetime.now()}] No 'regulatory_frameworks' key found in {path}")
                return False
            
            # Process regulatory frameworks
            framework_count = 0
            for framework in data['regulatory_frameworks']:
                self._process_regulatory_framework(framework)
                framework_count += 1
                
            logging.info(f"[{datetime.now()}] Successfully loaded {framework_count} regulatory frameworks")
            return True
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] Error loading regulatory frameworks: {str(e)}")
            return False
    
    def _process_regulatory_framework(self, reg_def):
        """
        Process a regulatory framework definition.
        
        Args:
            reg_def (dict): Regulatory framework definition dictionary
            
        Returns:
            str: The UID of the created regulatory framework node
        """
        if not self.db_manager:
            logging.warning(f"[{datetime.now()}] No DB manager available, skipping framework: {reg_def.get('id', 'unknown')}")
            return None
            
        # Create a unique ID for this framework
        node_uid = str(uuid.uuid4())
        
        # Extract basic node properties
        reg_id = reg_def.get('id')
        reg_label = reg_def.get('label', f"Regulatory Framework {reg_id}")
        reg_desc = reg_def.get('description', '')
        jurisdiction = reg_def.get('jurisdiction_scope', 'unknown')
        
        # Extract attributes
        attributes = reg_def.get('attributes', {})
        attributes['jurisdiction_scope'] = jurisdiction
        
        # Add the node to the database
        try:
            # Create the regulatory framework node
            self.db_manager.add_node(
                uid=node_uid,
                node_type="RegulatoryFrameworkNode",
                label=reg_label,
                description=reg_desc,
                original_id=reg_id,
                axis_number=12,  # Linked to Axis 12 (Locations)
                attributes=attributes
            )
            
            logging.debug(f"[{datetime.now()}] Added regulatory framework node: {reg_label} (ID: {reg_id})")
            
            # Link to locations if explicitly defined
            if 'associated_location' in attributes:
                loc_id = attributes['associated_location']
                loc_node = self.db_manager.get_node_by_original_id(loc_id)
                
                if loc_node:
                    self.db_manager.add_edge(
                        source_uid=node_uid,
                        target_uid=loc_node['uid'],
                        edge_type="applies_to_location",
                        label=f"Applies to {loc_node['label']}",
                        attributes={"relationship_type": "regulatory"}
                    )
                    logging.debug(f"[{datetime.now()}] Linked regulatory framework {reg_id} to location {loc_id}")
            
            return node_uid
            
        except Exception as e:
            logging.error(f"[{datetime.now()}] Error adding regulatory framework node {reg_id}: {str(e)}")
            return None
    
    def _load_file(self, file_path):
        """
        Load data from a YAML or JSON file.
        
        Args:
            file_path (str): Path to the file to load
            
        Returns:
            dict: The loaded data or None if loading failed
        """
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ('.yaml', '.yml'):
                with open(file_path, 'r') as f:
                    return yaml.safe_load(f)
            elif file_ext == '.json':
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                logging.error(f"[{datetime.now()}] Unsupported file format: {file_ext}")
                return None
                
        except Exception as e:
            logging.error(f"[{datetime.now()}] Error loading file {file_path}: {str(e)}")
            return None
    
    def load_all_data(self):
        """
        Load all available data into the UKG database.
        
        Returns:
            dict: Summary of loading results
        """
        results = {
            'locations': self.load_locations(),
            'regulatory_frameworks': self.load_regulatory_frameworks()
        }
        
        success_count = sum(1 for r in results.values() if r)
        total_count = len(results)
        
        logging.info(f"[{datetime.now()}] Data loading complete. {success_count}/{total_count} data sets loaded successfully.")
        
        return results
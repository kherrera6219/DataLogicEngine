import logging
import os
import yaml
import json
from datetime import datetime
import uuid
from .models import db, UkgNode, UkgEdge, KnowledgeAlgorithm, UkgSession
from .ukg_db import UkgDatabaseManager

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
        self.ukg_db = ukg_db_manager if ukg_db_manager else UkgDatabaseManager()
        self.data_dir = self.config.get('data_directory', 'data/ukg')
        logging.info(f"UKG Data Loader initialized with data directory: {self.data_dir}")
    
    def load_locations(self, file_path=None):
        """
        Load location data from a YAML or JSON file.
        
        Args:
            file_path (str, optional): Path to the locations file
                
        Returns:
            bool: True if loading succeeded, False otherwise
        """
        if not file_path:
            file_path = os.path.join(self.data_dir, 'locations_gazetteer.yaml')
        
        logging.info(f"Loading locations from {file_path}")
        
        try:
            data = self._load_file(file_path)
            if not data or 'Locations' not in data:
                logging.error(f"Invalid or missing location data in {file_path}")
                return False
            
            # Process top-level locations
            for loc_def in data['Locations']:
                self._process_location_recursive(loc_def, parent_uid=None)
            
            logging.info(f"Successfully loaded location data from {file_path}")
            return True
        except Exception as e:
            logging.error(f"Error loading locations: {str(e)}", exc_info=True)
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
        # Extract location information
        loc_id = loc_def.get('loc_id')
        if not loc_id:
            logging.warning(f"Skipping location without ID: {loc_def.get('loc_label', 'Unknown')}")
            return None
        
        # Create attributes dictionary
        attributes = {k: v for k, v in loc_def.items() if k not in ['loc_id', 'loc_label', 'type', 'children', 'precise_locations']}
        
        # Add the node to the database
        node = self.ukg_db.add_node(
            uid=f"loc-{str(uuid.uuid4())[:8]}-{loc_id}",
            node_type='Location',  # Can also use loc_def.get('type', 'Location')
            label=loc_def.get('loc_label', loc_id),
            description=attributes.get('description'),
            original_id=loc_id,
            attributes=attributes
        )
        
        if not node:
            logging.warning(f"Failed to create location node for {loc_id}")
            return None
        
        # If there's a parent, create the relationship
        if parent_uid:
            edge = self.ukg_db.add_edge(
                uid=f"edge-{str(uuid.uuid4())[:8]}",
                edge_type="contains_sub_location",
                source_uid=parent_uid,
                target_uid=node.uid
            )
            
            if not edge:
                logging.warning(f"Failed to create edge from {parent_uid} to {node.uid}")
        
        # Process children recursively
        for child_def in loc_def.get('children', []):
            self._process_location_recursive(child_def, parent_uid=node.uid)
        
        # Process precise locations (points within this location)
        for point_def in loc_def.get('precise_locations', []):
            self._process_location_recursive(point_def, parent_uid=node.uid)
        
        return node.uid
    
    def load_regulatory_frameworks(self, file_path=None):
        """
        Load regulatory framework data from a YAML or JSON file.
        
        Args:
            file_path (str, optional): Path to the regulatory frameworks file
                
        Returns:
            bool: True if loading succeeded, False otherwise
        """
        if not file_path:
            file_path = os.path.join(self.data_dir, 'regulatory_frameworks.yaml')
        
        logging.info(f"Loading regulatory frameworks from {file_path}")
        
        try:
            data = self._load_file(file_path)
            if not data or 'RegulatoryFrameworks' not in data:
                logging.error(f"Invalid or missing regulatory framework data in {file_path}")
                return False
            
            # Process regulatory frameworks
            for reg_def in data['RegulatoryFrameworks']:
                self._process_regulatory_framework(reg_def)
            
            logging.info(f"Successfully loaded regulatory framework data from {file_path}")
            return True
        except Exception as e:
            logging.error(f"Error loading regulatory frameworks: {str(e)}", exc_info=True)
            return False
    
    def _process_regulatory_framework(self, reg_def):
        """
        Process a regulatory framework definition.
        
        Args:
            reg_def (dict): Regulatory framework definition dictionary
            
        Returns:
            str: The UID of the created regulatory framework node
        """
        # Extract regulatory framework information
        reg_id = reg_def.get('reg_id')
        if not reg_id:
            logging.warning(f"Skipping regulatory framework without ID: {reg_def.get('reg_label', 'Unknown')}")
            return None
        
        # Create attributes dictionary
        attributes = {k: v for k, v in reg_def.items() if k not in ['reg_id', 'reg_label', 'description']}
        
        # Add the node to the database
        node = self.ukg_db.add_node(
            uid=f"reg-{str(uuid.uuid4())[:8]}-{reg_id}",
            node_type='RegulatoryFrameworkNode',
            label=reg_def.get('reg_label', reg_id),
            description=reg_def.get('description'),
            original_id=reg_id,
            attributes=attributes
        )
        
        if not node:
            logging.warning(f"Failed to create regulatory framework node for {reg_id}")
            return None
        
        return node.uid
    
    def _load_file(self, file_path):
        """
        Load data from a YAML or JSON file.
        
        Args:
            file_path (str): Path to the file to load
            
        Returns:
            dict: The loaded data or None if loading failed
        """
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return None
        
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in ['.yaml', '.yml']:
                with open(file_path, 'r') as f:
                    return yaml.safe_load(f)
            elif ext == '.json':
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                logging.error(f"Unsupported file extension: {ext}")
                return None
        except Exception as e:
            logging.error(f"Error loading file {file_path}: {str(e)}", exc_info=True)
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
        
        success_count = sum(1 for result in results.values() if result)
        total_count = len(results)
        
        logging.info(f"Data loading completed: {success_count}/{total_count} successful")
        
        return results
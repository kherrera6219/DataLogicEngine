import yaml
import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

class AxisMapper:
    """
    Axis Mapper
    
    Resolves text queries and context metadata into coordinates for Axis 1 (Pillars)
    and Axis 2 (Sectors) using the enterprise canonical definitions.
    """
    
    def __init__(self, axis1_path: Optional[str] = None, axis2_path: Optional[str] = None):
        """
        Initialize the Axis Mapper.
        
        Args:
            axis1_path: Path to Axis 1 Pillars YAML.
            axis2_path: Path to Axis 2 Sectors YAML.
        """
        base_path = os.path.dirname(__file__)
        self.axis1_path = axis1_path or os.path.join(base_path, "registry", "coordinates", "axis1_pillars.yaml")
        self.axis2_path = axis2_path or os.path.join(base_path, "registry", "coordinates", "axis2_sectors.yaml")
        
        self.pillars = []
        self.sectors = []
        
        self._load_axis_definitions()

    def _load_axis_definitions(self):
        """Load and normalize pillar and sector definitions."""
        try:
            # Load Pillar (Axis 1)
            if os.path.exists(self.axis1_path):
                with open(self.axis1_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    self.pillars = data.get('sheets', {}).get('Raw', {}).get('rows', [])
                logging.info(f"Loaded {len(self.pillars)} Pillars from Axis 1 Registry.")
            
            # Load Sector (Axis 2)
            if os.path.exists(self.axis2_path):
                with open(self.axis2_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    raw_sectors = data.get('sheets', {}).get('Raw', {}).get('rows', [])
                    
                    # Normalize columns based on observed schemas
                    for row in raw_sectors:
                        if not isinstance(row, dict):
                            continue
                            
                        # Schema 1: Unnamed cols (observed in header/first half)
                        name_u = row.get('Unnamed: 2')
                        coord_u = row.get('Unnamed: 3')
                        
                        # Schema 2: Explicit names (observed in second half)
                        title = row.get('title')
                        desc = row.get('description')
                        sector_name = row.get('sector')
                        
                        name = name_u or title
                        coord = coord_u or desc
                        
                        if name and coord:
                            # Heuristic: description/coord should look like '2.X.X.X'
                            if isinstance(coord, str) and (coord.startswith('2.') or '.' in coord):
                                self.sectors.append({
                                    "id": row.get('id'),
                                    "name": str(name),
                                    "coordinate": str(coord),
                                    "sector_group": str(sector_name or "")
                                })
                logging.info(f"Loaded {len(self.sectors)} Sectors from Axis 2 Registry.")
                
        except Exception as e:
            logging.error(f"Error loading axis definitions: {str(e)}")

    def resolve_pillar(self, text: str) -> Optional[Dict]:
        """
        Resolve the best matching Pillar for a text query.
        """
        if not text:
            return None
            
        text_lower = text.lower()
        best_match = None
        highest_score = 0
        
        stop_words = {'and', 'the', 'for', 'with', 'management', 'system', 'systems'}
        
        for pillar in self.pillars:
            if not isinstance(pillar, dict):
                continue
                
            score = 0
            name = str(pillar.get('Pillar Name', '')).lower()
            members = str(pillar.get('Top-Level Members', '')).lower()
            
            # 1. Exact Name Match
            if name and (name in text_lower or text_lower in name):
                score += 20
            
            # 2. Keyword matching for Name
            name_words = [w.strip() for w in name.split() if w.strip() and w not in stop_words]
            for word in name_words:
                if len(word) > 3 and word in text_lower:
                    score += 5
            
            # 3. Member matching
            if members:
                member_list = [m.strip().lower() for m in members.split(',')]
                for member in member_list:
                    if member and member in text_lower:
                        score += 3
            
            if score > highest_score:
                highest_score = score
                best_match = pillar
                
        return best_match

    def resolve_sector(self, text: str) -> Optional[Dict]:
        """Resolve the best matching Sector for a text query."""
        if not text:
            return None
            
        text_lower = text.lower()
        best_match = None
        highest_score = 0
        
        stop_words = {'and', 'the', 'for', 'of', 'sector', 'services'}
        
        for sector in self.sectors:
            if not isinstance(sector, dict):
                continue
                
            score = 0
            name = str(sector.get('name', '')).lower()
            group = str(sector.get('sector_group', '')).lower()
            
            # 1. Exact Name/Title Match
            if name and (name in text_lower or text_lower in name):
                score += 20
                
            # 2. Keyword matching for Name
            name_words = [w.strip() for w in name.split() if w.strip() and w not in stop_words]
            for word in name_words:
                if len(word) > 3 and word in text_lower:
                    score += 5

            # 3. Group matching
            if group:
                group_words = [w.strip() for w in group.split() if w.strip() and w not in stop_words]
                for word in group_words:
                    if len(word) > 3 and word in text_lower:
                        score += 2
                
            if score > highest_score:
                highest_score = score
                best_match = sector
                
        return best_match

    def get_17axis_vector(self, query: str, context: Optional[Dict] = None) -> Dict[int, str]:
        """
        Generate a full 17-axis coordinate vector for a query.
        
        Initial implementation fokus on Axis 1 and 2.
        Axis 14-17 are reserved for TruthEngine outcomes.
        """
        vector = {i: "0.0.0.0" for i in range(1, 18)}
        
        # Resolve Axis 1 (Pillar)
        pillar = self.resolve_pillar(query)
        if pillar:
            vector[1] = pillar.get('Axis-Coordinate ID', '1.0.0.0')
            
        # Resolve Axis 2 (Sector)
        sector = self.resolve_sector(query)
        if sector:
            vector[2] = sector.get('coordinate', '2.0.0.0')
            
        # Context-based defaults for other axes could go here
        
        return vector

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

    def _get_acronym_map(self) -> Dict[str, str]:
        return {
            "ai": "artificial intelligence",
            "ml": "machine learning",
            "it": "information technology",
            "hr": "human resources",
            "rd": "research and development",
            "nlp": "natural language processing",
            "llm": "large language model",
            "def": "decentralized finance",
            "kyc": "know your customer",
            "aml": "anti-money laundering"
        }

    def _get_stop_words(self) -> set:
        return {'and', 'the', 'for', 'with', 'of', 'management', 'system', 'systems', 'sector', 'services'}

    def _process_text(self, text: str) -> str:
        text_lower = text.lower()
        acronyms = self._get_acronym_map()
        processed_text = text_lower
        for acr, full in acronyms.items():
            if f" {acr} " in f" {text_lower} " or text_lower.startswith(acr + " ") or text_lower.endswith(" " + acr) or text_lower == acr:
                processed_text += f" {full}"
        return processed_text

    def resolve_pillar(self, text: str) -> Optional[Dict]:
        """Resolve the best matching Pillar for a text query."""
        if not text:
            return None
            
        processed_text = self._process_text(text)
        best_match = None
        highest_score = 0
        stop_words = self._get_stop_words()
        
        for pillar in self.pillars:
            if not isinstance(pillar, dict):
                continue
                
            score = 0
            name = str(pillar.get('Pillar Name', '')).lower()
            members = str(pillar.get('Top-Level Members', '')).lower()
            
            # 1. Exact Name Match
            if name and (name in processed_text or processed_text in name):
                score += 30
            
            # 2. Keyword matching for Name
            name_words = [w.strip() for w in name.split() if w.strip() and w not in stop_words]
            for word in name_words:
                if len(word) > 3:
                     if word in processed_text or word[:5] in processed_text:
                        score += 5
            
            # 3. Member matching
            if members:
                member_list = [m.strip().lower() for m in members.split(',')]
                for member in member_list:
                    if member and (member in processed_text or processed_text in member):
                        score += 3
            
            if score > highest_score:
                highest_score = score
                best_match = pillar
                
        return best_match

    def resolve_sector(self, text: str) -> Optional[Dict]:
        """Resolve the best matching Sector for a text query."""
        if not text:
            return None
            
        processed_text = self._process_text(text)
        best_match = None
        highest_score = 0
        stop_words = self._get_stop_words()
        
        for sector in self.sectors:
            if not isinstance(sector, dict):
                continue
                
            score = 0
            name = str(sector.get('name', '')).lower()
            group = str(sector.get('sector_group', '')).lower()
            
            # 1. Exact Name/Title Match
            if name and (name in processed_text or processed_text in name):
                score += 20
                
            # 2. Keyword matching for Name
            name_words = [w.strip() for w in name.split() if w.strip() and w not in stop_words]
            for word in name_words:
                if len(word) > 3 and word in processed_text:
                    score += 5
            
            # 3. Group matching
            if group and group in processed_text:
                score += 3
                
            if score > highest_score:
                highest_score = score
                best_match = sector
                
        return best_match

    def resolve_honeycomb(self, text: str, primary_pillar: Optional[Dict]) -> str:
        """Resolve Axis 3 (Honeycomb) by finding a cross-domain link."""
        query_processed = self._process_text(text)
        secondary_pillar = None
        highest_score = 0
        stop_words = self._get_stop_words()
        
        primary_id = str(primary_pillar.get('Axis-Coordinate ID')) if primary_pillar else None
        
        for pillar in self.pillars:
            if not isinstance(pillar, dict):
                continue
                
            p_id = str(pillar.get('Axis-Coordinate ID'))
            if primary_id and p_id == primary_id:
                continue
                
            score = 0
            name = str(pillar.get('Pillar Name', '')).lower()
            members = str(pillar.get('Top-Level Members', '')).lower()
            
            # 1. Exact Name Match in processed query
            if name and name in query_processed:
                score += 20
                
            # 2. Keyword matching for Name
            name_words = [w.strip() for w in name.split() if w.strip() and w not in stop_words]
            for word in name_words:
                if len(word) > 3 and word in query_processed:
                    score += 5
            
            # 3. Member matching
            if members:
                for member in [m.strip().lower() for m in members.split(',')]:
                    if member and member in query_processed:
                        score += 5
                        break
            
            if score > highest_score:
                highest_score = score
                secondary_pillar = pillar
        
        if secondary_pillar and highest_score >= 5:
            # Generate link coordinate 3.X.Y.Z where X is primary, Y is secondary
            p_id_val = primary_id.split('.')[1] if primary_id else '0'
            s_id_val = str(secondary_pillar.get('Axis-Coordinate ID', '1.0.0.0')).split('.')[1]
            return f"3.{p_id_val}.{s_id_val}.0"
            
        return "3.0.0.0"

    def resolve_branch_and_node(self, query: str, sector: Optional[Dict]) -> Tuple[str, str]:
        """Resolve Axis 4 (Branch) and Axis 5 (Node) from sector hierarchy."""
        if not sector:
            return "4.0.0.0", "5.0.0.0"
            
        coord = str(sector.get('coordinate', '2.0.0.0'))
        parts = coord.split('.')
        
        # Axis 4: Branch (Sector level 3)
        branch = f"4.{parts[1]}.{parts[2]}.0" if len(parts) > 2 else "4.0.0.0"
        # Axis 5: Node (Sector level 4)
        node = f"5.{parts[1]}.{parts[2]}.{parts[3]}" if len(parts) > 3 else "5.0.0.0"
        
        return branch, node

    def resolve_regulatory_crosswalk(self, text: str, sector: Optional[Dict]) -> Dict[str, str]:
        """Resolve Axis 6 (Octopus) and Axis 7 (Spiderweb) based on sector context."""
        results = {"axis6": "6.0.0.0", "axis7": "7.0.0.0"}
        
        query_lower = text.lower()
        name = str((sector or {}).get('name', '')).lower()
        context = name + " " + query_lower
        
        # Mapping Context Keywords to Regulatory Frameworks
        reg_map = {
            "banking": ("6.1.0.0", "7.1.0.0"),  
            "finance": ("6.1.0.0", "7.2.0.0"),  
            "healthcare": ("6.2.0.0", "7.3.0.0"), 
            "medical": ("6.2.0.0", "7.3.0.0"),
            "clinical": ("6.2.0.0", "7.3.0.0"),
            "hospital": ("6.2.0.0", "7.3.0.0"),
            "energy": ("6.3.0.0", "7.4.0.0"),     
            "technology": ("6.4.0.0", "7.5.0.0"), 
            "software": ("6.4.0.0", "7.5.0.0"),
            "blockchain": ("6.4.0.0", "7.6.0.0"),
            "crypto": ("6.4.0.0", "7.6.0.0"),
            "oil": ("6.3.0.0", "7.4.0.0")
        }
        
        for key, coords in reg_map.items():
            if key in context:
                results["axis6"] = coords[0]
                results["axis7"] = coords[1]
                break
                
        return results

    def resolve_temporal(self, text: str) -> str:
        """Resolve Axis 8 (Temporal) coordinate."""
        text_lower = text.lower()
        if "2026" in text_lower:
            return "8.6.0.0"
        if "2025" in text_lower:
            return "8.5.0.0"
        if "q1" in text_lower:
            return "8.1.1.0"
        if "real-time" in text_lower or "live" in text_lower:
            return "8.0.1.0"
        return "8.0.0.0"

    def resolve_spatial(self, text: str) -> str:
        """Resolve Axis 9 (Spatial) coordinate."""
        text_lower = text.lower()
        spatial_map = {
            "global": "9.1.0.0",
            "europe": "9.2.0.0",
            " eu ": "9.2.0.0",
            "usa": "9.3.0.0",
            "asia": "9.4.0.0"
        }
        for key, coord in spatial_map.items():
            if key in f" {text_lower} ":
                return coord
        return "9.0.0.0"

    def resolve_attribute_axes(self, text: str) -> Dict[str, str]:
        """Resolve Axes 10-13 (Quantitative, Qualitative, Actionable, Persona)."""
        text_lower = text.lower()
        results = {
            "axis10": "10.0.0.0",
            "axis11": "11.0.0.0",
            "axis12": "12.0.0.0",
            "axis13": "13.0.0.0"
        }
        
        # Quantitative heuristics
        if any(w in text_lower for w in ["budget", "allocation", "metric", "cost", "price"]):
            results["axis10"] = "10.5.0.0"
            
        # Qualitative heuristics
        if any(w in text_lower for w in ["sentiment", "impact", "ethical", "moral", "quality"]):
            results["axis11"] = "11.5.0.0"
            
        # Actionable heuristics
        if any(w in text_lower for w in ["strategy", "implementation", "deployment", "plan"]):
            results["axis12"] = "12.5.0.0"
            
        # Persona heuristics
        if any(w in text_lower for w in ["executive", "developer", "customer", "analyst"]):
            results["axis13"] = "13.5.0.0"
            
        return results

    def get_17axis_vector(self, text: str, context: Optional[Dict] = None) -> Dict[int, str]:
        """
        Generate a full 17-axis coordinate vector for a query.
        
        Args:
            text: Query text.
            context: Optional metadata context.
            
        Returns:
            Dict mapping axis ID to coordinate string.
        """
        vector = {i: "0.0.0.0" for i in range(1, 18)}
        
        # 1. Axis 1 & 2: Primary Semantic Layer
        pillar = self.resolve_pillar(text)
        sector = self.resolve_sector(text)
        
        if pillar:
            vector[1] = str(pillar.get('Axis-Coordinate ID', '1.0.0.0'))
        if sector:
            vector[2] = str(sector.get('coordinate', '2.0.0.0'))
            
        # 2. Axis 3: Honeycomb (Cross-domain link)
        vector[3] = self.resolve_honeycomb(text, pillar)
        
        # 3. Axis 4 & 5: Structural Layer
        branch, node = self.resolve_branch_and_node(text, sector)
        vector[4] = branch
        vector[5] = node
        
        # 4. Axis 6 & 7: Regulatory / Compliance Layer
        reg = self.resolve_regulatory_crosswalk(text, sector)
        vector[6] = reg["axis6"]
        vector[7] = reg["axis7"]
        
        # 5. Axis 8 & 9: Spatio-Temporal Layer
        vector[8] = self.resolve_temporal(text)
        vector[9] = self.resolve_spatial(text)
        
        # 6. Axes 10-13: Attribute Layer
        attrs = self.resolve_attribute_axes(text)
        vector[10] = attrs["axis10"]
        vector[11] = attrs["axis11"]
        vector[12] = attrs["axis12"]
        vector[13] = attrs["axis13"]
        
        # 7. Axes 14-17: Logic/Truth Essence (Reserved for Truth Engine outcome)
        # These are initially 0 and filled during the simulation pass closure
        
        return vector

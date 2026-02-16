"""
Unified Coordinate System for UKG/USKD

This module implements the 17-dimensional coordinate system for indexing and navigating
all knowledge elements in the Universal Knowledge Graph (UKG) and Universal Simulated
Knowledge Database (USKD).

The coordinate system uses:
- Nuremberg-style hierarchical numbering (dot-delimited numeric notation)
- 17 axes covering knowledge dimensions, crosswalks, expert roles, and context
- Meta-tag overlays for preserving original naming from regulatory/industry sources
- Dynamic traversal via Octopus, Honeycomb, and Spiderweb node systems

A knowledge node is identified by: K ≡ (x1, x2, ..., x17)
where xi is the coordinate value along Axis i.
"""

import logging
import re
import hashlib
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AxisCoordinate:
    """
    Represents a coordinate value along a single axis with Nuremberg numbering.
    
    The Nuremberg numbering system uses dot-delimited numeric notation to capture
    parent-child relationships. For example: 1.13.2.2.3 indicates Axis 1 value 13
    with subordinate levels 2, 2, 3.
    """
    axis_number: int
    value: str
    levels: List[int] = field(default_factory=list)
    meta_tag: Optional[str] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        """Parse the value into hierarchical levels."""
        if self.value and not self.levels:
            self.levels = self._parse_levels(self.value)
    
    def _parse_levels(self, value: str) -> List[int]:
        """Parse a dot-delimited value into hierarchical levels."""
        try:
            parts = str(value).split('.')
            return [int(p) for p in parts if p.isdigit()]
        except (ValueError, AttributeError):
            return []
    
    @property
    def depth(self) -> int:
        """Return the depth of the hierarchy."""
        return len(self.levels)
    
    @property
    def parent_coordinate(self) -> Optional[str]:
        """Return the parent coordinate (one level up)."""
        if self.depth > 1:
            return '.'.join(str(l) for l in self.levels[:-1])
        return None
    
    def is_descendant_of(self, other: 'AxisCoordinate') -> bool:
        """Check if this coordinate is a descendant of another."""
        if self.axis_number != other.axis_number:
            return False
        if self.depth <= other.depth:
            return False
        return self.levels[:other.depth] == other.levels
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'axis_number': self.axis_number,
            'value': self.value,
            'levels': self.levels,
            'depth': self.depth,
            'meta_tag': self.meta_tag,
            'description': self.description
        }
    
    def __str__(self) -> str:
        if self.meta_tag:
            return f"{self.meta_tag}.{self.value}"
        return f"{self.axis_number}.{self.value}"


@dataclass
class UnifiedCoordinate:
    """
    A 17-dimensional coordinate identifying a knowledge node in the UKG/USKD.
    
    Each axis coordinate can be None (unspecified) or an AxisCoordinate object.
    The coordinate acts as a unique identifier and navigation point in the
    multi-dimensional knowledge space.
    """
    
    coordinates: Dict[int, AxisCoordinate] = field(default_factory=dict)
    node_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    meta_tags: Dict[str, str] = field(default_factory=dict)
    
    AXIS_NAMES = {
        1: "Pillar Levels",
        2: "Sectors",
        3: "Honeycomb (Cross-domain)",
        4: "Branches",
        5: "Nodes",
        6: "Octopus Crosswalk",
        7: "Spiderweb Crosswalk",
        8: "Knowledge Role",
        9: "Qualifications & Skills",
        10: "Octopus Regulatory Expert",
        11: "Spiderweb Compliance Expert",
        12: "Location",
        13: "Temporal",
        14: "Risk & Confidence",
        15: "Federated Intelligence",
        16: "Arrows of Time",
        17: "Observability & Analytics"
    }
    
    AXIS_FORMATS = {
        1: "1.<PillarID>[.<SubLevel>...]",
        2: "2.<Sector>.<CodeSystem>.<TopCode>[.<SubCode>...]",
        3: "3.<CrossLinkID>[.<FacetID>...]",
        4: "4.<Branch>.<SubBranch>...",
        5: "5.<NodeID>[.<SubNode>...]",
        6: "6.<OctopusNodeID>",
        7: "7.<SpiderNodeID>",
        8: "8.<RoleID>",
        9: "9.<QualID>[.<CertID>]",
        10: "10.<MetaRoleID>",
        11: "11.<ComplianceProfileID>",
        12: "12.<LocationID>[.<SubLocation>]",
        13: "13.<TimeID>[.<Period>]",
        14: "14.<RiskLevel>.<ConfidenceScore>[.<ValidationMetric>]",
        15: "15.<SystemID>.<SyncState>[.<DistributedNode>]",
        16: "16.<CausalityChain>.<TemporalVector>[.<PredictiveModel>]",
        17: "17.<MetricID>.<AuditTrailID>[.<PerformanceMarker>]"
    }
    
    def __post_init__(self):
        """Generate node_id if not provided."""
        if not self.node_id:
            self.node_id = self._generate_node_id()
    
    def _generate_node_id(self) -> str:
        """Generate a unique node ID based on coordinates."""
        coord_str = self.to_coordinate_string()
        hash_obj = hashlib.sha256(coord_str.encode())
        return f"node_{hash_obj.hexdigest()[:16]}"
    
    def set_axis(self, axis_number: int, value: str, 
                 meta_tag: Optional[str] = None,
                 description: Optional[str] = None) -> None:
        """
        Set or update a coordinate value for a specific axis with validation.
        
        Args:
            axis_number: The axis number (1-17)
            value: The coordinate value (Nuremberg numbered)
            meta_tag: Optional meta-tag for the coordinate
            description: Optional description
        """
        if not isinstance(axis_number, int) or not 1 <= axis_number <= 17:
            logger.error(f"Invalid axis number: {axis_number}. Must be 1-17.")
            raise ValueError(f"Axis number must be between 1 and 17, got {axis_number}")
        
        # Enhanced validation for value format
        if value and not re.match(r'^[\d\.]+$', str(value)) and not meta_tag:
            # Check if it's a special placeholder or if it contains letters without a meta_tag
            if any(c.isalpha() for c in str(value)):
                 logger.warning(f"Axis {axis_number} value '{value}' contains letters but no meta_tag provided. This may cause resolution issues.")

        self.coordinates[axis_number] = AxisCoordinate(
            axis_number=axis_number,
            value=str(value) if value is not None else "*",
            meta_tag=meta_tag,
            description=description
        )
    
    def get_axis(self, axis_number: int) -> Optional[AxisCoordinate]:
        """Get the coordinate for a specific axis."""
        return self.coordinates.get(axis_number)
    
    def to_tuple(self) -> Tuple[Optional[str], ...]:
        """
        Return the coordinate as a 17-tuple.
        
        Returns:
            Tuple of 17 coordinate values (None for unspecified axes)
        """
        return tuple(
            self.coordinates[i].value if i in self.coordinates else None
            for i in range(1, 18)
        )
    
    def to_coordinate_string(self) -> str:
        """
        Return the full coordinate as a formatted string.
        
        Format: [<Axis1>].[<Axis2>]...[<Axis17>]
        Uses meta-tags where available.
        """
        parts = []
        for i in range(1, 18):
            if i in self.coordinates:
                coord = self.coordinates[i]
                if coord.meta_tag:
                    parts.append(f"{coord.meta_tag}.{coord.value}")
                else:
                    parts.append(f"{i}.{coord.value}")
            else:
                parts.append("*")
        return ":".join(parts)
    
    def to_short_string(self) -> str:
        """Return a compact representation with only specified axes."""
        parts = []
        for axis_num, coord in sorted(self.coordinates.items()):
            if coord.meta_tag:
                parts.append(f"{coord.meta_tag}.{coord.value}")
            else:
                parts.append(f"A{axis_num}:{coord.value}")
        return " | ".join(parts)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UnifiedCoordinate':
        """Create a UnifiedCoordinate from a dictionary."""
        coord = cls()
        coord.node_id = data.get('node_id')
        coord.meta_tags = data.get('meta_tags', {})
        
        for axis_data in data.get('coordinates', []):
            coord.set_axis(
                axis_number=axis_data['axis_number'],
                value=axis_data['value'],
                meta_tag=axis_data.get('meta_tag'),
                description=axis_data.get('description')
            )
        
        return coord
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'node_id': self.node_id,
            'coordinates': [c.to_dict() for c in self.coordinates.values()],
            'coordinate_string': self.to_coordinate_string(),
            'tuple': self.to_tuple(),
            'meta_tags': self.meta_tags,
            'created_at': self.created_at.isoformat()
        }
    
    def get_dimension_count(self) -> int:
        """Return the number of specified dimensions."""
        return len(self.coordinates)
    
    def is_fully_specified(self) -> bool:
        """Check if all 17 axes are specified."""
        return len(self.coordinates) == 17
    
    def matches_partial(self, partial: 'UnifiedCoordinate') -> bool:
        """
        Check if this coordinate matches a partial coordinate.
        
        A partial coordinate matches if all its specified axes
        match the corresponding axes in this coordinate.
        """
        for axis_num, coord in partial.coordinates.items():
            if axis_num not in self.coordinates:
                return False
            if self.coordinates[axis_num].value != coord.value:
                return False
        return True


class CoordinateParser:
    """
    Parses coordinate strings into UnifiedCoordinate objects.
    
    Supports various input formats including:
    - Full 17-tuple format: "1.32:2.3.3.4:3.*:..."
    - Short format: "FAR.1.1.1.1 | NAICS.541512"
    - Individual axis format: "1.32.2.1"
    """
    
    AXIS_PATTERN = re.compile(r'^(\d+)\.(.+)$')
    META_TAG_PATTERN = re.compile(r'^([A-Z]+)\.(.+)$')
    
    KNOWN_META_TAGS = {
        'FAR': 1,
        'DFARS': 1,
        'CFR': 1,
        'NAICS': 2,
        'SIC': 2,
        'PSC': 2,
        'NIC': 2,
        'ISO': 7,
        'NIST': 7,
        'GDPR': 6,
        'HIPAA': 6,
        'SOX': 6
    }
    
    @classmethod
    def parse_axis_coordinate(cls, value: str, axis_number: Optional[int] = None) -> AxisCoordinate:
        """
        Parse a single axis coordinate string.
        
        Args:
            value: The coordinate string (e.g., "1.32.2.1" or "FAR.1.1.1.1")
            axis_number: Optional axis number if not in the string
            
        Returns:
            AxisCoordinate object
        """
        meta_tag = None
        coord_value = value
        
        meta_match = cls.META_TAG_PATTERN.match(value)
        if meta_match:
            meta_tag = meta_match.group(1)
            coord_value = meta_match.group(2)
            if axis_number is None and meta_tag in cls.KNOWN_META_TAGS:
                axis_number = cls.KNOWN_META_TAGS[meta_tag]
        
        if axis_number is None:
            axis_match = cls.AXIS_PATTERN.match(value)
            if axis_match:
                axis_number = int(axis_match.group(1))
                coord_value = axis_match.group(2)
            else:
                raise ValueError(f"Cannot determine axis number for coordinate: {value}")
        else:
            axis_match = cls.AXIS_PATTERN.match(coord_value)
            if axis_match:
                parsed_axis = int(axis_match.group(1))
                if parsed_axis == axis_number:
                    coord_value = axis_match.group(2)
        
        return AxisCoordinate(
            axis_number=axis_number,
            value=coord_value,
            meta_tag=meta_tag
        )
    
    @classmethod
    def parse_full_coordinate(cls, coord_string: str) -> UnifiedCoordinate:
        """
        Parse a full coordinate string into a UnifiedCoordinate with error handling.
        
        Supports formats:
        - Colon-separated: "1.32:2.3.3.4:*:4.3.2:..."
        - Pipe-separated: "FAR.1.1 | NAICS.541512 | ..."
        
        Args:
            coord_string: The coordinate string to parse
            
        Returns:
            UnifiedCoordinate object
        """
        coord = UnifiedCoordinate()
        
        if not coord_string:
            return coord

        try:
            if '|' in coord_string:
                parts = [p.strip() for p in coord_string.split('|')]
                for part in parts:
                    if part and part != '*':
                        try:
                            axis_coord = cls.parse_axis_coordinate(part)
                            coord.set_axis(
                                axis_coord.axis_number,
                                axis_coord.value,
                                axis_coord.meta_tag
                            )
                        except ValueError as e:
                            logger.error(f"Error parsing coordinate part '{part}': {e}")
                            # Continue parsing other parts
            elif ':' in coord_string:
                parts = coord_string.split(':')
                for i, part in enumerate(parts, start=1):
                    if i > 17:
                        logger.warning(f"Found more than 17 axes in coordinate string. Ignoring from index {i}.")
                        break
                    if part and part != '*':
                        try:
                            axis_coord = cls.parse_axis_coordinate(part, axis_number=i)
                            coord.set_axis(i, axis_coord.value, axis_coord.meta_tag)
                        except ValueError as e:
                            logger.error(f"Error parsing axis {i} part '{part}': {e}")
            else:
                try:
                    axis_coord = cls.parse_axis_coordinate(coord_string)
                    coord.set_axis(
                        axis_coord.axis_number,
                        axis_coord.value,
                        axis_coord.meta_tag
                    )
                except ValueError as e:
                    logger.error(f"Error parsing single coordinate '{coord_string}': {e}")
        except Exception as e:
            logger.critical(f"Failed to parse coordinate string '{coord_string}': {e}")
            # Return empty or partially parsed coordinate instead of crashing
        
        return coord


class CoordinateResolver:
    """
    Resolves coordinates to knowledge nodes and handles coordinate mathematics.
    
    The resolver interprets composite axis values, performs lookups, and
    supports the AKF (Advanced Knowledge Framework) formula integration.
    """
    
    def __init__(self, db_manager=None, graph_manager=None):
        """
        Initialize the coordinate resolver.
        
        Args:
            db_manager: Database manager for lookups
            graph_manager: Graph manager for traversal
        """
        self.db_manager = db_manager
        self.graph_manager = graph_manager
        self.cache = {}
    
    def resolve_axis(self, axis_coord: AxisCoordinate) -> Dict[str, Any]:
        """
        Resolve a single axis coordinate to its full context.
        
        Args:
            axis_coord: The axis coordinate to resolve
            
        Returns:
            Dictionary with resolved context
        """
        axis_num = axis_coord.axis_number
        result = {
            'axis_number': axis_num,
            'axis_name': UnifiedCoordinate.AXIS_NAMES.get(axis_num, f"Axis {axis_num}"),
            'value': axis_coord.value,
            'levels': axis_coord.levels,
            'depth': axis_coord.depth,
            'meta_tag': axis_coord.meta_tag
        }
        
        if axis_num == 1:
            result['pillar_context'] = self._resolve_pillar(axis_coord)
        elif axis_num == 2:
            result['sector_context'] = self._resolve_sector(axis_coord)
        elif axis_num in (6, 7):
            result['crosswalk_context'] = self._resolve_crosswalk(axis_coord)
        elif axis_num in (8, 9, 10, 11):
            result['role_context'] = self._resolve_role(axis_coord)
        elif axis_num == 12:
            result['location_context'] = self._resolve_location(axis_coord)
        elif axis_num == 13:
            result['temporal_context'] = self._resolve_temporal(axis_coord)
        elif axis_num == 14:
            result['risk_context'] = self._resolve_risk(axis_coord)
        elif axis_num == 15:
            result['federated_context'] = self._resolve_federated(axis_coord)
        elif axis_num == 16:
            result['arrows_of_time_context'] = self._resolve_arrows_of_time(axis_coord)
        elif axis_num == 17:
            result['observability_context'] = self._resolve_observability(axis_coord)
        
        return result
    
    def resolve_full_coordinate(self, coord: UnifiedCoordinate) -> Dict[str, Any]:
        """
        Resolve a full coordinate to its complete context.
        
        Args:
            coord: The unified coordinate to resolve
            
        Returns:
            Dictionary with resolved context for all specified axes
        """
        result = {
            'node_id': coord.node_id,
            'coordinate_string': coord.to_coordinate_string(),
            'dimension_count': coord.get_dimension_count(),
            'axes': {},
            'resolved_at': datetime.now(UTC).isoformat()
        }
        
        for axis_num, axis_coord in coord.coordinates.items():
            result['axes'][axis_num] = self.resolve_axis(axis_coord)
        
        return result
    
    def _resolve_pillar(self, coord: AxisCoordinate) -> Dict[str, Any]:
        """Resolve Axis 1 (Pillar) context."""
        levels = coord.levels
        return {
            'pillar_id': levels[0] if levels else None,
            'hierarchy_depth': len(levels),
            'full_path': '.'.join(str(l) for l in levels),
            'type': 'pillar_level'
        }
    
    def _resolve_sector(self, coord: AxisCoordinate) -> Dict[str, Any]:
        """Resolve Axis 2 (Sector) context."""
        levels = coord.levels
        return {
            'sector_id': levels[0] if levels else None,
            'code_system': levels[1] if len(levels) > 1 else None,
            'top_code': levels[2] if len(levels) > 2 else None,
            'sub_codes': levels[3:] if len(levels) > 3 else [],
            'original_code': coord.meta_tag,
            'type': 'sector_industry'
        }
    
    def _resolve_crosswalk(self, coord: AxisCoordinate) -> Dict[str, Any]:
        """Resolve Axis 6/7 (Octopus/Spiderweb) crosswalk context."""
        crosswalk_type = 'octopus' if coord.axis_number == 6 else 'spiderweb'
        return {
            'crosswalk_type': crosswalk_type,
            'node_id': coord.levels[0] if coord.levels else None,
            'link_type': 'one_to_many' if crosswalk_type == 'octopus' else 'many_to_many',
            'type': 'crosswalk'
        }
    
    def _resolve_role(self, coord: AxisCoordinate) -> Dict[str, Any]:
        """Resolve Axes 8-11 (Role/Expert) context."""
        role_types = {
            8: 'knowledge_role',
            9: 'qualifications_skills',
            10: 'octopus_regulatory_expert',
            11: 'spiderweb_compliance_expert'
        }
        return {
            'role_type': role_types.get(coord.axis_number, 'unknown'),
            'role_id': coord.levels[0] if coord.levels else None,
            'qualifications': coord.levels[1:] if len(coord.levels) > 1 else [],
            'type': 'expert_role'
        }
    
    def _resolve_location(self, coord: AxisCoordinate) -> Dict[str, Any]:
        """Resolve Axis 12 (Location) context."""
        levels = coord.levels
        return {
            'location_id': levels[0] if levels else None,
            'jurisdiction_level': len(levels),
            'hierarchy': levels,
            'type': 'geospatial'
        }
    
    def _resolve_temporal(self, coord: AxisCoordinate) -> Dict[str, Any]:
        """Resolve Axis 13 (Temporal) context."""
        levels = coord.levels
        return {
            'time_id': levels[0] if levels else None,
            'period': levels[1] if len(levels) > 1 else None,
            'version': levels[2] if len(levels) > 2 else None,
            'type': 'temporal'
        }
    
    def _resolve_risk(self, coord: AxisCoordinate) -> Dict[str, Any]:
        """Resolve Axis 14 (Risk & Confidence) context."""
        levels = coord.levels
        return {
            'risk_level': levels[0] if levels else None,
            'confidence_score': levels[1] / 100 if len(levels) > 1 else None,
            'validation_metric': levels[2] if len(levels) > 2 else None,
            'risk_classification': self._classify_risk_level(levels[0] if levels else 0),
            'type': 'risk_confidence'
        }
    
    def _resolve_federated(self, coord: AxisCoordinate) -> Dict[str, Any]:
        """Resolve Axis 15 (Federated Intelligence) context."""
        levels = coord.levels
        sync_states = {0: 'disconnected', 1: 'syncing', 2: 'synchronized', 3: 'propagating'}
        return {
            'system_id': levels[0] if levels else None,
            'sync_state': sync_states.get(levels[1], 'unknown') if len(levels) > 1 else None,
            'distributed_node': levels[2] if len(levels) > 2 else None,
            'type': 'federated_intelligence'
        }
    
    def _resolve_arrows_of_time(self, coord: AxisCoordinate) -> Dict[str, Any]:
        """Resolve Axis 16 (Arrows of Time) context."""
        levels = coord.levels
        return {
            'causality_chain': levels[0] if levels else None,
            'temporal_vector': levels[1] if len(levels) > 1 else None,
            'predictive_model': levels[2] if len(levels) > 2 else None,
            'direction': 'forward' if (levels[1] if len(levels) > 1 else 0) > 0 else 'backward',
            'type': 'arrows_of_time'
        }
    
    def _resolve_observability(self, coord: AxisCoordinate) -> Dict[str, Any]:
        """Resolve Axis 17 (Observability & Analytics) context."""
        levels = coord.levels
        return {
            'metric_id': levels[0] if levels else None,
            'audit_trail_id': levels[1] if len(levels) > 1 else None,
            'performance_marker': levels[2] if len(levels) > 2 else None,
            'type': 'observability_analytics'
        }
    
    def _classify_risk_level(self, level: int) -> str:
        """Classify risk level into categories."""
        if level <= 1:
            return 'minimal'
        elif level <= 3:
            return 'low'
        elif level <= 5:
            return 'moderate'
        elif level <= 7:
            return 'high'
        else:
            return 'critical'


class CrosswalkTraversal:
    """
    Handles dynamic traversal across axes using Octopus, Honeycomb, and Spiderweb nodes.
    
    Traversal types:
    - Honeycomb (Axis 3): Intra-domain expansion, multi-faceted connections
    - Octopus (Axis 6): One-to-many hub connections
    - Spiderweb (Axis 7): Many-to-many cross-domain connections
    """
    
    def __init__(self, resolver: CoordinateResolver = None):
        """Initialize the traversal system."""
        self.resolver = resolver or CoordinateResolver()
        self.traversal_log = []
    
    def traverse_honeycomb(self, coord: UnifiedCoordinate, 
                           depth: int = 1) -> List[UnifiedCoordinate]:
        """
        Traverse via Honeycomb nodes for intra-domain expansion.
        
        Honeycomb traversal expands the context breadth-wise, pulling in
        analogous points from the same general area.
        
        Args:
            coord: Starting coordinate
            depth: How many levels deep to traverse
            
        Returns:
            List of connected coordinates
        """
        connected = []
        axis_3 = coord.get_axis(3)
        
        if axis_3:
            self._log_traversal('honeycomb', coord, depth)
            
            base_levels = axis_3.levels
            for d in range(1, depth + 1):
                for variation in range(-d, d + 1):
                    if variation == 0:
                        continue
                    new_levels = base_levels.copy()
                    if new_levels:
                        new_levels[-1] = max(1, new_levels[-1] + variation)
                        new_coord = UnifiedCoordinate()
                        for axis_num, axis_coord in coord.coordinates.items():
                            if axis_num == 3:
                                new_coord.set_axis(3, '.'.join(str(l) for l in new_levels))
                            else:
                                new_coord.set_axis(
                                    axis_num, axis_coord.value, 
                                    axis_coord.meta_tag, axis_coord.description
                                )
                        connected.append(new_coord)
        
        return connected
    
    def traverse_octopus(self, coord: UnifiedCoordinate) -> List[UnifiedCoordinate]:
        """
        Traverse via Octopus nodes for one-to-many propagation.
        
        Octopus traversal fans out from a central hub to all connected nodes,
        enabling knowledge integration across disparate sources.
        
        Args:
            coord: Starting coordinate with Axis 6 (Octopus) specified
            
        Returns:
            List of connected coordinates
        """
        connected = []
        axis_6 = coord.get_axis(6)
        
        if axis_6:
            self._log_traversal('octopus', coord, 1)
            
            hub_id = axis_6.levels[0] if axis_6.levels else 0
            tentacle_targets = self._get_octopus_connections(hub_id)
            
            for target in tentacle_targets:
                new_coord = UnifiedCoordinate()
                for axis_num, axis_coord in coord.coordinates.items():
                    new_coord.set_axis(
                        axis_num, axis_coord.value,
                        axis_coord.meta_tag, axis_coord.description
                    )
                if 'pillar' in target:
                    new_coord.set_axis(1, target['pillar'])
                if 'sector' in target:
                    new_coord.set_axis(2, target['sector'])
                connected.append(new_coord)
        
        return connected
    
    def traverse_spiderweb(self, coord: UnifiedCoordinate) -> List[UnifiedCoordinate]:
        """
        Traverse via Spiderweb nodes for many-to-many cross-domain connections.
        
        Spiderweb traversal performs lateral jumps between equivalent or
        analogous nodes in different hierarchies (e.g., across regulations).
        
        Args:
            coord: Starting coordinate with Axis 7 (Spiderweb) specified
            
        Returns:
            List of connected coordinates
        """
        connected = []
        axis_7 = coord.get_axis(7)
        
        if axis_7:
            self._log_traversal('spiderweb', coord, 1)
            
            web_id = axis_7.levels[0] if axis_7.levels else 0
            web_connections = self._get_spiderweb_connections(web_id)
            
            for connection in web_connections:
                new_coord = UnifiedCoordinate()
                for axis_num, axis_coord in coord.coordinates.items():
                    new_coord.set_axis(
                        axis_num, axis_coord.value,
                        axis_coord.meta_tag, axis_coord.description
                    )
                if 'pillar' in connection:
                    new_coord.set_axis(1, connection['pillar'], connection.get('meta_tag'))
                if 'regulatory' in connection:
                    new_coord.set_axis(6, connection['regulatory'])
                if 'compliance' in connection:
                    new_coord.set_axis(7, connection['compliance'])
                connected.append(new_coord)
        
        return connected
    
    def dynamic_traverse(self, coord: UnifiedCoordinate, 
                        query_context: Dict[str, Any] = None) -> List[UnifiedCoordinate]:
        """
        Perform dynamic multi-axis traversal based on query context.
        
        This method combines all traversal types as needed to build a
        comprehensive set of related coordinates.
        
        Args:
            coord: Starting coordinate
            query_context: Context to guide traversal decisions
            
        Returns:
            List of all discovered coordinates
        """
        all_connected = []
        query_context = query_context or {}
        
        if coord.get_axis(3):
            honeycomb_depth = query_context.get('honeycomb_depth', 1)
            all_connected.extend(self.traverse_honeycomb(coord, honeycomb_depth))
        
        if coord.get_axis(6):
            all_connected.extend(self.traverse_octopus(coord))
        
        if coord.get_axis(7):
            all_connected.extend(self.traverse_spiderweb(coord))
        
        unique_coords = self._deduplicate_coordinates(all_connected)
        
        return unique_coords
    
    def _get_octopus_connections(self, hub_id: int) -> List[Dict[str, Any]]:
        """Get predefined octopus hub connections."""
        connections = {
            1: [{'pillar': '32', 'sector': '54'}, {'pillar': '33', 'sector': '61'}],
            2: [{'pillar': '11', 'sector': '62'}, {'pillar': '12', 'sector': '52'}],
            3: [{'pillar': '6', 'sector': '54.7'}, {'pillar': '7', 'sector': '51'}],
        }
        return connections.get(hub_id, [])
    
    def _get_spiderweb_connections(self, web_id: int) -> List[Dict[str, Any]]:
        """Get predefined spiderweb web connections."""
        connections = {
            1: [
                {'pillar': '32.1', 'meta_tag': 'FAR', 'regulatory': '1'},
                {'pillar': '32.2', 'meta_tag': 'DFARS', 'regulatory': '2'}
            ],
            2: [
                {'pillar': '11.1', 'compliance': '1'},
                {'pillar': '11.2', 'compliance': '2'}
            ],
        }
        return connections.get(web_id, [])
    
    def _deduplicate_coordinates(self, coords: List[UnifiedCoordinate]) -> List[UnifiedCoordinate]:
        """Remove duplicate coordinates based on coordinate string."""
        seen = set()
        unique = []
        for coord in coords:
            coord_str = coord.to_coordinate_string()
            if coord_str not in seen:
                seen.add(coord_str)
                unique.append(coord)
        return unique
    
    def _log_traversal(self, traversal_type: str, coord: UnifiedCoordinate, depth: int) -> None:
        """Log a traversal operation."""
        self.traversal_log.append({
            'type': traversal_type,
            'from_coordinate': coord.to_short_string(),
            'depth': depth,
            'timestamp': datetime.now(UTC).isoformat()
        })


class UnifiedCoordinateSystem:
    """
    Main interface for the 17-dimensional Unified Coordinate System.
    
    This class provides the central API for:
    - Creating and parsing coordinates
    - Resolving coordinates to knowledge contexts
    - Traversing the knowledge graph via crosswalk systems
    - Managing meta-tags and naming conventions
    """
    
    def __init__(self, db_manager=None, graph_manager=None):
        """
        Initialize the Unified Coordinate System.
        
        Args:
            db_manager: Database manager for persistence
            graph_manager: Graph manager for knowledge graph operations
        """
        self.parser = CoordinateParser()
        self.resolver = CoordinateResolver(db_manager, graph_manager)
        self.traversal = CrosswalkTraversal(self.resolver)
        self.db_manager = db_manager
        self.graph_manager = graph_manager
        
        logger.info("UnifiedCoordinateSystem initialized with 17-axis support")
    
    def create_coordinate(self, **axis_values) -> UnifiedCoordinate:
        """
        Create a new coordinate with specified axis values.
        
        Args:
            **axis_values: Keyword arguments where keys are axis names or numbers
                          and values are coordinate strings
        
        Returns:
            UnifiedCoordinate object
        
        Example:
            coord = system.create_coordinate(
                pillar="32.1.2",
                sector="54.7",
                risk="3.85.1"
            )
        """
        coord = UnifiedCoordinate()
        
        axis_name_map = {
            'pillar': 1, 'sectors': 2, 'sector': 2,
            'honeycomb': 3, 'branches': 4, 'branch': 4,
            'nodes': 5, 'node': 5,
            'octopus': 6, 'spiderweb': 7,
            'knowledge_role': 8, 'qualifications': 9,
            'regulatory_expert': 10, 'compliance_expert': 11,
            'location': 12, 'time': 13, 'temporal': 13,
            'risk': 14, 'federated': 15,
            'arrows_of_time': 16, 'observability': 17
        }
        
        for key, value in axis_values.items():
            if isinstance(key, int):
                axis_num = key
            elif key.startswith('axis'):
                axis_num = int(key.replace('axis', ''))
            else:
                axis_num = axis_name_map.get(key.lower())
            
            if axis_num:
                meta_tag = None
                if isinstance(value, dict):
                    coord.set_axis(
                        axis_num,
                        value.get('value', ''),
                        value.get('meta_tag'),
                        value.get('description')
                    )
                else:
                    coord.set_axis(axis_num, str(value), meta_tag)
        
        return coord
    
    def parse(self, coord_string: str) -> UnifiedCoordinate:
        """
        Parse a coordinate string into a UnifiedCoordinate object.
        
        Args:
            coord_string: The coordinate string to parse
            
        Returns:
            UnifiedCoordinate object
        """
        return self.parser.parse_full_coordinate(coord_string)
    
    def resolve(self, coord: UnifiedCoordinate) -> Dict[str, Any]:
        """
        Resolve a coordinate to its full knowledge context.
        
        Args:
            coord: The coordinate to resolve
            
        Returns:
            Dictionary with resolved context
        """
        return self.resolver.resolve_full_coordinate(coord)
    
    def traverse(self, coord: UnifiedCoordinate, 
                query_context: Dict[str, Any] = None) -> List[UnifiedCoordinate]:
        """
        Traverse the knowledge graph from a starting coordinate.
        
        Args:
            coord: Starting coordinate
            query_context: Context to guide traversal
            
        Returns:
            List of discovered coordinates
        """
        return self.traversal.dynamic_traverse(coord, query_context)
    
    def find_related(self, coord: UnifiedCoordinate, 
                    axes_to_match: List[int] = None) -> List[UnifiedCoordinate]:
        """
        Find coordinates related to the given coordinate.
        
        Args:
            coord: The reference coordinate
            axes_to_match: Which axes to use for matching (default: all specified)
            
        Returns:
            List of related coordinates
        """
        if axes_to_match is None:
            axes_to_match = list(coord.coordinates.keys())
        
        related = self.traverse(coord)
        
        return [r for r in related if any(
            r.get_axis(axis) for axis in axes_to_match
        )]
    
    def get_axis_info(self, axis_number: int) -> Dict[str, Any]:
        """
        Get information about a specific axis.
        
        Args:
            axis_number: The axis number (1-17)
            
        Returns:
            Dictionary with axis information
        """
        if not 1 <= axis_number <= 17:
            raise ValueError("Axis number must be between 1 and 17")
        
        return {
            'axis_number': axis_number,
            'name': UnifiedCoordinate.AXIS_NAMES.get(axis_number),
            'format': UnifiedCoordinate.AXIS_FORMATS.get(axis_number),
            'category': self._get_axis_category(axis_number)
        }
    
    def _get_axis_category(self, axis_number: int) -> str:
        """Get the category for an axis."""
        if axis_number <= 5:
            return 'hierarchical_core'
        elif axis_number <= 7:
            return 'crosswalk'
        elif axis_number <= 11:
            return 'expert_role'
        elif axis_number <= 13:
            return 'context'
        else:
            return 'extended_enterprise'
    
    def validate_coordinate(self, coord: UnifiedCoordinate) -> Dict[str, Any]:
        """
        Validate a coordinate for correctness.
        
        Args:
            coord: The coordinate to validate
            
        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []
        
        for axis_num, axis_coord in coord.coordinates.items():
            if not 1 <= axis_num <= 17:
                issues.append(f"Invalid axis number: {axis_num}")
            
            if not axis_coord.value:
                issues.append(f"Axis {axis_num} has empty value")
            
            if axis_coord.depth == 0:
                warnings.append(f"Axis {axis_num} has no hierarchical levels")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'dimension_count': coord.get_dimension_count()
        }


def create_coordinate_system(db_manager=None, graph_manager=None) -> UnifiedCoordinateSystem:
    """
    Factory function to create a UnifiedCoordinateSystem.
    
    Args:
        db_manager: Optional database manager
        graph_manager: Optional graph manager
        
    Returns:
        Configured UnifiedCoordinateSystem instance
    """
    return UnifiedCoordinateSystem(db_manager, graph_manager)

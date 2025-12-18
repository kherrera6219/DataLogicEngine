"""
Import reference data from Excel files into the UKG database.
Imports PL-1-107 pillars and AXIS-2 sector codes.
"""

import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app import app, db
from models import UnifiedCoordinate, AxisValue, MetaTagMapping, AxisConfiguration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_nuremberg_coordinate(coord_str: str) -> dict:
    """Parse a Nuremberg-style coordinate string into components."""
    parts = coord_str.strip().split('.')
    result = {
        'axis_1': parts[0] if len(parts) > 0 else None,
        'axis_2': parts[1] if len(parts) > 1 else None,
        'axis_3': parts[2] if len(parts) > 2 else None,
        'axis_4': parts[3] if len(parts) > 3 else None,
        'levels': parts,
        'depth': len(parts),
        'full_coordinate': coord_str
    }
    return result


def import_pillars(excel_path: str) -> int:
    """Import PL-1-107 pillar data into unified_coordinates and axis_values."""
    logger.info(f"Importing pillars from {excel_path}")
    
    df = pd.read_excel(excel_path)
    df = df.dropna(subset=['Pillar ID', 'Pillar Name', 'Axis-Coordinate ID'])
    imported_count = 0
    
    for _, row in df.iterrows():
        pillar_id = str(row['Pillar ID']).strip()
        pillar_name = str(row['Pillar Name']).strip()
        coord_str = str(row['Axis-Coordinate ID']).strip()
        members_str = str(row['Top-Level Members']).strip() if pd.notna(row['Top-Level Members']) else ""
        
        if not pillar_id or pillar_id.lower() == 'nan':
            continue
        
        coord_parts = parse_nuremberg_coordinate(coord_str)
        
        existing = UnifiedCoordinate.query.filter_by(
            coordinate_string=coord_str
        ).first()
        
        if existing:
            logger.debug(f"Coordinate {coord_str} already exists, updating...")
            unified_coord = existing
            unified_coord.label = pillar_name
            unified_coord.description = f"Pillar {pillar_id}: {pillar_name}"
            unified_coord.axis_1_pillar = coord_parts['axis_1']
            unified_coord.updated_at = datetime.utcnow()
        else:
            import uuid as uuid_mod
            unified_coord = UnifiedCoordinate(
                coordinate_id=f"PL-{pillar_id}-{str(uuid_mod.uuid4())[:8]}",
                coordinate_string=coord_str,
                label=pillar_name,
                description=f"Pillar {pillar_id}: {pillar_name}",
                axis_1_pillar=coord_parts['axis_1'],
                axis_2_sector=coord_parts['axis_2'],
                axis_3_honeycomb=coord_parts['axis_3'],
                axis_4_branch=coord_parts['axis_4'],
                meta_tags={'pillar_id': pillar_id, 'source': 'PL-1-107', 'type': 'pillar'},
            )
            db.session.add(unified_coord)
            db.session.flush()
        
        existing_axis_value = AxisValue.query.filter_by(
            coordinate_id=unified_coord.id,
            axis_number=1
        ).first()
        
        if not existing_axis_value:
            axis_value = AxisValue(
                coordinate_id=unified_coord.id,
                axis_number=1,
                value=pillar_name,
                levels=coord_parts['levels'],
                depth=coord_parts['depth'],
                meta_tag=pillar_id,
                axis_metadata={
                    'pillar_id': pillar_id,
                    'members': [m.strip() for m in members_str.split(',') if m.strip()]
                }
            )
            db.session.add(axis_value)
        
        imported_count += 1
    
    db.session.commit()
    logger.info(f"Imported {imported_count} pillars")
    return imported_count


def import_sector_codes(excel_path: str) -> int:
    """Import AXIS-2 worldwide sector codes into meta_tag_mappings."""
    logger.info(f"Importing sector codes from {excel_path}")
    
    df = pd.read_excel(excel_path)
    
    df.columns = ['col1', 'col2', 'col3', 'col4']
    
    imported_count = 0
    current_code_system = None
    current_sector_group = None
    
    for _, row in df.iterrows():
        col1 = str(row['col1']) if pd.notna(row['col1']) else ""
        col2 = str(row['col2']) if pd.notna(row['col2']) else ""
        col3 = str(row['col3']) if pd.notna(row['col3']) else ""
        col4 = str(row['col4']) if pd.notna(row['col4']) else ""
        
        if col1.startswith('Axis 2:') or not col1.strip():
            continue
        
        if col1 and not col2 and not col3:
            current_sector_group = col1.strip()
            continue
        
        if col1 == 'Code System':
            continue
        
        if col1 and 'NAICS' in col1.upper():
            current_code_system = 'NAICS'
            code = col2.strip() if col2 else None
            name = col3.strip() if col3 else None
            coordinate = col4.strip() if col4 else None
        elif col2 and col3:
            code = col2.strip()
            name = col3.strip()
            coordinate = col4.strip() if col4 else None
            if col1:
                current_code_system = col1.strip()
        else:
            continue
        
        if not code or not name:
            continue
        
        if current_code_system and code:
            existing = MetaTagMapping.query.filter_by(
                meta_tag=current_code_system,
                external_code=code
            ).first()
            
            if not existing:
                import uuid as uuid_mod
                mapping = MetaTagMapping(
                    mapping_id=f"MT-{current_code_system}-{code}-{str(uuid_mod.uuid4())[:8]}",
                    meta_tag=current_code_system,
                    external_code=code,
                    standard_name=name,
                    target_axis=2,
                    nuremberg_value=coordinate if coordinate else f"2.{code}",
                    mapping_metadata={
                        'sector_group': current_sector_group,
                        'source': 'AXIS-2'
                    },
                    is_active=True
                )
                db.session.add(mapping)
                imported_count += 1
    
    db.session.commit()
    logger.info(f"Imported {imported_count} sector code mappings")
    return imported_count


def setup_axis_configurations():
    """Setup default axis configurations for the 17-axis system."""
    logger.info("Setting up axis configurations")
    
    axis_configs = [
        (1, 'Pillar', 'PL', 'core', 'hierarchical', ['honeycomb', 'vertical']),
        (2, 'Sector', 'SC', 'core', 'hierarchical', ['honeycomb', 'octopus']),
        (3, 'Honeycomb', 'HC', 'core', 'cross_reference', ['spiderweb', 'octopus']),
        (4, 'Branch', 'BR', 'core', 'hierarchical', ['vertical', 'honeycomb']),
        (5, 'Node', 'ND', 'core', 'hierarchical', ['vertical']),
        (6, 'Octopus', 'OC', 'crosswalk', 'one_to_many', ['regulatory', 'spiderweb']),
        (7, 'Spiderweb', 'SW', 'crosswalk', 'many_to_many', ['compliance', 'octopus']),
        (8, 'Knowledge Expert', 'KE', 'persona', 'persona', ['knowledge_graph']),
        (9, 'Sector Expert', 'SE', 'persona', 'persona', ['sector_mapping']),
        (10, 'Regulatory Expert', 'RE', 'persona', 'persona', ['octopus', 'regulatory']),
        (11, 'Compliance Expert', 'CE', 'persona', 'persona', ['spiderweb', 'compliance']),
        (12, 'Location', 'LO', 'context', 'geographic', ['hierarchical']),
        (13, 'Temporal', 'TE', 'context', 'time_based', ['chronological']),
        (14, 'Risk & Confidence', 'RC', 'extended', 'numeric', ['confidence_scoring']),
        (15, 'Federated Intelligence', 'FI', 'extended', 'distributed', ['multi_source']),
        (16, 'Arrows of Time', 'AT', 'extended', 'directional', ['temporal_flow']),
        (17, 'Observability & Analytics', 'OA', 'extended', 'metrics', ['tracking'])
    ]
    
    for axis_num, name, short_name, category, value_type, traversals in axis_configs:
        existing = AxisConfiguration.query.filter_by(axis_number=axis_num).first()
        if not existing:
            config = AxisConfiguration(
                axis_number=axis_num,
                axis_name=name,
                axis_short_name=short_name,
                axis_category=category,
                value_type=value_type,
                supported_traversals=traversals,
                is_required=(axis_num <= 5),
                is_active=True
            )
            db.session.add(config)
    
    db.session.commit()
    logger.info("Axis configurations setup complete")


def main():
    """Main import function."""
    with app.app_context():
        pillar_file = 'attached_assets/PL-1-107_with_members_1766028647731.xlsx'
        sector_file = 'attached_assets/AXIS-2_world_wide_codes_systems_1766028647731.xlsx'
        
        setup_axis_configurations()
        
        if os.path.exists(pillar_file):
            pillar_count = import_pillars(pillar_file)
            print(f"Imported {pillar_count} pillars")
        else:
            print(f"Pillar file not found: {pillar_file}")
        
        if os.path.exists(sector_file):
            sector_count = import_sector_codes(sector_file)
            print(f"Imported {sector_count} sector codes")
        else:
            print(f"Sector file not found: {sector_file}")
        
        print("\nImport Summary:")
        print(f"  Unified Coordinates: {UnifiedCoordinate.query.count()}")
        print(f"  Axis Values: {AxisValue.query.count()}")
        print(f"  Meta Tag Mappings: {MetaTagMapping.query.count()}")
        print(f"  Axis Configurations: {AxisConfiguration.query.count()}")


if __name__ == '__main__':
    main()

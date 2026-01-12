import logging
import os
import sys
from backend.knowledge_algorithm.axis_mapper import AxisMapper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def verify_axis_mapper():
    logging.info("=== UKG Axis Mapper Verification ===")
    
    mapper = AxisMapper()
    
    logging.info(f"Loaded {len(mapper.pillars)} Pillars and {len(mapper.sectors)} Sectors.")
    if mapper.sectors:
        logging.info(f"Sample Sector: {mapper.sectors[len(mapper.sectors)//2]}")
    
    # 1. Test Pillar Resolution
    logging.info("\n1. Testing Pillar Resolution (Axis 1)...")
    query_1 = "What are the latest developments in quantum computing and metadata management?"
    pillar_match = mapper.resolve_pillar(query_1)
    if pillar_match:
        logging.info(f"SUCCESS: Matched Pillar '{pillar_match.get('Pillar Name')}' (ID: {pillar_match.get('Pillar ID')}, Coord: {pillar_match.get('Axis-Coordinate ID')})")
    else:
        logging.warning("FAILURE: No Pillar match found for query.")

    # 2. Test Sector Resolution
    logging.info("\n2. Testing Sector Resolution (Axis 2)...")
    query_2 = "Analysis of the automotive manufacturing supply chain in Europe."
    sector_match = mapper.resolve_sector(query_2)
    if sector_match:
        logging.info(f"SUCCESS: Matched Sector '{sector_match['name']}' (Coord: {sector_match['coordinate']})")
    else:
        logging.warning("FAILURE: No Sector match found for query.")

    # 3. Test Full Vector Resolution
    logging.info("\n3. Testing 17-Axis Vector Resolution...")
    vector = mapper.get_17axis_vector("Regulatory compliance in the financial sector for blockchain systems.")
    logging.info(f"Vector Result: {vector}")
    
    if vector[1] != "0.0.0.0" and vector[2] != "0.0.0.0":
        logging.info("SUCCESS: Multi-axis resolution confirmed.")
    else:
        logging.warning("PARTIAL SUCCESS: One or more primary axes failed to resolve.")

    logging.info("\n=== Verification Complete ===")

if __name__ == "__main__":
    verify_axis_mapper()

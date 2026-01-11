import logging
import sys
import os
from datetime import datetime
from backend.knowledge_algorithm.axis_mapper import AxisMapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def verify_phase5_coordinates():
    logging.info("=== UKG Phase 5 High-Fidelity Coordinate Verification ===")
    
    try:
        mapper = AxisMapper()
        
        # Test Case 1: Multi-domain (Pillar 1 + Pillar 2) for Honeycomb
        query1 = "Impact of Artificial Intelligence on Medical Ethics and Healthcare"
        logging.info(f"Testing Query 1: '{query1}'")
        vector1 = mapper.get_17axis_vector(query1)
        
        logging.info(f"Resolved Vector 1: {vector1}")
        
        # Axis 1 (AI) should be 1.41.0.0
        # Axis 2 (Healthcare) should be 2.22.X.X (Sector 62: Health Care)
        # Axis 3 (Honeycomb) should link 41 and 90 (Medicine) or 88 (Public Health)
        
        if vector1[1].startswith("1.41"):
            logging.info("SUCCESS: Axis 1 (Pillar) correctly resolved to AI.")
        else:
            logging.error(f"FAILURE: Axis 1 Pillar resolution incorrect: {vector1[1]}")
            
        if vector1[3].startswith("3.41"):
            logging.info(f"SUCCESS: Axis 3 (Honeycomb) correctly detected AI link: {vector1[3]}")
        else:
            logging.error(f"FAILURE: Axis 3 Honeycomb failed to link AI: {vector1[3]}")

        # Test Case 2: Regulatory Crosswalk
        query2 = "Banking liquidity requirements under Basel III using Blockchain"
        logging.info(f"\nTesting Query 2: '{query2}'")
        vector2 = mapper.get_17axis_vector(query2)
        logging.info(f"Resolved Vector 2: {vector2}")
        
        if vector2[6].startswith("6.1"):
            logging.info("SUCCESS: Axis 6 (Octopus) correctly resolved Financial Regulatory framework.")
        else:
            logging.error(f"FAILURE: Axis 6 Regulatory resolution incorrect: {vector2[6]}")

        if vector2[7].startswith("7.1"):
            logging.info("SUCCESS: Axis 7 (Spiderweb) correctly resolved Banking/Basel compliance.")
        else:
            logging.error(f"FAILURE: Axis 7 Compliance resolution incorrect: {vector2[7]}")

        # Test Case 3: Branch & Node
        query3 = "Oilseed and Grain Farming sustainability"
        logging.info(f"\nTesting Query 3: '{query3}'")
        vector3 = mapper.get_17axis_vector(query3)
        logging.info(f"Resolved Vector 3: {vector3}")
        
        # Sector 111 (Oilseed) coordinate is 2.1.1.1
        # Axis 4 (Branch) should be 4.1.0.0
        # Axis 5 (Node) should be 5.1.0.0
        
        if vector3[4] == "4.1.0.0" and vector3[5] == "5.1.0.0":
            logging.info("SUCCESS: Axis 4/5 Branch & Node correctly derived from sectoral hierarchy.")
        else:
            logging.error(f"FAILURE: Axis 4/5 resolution incorrect: 4={vector3[4]}, 5={vector3[5]}")

        logging.info("\n=== Phase 5 High-Fidelity Coordinate Verification Complete ===")
        return True

    except Exception as e:
        logging.error(f"CRITICAL FAILURE during verification: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_phase5_coordinates()
    sys.exit(0 if success else 1)

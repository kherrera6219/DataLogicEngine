import logging
import sys
import os
import re
from datetime import datetime
from backend.knowledge_algorithm.axis_mapper import AxisMapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def verify_phase6_full_axes():
    logging.info("=== UKG Phase 6 Full 17-Axis Spectrum Verification ===")
    
    try:
        mapper = AxisMapper()
        
        # Comprehensive Query
        query = "Live EU regulatory sentiment for medical AI budget allocation in 2026"
        logging.info(f"Testing Complex Query: '{query}'")
        vector = mapper.get_17axis_vector(query)
        
        logging.info(f"Full 17-Axis Vector: {vector}")
        
        # Assertions
        results = []
        
        # Axis 1-2 (Basic)
        logging.info(f"Checking Axis 1: {vector[1]}")
        if vector[1].startswith("1.41") or vector[1].startswith("1.90"): 
            results.append("✅ Axis 1 (Pillar): AI/Medicine detected.")
        else:
            results.append(f"❌ Axis 1 (Pillar): Resolution failed. Got: {vector[1]}")
            
        # Axis 8 (Temporal)
        logging.info(f"Checking Axis 8: {vector[8]}")
        if vector[8] == "8.6.0.0": 
             results.append("✅ Axis 8 (Temporal): Year 2026 detected.")
        else:
             results.append(f"❌ Axis 8 (Temporal): Year detection failed. Got: {vector[8]}")

        # Axis 9 (Spatial)
        logging.info(f"Checking Axis 9: {vector[9]}")
        if vector[9] == "9.2.0.0": 
             results.append("✅ Axis 9 (Spatial): EU context detected.")
        else:
             results.append(f"❌ Axis 9 (Spatial): EU detection failed. Got: {vector[9]}")

        # Axis 10 (Quantitative)
        logging.info(f"Checking Axis 10: {vector[10]}")
        if vector[10] == "10.5.0.0": 
             results.append("✅ Axis 10 (Quantitative): Budget metric detected.")
        else:
             results.append(f"❌ Axis 10 (Quantitative): Budget detection failed. Got: {vector[10]}")

        # Axis 11 (Qualitative)
        logging.info(f"Checking Axis 11: {vector[11]}")
        if vector[11] == "11.5.0.0": 
             results.append("✅ Axis 11 (Qualitative): Sentiment intent detected.")
        else:
             results.append(f"❌ Axis 11 (Qualitative): Sentiment detection failed. Got: {vector[11]}")

        # Summary output
        for r in results:
            logging.info(r)

        logging.info("\n=== Phase 6 Verification Complete ===")
        return all("✅" in r for r in results)

    except Exception as e:
        logging.error(f"CRITICAL FAILURE during verification: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_phase6_full_axes()
    sys.exit(0 if success else 1)

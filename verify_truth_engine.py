import logging
import os
import sys
from backend.knowledge_algorithm.truth_engine import TruthEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def verify_truth_engine():
    logging.info("=== UKG Truth Engine Verification ===")
    
    engine = TruthEngine()
    
    # 1. Simulate KA Results
    # We provide a mix of Fact-checking, Reasoning, and Ethics results
    ka_results = [
        {"ka_id": "KA-009", "results": {"confidence": 0.85}}, # Evidence Validation (Factuality)
        {"ka_id": "KA-018", "results": {"confidence": 0.90}}, # Source Provenance (Factuality)
        {"ka_id": "KA-001", "results": {"confidence": 0.75}}, # AoT (Reasoning)
        {"ka_id": "KA-002", "results": {"confidence": 0.80}}, # ToT (Reasoning)
        {"ka_id": "KA-010", "results": {"confidence": 0.95}}, # Bias Detection (Ethics)
        {"ka_id": "KA-019", "results": {"confidence": 0.88}}, # Knowledge Synthesis (Synthesis)
    ]
    
    logging.info(f"\n1. Calculating Truth Vector from {len(ka_results)} KA results...")
    truth_vector = engine.calculate_truth_vector(ka_results)
    logging.info(f"Truth Vector (Scores): {truth_vector}")
    
    # 2. Convert to Coordinates
    logging.info("\n2. Converting to 17-Axis Coordinates...")
    coords = engine.get_truth_coordinates(truth_vector)
    for axis, coord in coords.items():
        logging.info(f"Axis {axis}: {coord}")
        
    if coords[14].startswith("14.8") and coords[16].startswith("16.9"):
        logging.info("SUCCESS: Truth coordinate resolution verified.")
    else:
        logging.warning("FAILURE: Coordinate mapping mismatch.")

    # 3. Validation Check
    logging.info("\n3. Testing Validation Logic...")
    is_valid, reason = engine.get_validation_status(truth_vector)
    logging.info(f"Status: {is_valid}, Reason: {reason}")
    
    if is_valid:
        logging.info("SUCCESS: High-confidence simulation validated.")
    else:
        logging.warning("FAILURE: Simulation rejected unexpectedly.")

    # 4. Low Factuality Failure Test
    logging.info("\n4. Testing Low Factuality Rejection...")
    low_fact_results = [{"ka_id": "KA-009", "results": {"confidence": 0.3}}]
    low_fact_vector = engine.calculate_truth_vector(low_fact_results)
    is_valid_low, reason_low = engine.get_validation_status(low_fact_vector)
    logging.info(f"Status: {is_valid_low}, Reason: {reason_low}")
    
    if not is_valid_low:
        logging.info("SUCCESS: Low factuality correctly rejected.")
    else:
        logging.warning("FAILURE: Low factuality should have been rejected.")

    logging.info("\n=== Verification Complete ===")

if __name__ == "__main__":
    verify_truth_engine()

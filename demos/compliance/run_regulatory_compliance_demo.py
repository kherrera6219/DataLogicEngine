#!/usr/bin/env python
"""
Regulatory and Compliance Demo for Knowledge Algorithms KA-06 to KA-10

This script demonstrates how the specialized Knowledge Algorithms work together
to provide advanced regulatory and compliance analysis for the UKG system.
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("regulatory_compliance_demo")

# Ensure the knowledge_algorithms directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Knowledge Algorithms
from knowledge_algorithms.ka_06_coordinate_mapper import run as run_ka_06
from knowledge_algorithms.ka_07_regulatory_expert_simulation import run as run_ka_07
from knowledge_algorithms.ka_08_compliance_expert_simulation import run as run_ka_08
from knowledge_algorithms.ka_09_conflict_resolution import run as run_ka_09
from knowledge_algorithms.ka_10_contractual_logic_validator import run as run_ka_10
from knowledge_algorithms.ka_16_simulation_memory_patch import run as run_ka_16


def generate_coordinate_mappings(pillar_level: str, axes: List[int], domain: str) -> Dict[str, Any]:
    """Generate UKG coordinate mappings using KA-06."""
    logger.info(f"Generating coordinate mappings for PL{pillar_level}, axes {axes}, domain {domain}")
    
    # Prepare data for KA-06
    data = {
        "pillar_level": f"PL{pillar_level}",
        "axes": axes,
        "domain": domain
    }
    
    # Run KA-06 (Coordinate Projection Mapper)
    result = run_ka_06(data)
    
    if result.get("success", False):
        logger.info(f"Generated coordinate string: {result.get('coordinate_string')}")
    else:
        logger.error(f"Failed to generate coordinates: {result.get('error')}")
    
    return result


def analyze_regulatory_perspective(query: str, domain: Optional[str] = None) -> Dict[str, Any]:
    """Analyze query from regulatory perspective using KA-07."""
    logger.info(f"Analyzing regulatory perspective for query: {query}")
    
    # Prepare data for KA-07
    data = {
        "query": query,
        "context": {"domain": domain} if domain else {}
    }
    
    # Run KA-07 (Regulatory Expert Simulation)
    result = run_ka_07(data)
    
    if result.get("success", False):
        logger.info(f"Regulatory analysis complete with confidence: {result.get('confidence', 0):.2f}")
        
        # Log key insights
        regulations = result.get("applicable_regulations", [])
        logger.info(f"Identified {len(regulations)} applicable regulations")
        for reg in regulations[:3]:  # Show top 3
            logger.info(f"  - {reg.get('code')}: {reg.get('title')} ({reg.get('relevance')})")
    else:
        logger.error(f"Failed to complete regulatory analysis: {result.get('error')}")
    
    return result


def analyze_compliance_perspective(query: str, sector: Optional[str] = None) -> Dict[str, Any]:
    """Analyze query from compliance perspective using KA-08."""
    logger.info(f"Analyzing compliance perspective for query: {query}")
    
    # Prepare data for KA-08
    data = {
        "query": query,
        "context": {"sector": sector} if sector else {}
    }
    
    # Run KA-08 (Compliance Expert Simulation)
    result = run_ka_08(data)
    
    if result.get("success", False):
        logger.info(f"Compliance analysis complete with confidence: {result.get('confidence', 0):.2f}")
        
        # Log key insights
        standards = result.get("applicable_standards", [])
        logger.info(f"Identified {len(standards)} applicable standards")
        for std in standards[:3]:  # Show top 3
            logger.info(f"  - {std.get('id')}: {std.get('title')} ({std.get('relevance')})")
    else:
        logger.error(f"Failed to complete compliance analysis: {result.get('error')}")
    
    return result


def analyze_conflicts(regulatory_result: Dict[str, Any], compliance_result: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze potential conflicts between regulatory and compliance findings using KA-09."""
    logger.info("Analyzing potential conflicts between regulatory and compliance findings")
    
    # Extract clauses for conflict analysis
    clauses = []
    
    # Add regulatory guidance as a clause
    if "guidance" in regulatory_result:
        clauses.append(regulatory_result["guidance"])
    
    # Add compliance guidance as a clause
    if "guidance" in compliance_result:
        clauses.append(compliance_result["guidance"])
    
    # Add major regulations as clauses
    for reg in regulatory_result.get("applicable_regulations", [])[:3]:
        if "code" in reg and "title" in reg:
            clauses.append(f"{reg['code']}: {reg['title']}")
    
    # Add major standards as clauses
    for std in compliance_result.get("applicable_standards", [])[:3]:
        if "id" in std and "title" in std:
            clauses.append(f"{std['id']}: {std['title']}")
    
    # Prepare context
    context = {
        "domain": regulatory_result.get("domain", "general"),
        "sector": compliance_result.get("sector", "general")
    }
    
    # Prepare data for KA-09
    data = {
        "clauses": clauses,
        "context": context
    }
    
    # Run KA-09 (Conflict Resolution Engine)
    result = run_ka_09(data)
    
    if result.get("success", False):
        logger.info(f"Conflict analysis complete with confidence: {result.get('confidence', 0):.2f}")
        
        # Log conflict status
        conflicts = result.get("conflicts_detected", [])
        logger.info(f"Identified {len(conflicts)} potential conflicts")
        
        # Log resolution plan if exists
        if "resolution_plan" in result and result["resolution_plan"]:
            priority = result["resolution_plan"].get("priority", "unknown")
            steps = result["resolution_plan"].get("recommended_steps", [])
            logger.info(f"Resolution plan priority: {priority}")
            logger.info(f"Recommended steps: {len(steps)}")
    else:
        logger.error(f"Failed to complete conflict analysis: {result.get('error')}")
    
    return result


def validate_contract_clauses(contract_clauses: List[str], contract_type: Optional[str] = None) -> Dict[str, Any]:
    """Validate contract clauses using KA-10."""
    logger.info(f"Validating {len(contract_clauses)} contract clauses")
    
    # Prepare data for KA-10
    data = {
        "contract_clauses": contract_clauses,
        "contract_type": contract_type
    }
    
    # Run KA-10 (Contractual Logic Validator)
    result = run_ka_10(data)
    
    if result.get("success", False):
        logger.info(f"Contract validation complete with confidence: {result.get('confidence', 0):.2f}")
        logger.info(f"Contract validity: {result.get('valid_contract', False)}")
        
        # Log recommendations
        recommendations = result.get("recommendations", [])
        high_priority = [r for r in recommendations if r.get("priority") == "high"]
        logger.info(f"Identified {len(recommendations)} recommendations, {len(high_priority)} high priority")
    else:
        logger.error(f"Failed to validate contract: {result.get('error')}")
    
    return result


def store_in_memory(session_id: str, query: str, results: Dict[str, Any]) -> Dict[str, Any]:
    """Store analysis results in memory using KA-16."""
    logger.info(f"Storing results in memory for session {session_id}")
    
    # Prepare data for KA-16
    data = {
        "action": "patch",
        "session_id": session_id,
        "query": query,
        "domain": results.get("domain", "general"),
        "result": results
    }
    
    # Run KA-16 (Simulation Memory Patch)
    result = run_ka_16(data)
    
    if result.get("success", False):
        logger.info("Successfully stored results in memory")
        
        # Log memory status
        memory_status = result.get("memory_status", {})
        logger.info(f"Memory status: {memory_status}")
    else:
        logger.error(f"Failed to store results in memory: {result.get('error')}")
    
    return result


def retrieve_from_memory(session_id: str, query: str) -> Dict[str, Any]:
    """Retrieve context from memory using KA-16."""
    logger.info(f"Retrieving context from memory for session {session_id}")
    
    # Prepare data for KA-16
    data = {
        "action": "retrieve",
        "session_id": session_id,
        "query": query
    }
    
    # Run KA-16 (Simulation Memory Patch)
    result = run_ka_16(data)
    
    if "context" in result:
        logger.info("Successfully retrieved context from memory")
        
        # Log context highlights
        context = result.get("context", {})
        entities = context.get("relevant_entities", [])
        concepts = context.get("relevant_concepts", [])
        facts = context.get("relevant_facts", [])
        
        logger.info(f"Retrieved {len(entities)} relevant entities, {len(concepts)} concepts, {len(facts)} facts")
    else:
        logger.error(f"Failed to retrieve context from memory: {result.get('error')}")
    
    return result


def run_healthcare_compliance_demo() -> None:
    """Run a demo of healthcare compliance analysis."""
    logger.info("\n=== HEALTHCARE COMPLIANCE DEMO ===\n")
    
    session_id = "healthcare_demo_session"
    
    # Step 1: Generate UKG coordinates
    coord_result = generate_coordinate_mappings("4", [8, 11], "healthcare")
    
    # Step 2: Run regulatory analysis on a healthcare query
    query = "What are the HIPAA compliance requirements for storing patient data in cloud services?"
    reg_result = analyze_regulatory_perspective(query, domain="healthcare")
    
    # Step 3: Run compliance analysis on the same query
    comp_result = analyze_compliance_perspective(query, sector="healthcare")
    
    # Step 4: Analyze potential conflicts between regulatory and compliance findings
    conflict_result = analyze_conflicts(reg_result, comp_result)
    
    # Step 5: Store results in memory
    memory_result = store_in_memory(session_id, query, {
        "coordinate_result": coord_result,
        "regulatory_result": reg_result,
        "compliance_result": comp_result,
        "conflict_result": conflict_result,
        "domain": "healthcare"
    })
    
    # Step 6: Run contract validation on sample healthcare clauses
    healthcare_clauses = [
        "Provider shall maintain all patient data in accordance with HIPAA requirements.",
        "Provider may share anonymized data for research purposes.",
        "In the event of a data breach, Provider must notify affected individuals within a reasonable time.",
        "All Protected Health Information must be encrypted both at rest and in transit.",
        "Business Associate agrees to implement appropriate safeguards to prevent use or disclosure of PHI."
    ]
    
    contract_result = validate_contract_clauses(healthcare_clauses, contract_type="data_processing")
    
    # Step 7: Demonstrate memory retrieval with a follow-up query
    followup_query = "What about GDPR requirements for patient data in Europe?"
    context_result = retrieve_from_memory(session_id, followup_query)
    
    # Log final summary
    logger.info("\n=== HEALTHCARE COMPLIANCE DEMO COMPLETE ===\n")
    logger.info(f"Coordinate string: {coord_result.get('coordinate_string', 'N/A')}")
    logger.info(f"Regulatory confidence: {reg_result.get('confidence', 0):.2f}")
    logger.info(f"Compliance confidence: {comp_result.get('confidence', 0):.2f}")
    logger.info(f"Contract validity: {contract_result.get('valid_contract', False)}")


def run_financial_compliance_demo() -> None:
    """Run a demo of financial compliance analysis."""
    logger.info("\n=== FINANCIAL COMPLIANCE DEMO ===\n")
    
    session_id = "financial_demo_session"
    
    # Step 1: Generate UKG coordinates
    coord_result = generate_coordinate_mappings("5", [9, 10], "finance")
    
    # Step 2: Run regulatory analysis on a financial query
    query = "What regulatory requirements apply to cross-border payments between US and EU financial institutions?"
    reg_result = analyze_regulatory_perspective(query, domain="finance")
    
    # Step 3: Run compliance analysis on the same query
    comp_result = analyze_compliance_perspective(query, sector="finance")
    
    # Step 4: Analyze potential conflicts between regulatory and compliance findings
    conflict_result = analyze_conflicts(reg_result, comp_result)
    
    # Step 5: Store results in memory
    memory_result = store_in_memory(session_id, query, {
        "coordinate_result": coord_result,
        "regulatory_result": reg_result,
        "compliance_result": comp_result,
        "conflict_result": conflict_result,
        "domain": "finance"
    })
    
    # Step 6: Run contract validation on sample financial clauses
    financial_clauses = [
        "Bank shall comply with all applicable anti-money laundering regulations.",
        "Customer must provide identification as required by Know Your Customer regulations.",
        "Bank will report suspicious transactions in accordance with local regulations.",
        "Transactions over $10,000 require additional verification.",
        "Bank reserves the right to freeze accounts if compliance concerns arise."
    ]
    
    contract_result = validate_contract_clauses(financial_clauses, contract_type="finance")
    
    # Step 7: Demonstrate memory retrieval with a follow-up query
    followup_query = "What are the implications of Basel III for international wire transfers?"
    context_result = retrieve_from_memory(session_id, followup_query)
    
    # Log final summary
    logger.info("\n=== FINANCIAL COMPLIANCE DEMO COMPLETE ===\n")
    logger.info(f"Coordinate string: {coord_result.get('coordinate_string', 'N/A')}")
    logger.info(f"Regulatory confidence: {reg_result.get('confidence', 0):.2f}")
    logger.info(f"Compliance confidence: {comp_result.get('confidence', 0):.2f}")
    logger.info(f"Contract validity: {contract_result.get('valid_contract', False)}")


def main():
    """Main function to run the appropriate demo."""
    parser = argparse.ArgumentParser(description="Run Regulatory and Compliance Knowledge Algorithm Demo")
    parser.add_argument("--demo", choices=["healthcare", "finance", "both"], default="both",
                      help="Which demo to run (healthcare, finance, or both)")
    
    args = parser.parse_args()
    
    logger.info("Starting Regulatory and Compliance Knowledge Algorithm Demo")
    
    if args.demo == "healthcare" or args.demo == "both":
        run_healthcare_compliance_demo()
    
    if args.demo == "finance" or args.demo == "both":
        run_financial_compliance_demo()
    
    logger.info("Demo completed successfully")


if __name__ == "__main__":
    main()
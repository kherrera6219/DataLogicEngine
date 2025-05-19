"""
Knowledge Algorithms (KA) Demonstration Script

This script demonstrates the capability of the Knowledge Algorithms to enhance
the Universal Knowledge Graph (UKG) system with specialized processing.
"""

import logging
import sys
import json
from typing import Dict, Any

from knowledge_algorithms.ka_demo import main as run_ka_demo
from knowledge_algorithms.ka_system_integration import get_ka_integration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def test_ka_integration(query: str, domain: str = None) -> Dict[str, Any]:
    """
    Test the KA System Integration with a query.
    
    Args:
        query: The query text
        domain: Optional domain context
        
    Returns:
        The processing results
    """
    # Get the integration instance
    ka_integration = get_ka_integration()
    
    # Process the query
    context = {"domain": domain} if domain else {}
    
    logger.info(f"Processing query via KA Integration: \"{query}\"")
    logger.info(f"Context: {json.dumps(context)}")
    
    result = ka_integration.process_query(query, context)
    
    # Print summary
    summary = result.get("ka_system_summary", {})
    
    logger.info(f"\n----- KA Integration Result -----")
    logger.info(f"Query: \"{query}\"")
    
    if "domain" in summary:
        logger.info(f"Domain: {summary['domain']}")
    
    if "pillar_levels" in summary:
        logger.info(f"Pillar Levels: {', '.join(summary['pillar_levels'])}")
    
    if "axes" in summary:
        logger.info(f"Axes: {', '.join(map(str, summary['axes']))}")
    
    if "related_sectors" in summary:
        logger.info(f"Related Sectors: {', '.join(summary['related_sectors'][:3])}...")
    
    if "active_personas" in summary:
        logger.info(f"Active Personas: {', '.join(summary['active_personas'])}")
    
    if "integrated_response" in summary:
        response = summary["integrated_response"]
        preview = response[:300] + "..." if len(response) > 300 else response
        logger.info(f"Response Preview:\n{preview}")
    
    if "confidence" in summary:
        logger.info(f"Confidence: {summary['confidence']:.2f}")
    
    return result

def main():
    """Main function to run the demonstration."""
    logger.info("Starting Knowledge Algorithms (KA) Integration Demo")
    
    # Define test queries
    test_queries = [
        {
            "query": "What are the key healthcare regulations that apply to telemedicine across international borders?",
            "domain": "healthcare"
        },
        {
            "query": "How do financial technology standards apply to blockchain-based payment systems?",
            "domain": "finance"
        },
        {
            "query": "What environmental compliance considerations apply to cloud computing data centers?",
            "domain": "technology"
        }
    ]
    
    # Test each query
    for test in test_queries:
        query = test["query"]
        domain = test.get("domain")
        
        # Process query
        test_ka_integration(query, domain)
        logger.info("\n" + "="*50 + "\n")
    
    logger.info("KA Integration Demo completed successfully")
    
    # Option to run detailed algorithmic testing
    logger.info("\nRunning individual algorithm testing...")
    run_ka_demo()
    
    logger.info("\nAll demonstrations completed")

if __name__ == "__main__":
    main()
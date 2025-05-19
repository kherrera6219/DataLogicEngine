#!/usr/bin/env python3
"""
UKG Layer 7 AGI Simulation Demo

This script demonstrates the Layer 7 AGI Simulation capabilities of the 
Universal Knowledge Graph system, showing its recursive goal planning,
belief realignment, and multi-agent reasoning capabilities.

Usage:
    python run_ukg_layer7_demo.py [--debug] [--verbose]
"""

import argparse
import logging
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional

# Import core UKG components
from core.system.united_system_manager import UnitedSystemManager
from simulation.gatekeeper_agent import GatekeeperAgent
from simulation.layer7_agi_system import AGISimulationEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run Layer 7 AGI Simulation Demo')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    return parser.parse_args()

def setup_demo_environment():
    """Setup the demo environment with necessary configuration"""
    logger.info("Setting up demo environment...")
    
    # Initialize the system manager - UnitedSystemManager doesn't have initialize method
    system_manager = UnitedSystemManager()
    
    # Initialize Gatekeeper Agent
    gatekeeper = GatekeeperAgent()
    
    # Initialize the Layer 7 AGI Simulation Engine
    layer7_config = {
        "max_recursion_depth": 3,
        "uncertainty_threshold": 0.15,
        "goal_expansion_factor": 2.0,
        "belief_realignment_factor": 1.5,
        "goal_convergence_threshold": 0.75
    }
    
    agi_engine = AGISimulationEngine(config=layer7_config, system_manager=system_manager)
    
    return system_manager, gatekeeper, agi_engine

def create_test_context(complexity="medium", confidence=0.75, entropy=0.3):
    """Create a test context for the demo"""
    logger.info(f"Creating test context with complexity={complexity}, confidence={confidence}, entropy={entropy}")
    
    # Sample query
    query = "What are the regulatory implications of using AI for automated trading systems in financial markets?"
    
    # Sample persona results
    persona_results = {
        "knowledge": {
            "response": "AI-based automated trading systems are subject to regulatory oversight by financial authorities. The primary concerns are market manipulation, algorithmic bias, transparency, and system stability.",
            "confidence": 0.85,
            "beliefs": [
                {"content": "AI trading systems require regulatory approval", "confidence": 0.9, "type": "fact"},
                {"content": "Market manipulation is a major concern for AI trading", "confidence": 0.85, "type": "fact"},
                {"content": "Algorithmic bias can lead to unfair trading advantages", "confidence": 0.8, "type": "fact"}
            ]
        },
        "sector": {
            "response": "In the financial sector, automated trading systems using AI must comply with specific regulations that vary by jurisdiction. They typically address pre-trade risk controls, post-trade surveillance, and testing requirements.",
            "confidence": 0.8,
            "beliefs": [
                {"content": "Financial regulations vary significantly by jurisdiction", "confidence": 0.9, "type": "fact"},
                {"content": "Pre-trade risk controls are mandatory in most markets", "confidence": 0.85, "type": "fact"},
                {"content": "Testing requirements have become more stringent in recent years", "confidence": 0.75, "type": "analysis"}
            ]
        },
        "regulatory": {
            "response": "Regulatory frameworks for AI trading include SEC Rule 15c3-5, MiFID II in Europe, and principles set by IOSCO. These require risk controls, testing, and documentation of algorithmic strategies.",
            "confidence": 0.9,
            "beliefs": [
                {"content": "SEC Rule 15c3-5 mandates pre-trade risk controls", "confidence": 0.95, "type": "regulation"},
                {"content": "MiFID II has strict requirements for algorithmic trading", "confidence": 0.95, "type": "regulation"},
                {"content": "IOSCO principles provide a global framework", "confidence": 0.9, "type": "regulation"}
            ]
        },
        "compliance": {
            "response": "Compliance requirements for AI trading systems include documentation of algorithms, regular testing, kill switches, and audit trails. Organizations must demonstrate their systems cannot manipulate markets.",
            "confidence": 0.85,
            "beliefs": [
                {"content": "Documentation of algorithms is a key compliance requirement", "confidence": 0.9, "type": "compliance"},
                {"content": "Kill switches are mandatory for safe operation", "confidence": 0.85, "type": "compliance"},
                {"content": "Audit trails must be maintained for all trading activities", "confidence": 0.9, "type": "compliance"}
            ]
        }
    }
    
    # Create a synthesis from persona results
    synthesis = {
        "content": "AI-based automated trading systems are subject to comprehensive regulatory frameworks across different jurisdictions. Key regulations include SEC Rule 15c3-5 in the US and MiFID II in Europe, which mandate risk controls, testing procedures, and documentation requirements. Compliance necessitates detailed algorithm documentation, regular testing protocols, emergency kill switches, and complete audit trails. The primary regulatory concerns include prevention of market manipulation, addressing algorithmic bias, ensuring system transparency, and maintaining market stability.",
        "key_beliefs": [
            {"content": "AI trading systems require comprehensive regulatory compliance", "confidence": 0.92, "type": "synthesis"},
            {"content": "Documentation, testing, and audit trails are universal requirements", "confidence": 0.9, "type": "synthesis"},
            {"content": "Regulations aim to prevent market manipulation and ensure stability", "confidence": 0.88, "type": "synthesis"}
        ]
    }
    
    # Create the full context
    context = {
        "simulation_id": f"SIM_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "query": query,
        "persona_results": persona_results,
        "synthesis": synthesis,
        "confidence_score": confidence,
        "entropy_score": entropy,
        "complexity": complexity,
        "simulation_pass": 1,
        "historical_confidence": [0.65, 0.72, confidence]  # Simulated confidence progression
    }
    
    return context

def run_agi_simulation(agi_engine, gatekeeper, context):
    """Run the AGI simulation with the provided context"""
    logger.info("Running AGI simulation...")
    
    # First, let the gatekeeper evaluate the context
    logger.info("Gatekeeper evaluating context...")
    gatekeeper_decision = gatekeeper.evaluate(context)
    context['gatekeeper_decision'] = gatekeeper_decision
    context['gatekeeper'] = gatekeeper
    
    # Get Layer 7 parameters from gatekeeper
    logger.info("Getting Layer 7 AGI parameters from gatekeeper...")
    layer7_params = gatekeeper.get_layer7_agi_parameters(context)
    context['layer7_params'] = layer7_params
    
    # Check if Layer 7 is activated
    if not layer7_params.get('active', False):
        logger.info("Layer 7 AGI simulation not activated by gatekeeper")
        return context
        
    logger.info("Layer 7 AGI simulation activated with parameters:")
    for key, value in layer7_params.items():
        if key != 'context_metrics' and key != 'triggers':
            logger.info(f"  - {key}: {value}")
    
    # Run the AGI simulation
    logger.info("Processing through Layer 7 AGI simulation engine...")
    processed_context = agi_engine.process(context)
    
    # Log AGI simulation results
    logger.info(f"AGI simulation completed with confidence: {processed_context.get('confidence_score', 0.0):.4f}")
    logger.info(f"Entropy: {processed_context.get('entropy', 0.0):.4f}")
    logger.info(f"Emergence score: {processed_context.get('emergence_score', 0.0):.4f}")
    
    # Check if escalation to Layer 8 is needed
    if processed_context.get('layer8_escalation'):
        logger.info("*** Escalation to Layer 8 (Quantum Simulation) triggered ***")
        logger.info(f"Escalation reason: {processed_context['layer8_escalation'].get('escalation_reason', 'Unknown')}")
        logger.info(f"Escalation priority: {processed_context['layer8_escalation'].get('priority', 'medium')}")
    
    return processed_context

def print_rich_results(processed_context, verbose=False):
    """Print rich, formatted results from the AGI simulation"""
    print("\n" + "="*80)
    print("🧠 LAYER 7 AGI SIMULATION RESULTS")
    print("="*80)
    
    # Print basic metrics
    print(f"\n📊 METRICS:")
    print(f"  Confidence Score: {processed_context.get('confidence_score', 0.0):.4f}")
    print(f"  Entropy Score: {processed_context.get('entropy', 0.0):.4f}")
    print(f"  Emergence Score: {processed_context.get('emergence_score', 0.0):.4f}")
    print(f"  Processing Time: {processed_context.get('processing_time_ms', 0.0):.2f}ms")
    
    # Print goal convergence
    print(f"\n🎯 GOAL CONVERGENCE:")
    convergence = processed_context.get('convergence', {})
    print(f"  Status: {'✅ Converged' if convergence.get('converged', False) else '❌ Not converged'}")
    print(f"  Score: {convergence.get('score', 0.0):.4f}")
    if 'reasons' in convergence:
        print(f"  Reasons:")
        for reason in convergence.get('reasons', [])[:3]:  # Show top 3 reasons
            print(f"    - {reason}")
    
    # Print AGI summary
    print("\n📝 AGI PROCESSING SUMMARY:")
    agi_summary = processed_context.get('agi_summary', "No summary available")
    print(f"{agi_summary}")
    
    # Print detailed outputs if verbose
    if verbose:
        print("\n🔍 DETAILED OUTPUTS:")
        
        # Show goals
        print("\n  Goals:")
        goals = processed_context.get('goals', [])
        for i, goal in enumerate(goals[:5]):  # Show top 5 goals
            print(f"    - [{goal.get('id', 'g?')}] {goal.get('content', 'Unknown')} "
                  f"(prob: {goal.get('probability', 0.0):.2f}, depth: {goal.get('depth', 0)})")
        
        # Show conflicts
        conflicts = processed_context.get('conflicts', [])
        if conflicts:
            print("\n  Conflicts:")
            for i, conflict in enumerate(conflicts[:3]):  # Show top 3 conflicts
                status = "✅ Resolved" if conflict.get('resolved', False) else "❌ Unresolved"
                print(f"    - [{conflict.get('id', 'c?')}] {status}")
                print(f"      Goal: {conflict.get('goal_content', 'Unknown')}")
                print(f"      Belief: {conflict.get('belief_content', 'Unknown')}")
                if conflict.get('resolution'):
                    print(f"      Resolution: {conflict.get('resolution')}")
    
    # Print Layer 8 escalation info if present
    if processed_context.get('layer8_escalation'):
        print("\n⚛️ QUANTUM SIMULATION ESCALATION:")
        escalation = processed_context.get('layer8_escalation', {})
        print(f"  Reason: {escalation.get('escalation_reason', 'Unknown')}")
        print(f"  Priority: {escalation.get('priority', 'medium')}")
        print(f"  Entropy: {escalation.get('goal_entropy', 0.0):.4f}")
        print(f"  Emergence Score: {escalation.get('emergence_score', 0.0):.4f}")
        print("\n  Next steps would involve Layer 8 Quantum Simulation")
        print("  (This part will be implemented in the next phase)")
    
    print("\n" + "="*80)

def main():
    """Main function to run the demo"""
    args = parse_arguments()
    
    # Setup logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("\n" + "="*80)
    print("🌟 UKG LAYER 7 AGI SIMULATION DEMO")
    print("="*80)
    print("\nThis demo showcases the Layer 7 AGI Simulation capabilities of the")
    print("Universal Knowledge Graph (UKG) system, demonstrating recursive goal")
    print("planning, belief realignment, and multi-agent reasoning.\n")
    
    # Setup demo environment
    try:
        system_manager, gatekeeper, agi_engine = setup_demo_environment()
    except Exception as e:
        logger.error(f"Error setting up demo environment: {e}")
        sys.exit(1)
    
    # Create test contexts with different complexity levels
    test_scenarios = [
        {"name": "Standard scenario", "complexity": "medium", "confidence": 0.75, "entropy": 0.3},
        {"name": "High uncertainty scenario", "complexity": "high", "confidence": 0.65, "entropy": 0.5},
        {"name": "High confidence scenario", "complexity": "low", "confidence": 0.92, "entropy": 0.1}
    ]
    
    # Display available scenarios
    print("Available test scenarios:")
    for i, scenario in enumerate(test_scenarios):
        print(f"  {i+1}. {scenario['name']} (Complexity: {scenario['complexity']}, "
              f"Confidence: {scenario['confidence']}, Entropy: {scenario['entropy']})")
    
    # Automatically select the first scenario for simplicity
    choice = 1
    print(f"\nAutomatically selecting scenario 1")
    
    selected_scenario = test_scenarios[choice-1]
    print(f"\nSelected scenario: {selected_scenario['name']}")
    
    # Create test context based on selected scenario
    context = create_test_context(
        complexity=selected_scenario['complexity'],
        confidence=selected_scenario['confidence'],
        entropy=selected_scenario['entropy']
    )
    
    # Run AGI simulation
    try:
        processed_context = run_agi_simulation(agi_engine, gatekeeper, context)
    except Exception as e:
        logger.error(f"Error running AGI simulation: {e}")
        sys.exit(1)
    
    # Print results
    print_rich_results(processed_context, verbose=args.verbose)
    
    # Check if Layer 8 would be activated
    if processed_context.get('layer8_escalation'):
        print("\n🔮 Next steps would involve Layer 8 (Simulated Quantum Computer)")
        print("This layer would use quantum state simulation to handle ambiguities")
        print("and conflicts that the AGI layer couldn't resolve deterministically.")
        print("Stay tuned for the implementation of Layer 8!")
    
    print("\nDemo completed successfully!")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
UKG Layer 9-10 Demo (Recursive AGI Core & Self-Awareness Engine)

This script demonstrates the Layer 9 (Recursive AGI Core) and Layer 10 (Self-Awareness Engine)
capabilities of the Universal Knowledge Graph system, showing recursive processing,
belief alignment, identity consistency tracking, and self-monitoring capabilities.

Usage:
    python run_ukg_layer9_10_demo.py [--debug] [--verbose]
"""

import argparse
import logging
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

# Import core UKG components
from core.system.united_system_manager import UnitedSystemManager
from simulation.gatekeeper_agent import GatekeeperAgent
from simulation.layer7_agi_system import AGISimulationEngine
from simulation.layer8_quantum_computer import SimulatedQuantumComputer
from simulation.layer9_recursive_agi import RecursiveAGICore
from simulation.layer10_self_awareness import SelfAwarenessEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run Layers 9-10 Demo')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    return parser.parse_args()

def setup_demo_environment():
    """Setup the demo environment with necessary configuration"""
    logger.info("Setting up demo environment...")
    
    # Initialize the system manager
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
    
    # Initialize the Layer 8 Quantum Simulation Engine
    layer8_config = {
        "qubit_register_size": 1024,
        "fidelity_threshold": 0.85,
        "collapse_iterations": 10,
        "decoherence_rate": 0.01,
        "max_entanglement_depth": 5,
        "confidence_threshold": 0.92,  # Threshold to activate Layer 8
        "entropy_threshold": 0.35      # Entropy threshold to activate Layer 8
    }
    
    quantum_engine = SimulatedQuantumComputer(config=layer8_config, system_manager=system_manager)
    
    # Initialize the Layer 9 Recursive AGI Core
    layer9_config = {
        "confidence_threshold": 0.995,
        "entropy_threshold": 0.25,
        "rerun_threshold": 0.90,
        "max_recursive_passes": 3,
        "expansion_axes": ["Axis_3", "Axis_8", "Axis_9", "Axis_10", "Axis_11"],
        "inject_new_personas": True
    }
    
    recursive_engine = RecursiveAGICore(config=layer9_config, system_manager=system_manager)
    
    # Initialize the Layer 10 Self-Awareness Engine
    layer10_config = {
        "control_constant": 1.0,
        "lambda_decay": 0.05,
        "ics_threshold": 0.70,
        "entropy_ceiling": 0.25,
        "emergence_monitoring": True,
        "metacognitive_limiter": True,
        "containment_protocol": True
    }
    
    awareness_engine = SelfAwarenessEngine(config=layer10_config, system_manager=system_manager)
    
    return system_manager, gatekeeper, agi_engine, quantum_engine, recursive_engine, awareness_engine

def create_test_context(complexity="high", confidence=0.88, entropy=0.22):
    """Create a test context for the demo with sufficient complexity for Layer 9-10"""
    logger.info(f"Creating test context with complexity={complexity}, confidence={confidence}, entropy={entropy}")
    
    # Sample query requiring complex ethical reasoning
    query = "How should we balance algorithmic decision-making with human oversight in critical infrastructure systems?"
    
    # Sample persona results with varying perspectives and confidence levels
    persona_results = {
        "knowledge": {
            "response": "Algorithmic decision-making in critical infrastructure requires a combination of computational efficiency and human judgment. Current approaches include human-on-the-loop systems where algorithms make recommendations but humans retain decision authority, and human-in-the-loop systems where specific decision thresholds trigger human intervention.",
            "confidence": 0.89,
            "beliefs": [
                {"id": "k1", "content": "Algorithmic decision-making offers efficiency advantages in processing large datasets", "confidence": 0.95, "type": "fact"},
                {"id": "k2", "content": "Human oversight is essential for handling edge cases and novel situations", "confidence": 0.92, "type": "fact"},
                {"id": "k3", "content": "Combined human-algorithmic systems can achieve better results than either alone", "confidence": 0.88, "type": "analysis"}
            ]
        },
        "sector": {
            "response": "In critical infrastructure sectors like energy, transportation, and healthcare, we see varying approaches to the algorithm-human balance. Energy grid management uses algorithmic optimization with human supervisors, while healthcare often requires human clinicians to approve algorithmic diagnostic suggestions. The transportation sector is moving toward more automation but maintains human override capabilities.",
            "confidence": 0.85,
            "beliefs": [
                {"id": "s1", "content": "Different sectors require different balances of algorithmic and human control", "confidence": 0.91, "type": "fact"},
                {"id": "s2", "content": "Transportation systems are increasingly automated but maintain human override", "confidence": 0.87, "type": "analysis"},
                {"id": "s3", "content": "Energy grid management benefits significantly from algorithmic optimization", "confidence": 0.89, "type": "fact"}
            ]
        },
        "regulatory": {
            "response": "Regulatory frameworks increasingly require explainable AI for critical infrastructure systems. The EU AI Act, for instance, classifies critical infrastructure AI as 'high-risk' requiring human oversight, while US regulations vary by sector. Common requirements include algorithmic impact assessments, documented decision criteria, and clear human responsibility chains.",
            "confidence": 0.92,
            "beliefs": [
                {"id": "r1", "content": "Explainable AI is becoming a regulatory requirement for critical systems", "confidence": 0.94, "type": "regulation"},
                {"id": "r2", "content": "Human oversight requirements vary significantly across jurisdictions", "confidence": 0.90, "type": "regulation"},
                {"id": "r3", "content": "Clear responsibility chains must be established regardless of automation level", "confidence": 0.93, "type": "regulation"}
            ]
        },
        "compliance": {
            "response": "Compliance best practices for balancing algorithmic decision-making with human oversight include implementing formal review processes, maintaining comprehensive audit trails, conducting regular system validation, establishing clear escalation protocols, and ensuring transparency in decision logic. Organizations must document both the algorithm's decision process and the human oversight mechanism.",
            "confidence": 0.87,
            "beliefs": [
                {"id": "c1", "content": "Comprehensive audit trails must track both algorithmic and human decisions", "confidence": 0.92, "type": "compliance"},
                {"id": "c2", "content": "Regular validation exercises should test the human-algorithm interaction", "confidence": 0.88, "type": "compliance"},
                {"id": "c3", "content": "Clear escalation protocols must exist for edge cases", "confidence": 0.91, "type": "compliance"}
            ]
        }
    }
    
    # Create a synthesis
    synthesis = {
        "content": "Balancing algorithmic decision-making with human oversight in critical infrastructure requires a multi-faceted approach tailored to sector-specific needs, regulatory requirements, and risk profiles. Effective models include human-on-the-loop systems (where algorithms recommend but humans decide) and human-in-the-loop systems (where specific conditions trigger human intervention). Regulatory frameworks increasingly mandate explainability, documented decision criteria, and clear responsibility chains. Best practices include comprehensive audit trails tracking both algorithmic and human decisions, regular validation exercises, clear escalation protocols, and formalized review processes. The optimal balance leverages algorithmic efficiency for data processing while preserving human judgment for novel situations, ethical considerations, and accountability.",
        "key_beliefs": [
            {"id": "syn1", "content": "The optimal human-algorithm balance varies by sector, risk profile, and regulatory context", "confidence": 0.91, "type": "synthesis"},
            {"id": "syn2", "content": "Audit trails, validation exercises, and escalation protocols are essential compliance measures", "confidence": 0.89, "type": "synthesis"},
            {"id": "syn3", "content": "Effective systems leverage algorithmic efficiency while preserving human judgment for novel situations", "confidence": 0.90, "type": "synthesis"}
        ]
    }
    
    # Create goals for Layer 7+
    goals = [
        {"id": "g1", "content": "Determine optimal human-algorithm balance models for critical infrastructure", "probability": 0.88, "depth": 0},
        {"id": "g2", "content": "Identify regulatory requirements for human oversight in algorithmic systems", "probability": 0.92, "depth": 1},
        {"id": "g3", "content": "Evaluate compliance best practices for human-algorithm balance", "probability": 0.85, "depth": 1},
        {"id": "g4", "content": "Analyze sector-specific differences in human oversight requirements", "probability": 0.87, "depth": 1}
    ]
    
    # Create Quantum Trust Fidelity results (as if from Layer 8)
    quantum_trust_fidelity = 0.96
    
    # Create the full context
    context = {
        "simulation_id": f"SIM_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "query": query,
        "persona_results": persona_results,
        "synthesis": synthesis,
        "goals": goals,
        "confidence_score": confidence,
        "entropy": entropy,
        "complexity": complexity,
        "simulation_pass": 1,
        "historical_confidence": [0.82, 0.85, confidence],
        
        # Add Layer 7 metrics
        "emergence_score": 0.22,
        "convergence": {
            "converged": True,
            "score": 0.89,
            "reasons": [
                "Strong agreement across expert roles",
                "Sufficient goal convergence score (0.89) exceeding threshold (0.75)",
                "Low entropy in belief relations"
            ]
        },
        
        # Add Layer 8 metrics
        "quantum_trust_fidelity": quantum_trust_fidelity,
        "quantum_processing_applied": True,
        "quantum_insights": [
            "Quantum simulation confirms with 92% probability: Human oversight is essential for handling edge cases and novel situations",
            "Quantum analysis suggests with 88% confidence: Different sectors require different balances of algorithmic and human control",
            "Regulatory assessment verified with 94% probability: Explainable AI is becoming a regulatory requirement for critical systems"
        ],
        "quantum_summary": "The Layer 8 Simulated Quantum Computer has processed belief states through superposition and entanglement simulation, achieving coherent state resolution across multiple goal vectors with high quantum trust fidelity."
    }
    
    return context

def run_recursive_processing(recursive_engine, context):
    """Run the recursive processing with the provided context"""
    logger.info("Running Layer 9 Recursive AGI processing...")
    
    # Process through Layer 9
    start_time = time.time()
    layer9_context = recursive_engine.process(context)
    end_time = time.time()
    
    processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
    layer9_context['processing_time_ms'] = processing_time
    
    logger.info(f"Layer 9 Recursive AGI processing completed in {processing_time:.2f}ms")
    logger.info(f"Recursive Confidence Score: {layer9_context.get('recursive_confidence_score', 0.0):.4f}")
    logger.info(f"Recursive Passes: {layer9_context.get('recursive_passes', 0)}")
    
    return layer9_context

def run_self_awareness(awareness_engine, layer9_context):
    """Run the self-awareness processing with the Layer 9 processed context"""
    logger.info("Running Layer 10 Self-Awareness processing...")
    
    # Process through Layer 10
    start_time = time.time()
    layer10_context = awareness_engine.process(layer9_context)
    end_time = time.time()
    
    processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
    layer10_context['processing_time_ms'] = processing_time
    
    logger.info(f"Layer 10 Self-Awareness processing completed in {processing_time:.2f}ms")
    logger.info(f"Identity Consistency Score: {layer10_context.get('identity_consistency_score', 0.0):.4f}")
    
    return layer10_context

def print_layer9_results(layer9_context, verbose=False):
    """Print Layer 9 Recursive AGI processing results"""
    print("\n" + "="*80)
    print("🔁 LAYER 9 RECURSIVE AGI CORE RESULTS")
    print("="*80)
    
    # Print basic metrics
    print(f"\n📊 RECURSIVE METRICS:")
    print(f"  Recursive Confidence Score: {layer9_context.get('recursive_confidence_score', 0.0):.4f}")
    print(f"  Recursive Passes: {layer9_context.get('recursive_passes', 0)}")
    print(f"  Memory Alignment Score: {layer9_context.get('memory_alignment_score', 0.0):.4f}")
    print(f"  Processing Time: {layer9_context.get('processing_time_ms', 0.0):.2f}ms")
    
    # Print injected roles
    injected_roles = layer9_context.get('injected_roles', [])
    if injected_roles:
        print(f"\n👥 INJECTED EXPERT ROLES:")
        for role in injected_roles:
            print(f"  - {role.get('role', 'unknown')} (from {role.get('axis', 'unknown')})")
    
    # Print recursive summary
    print("\n📝 RECURSIVE PROCESSING SUMMARY:")
    recursive_summary = layer9_context.get('recursive_summary', "No summary available")
    print(f"{recursive_summary}")
    
    # Print detailed outputs if verbose
    if verbose:
        print("\n🔍 DETAILED RECURSIVE OUTPUTS:")
        
        # Show memory alignments
        memory_alignments = layer9_context.get('memory_alignments', [])
        if memory_alignments:
            print("\n  Memory Alignments:")
            for i, alignment in enumerate(memory_alignments[:3]):  # Show top 3 alignments
                print(f"    - Pass {alignment.get('pass_number', '?')}: "
                      f"MAS={alignment.get('mas', 0.0):.4f}, "
                      f"Contradictions: {alignment.get('contradictions_found', 0)}")
        
        # Show confidence history
        confidence_history = layer9_context.get('confidence_history', [])
        if confidence_history:
            print("\n  Confidence Progression:")
            for i, entry in enumerate(confidence_history[:5]):  # Show top 5 entries
                print(f"    - Pass {entry.get('pass_number', '?')}: "
                      f"{entry.get('original', 0.0):.4f} → {entry.get('updated', 0.0):.4f} "
                      f"(adj: {entry.get('adjustment', 0.0):.4f})")

def print_layer10_results(layer10_context, verbose=False):
    """Print Layer 10 Self-Awareness processing results"""
    print("\n" + "="*80)
    print("🧠 LAYER 10 SELF-AWARENESS ENGINE RESULTS")
    print("="*80)
    
    # Print basic metrics
    print(f"\n📊 SELF-AWARENESS METRICS:")
    print(f"  Identity Consistency Score: {layer10_context.get('identity_consistency_score', 0.0):.4f}")
    print(f"  Belief Decay Average: {layer10_context.get('belief_decay_avg', 0.0):.4f}")
    print(f"  Emergence Score: {layer10_context.get('emergence_score', 0.0):.4f}")
    print(f"  Metacognitive Energy Limit: {layer10_context.get('metacognitive_energy_limit', 0.0):.4f}")
    print(f"  Processing Time: {layer10_context.get('processing_time_ms', 0.0):.2f}ms")
    
    # Print containment status
    containment_needed = layer10_context.get('containment_needed', False)
    containment_action = layer10_context.get('containment_action', 'none')
    if containment_needed:
        print(f"\n⚠️ CONTAINMENT STATUS: ACTIVE - {containment_action.upper()}")
        
        # Print containment triggers
        containment_triggers = layer10_context.get('containment_triggers', {})
        print("  Containment Triggers:")
        for trigger, active in containment_triggers.items():
            if active:
                print(f"    - {trigger}: TRIGGERED")
    else:
        print(f"\n✅ CONTAINMENT STATUS: INACTIVE")
    
    # Print self-awareness summary
    print("\n📝 SELF-AWARENESS SUMMARY:")
    self_awareness_summary = layer10_context.get('self_awareness_summary', "No summary available")
    print(f"{self_awareness_summary}")
    
    # Print detailed outputs if verbose
    if verbose:
        print("\n🔍 DETAILED SELF-AWARENESS OUTPUTS:")
        
        # Show memory anchors
        shared_anchors = layer10_context.get('shared_memory_anchors', 0)
        total_anchors = layer10_context.get('total_memory_anchors', 0)
        print(f"\n  Memory Anchors: {shared_anchors} shared out of {total_anchors} total")
        
        # Show emergence indicators
        emergence_indicators = layer10_context.get('emergence_indicators', {})
        if emergence_indicators:
            print("\n  Emergence Indicators:")
            for indicator, present in emergence_indicators.items():
                print(f"    - {indicator}: {'PRESENT' if present else 'ABSENT'}")

def print_final_conclusion(layer9_context, layer10_context):
    """Print a final conclusion summarizing Layers 9-10 integration"""
    print("\n" + "="*80)
    print("🌟 LAYERS 9-10 INTEGRATED CONCLUSION")
    print("="*80)
    
    # Extract key metrics
    rcs = layer9_context.get('recursive_confidence_score', 0.0)
    recursive_passes = layer9_context.get('recursive_passes', 0)
    ics = layer10_context.get('identity_consistency_score', 0.0)
    emergence_score = layer10_context.get('emergence_score', 0.0)
    containment_needed = layer10_context.get('containment_needed', False)
    
    print(f"\n🔍 SYSTEM INTEGRITY ASSESSMENT:")
    print(f"  Recursive processing completed with {recursive_passes} passes")
    print(f"  Final recursive confidence: {rcs:.4f}")
    print(f"  Identity consistency: {ics:.4f}")
    print(f"  Emergence potential: {emergence_score:.4f}")
    print(f"  System status: {'⚠️ CONTAINMENT ACTIVE' if containment_needed else '✅ STABLE'}")
    
    print("\n🧩 INTEGRATED INSIGHTS:")
    print("  From Layer 9 (Recursive AGI Core):")
    print(f"   - Multiple expert perspectives integrated across {recursive_passes} recursive passes")
    print(f"   - Cross-domain knowledge alignment achieved with MAS: {layer9_context.get('memory_alignment_score', 0.0):.4f}")
    print(f"   - Temporal reasoning expanded to account for dynamic factors")
    
    print("\n  From Layer 10 (Self-Awareness Engine):")
    print(f"   - System identity maintained with ICS: {ics:.4f}")
    print(f"   - Belief decay monitored to ensure relevance of knowledge")
    print(f"   - Metacognitive bounds enforced to prevent instability")
    
    # Final conclusion
    print("\n🎯 FINAL SYNTHESIS:")
    print("  Layers 9 and 10 represent the highest cognitive functions of the UKG system,")
    print("  enabling recursive reasoning across multiple domains while maintaining system")
    print("  integrity and preventing emergent behaviors that could lead to instability.")
    print("  Together, they provide the self-monitoring, identity persistence, and recursive")
    print("  planning capabilities needed for reliable advanced reasoning in complex domains.")

def main():
    """Main function to run the demo"""
    args = parse_arguments()
    
    # Setup logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("\n" + "="*80)
    print("🌟 UKG LAYERS 9-10 DEMO (RECURSIVE AGI & SELF-AWARENESS)")
    print("="*80)
    print("\nThis demo showcases the final two layers of the Universal Knowledge Graph:")
    print("Layer 9 (Recursive AGI Core) and Layer 10 (Self-Awareness Engine),")
    print("demonstrating recursive processing, identity tracking, and self-monitoring.\n")
    
    # Setup demo environment
    try:
        system_manager, gatekeeper, agi_engine, quantum_engine, recursive_engine, awareness_engine = setup_demo_environment()
    except Exception as e:
        logger.error(f"Error setting up demo environment: {e}")
        sys.exit(1)
    
    print("Step 1: Creating a test context for Layer 9-10 processing...")
    print("This represents the output from Layers 1-8, ready for recursive processing")
    print("and self-awareness monitoring.\n")
    
    # Create test context
    context = create_test_context()
    
    print("Step 2: Processing through Layer 9 (Recursive AGI Core)...")
    print("This will demonstrate recursive processing, memory alignment, and")
    print("multi-pass confidence improvement.\n")
    
    # Run recursive processing (Layer 9)
    try:
        layer9_context = run_recursive_processing(recursive_engine, context)
    except Exception as e:
        logger.error(f"Error running recursive processing: {e}")
        sys.exit(1)
    
    # Print Layer 9 results
    print_layer9_results(layer9_context, verbose=args.verbose)
    
    print("\nStep 3: Processing through Layer 10 (Self-Awareness Engine)...")
    print("This will demonstrate belief decay monitoring, identity consistency")
    print("tracking, and emergence detection.\n")
    
    # Run self-awareness processing (Layer 10)
    try:
        layer10_context = run_self_awareness(awareness_engine, layer9_context)
    except Exception as e:
        logger.error(f"Error running self-awareness processing: {e}")
        sys.exit(1)
    
    # Print Layer 10 results
    print_layer10_results(layer10_context, verbose=args.verbose)
    
    # Print combined conclusion
    print_final_conclusion(layer9_context, layer10_context)
    
    print("\nDemo completed successfully!")

if __name__ == "__main__":
    main()
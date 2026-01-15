"""
Verification Script: TruthCore v2.0 Intelligence Layer
Tests the integrated Persona Consensus (KA-038) and Conflict Resolution (KA-030) pipeline.
"""
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.truth_engine.truth_core.engine import TruthCoreEngine
from knowledge_algorithms.ka_master_controller import KAMasterController

# Mock requirements for TruthCore
class MockAxisSystem:
    def resolve_multi_axis_context(self, data):
        return {"pillar": 1.0, "sector": 2.0}

def test_consensus_pipeline():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Verification")
    
    # 1. Setup Engine
    ka_controller = KAMasterController()
    engine = TruthCoreEngine(
        ka_controller=ka_controller,
        axis_system=MockAxisSystem()
    )
    
    # 2. Simulate High-Stakes Query
    query = "Analyze the regulatory impact of decentralizing trust scoring in the healthcare sector."
    context = {"force_tier": "high_stakes"}
    
    logger.info(f"Starting test for query: {query}")
    session = engine.create_session(query, context=context)
    
    # 3. Process
    session = engine.process(session['session_id'])
    
    # 4. Verify Steps
    steps = [s['step'] for s in session.get('workflow_steps', [])]
    logger.info(f"Executed Steps: {steps}")
    
    # Check if our new v2.0 steps were executed
    v2_steps_found = [s for s in ['consensus_evaluation', 'conflict_resolution'] if s in steps]
    logger.info(f"Found v2.0 Intelligence Layer Steps: {v2_steps_found}")
    
    assert 'multi_persona_reasoning' in steps or 'KA-012' in str(steps)
    assert 'consensus_evaluation' in steps
    assert 'conflict_resolution' in steps
    
    # 5. Check Outputs
    for step_res in session.get('workflow_steps', []):
        if step_res['step'] == 'consensus_evaluation':
            logger.info("Consensus Evaluation Result Found")
            output = step_res['output']
            assert output.get('success') is True
            assert 'consensus_results' in output
            
        if step_res['step'] == 'conflict_resolution':
            logger.info("Conflict Resolution Result Found")
            output = step_res['output']
            assert output.get('success') is True
            assert 'resolved_findings' in output

    logger.info("Verification PASSED: Consensus and Conflict Resolution pipeline successfully integrated.")

if __name__ == "__main__":
    try:
        test_consensus_pipeline()
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

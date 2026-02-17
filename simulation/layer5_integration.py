"""
Layer 5 Integration Engine

This module provides the Layer 5 Integration Engine for the UKG/USKD multi-layer simulation engine.
It now uses a Multi-Agent System (MAS) orchestrated by LangGraph, implementing the "Gatekeeper + Quad Persona" architecture.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

# New Implementation Imports
from simulation.layer5_pipeline import build_layer5_graph, Layer5State

class Layer5IntegrationEngine:
    """
    Layer 5 Integration Engine (LangGraph-backed).

    Provides advanced cross-domain knowledge integration, uncertainty reduction,
    and verification capabilities using a multi-agent debate architecture.
    
    Architecture:
        - Orchestrator/Gatekeeper: Controls agent spawning and policy.
        - Personas: Specialized agents (Knowledge, Sector, Regulatory, Compliance).
        - Adjudication: Logic for consensus, veto, and escalation.
        - State Machine: Managed by LangGraph (Gatekeeper -> Personas -> Adjudication -> Loop/End).
    """

    def __init__(self, config=None, system_manager=None):
        """
        Initialize the Layer 5 Integration Engine.
        """
        self.config = config or {}
        self.system_manager = system_manager
        
        # Initialize the LangGraph executable
        self.pipeline = build_layer5_graph()
        
        logging.info(f"[{datetime.now()}] Layer5IntegrationEngine initialized with LangGraph pipeline")

    def process(self, context: Dict, integration_params: Optional[Dict] = None) -> Dict:
        """
        Process context information through Layer 5 (Multi-Agent Consensus).
        
        Args:
            context: Context from lower layers (L1-L4).
            integration_params: Optional parameters to customize integration process.
            
        Returns:
            dict: Processed and integrated results suitable for L6.
        """
        session_id = context.get('session_id', f"L5_{str(uuid.uuid4())[:8]}")
        run_trace_id = f"trace-{uuid.uuid4().hex[:8]}"

        # 1. Map Context to Layer5State
        #    Extract inputs from the unified context object
        
        # Heuristic mapping from flat context to structured L5 Request
        inputs: Layer5State = {
            "run_id": session_id,
            "trace_id": run_trace_id,
            "problem_spec": {
                "task_type": "evaluate", # Default, ideally extracted from L1
                "risk_profile": {
                    "domain_risk": "med", 
                    "safety_class": "internal" # Default to safer baseline
                }
            },
            "coord": self._extract_coordinates(context),
            "context_pack": {
                "budgets": {
                    "time_ms": 5000, 
                    "tokens": 4096, 
                    "max_iterations": self.config.get('verification_cycles', 2)
                },
                "evidence": context.get("evidence_pack", {}).get("items", []) # Try to grab evidence
            },
            "gatekeeper_config": {
                "release_threshold": self.config.get('uncertainty_threshold', 0.92),
                "escalate_threshold": 0.75,
                "complexity_score": context.get("complexity_score", 0.5)
            }
        }
        
        # 2. Execute Graph
        try:
            logging.info(f"Invoking Layer 5 Graph for session {session_id}")
            final_state = self.pipeline.invoke(inputs)
            
            # 3. Map Results back to Unified Context
            result = context.copy()
            
            consensus = final_state.get("consensus", {})
            persona_outputs = final_state.get("persona_outputs", [])
            
            metrics = {
                "confidence_score": consensus.get("confidence_sys", 0.0),
                "integration_quality": 1.0, # Placeholder
                "uncertainty_level": 1.0 - consensus.get("confidence_sys", 0.0)
            }
            
            result.update({
                "layer5_processed": True,
                "layer5_status": consensus.get("status"),
                "layer5_consensus": consensus,
                "layer5_personas": [p.get("persona_type") for p in persona_outputs],
                "layer5_outputs": persona_outputs,
                "confidence_score": metrics["confidence_score"],
                "uncertainty_level": metrics["uncertainty_level"],
                "content": self._synthesize_content(result.get("content", ""), persona_outputs, consensus)
            })
            
            if final_state.get("vetoed"):
                result["layer5_error"] = f"Vetoed: {final_state.get('veto_reason')}"
                result["status"] = "BLOCKED"
                
            return result
            
        except Exception as e:
            error_msg = f"Layer 5 execution failed: {str(e)}"
            logging.error(f"[{datetime.now()}] {error_msg}")
            context['layer5_error'] = error_msg
            return context

    def _extract_coordinates(self, context: Dict) -> Dict:
        """
        Extract and normalize 17-Axis coordinates from L1 context.
        """
        coords = {}
        
        # 1. Try to find explicit 'axis_coords' dictionary from L1
        if "axis_coords" in context:
            return context["axis_coords"]

        # 2. Fallback: Map known keys from L1/Intent to Axes usually found in context
        # Canonical mappings based on L1 output structure
        mapping = {
            "pillar": "a1",
            "sector": "a2", 
            "honeycomb": "a3",
            "branch": "a4",
            "node": "a5",
            "regulatory": "a6", # or a10 depending on definition variation, sticking to doc Group I/II split
            "compliance": "a7",
            # Personas (Group II) often inferred, but if explicit:
            "persona_knowledge": "a8",
            "persona_sector": "a9",
            "persona_regulatory": "a10",
            "persona_compliance": "a11",
            "location": "a12",
            "time": "a13",
            "risk": "a14",
            "cost": "a15",
            "ethics": "a16",
            "adaptation": "a17"
        }

        # Check top-level context and 'intent' sub-dictionary
        sources = [context, context.get("intent", {}), context.get("analysis", {})]
        
        for source in sources:
            if not isinstance(source, dict):
                continue
            for k, v in source.items():
                # Direct match (e.g. 'a1', 'axis_1')
                if k in mapping.values(): 
                    coords[k] = str(v)
                elif k.lower() in mapping:
                    coords[mapping[k.lower()]] = str(v)
                elif k.startswith("axis_"):
                    # Extract number 
                    try:
                        num = k.split('_')[1]
                        coords[f"a{num}"] = str(v)
                    except (IndexError, TypeError):
                        pass

        return coords

    def _synthesize_content(self, original_content: str, persona_outputs: List[Dict], consensus: Dict) -> str:
        """
        Synthesize results into a text summary (Placeholder for L6).
        Currently appends the Consensus Review to the content.
        """
        summary = "\n\n--- Layer 5 Consensus Review ---\n"
        summary += f"Status: {consensus.get('status')} (Confidence: {consensus.get('confidence_sys', 0.0):.2f})\n"
        
        for p in persona_outputs:
            ptype = p.get('persona_type')
            claims = p.get('claims', [])
            summary += f"\n[{ptype}] contributed {len(claims)} verified points."
            
        return original_content + summary

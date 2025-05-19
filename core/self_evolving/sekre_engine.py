import logging
import random
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Set, Tuple
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from core.graph.graph_manager import GraphManager

class SekreEngine:
    """
    Self-Evolving Knowledge Refinement Engine (SEKRE)
    
    This component is responsible for the continuous improvement of the Universal
    Knowledge Graph (UKG) by analyzing patterns, identifying knowledge gaps,
    and proposing ontological refinements to enhance the system's understanding.
    """
    
    def __init__(self, config, graph_manager, memory_manager, united_system_manager, simulation_validator):
        """
        Initialize the SEKRE Engine.
        
        Args:
            config (dict): Configuration dictionary
            graph_manager: Reference to the GraphManager
            memory_manager: Reference to the StructuredMemoryManager
            united_system_manager: Reference to the UnitedSystemManager
            simulation_validator: Reference to the SimulationValidator component
        """
        logging.info(f"[{datetime.now()}] Initializing SEKREngine...")
        self.config = config
        self.gm = graph_manager
        self.smm = memory_manager
        self.usm = united_system_manager
        self.simulation_validator = simulation_validator
        self.proposal_confidence_threshold = self.config.get('proposal_confidence_threshold', 0.975)
        self.sekre_log_entry_type = "sekre_action_log"
        self.ontology_proposal_entry_type = "sekre_ontology_proposal"
        self.low_confidence_query_threshold = self.config.get('low_confidence_query_threshold', 0.90)
        self.sparse_node_neighbor_threshold = self.config.get('sparse_node_neighbor_threshold', 3)
        logging.info(f"[{datetime.now()}] SEKREngine initialized.")
    
    def run_evolution_cycle(self, simulation_context_summary: dict = None):
        """
        Execute a full evolution cycle for the UKG.
        This involves:
        1. Analyzing for knowledge gaps
        2. Generating ontology proposals
        3. Validating proposals through simulation
        4. Integrating validated proposals into the UKG
        
        Args:
            simulation_context_summary (dict, optional): Summary of recent simulation activity
            
        Returns:
            dict: Summary of the evolution cycle
        """
        logging.info(f"[{datetime.now()}] SEKRE: Starting new evolution cycle...")
        
        detected_gaps = self._analyze_for_gaps(simulation_context_summary)
        if not detected_gaps:
            logging.info(f"[{datetime.now()}] SEKRE: No significant knowledge gaps detected for evolution this cycle.")
            self.smm.add_memory_entry(
                session_id="SEKRE_CYCLE", 
                pass_num=0, 
                layer_num=99,
                entry_type=self.sekre_log_entry_type,
                content={"action": "analyze_gaps", "status": "no_gaps_found"},
                confidence=1.0
            )
            return {"status": "no_gaps_found"}
        
        proposals = self._generate_proposals(detected_gaps)
        if not proposals:
            logging.info(f"[{datetime.now()}] SEKRE: No new ontology proposals generated from detected gaps.")
            self.smm.add_memory_entry(
                session_id="SEKRE_CYCLE", 
                pass_num=0, 
                layer_num=99,
                entry_type=self.sekre_log_entry_type,
                content={
                    "action": "generate_proposals", 
                    "status": "no_proposals_generated", 
                    "gap_count": len(detected_gaps)
                },
                confidence=1.0
            )
            return {"status": "no_proposals_generated"}
        
        validated_proposals = []
        for prop_idx, proposal in enumerate(proposals):
            logging.info(f"[{datetime.now()}] SEKRE: Validating proposal {prop_idx+1}/{len(proposals)}: {proposal.get('type')} - {proposal.get('label', 'N/A')}")
            
            validation_result = self._validate_proposal(proposal)
            proposal["validation_metrics"] = validation_result
            
            self.smm.add_memory_entry(
                session_id="SEKRE_CYCLE", 
                pass_num=0, 
                layer_num=99, 
                uid=proposal.get("proposed_uid", f"PROP_{datetime.now().timestamp()}"), 
                entry_type=self.ontology_proposal_entry_type,
                content=proposal, 
                confidence=validation_result["simulated_confidence"]
            )
            
            if validation_result["simulated_confidence"] >= self.proposal_confidence_threshold and validation_result["potential_conflicts"] == 0:
                validated_proposals.append(proposal)
                logging.info(f"[{datetime.now()}] SEKRE: Proposal passed validation ({validation_result['simulated_confidence']:.3f})")
            else:
                logging.info(f"[{datetime.now()}] SEKRE: Proposal failed validation ({validation_result['simulated_confidence']:.3f})")
        
        integrated_count = 0
        for proposal in validated_proposals:
            integration_success = self._integrate_proposal_into_ukg(proposal)
            if integration_success:
                integrated_count += 1
                logging.info(f"[{datetime.now()}] SEKRE: Successfully integrated proposal {proposal.get('label')}")
                
                self.smm.add_memory_entry(
                    session_id="SEKRE_CYCLE", 
                    pass_num=0, 
                    layer_num=99, 
                    uid=f"INTEGRATION_{proposal.get('proposed_uid')}",
                    entry_type=self.sekre_log_entry_type,
                    content={
                        "action": "integrate_proposal",
                        "status": "success",
                        "proposal_uid": proposal.get("proposed_uid"),
                        "proposal_label": proposal.get("label")
                    },
                    confidence=1.0
                )
            else:
                logging.warning(f"[{datetime.now()}] SEKRE: Failed to integrate proposal {proposal.get('label')}")
                
                self.smm.add_memory_entry(
                    session_id="SEKRE_CYCLE", 
                    pass_num=0, 
                    layer_num=99, 
                    uid=f"INTEGRATION_{proposal.get('proposed_uid')}",
                    entry_type=self.sekre_log_entry_type,
                    content={
                        "action": "integrate_proposal",
                        "status": "failed",
                        "proposal_uid": proposal.get("proposed_uid"),
                        "proposal_label": proposal.get("label")
                    },
                    confidence=0.0
                )
        
        summary = {
            "gaps_detected_count": len(detected_gaps),
            "gaps_details": detected_gaps,
            "proposals_generated_count": len(proposals),
            "proposals_validated_successfully_count": len(validated_proposals),
            "proposals_integrated_into_ukg_count": integrated_count
        }
        
        self.smm.add_memory_entry(
            session_id="SEKRE_CYCLE", 
            pass_num=0, 
            layer_num=99,
            entry_type=self.sekre_log_entry_type,
            content={
                "action": "evolution_cycle_summary", 
                "summary": summary
            },
            confidence=1.0
        )
        
        logging.info(f"[{datetime.now()}] SEKRE: Evolution cycle complete. Summary: {summary}")
        return summary
    
    def _analyze_for_gaps(self, simulation_context_summary: dict = None) -> list:
        """
        Analyzes the structured memory and knowledge graph for potential knowledge gaps.
        Identifies areas where knowledge is sparse, inconsistent, or leads to low confidence responses.
        
        Args:
            simulation_context_summary (dict, optional): Summary of recent simulation activity
            
        Returns:
            list: Detected knowledge gaps with details and priority
        """
        gaps_found = []
        logging.info(f"[{datetime.now()}] SEKRE_Gaps: Analyzing for knowledge gaps. Context summary: {simulation_context_summary}")
        
        # 1. Check if the context summary indicates a low confidence session
        if simulation_context_summary and simulation_context_summary.get("final_confidence", 1.0) < self.low_confidence_query_threshold:
            trigger_uid = simulation_context_summary.get("query_topic_uid", f"CONTEXT_TRIGGER_{str(uuid.uuid4())[:8]}")
            gap_detail = f"Persistent low confidence (<{self.low_confidence_query_threshold}) for queries related to UID context '{trigger_uid[:20]}...'."
            
            gaps_found.append({
                "gap_type": "LOW_CONFIDENCE_AREA", 
                "details": gap_detail,
                "triggering_uid_context": trigger_uid,
                "priority": 1  # High priority to fix low confidence areas
            })
            
            logging.info(f"[{datetime.now()}] SEKRE_Gaps: Found LOW_CONFIDENCE_AREA: {gap_detail}")
        
        # 2. Check for sparsely connected Pillar Levels or Nodes
        # This is a simple implementation - in a full system, you'd implement more sophisticated analysis
        for pl_id in range(1, 101):  # Check all 100 Pillar Levels
            pl_original_id = f"PL{pl_id:02d}"
            pl_uid = self.gm.get_pillar_level_uid(pl_original_id)
            
            if pl_uid and self.gm.graph.has_node(pl_uid):
                # Check number of children (sublevels/members) or other connections
                num_children = len(list(self.gm.graph.successors(pl_uid)))
                
                if num_children < self.sparse_node_neighbor_threshold:
                    gap_detail = f"Pillar Level '{pl_original_id}' (UID {pl_uid[:15]}) appears sparsely populated (children: {num_children} < {self.sparse_node_neighbor_threshold})."
                    
                    gaps_found.append({
                        "gap_type": "SPARSE_PILLAR_DEFINITION",
                        "details": gap_detail,
                        "target_uid": pl_uid,
                        "pillar_level": pl_original_id,
                        "priority": 2
                    })
                    
                    logging.info(f"[{datetime.now()}] SEKRE_Gaps: Found SPARSE_PILLAR_DEFINITION: {gap_detail}")
        
        # 3. Check for missing connections between related concepts in the UKG
        # In a full implementation, you would implement more sophisticated analysis here
        
        logging.info(f"[{datetime.now()}] SEKRE_Gaps: Total gaps identified for potential evolution: {len(gaps_found)}")
        return gaps_found
    
    def _generate_proposals(self, gaps: list) -> list:
        """
        Generate ontology proposals based on identified knowledge gaps.
        
        Args:
            gaps (list): List of detected knowledge gaps
            
        Returns:
            list: Generated ontology proposals
        """
        proposals = []
        logging.info(f"[{datetime.now()}] SEKRE_Proposals: Generating ontology proposals for {len(gaps)} gaps...")
        
        for gap in gaps:
            proposal = None
            
            if gap["gap_type"] == "LOW_CONFIDENCE_AREA":
                # Generate proposal to add more context nodes for low confidence areas
                target_context_uid = gap["triggering_uid_context"]
                new_label = f"RefinedContextNode_for_{target_context_uid[:10]}"
                
                # Generate a new UID for the proposal
                # In a full implementation, this would use the UnitedSystemManager
                proposed_uid = f"PROPOSED_{str(uuid.uuid4())}"
                
                proposal = {
                    "type": "ADD_CONTEXT_NODE_AND_LINK", 
                    "label": new_label,
                    "proposed_uid": proposed_uid,
                    "link_to_uids": [target_context_uid],
                    "description": f"Refined context node to enhance understanding around {target_context_uid[:10]}...",
                    "attributes": {
                        "gap_type": gap["gap_type"],
                        "proposal_reason": "Enhance low-confidence area with additional context"
                    }
                }
                
                logging.info(f"[{datetime.now()}] SEKRE_Proposals: Generated proposal to add context node for {target_context_uid[:15]}...")
            
            elif gap["gap_type"] == "SPARSE_PILLAR_DEFINITION":
                # Generate proposal to expand pillar level with additional sub-concepts
                target_uid = gap["target_uid"]
                pillar_level = gap.get("pillar_level", "unknown_PL")
                
                # Generate 1-3 potential sub-concepts
                subconcepts = []
                for i in range(random.randint(1, 3)):
                    subconcept_id = f"{pillar_level}_SUB_{i+1}"
                    subconcept_label = f"Subconcept {i+1} for {pillar_level}"
                    subconcept_desc = f"A refined sub-concept for {pillar_level} to enhance sparse pillar definition"
                    
                    # Generate a new UID for each subconcept
                    subconcept_uid = f"PROPOSED_SUB_{str(uuid.uuid4())}"
                    
                    subconcepts.append({
                        "proposed_uid": subconcept_uid,
                        "original_id": subconcept_id,
                        "label": subconcept_label,
                        "description": subconcept_desc
                    })
                
                proposal = {
                    "type": "EXPAND_PILLAR_LEVEL",
                    "label": f"Expansion for {pillar_level}",
                    "proposed_uid": f"PROPOSED_{str(uuid.uuid4())}",
                    "target_uid": target_uid,
                    "pillar_level": pillar_level,
                    "subconcepts": subconcepts,
                    "attributes": {
                        "gap_type": gap["gap_type"],
                        "proposal_reason": "Expand sparse pillar level with additional structured subconcepts"
                    }
                }
                
                logging.info(f"[{datetime.now()}] SEKRE_Proposals: Generated proposal to expand {pillar_level} with {len(subconcepts)} subconcepts")
                
            # Add the proposal if it was created
            if proposal:
                proposals.append(proposal)
        
        logging.info(f"[{datetime.now()}] SEKRE_Proposals: Generated {len(proposals)} total proposals")
        return proposals
    
    def _validate_proposal(self, proposal: dict) -> dict:
        """
        Validate an ontology proposal by simulating its impact on the UKG.
        
        Args:
            proposal (dict): The ontology proposal to validate
            
        Returns:
            dict: Validation metrics and results
        """
        # In a full implementation, this would use the SimulationValidator component
        # For now, we'll return mock validation results
        
        # Generate a semi-realistic confidence score
        # Proposals for low priority gaps tend to get higher confidence
        base_confidence = 0.9
        random_factor = random.uniform(-0.1, 0.1)
        
        if proposal["attributes"]["gap_type"] == "LOW_CONFIDENCE_AREA":
            # These are high priority, so may have more variance in confidence
            simulated_confidence = base_confidence + random_factor
        else:
            # Less critical gaps tend to be easier to validate
            simulated_confidence = base_confidence + 0.05 + random_factor
        
        # Ensure confidence is in valid range
        simulated_confidence = max(0.7, min(0.99, simulated_confidence))
        
        # Assess complexity and conflicts
        complexity_score = random.uniform(0.1, 0.5)
        potential_conflicts = random.randint(0, 1) if simulated_confidence < 0.92 else 0
        
        validation_result = {
            "proposal_uid": proposal.get("proposed_uid", "unknown"),
            "simulated_confidence": simulated_confidence,
            "integration_complexity_score": complexity_score,
            "potential_conflicts": potential_conflicts
        }
        
        return validation_result
    
    def _integrate_proposal_into_ukg(self, proposal: dict) -> bool:
        """
        Integrate a validated proposal into the UKG.
        
        Args:
            proposal (dict): The validated proposal to integrate
            
        Returns:
            bool: True if integration was successful, False otherwise
        """
        proposal_type = proposal.get("type")
        
        if proposal_type == "ADD_CONTEXT_NODE_AND_LINK":
            try:
                # Create the new context node
                new_node_uid = self.gm.add_node(
                    node_type="ContextRefinementNode",
                    label=proposal.get("label"),
                    description=proposal.get("description"),
                    attributes=proposal.get("attributes")
                )
                
                if not new_node_uid:
                    logging.error(f"[{datetime.now()}] SEKRE_Integration: Failed to create new context node")
                    return False
                
                # Create links to related nodes
                for link_to_uid in proposal.get("link_to_uids", []):
                    if self.gm.graph.has_node(link_to_uid):
                        edge_uid = self.gm.add_edge(
                            source_uid=new_node_uid,
                            target_uid=link_to_uid,
                            edge_type="refines_context_of",
                            label=f"Refines context of {link_to_uid[:10]}",
                            attributes={"created_by": "SEKRE", "proposal_uid": proposal.get("proposed_uid")}
                        )
                        
                        if not edge_uid:
                            logging.warning(f"[{datetime.now()}] SEKRE_Integration: Failed to create edge to {link_to_uid}")
                
                logging.info(f"[{datetime.now()}] SEKRE_Integration: Successfully integrated context node proposal")
                return True
                
            except Exception as e:
                logging.error(f"[{datetime.now()}] SEKRE_Integration: Error integrating context node proposal: {str(e)}")
                return False
                
        elif proposal_type == "EXPAND_PILLAR_LEVEL":
            try:
                target_uid = proposal.get("target_uid")
                pillar_level = proposal.get("pillar_level")
                subconcepts = proposal.get("subconcepts", [])
                
                if not self.gm.graph.has_node(target_uid):
                    logging.error(f"[{datetime.now()}] SEKRE_Integration: Target pillar level {pillar_level} not found")
                    return False
                
                # Create each subconcept and link to pillar level
                for subconcept in subconcepts:
                    subconcept_uid = self.gm.add_node(
                        node_type="PillarSubconceptNode",
                        label=subconcept.get("label"),
                        description=subconcept.get("description"),
                        original_id=subconcept.get("original_id"),
                        attributes={
                            "created_by": "SEKRE",
                            "proposal_uid": proposal.get("proposed_uid"),
                            "parent_pillar_level": pillar_level
                        }
                    )
                    
                    if not subconcept_uid:
                        logging.warning(f"[{datetime.now()}] SEKRE_Integration: Failed to create subconcept {subconcept.get('label')}")
                        continue
                    
                    # Link to parent pillar level
                    edge_uid = self.gm.add_edge(
                        source_uid=target_uid,
                        target_uid=subconcept_uid,
                        edge_type="has_subconcept",
                        label=f"Has subconcept {subconcept.get('label')}",
                        attributes={"created_by": "SEKRE", "proposal_uid": proposal.get("proposed_uid")}
                    )
                    
                    if not edge_uid:
                        logging.warning(f"[{datetime.now()}] SEKRE_Integration: Failed to create edge to subconcept {subconcept_uid}")
                
                logging.info(f"[{datetime.now()}] SEKRE_Integration: Successfully integrated pillar expansion proposal")
                return True
                
            except Exception as e:
                logging.error(f"[{datetime.now()}] SEKRE_Integration: Error integrating pillar expansion proposal: {str(e)}")
                return False
        
        else:
            logging.error(f"[{datetime.now()}] SEKRE_Integration: Unsupported proposal type: {proposal_type}")
            return False
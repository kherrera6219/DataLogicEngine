import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

class RefinementOrchestrator:
    """
    The RefinementOrchestrator (RO) takes the output from the QueryPersonaEngine (QPE)
    and refines it through a 12-step process to produce a coherent, comprehensive answer.
    
    The 12 steps are:
    1. Analysis of QPE Outputs
    2. Initial Synthesis
    3. Gap Identification
    4. Premise Validation
    5. Context Expansion
    6. Logical Flow Enhancement
    7. Evidence Strengthening
    8. Governance Check
    9. Final Synthesis
    10. Answer Quality Evaluation
    11. Final Answer Generation
    12. Meta-Learning
    """
    
    def __init__(self, config, graph_manager, memory_manager, united_system_manager, ka_loader):
        """
        Initialize the RefinementOrchestrator.
        
        Args:
            config (dict): Configuration dictionary
            graph_manager (GraphManager): Reference to the GraphManager
            memory_manager (StructuredMemoryManager): Reference to the StructuredMemoryManager
            united_system_manager (UnitedSystemManager): Reference to the UnitedSystemManager
            ka_loader (KALoader): Reference to the KALoader
        """
        self.config = config
        self.gm = graph_manager
        self.smm = memory_manager
        self.usm = united_system_manager
        self.ka_loader = ka_loader
        
        # Get configuration for Layer 2/RO
        self.ro_config = self.config.get('layer2_qpe_ro', {})
        
        logging.info(f"[{datetime.now()}] RefinementOrchestrator initialized")
    
    def run(self, qpe_output: Dict[str, Any], query_text: str, query_topic_uid: str,
            initial_axis_context_scores: Dict[str, float], active_location_context: List[str],
            session_id: str, pass_num: int) -> Dict[str, Any]:
        """
        Run the 12-step refinement process.
        
        Args:
            qpe_output (dict): Output from QueryPersonaEngine
            query_text (str): The original query text
            query_topic_uid (str): The UID for the query topic
            initial_axis_context_scores (dict): Scores for each axis relevance from Layer 1
            active_location_context (list): List of active location UIDs
            session_id (str): The session ID
            pass_num (int): Current pass number
            
        Returns:
            dict: Results of the refinement process
        """
        logging.info(f"[{datetime.now()}] RO: Starting 12-step refinement process for session {session_id[:8] if session_id else 'N/A'}, pass {pass_num}")
        
        # Validate QPE output
        if qpe_output.get('status') != 'success':
            error_msg = f"Invalid QPE output: {qpe_output.get('error', 'Unknown error')}"
            logging.error(f"[{datetime.now()}] RO: {error_msg}")
            return {
                'status': 'error',
                'error': error_msg
            }
        
        try:
            # Create a RO execution record in memory
            ro_execution_uid = self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=2,
                entry_type='ro_execution',
                content={
                    'query_text': query_text,
                    'query_topic_uid': query_topic_uid,
                    'start_time': datetime.now().isoformat()
                },
                confidence=0.5  # Initial confidence, will be updated
            )
            
            # Initialize refinement state
            refinement_state = {
                'query_text': query_text,
                'query_topic_uid': query_topic_uid,
                'qpe_output': qpe_output,
                'initial_axis_context_scores': initial_axis_context_scores,
                'active_location_context': active_location_context,
                'session_id': session_id,
                'pass_num': pass_num,
                'refinement_steps_log': {},
                'current_draft': "",
                'step_confidence_scores': {},
                'research_needs': []
            }
            
            # Execute the 12 steps
            refinement_state = self._execute_step_1_analysis_of_qpe_outputs(refinement_state)
            refinement_state = self._execute_step_2_initial_synthesis(refinement_state)
            refinement_state = self._execute_step_3_gap_identification(refinement_state)
            refinement_state = self._execute_step_4_premise_validation(refinement_state)
            refinement_state = self._execute_step_5_context_expansion(refinement_state)
            refinement_state = self._execute_step_6_logical_flow_enhancement(refinement_state)
            refinement_state = self._execute_step_7_evidence_strengthening(refinement_state)
            refinement_state = self._execute_step_8_governance_check(refinement_state)
            refinement_state = self._execute_step_9_final_synthesis(refinement_state)
            refinement_state = self._execute_step_10_answer_quality_evaluation(refinement_state)
            refinement_state = self._execute_step_11_final_answer_generation(refinement_state)
            refinement_state = self._execute_step_12_meta_learning(refinement_state)
            
            # Calculate final confidence
            final_confidence = self._calculate_final_confidence(refinement_state)
            
            # Update the RO execution record
            self.smm.update_memory_entry(
                uid=ro_execution_uid,
                updates={
                    'content': {
                        'query_text': query_text,
                        'query_topic_uid': query_topic_uid,
                        'refinement_steps_log': refinement_state['refinement_steps_log'],
                        'final_confidence': final_confidence,
                        'end_time': datetime.now().isoformat()
                    },
                    'confidence': final_confidence
                }
            )
            
            # Prepare final output
            result = {
                'status': 'success',
                'final_confidence': final_confidence,
                'refined_answer_text': refinement_state['current_draft'],
                'refinement_steps_log': refinement_state['refinement_steps_log'],
                'research_needs': refinement_state['research_needs'],
                'final_scoring_factors_from_s11': refinement_state.get('final_scoring_factors', {})
            }
            
            logging.info(f"[{datetime.now()}] RO: Refinement process complete. Final confidence: {final_confidence:.3f}")
            
            return result
        
        except Exception as e:
            error_msg = f"Error in RO: {str(e)}"
            logging.error(f"[{datetime.now()}] RO: {error_msg}", exc_info=True)
            
            return {
                'status': 'error',
                'error': error_msg
            }
    
    def _execute_step_1_analysis_of_qpe_outputs(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 1: Analysis of QPE Outputs.
        
        Analyze the outputs from all personas to identify strengths, weaknesses,
        commonalities, and differences.
        
        Args:
            state (dict): Current refinement state
            
        Returns:
            dict: Updated refinement state
        """
        logging.info(f"[{datetime.now()}] RO_S1: Analyzing QPE outputs")
        
        step_name = "S1_Analysis_of_QPE_Outputs"
        qpe_output = state['qpe_output']
        personas_output = qpe_output.get('personas_output', {})
        
        try:
            # Identify which personas ran successfully
            successful_personas = []
            for persona_type, output in personas_output.items():
                if output.get('status') == 'success':
                    successful_personas.append(persona_type)
            
            if not successful_personas:
                raise ValueError("No successful persona outputs to analyze")
            
            # Extract commonalities and differences
            commonalities = self._identify_commonalities(personas_output)
            differences = self._identify_differences(personas_output)
            
            # Identify the most confident personas
            persona_confidences = []
            for persona_type, output in personas_output.items():
                if output.get('status') == 'success':
                    persona_confidences.append({
                        'persona_type': persona_type,
                        'confidence': output.get('confidence', 0.0)
                    })
            
            persona_confidences.sort(key=lambda x: x['confidence'], reverse=True)
            top_confident_personas = persona_confidences[:2]  # Top 2 most confident personas
            
            # Calculate step confidence
            step_confidence = min(0.9, sum(pc['confidence'] for pc in persona_confidences) / len(persona_confidences) + 0.1)
            
            # Store results in state
            step_output = {
                'successful_personas': successful_personas,
                'commonalities': commonalities,
                'differences': differences,
                'top_confident_personas': top_confident_personas,
                'step_confidence': step_confidence
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = step_confidence
            
            # Log the completion of this step
            self.smm.add_memory_entry(
                session_id=state['session_id'],
                pass_num=state['pass_num'],
                layer_num=2,
                entry_type=f'ro_{step_name.lower()}',
                content=step_output,
                confidence=step_confidence
            )
            
            logging.info(f"[{datetime.now()}] RO_S1: Analysis complete. Confidence: {step_confidence:.3f}")
            
            return state
        
        except Exception as e:
            error_msg = f"Error in Step 1: {str(e)}"
            logging.error(f"[{datetime.now()}] RO_S1: {error_msg}", exc_info=True)
            
            # Store error in state
            step_output = {
                'error': error_msg,
                'step_confidence': 0.3  # Low confidence due to error
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = 0.3
            
            return state
    
    def _execute_step_2_initial_synthesis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 2: Initial Synthesis.
        
        Create an initial draft by synthesizing the outputs from all personas.
        
        Args:
            state (dict): Current refinement state
            
        Returns:
            dict: Updated refinement state
        """
        logging.info(f"[{datetime.now()}] RO_S2: Performing initial synthesis")
        
        step_name = "S2_Initial_Synthesis"
        qpe_output = state['qpe_output']
        personas_output = qpe_output.get('personas_output', {})
        step_1_output = state['refinement_steps_log'].get("S1_Analysis_of_QPE_Outputs", {})
        
        try:
            successful_personas = step_1_output.get('successful_personas', [])
            top_confident_personas = step_1_output.get('top_confident_personas', [])
            
            if not successful_personas:
                raise ValueError("No successful persona outputs for synthesis")
            
            # Prioritize answers from top confident personas
            top_persona_types = [p['persona_type'] for p in top_confident_personas]
            
            # Synthesize a draft from all persona answers
            # In a full implementation, this would use more sophisticated NLP techniques
            draft = "# Synthesized Answer\n\n"
            
            # Add an introduction
            draft += f"## Introduction\n\n"
            draft += f"This response addresses the query: \"{state['query_text']}\"\n\n"
            
            # Add insights from each persona
            draft += f"## Key Insights\n\n"
            
            for persona_type in successful_personas:
                persona_output = personas_output.get(persona_type, {})
                if persona_output.get('status') == 'success':
                    persona_name = persona_output.get('persona_model', {}).get('name', persona_type)
                    draft += f"### From {persona_name} Perspective\n\n"
                    
                    # Extract key points from persona answer
                    # For simplicity, just take the first 200 characters
                    answer_text = persona_output.get('answer', '')
                    key_points = answer_text[:200] + "..." if len(answer_text) > 200 else answer_text
                    draft += f"{key_points}\n\n"
            
            # Calculate step confidence
            # Higher if top confident personas are included
            included_top_personas = sum(1 for p in top_persona_types if p in successful_personas)
            step_confidence = min(0.9, 0.5 + (included_top_personas / max(1, len(top_persona_types))) * 0.4)
            
            # Store results in state
            state['current_draft'] = draft
            
            step_output = {
                'draft_length': len(draft),
                'included_personas': successful_personas,
                'prioritized_personas': top_persona_types,
                'step_confidence': step_confidence
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = step_confidence
            
            # Log the completion of this step
            self.smm.add_memory_entry(
                session_id=state['session_id'],
                pass_num=state['pass_num'],
                layer_num=2,
                entry_type=f'ro_{step_name.lower()}',
                content={
                    **step_output,
                    'draft_preview': draft[:500] + "..." if len(draft) > 500 else draft
                },
                confidence=step_confidence
            )
            
            logging.info(f"[{datetime.now()}] RO_S2: Initial synthesis complete. Draft length: {len(draft)}, Confidence: {step_confidence:.3f}")
            
            return state
        
        except Exception as e:
            error_msg = f"Error in Step 2: {str(e)}"
            logging.error(f"[{datetime.now()}] RO_S2: {error_msg}", exc_info=True)
            
            # Create a minimal draft in case of error
            state['current_draft'] = f"# Response to Query\n\nQuery: {state['query_text']}\n\nA comprehensive answer is being generated."
            
            # Store error in state
            step_output = {
                'error': error_msg,
                'draft_length': len(state['current_draft']),
                'step_confidence': 0.3  # Low confidence due to error
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = 0.3
            
            return state
    
    def _execute_step_3_gap_identification(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 3: Gap Identification.
        
        Identify gaps, missing information, or areas that need clarification in the draft.
        
        Args:
            state (dict): Current refinement state
            
        Returns:
            dict: Updated refinement state
        """
        logging.info(f"[{datetime.now()}] RO_S3: Identifying gaps")
        
        step_name = "S3_Gap_Identification"
        current_draft = state['current_draft']
        
        try:
            # In a full implementation, this would use KAs specialized in identifying gaps
            # For simplicity, use some basic heuristics
            
            # Check for sections that are too short
            sections = current_draft.split('##')
            short_sections = []
            
            for section in sections[1:]:  # Skip the title section
                lines = section.strip().split('\n')
                section_title = lines[0].strip()
                section_content = '\n'.join(lines[1:]).strip()
                
                if len(section_content) < 100:  # Arbitrary threshold
                    short_sections.append(section_title)
            
            # Identify missing persona perspectives
            qpe_output = state['qpe_output']
            personas_output = qpe_output.get('personas_output', {})
            all_personas = list(personas_output.keys())
            
            successful_personas = []
            for persona_type, output in personas_output.items():
                if output.get('status') == 'success':
                    successful_personas.append(persona_type)
            
            missing_personas = [p for p in all_personas if p not in successful_personas]
            
            # Check if specific key terms are missing
            key_query_terms = set(state['query_text'].lower().split())
            draft_terms = set(current_draft.lower().split())
            missing_key_terms = [term for term in key_query_terms if term not in draft_terms and len(term) > 4]
            
            # Identify gaps based on initial axis context scores
            axis_scores = state['initial_axis_context_scores']
            high_relevance_axes = [axis_id for axis_id, score in axis_scores.items() if score > 0.7]
            
            axis_coverage_gaps = []
            for axis_id in high_relevance_axes:
                # Check if the draft mentions this axis
                # This is a simplified check; in a real system, we'd use more sophisticated methods
                if axis_id.lower() not in current_draft.lower():
                    axis_coverage_gaps.append(axis_id)
            
            # Identify need for deeper research
            research_needs = []
            
            if short_sections:
                research_needs.append({
                    'id': f"research_need_{len(research_needs) + 1}",
                    'description': f"More information needed for sections: {', '.join(short_sections)}",
                    'priority': 'high'
                })
            
            if missing_key_terms:
                research_needs.append({
                    'id': f"research_need_{len(research_needs) + 1}",
                    'description': f"Research needed on key terms: {', '.join(missing_key_terms[:5])}",
                    'priority': 'medium'
                })
            
            if axis_coverage_gaps:
                research_needs.append({
                    'id': f"research_need_{len(research_needs) + 1}",
                    'description': f"Coverage needed for high-relevance axes: {', '.join(axis_coverage_gaps)}",
                    'priority': 'high'
                })
            
            # Calculate step confidence
            gap_severity = len(short_sections) + len(missing_key_terms) + len(axis_coverage_gaps)
            step_confidence = max(0.3, min(0.9, 1.0 - (gap_severity / 20)))  # More gaps = lower confidence
            
            # Store results in state
            gaps_identified = {
                'short_sections': short_sections,
                'missing_personas': missing_personas,
                'missing_key_terms': missing_key_terms,
                'axis_coverage_gaps': axis_coverage_gaps
            }
            
            step_output = {
                'gaps_identified_details': gaps_identified,
                'research_needs': research_needs,
                'gap_severity': gap_severity,
                'step_confidence': step_confidence
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = step_confidence
            state['research_needs'] = research_needs
            
            # Log the completion of this step
            self.smm.add_memory_entry(
                session_id=state['session_id'],
                pass_num=state['pass_num'],
                layer_num=2,
                entry_type=f'ro_{step_name.lower()}',
                content=step_output,
                confidence=step_confidence
            )
            
            logging.info(f"[{datetime.now()}] RO_S3: Gap identification complete. Gaps: {gap_severity}, Confidence: {step_confidence:.3f}")
            
            return state
        
        except Exception as e:
            error_msg = f"Error in Step 3: {str(e)}"
            logging.error(f"[{datetime.now()}] RO_S3: {error_msg}", exc_info=True)
            
            # Store error in state
            step_output = {
                'error': error_msg,
                'gaps_identified_details': {'error_gaps': [error_msg]},
                'research_needs': [],
                'step_confidence': 0.3  # Low confidence due to error
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = 0.3
            
            return state
    
    def _execute_step_4_premise_validation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 4: Premise Validation.
        
        Validate the premises and assumptions in the draft against the UKG.
        
        Args:
            state (dict): Current refinement state
            
        Returns:
            dict: Updated refinement state
        """
        logging.info(f"[{datetime.now()}] RO_S4: Validating premises")
        
        step_name = "S4_Premise_Validation"
        current_draft = state['current_draft']
        
        try:
            # In a full implementation, this would validate against the UKG
            # For simplicity, use some basic checks
            
            # Extract statements that seem like premises
            # For simplicity, consider sentences with "is", "are", "should", etc.
            lines = current_draft.split('\n')
            potential_premises = []
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ["is", "are", "should", "must", "always", "never"]):
                    potential_premises.append(line.strip())
            
            # Validate premises
            # In a real system, we would check these against the UKG
            validated_premises = []
            uncertain_premises = []
            
            for premise in potential_premises:
                # Mock validation - in a real system, this would query the UKG
                if len(premise) > 20:  # Arbitrary criterion for this example
                    validation_confidence = 0.7  # Mock confidence
                    validated_premises.append({
                        'text': premise,
                        'validation_confidence': validation_confidence
                    })
                else:
                    uncertain_premises.append(premise)
            
            # Calculate premise validity ratio
            validity_ratio = len(validated_premises) / max(1, len(potential_premises))
            
            # Create list of needed modifications
            modifications_needed = []
            
            if uncertain_premises:
                modifications_needed.append({
                    'type': 'uncertain_premises',
                    'premises': uncertain_premises,
                    'suggestion': 'These statements require additional validation or should be modified to be more precise.'
                })
            
            # Calculate step confidence
            # Higher ratio of validated premises = higher confidence
            step_confidence = 0.4 + validity_ratio * 0.5
            
            # Store results in state
            premise_validation_details = {
                'potential_premises_count': len(potential_premises),
                'validated_premises': validated_premises,
                'uncertain_premises': uncertain_premises,
                'validity_ratio': validity_ratio,
                'modifications_needed': modifications_needed
            }
            
            step_output = {
                'premise_validation_details': premise_validation_details,
                'step_confidence': step_confidence
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = step_confidence
            
            # Log the completion of this step
            self.smm.add_memory_entry(
                session_id=state['session_id'],
                pass_num=state['pass_num'],
                layer_num=2,
                entry_type=f'ro_{step_name.lower()}',
                content=step_output,
                confidence=step_confidence
            )
            
            logging.info(f"[{datetime.now()}] RO_S4: Premise validation complete. Validity ratio: {validity_ratio:.3f}, Confidence: {step_confidence:.3f}")
            
            return state
        
        except Exception as e:
            error_msg = f"Error in Step 4: {str(e)}"
            logging.error(f"[{datetime.now()}] RO_S4: {error_msg}", exc_info=True)
            
            # Store error in state
            step_output = {
                'error': error_msg,
                'premise_validation_details': {'error': error_msg},
                'step_confidence': 0.3  # Low confidence due to error
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = 0.3
            
            return state
    
    def _execute_step_5_context_expansion(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 5: Context Expansion.
        
        Expand the context by incorporating additional relevant information from the UKG.
        
        Args:
            state (dict): Current refinement state
            
        Returns:
            dict: Updated refinement state
        """
        logging.info(f"[{datetime.now()}] RO_S5: Expanding context")
        
        step_name = "S5_Context_Expansion"
        current_draft = state['current_draft']
        active_location_context = state['active_location_context']
        
        try:
            # In a full implementation, this would query the UKG for additional context
            # For simplicity, add some contextual information
            
            context_additions = []
            
            # Add location context if available
            if active_location_context:
                # In a real system, we would get actual location names from the UKG
                location_names = [f"Location_{loc_id[-8:]}" for loc_id in active_location_context]
                
                context_additions.append({
                    'type': 'location_context',
                    'content': f"## Geographical Context\n\nThis information is specifically relevant to the following locations: {', '.join(location_names)}."
                })
            
            # Add axis context based on high-scoring axes
            axis_scores = state['initial_axis_context_scores']
            high_relevance_axes = [axis_id for axis_id, score in axis_scores.items() if score > 0.7]
            
            if high_relevance_axes:
                context_additions.append({
                    'type': 'axis_context',
                    'content': f"## Additional Context\n\nThis information draws on knowledge from the following domains: {', '.join(high_relevance_axes)}."
                })
            
            # Apply contextual additions to the draft
            expanded_draft = current_draft
            
            for addition in context_additions:
                expanded_draft += f"\n\n{addition['content']}"
            
            # Calculate expansion impact
            expansion_size = len(expanded_draft) - len(current_draft)
            expansion_ratio = expansion_size / max(1, len(current_draft))
            
            # Calculate step confidence
            # More additions = higher confidence, but not if excessive
            step_confidence = 0.5 + min(0.4, len(context_additions) * 0.1)
            
            # Store results in state
            state['current_draft'] = expanded_draft
            
            expansion_details = {
                'context_additions': context_additions,
                'expansion_size': expansion_size,
                'expansion_ratio': expansion_ratio
            }
            
            step_output = {
                'context_expansion_details': expansion_details,
                'step_confidence': step_confidence
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = step_confidence
            
            # Log the completion of this step
            self.smm.add_memory_entry(
                session_id=state['session_id'],
                pass_num=state['pass_num'],
                layer_num=2,
                entry_type=f'ro_{step_name.lower()}',
                content={
                    **step_output,
                    'draft_length_before': len(current_draft),
                    'draft_length_after': len(expanded_draft)
                },
                confidence=step_confidence
            )
            
            logging.info(f"[{datetime.now()}] RO_S5: Context expansion complete. Additions: {len(context_additions)}, Confidence: {step_confidence:.3f}")
            
            return state
        
        except Exception as e:
            error_msg = f"Error in Step 5: {str(e)}"
            logging.error(f"[{datetime.now()}] RO_S5: {error_msg}", exc_info=True)
            
            # Store error in state
            step_output = {
                'error': error_msg,
                'context_expansion_details': {'error': error_msg},
                'step_confidence': 0.3  # Low confidence due to error
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = 0.3
            
            return state
    
    def _execute_step_6_logical_flow_enhancement(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 6: Logical Flow Enhancement.
        
        Improve the logical flow and structure of the draft.
        
        Args:
            state (dict): Current refinement state
            
        Returns:
            dict: Updated refinement state
        """
        logging.info(f"[{datetime.now()}] RO_S6: Enhancing logical flow")
        
        step_name = "S6_Logical_Flow_Enhancement"
        current_draft = state['current_draft']
        
        try:
            # In a full implementation, this would use sophisticated NLP techniques
            # For simplicity, perform basic structure enhancements
            
            # Split the draft into sections
            sections = current_draft.split('##')
            title_section = sections[0].strip()
            content_sections = sections[1:]
            
            # Identify section titles
            section_titles = []
            for section in content_sections:
                lines = section.strip().split('\n')
                if lines:
                    section_titles.append(lines[0].strip())
            
            # Reorder sections for better flow
            # For simplicity, put Introduction first, Geographical Context last
            reordered_sections = []
            
            # First add the title section
            reordered_sections.append(title_section)
            
            # Then add the Introduction section if it exists
            intro_index = None
            for i, title in enumerate(section_titles):
                if 'introduction' in title.lower():
                    intro_index = i
                    reordered_sections.append('## ' + content_sections[i])
                    break
            
            # Then add remaining sections except Geographical Context
            geo_index = None
            for i, title in enumerate(section_titles):
                if 'geographical context' in title.lower():
                    geo_index = i
                    continue
                if i != intro_index:
                    reordered_sections.append('## ' + content_sections[i])
            
            # Finally add Geographical Context if it exists
            if geo_index is not None:
                reordered_sections.append('## ' + content_sections[geo_index])
            
            # Add transition phrases between sections
            enhanced_sections = []
            for i, section in enumerate(reordered_sections):
                if i == 0:  # Title section
                    enhanced_sections.append(section)
                elif i == 1:  # First content section
                    enhanced_sections.append(section)
                else:
                    # Add a transition phrase
                    previous_title = section_titles[i-2] if i-2 < len(section_titles) else "Previous Section"
                    current_title = section_titles[i-1] if i-1 < len(section_titles) else "Current Section"
                    
                    transition = f"Having examined {previous_title}, let's now explore {current_title}.\n\n"
                    
                    # Add the transition to the beginning of the section
                    section_lines = section.split('\n')
                    section_lines.insert(1, transition)  # Insert after the section title
                    enhanced_sections.append('\n'.join(section_lines))
            
            # Combine all sections into a cohesive draft
            enhanced_draft = '\n\n'.join(enhanced_sections)
            
            # Add a conclusion if none exists
            if 'conclusion' not in enhanced_draft.lower():
                conclusion = "\n\n## Conclusion\n\nTo summarize the key points discussed above, this response has provided insights on the query based on multiple perspectives and relevant contextual factors."
                enhanced_draft += conclusion
            
            # Calculate enhancement impact
            structure_changes = abs(len(reordered_sections) - len(sections))
            content_change_ratio = abs(len(enhanced_draft) - len(current_draft)) / max(1, len(current_draft))
            
            # Calculate step confidence
            # More structure changes = higher confidence, but not if excessive
            step_confidence = 0.5 + min(0.4, structure_changes * 0.1)
            
            # Store results in state
            state['current_draft'] = enhanced_draft
            
            flow_enhancement_details = {
                'original_structure': section_titles,
                'structure_changes': structure_changes,
                'content_change_ratio': content_change_ratio
            }
            
            step_output = {
                'flow_enhancement_details': flow_enhancement_details,
                'step_confidence': step_confidence
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = step_confidence
            
            # Log the completion of this step
            self.smm.add_memory_entry(
                session_id=state['session_id'],
                pass_num=state['pass_num'],
                layer_num=2,
                entry_type=f'ro_{step_name.lower()}',
                content={
                    **step_output,
                    'draft_length_before': len(current_draft),
                    'draft_length_after': len(enhanced_draft)
                },
                confidence=step_confidence
            )
            
            logging.info(f"[{datetime.now()}] RO_S6: Logical flow enhancement complete. Structure changes: {structure_changes}, Confidence: {step_confidence:.3f}")
            
            return state
        
        except Exception as e:
            error_msg = f"Error in Step 6: {str(e)}"
            logging.error(f"[{datetime.now()}] RO_S6: {error_msg}", exc_info=True)
            
            # Store error in state
            step_output = {
                'error': error_msg,
                'flow_enhancement_details': {'error': error_msg},
                'step_confidence': 0.3  # Low confidence due to error
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = 0.3
            
            return state
    
    def _execute_step_7_evidence_strengthening(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 7: Evidence Strengthening.
        
        Strengthen the evidence supporting the draft by adding citations, references,
        or examples from the UKG.
        
        Args:
            state (dict): Current refinement state
            
        Returns:
            dict: Updated refinement state
        """
        logging.info(f"[{datetime.now()}] RO_S7: Strengthening evidence")
        
        step_name = "S7_Evidence_Strengthening"
        current_draft = state['current_draft']
        
        try:
            # In a full implementation, this would query the UKG for supporting evidence
            # For simplicity, add some mock citations and examples
            
            # Identify statements that need support
            # For simplicity, look for sentences longer than a certain threshold
            lines = current_draft.split('\n')
            statements_needing_support = []
            
            for i, line in enumerate(lines):
                if len(line) > 100 and not line.startswith('#'):  # Long non-heading lines
                    statements_needing_support.append({
                        'line_index': i,
                        'text': line
                    })
            
            # Add evidence to statements
            evidence_additions = []
            modified_lines = lines.copy()
            
            for statement in statements_needing_support:
                # In a real system, this would query the UKG for supporting evidence
                # For simplicity, add a generic citation or example
                
                line_index = statement['line_index']
                original_text = statement['text']
                
                if 'example' not in original_text.lower() and '(' not in original_text:
                    # Add a citation
                    citation = " (Source: UKG Evidence Database, 2023)."
                    modified_lines[line_index] = original_text + citation
                    
                    evidence_additions.append({
                        'type': 'citation',
                        'original_text': original_text,
                        'modified_text': modified_lines[line_index]
                    })
                elif 'example' not in original_text.lower():
                    # Add an example
                    example = "\n\nFor example, in a similar context, this principle has been successfully applied in multiple scenarios."
                    modified_lines[line_index] = original_text + example
                    
                    evidence_additions.append({
                        'type': 'example',
                        'original_text': original_text,
                        'modified_text': modified_lines[line_index]
                    })
            
            # Add a references section
            if evidence_additions:
                modified_lines.append("\n\n## References")
                modified_lines.append("\n1. UKG Evidence Database (2023). Internal knowledge base.")
                modified_lines.append("\n2. Universal Knowledge Graph documentation (2023).")
            
            # Combine modified lines into a strengthened draft
            strengthened_draft = '\n'.join(modified_lines)
            
            # Calculate strengthening impact
            strengthening_ratio = len(evidence_additions) / max(1, len(statements_needing_support))
            
            # Calculate step confidence
            # Higher strengthening ratio = higher confidence
            step_confidence = 0.5 + min(0.4, strengthening_ratio * 0.5)
            
            # Store results in state
            state['current_draft'] = strengthened_draft
            
            evidence_strengthening_details = {
                'statements_needing_support': len(statements_needing_support),
                'evidence_additions': evidence_additions,
                'strengthening_ratio': strengthening_ratio
            }
            
            step_output = {
                'evidence_strengthening_details': evidence_strengthening_details,
                'step_confidence': step_confidence
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = step_confidence
            
            # Log the completion of this step
            self.smm.add_memory_entry(
                session_id=state['session_id'],
                pass_num=state['pass_num'],
                layer_num=2,
                entry_type=f'ro_{step_name.lower()}',
                content={
                    **step_output,
                    'draft_length_before': len(current_draft),
                    'draft_length_after': len(strengthened_draft)
                },
                confidence=step_confidence
            )
            
            logging.info(f"[{datetime.now()}] RO_S7: Evidence strengthening complete. Additions: {len(evidence_additions)}, Confidence: {step_confidence:.3f}")
            
            return state
        
        except Exception as e:
            error_msg = f"Error in Step 7: {str(e)}"
            logging.error(f"[{datetime.now()}] RO_S7: {error_msg}", exc_info=True)
            
            # Store error in state
            step_output = {
                'error': error_msg,
                'evidence_strengthening_details': {'error': error_msg},
                'step_confidence': 0.3  # Low confidence due to error
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = 0.3
            
            return state
    
    def _execute_step_8_governance_check(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 8: Governance Check.
        
        Check the draft for ethical, legal, and operational compliance.
        
        Args:
            state (dict): Current refinement state
            
        Returns:
            dict: Updated refinement state
        """
        logging.info(f"[{datetime.now()}] RO_S8: Performing governance check")
        
        step_name = "S8_Governance_Check"
        current_draft = state['current_draft']
        active_location_context = state['active_location_context']
        
        try:
            # In a full implementation, this would use specialized KAs for governance checks
            # For simplicity, perform basic checks
            
            # Ethics check
            # Look for potentially problematic terms
            ethics_flag_terms = ['classified', 'confidential', 'private', 'restricted', 'illegal', 
                               'unethical', 'harmful', 'dangerous', 'discriminate', 'bias']
            
            ethics_flags = []
            for term in ethics_flag_terms:
                if term in current_draft.lower():
                    ethics_flags.append({
                        'term': term,
                        'context': self._get_term_context(current_draft, term)
                    })
            
            # Legal compliance check
            # In a real system, this would check against regulations relevant to the active location context
            legal_issues = []
            
            if active_location_context:
                # Get applicable regulations for the active locations
                applicable_regulations = self._get_applicable_regulations(active_location_context)
                
                # Check for mentions of regulations without proper context
                for reg in applicable_regulations:
                    if reg['id'] in current_draft:
                        # Check if there's a proper compliance statement
                        if f"compliance with {reg['id']}" not in current_draft.lower():
                            legal_issues.append({
                                'regulation': reg['id'],
                                'issue': f"Mentioned without proper compliance context"
                            })
            
            # Security check
            # Look for security-sensitive terms
            security_flag_terms = ['vulnerability', 'exploit', 'attack', 'hack', 'breach', 'bypass', 'backdoor']
            
            security_flags = []
            for term in security_flag_terms:
                if term in current_draft.lower():
                    security_flags.append({
                        'term': term,
                        'context': self._get_term_context(current_draft, term)
                    })
            
            # Overall governance assessment
            governance_issues = {
                'ethics_flags': ethics_flags,
                'legal_issues': legal_issues,
                'security_flags': security_flags
            }
            
            governance_flags_count = len(ethics_flags) + len(legal_issues) + len(security_flags)
            governance_severity = 'Low' if governance_flags_count == 0 else 'Medium' if governance_flags_count <= 2 else 'High'
            
            # Make governance-related modifications to the draft
            modified_draft = current_draft
            
            if governance_flags_count > 0:
                # Add a disclaimer section
                disclaimer = "\n\n## Compliance Notice\n\n"
                disclaimer += "This information is provided for educational purposes only. "
                
                if ethics_flags:
                    disclaimer += "Some content may touch on sensitive ethical topics. "
                
                if legal_issues:
                    disclaimer += "Consult with legal professionals to ensure compliance with all applicable regulations. "
                
                if security_flags:
                    disclaimer += "Security-related information should be handled responsibly. "
                
                modified_draft += disclaimer
            
            # Calculate step confidence
            # Higher for fewer governance issues
            governance_confidence_factor = max(0.3, 1.0 - (governance_flags_count * 0.1))
            step_confidence = 0.6 * governance_confidence_factor
            
            # Store results in state
            state['current_draft'] = modified_draft
            
            governance_check_details = {
                'ethics_evaluation': {
                    'flags': ethics_flags,
                    'severity': 'Low' if len(ethics_flags) == 0 else 'Medium' if len(ethics_flags) <= 1 else 'High'
                },
                'legal_compliance_review': {
                    'issues': legal_issues,
                    'severity': 'Low' if len(legal_issues) == 0 else 'Medium' if len(legal_issues) <= 1 else 'High'
                },
                'ai_security_review_summary': {
                    'flags': security_flags,
                    'severity': 'Low' if len(security_flags) == 0 else 'Medium' if len(security_flags) <= 1 else 'High'
                },
                'overall_governance_severity': governance_severity
            }
            
            step_output = {
                'governance_check_details': governance_check_details,
                'governance_modifications_made': governance_flags_count > 0,
                'step_confidence': step_confidence
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = step_confidence
            
            # Log the completion of this step
            self.smm.add_memory_entry(
                session_id=state['session_id'],
                pass_num=state['pass_num'],
                layer_num=2,
                entry_type=f'ro_{step_name.lower()}',
                content=step_output,
                confidence=step_confidence
            )
            
            logging.info(f"[{datetime.now()}] RO_S8: Governance check complete. Issues: {governance_flags_count}, Severity: {governance_severity}, Confidence: {step_confidence:.3f}")
            
            return state
        
        except Exception as e:
            error_msg = f"Error in Step 8: {str(e)}"
            logging.error(f"[{datetime.now()}] RO_S8: {error_msg}", exc_info=True)
            
            # Store error in state
            step_output = {
                'error': error_msg,
                'governance_check_details': {'error': error_msg},
                'step_confidence': 0.3  # Low confidence due to error
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = 0.3
            
            return state
    
    def _execute_step_9_final_synthesis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 9: Final Synthesis.
        
        Create a final, coherent synthesis of the draft incorporating all refinements.
        
        Args:
            state (dict): Current refinement state
            
        Returns:
            dict: Updated refinement state
        """
        logging.info(f"[{datetime.now()}] RO_S9: Performing final synthesis")
        
        step_name = "S9_Final_Synthesis"
        current_draft = state['current_draft']
        
        try:
            # In a full implementation, this would use sophisticated NLP techniques
            # For simplicity, perform basic final adjustments
            
            # Check if we have all essential sections
            sections = current_draft.split('##')
            section_titles = []
            
            for section in sections[1:]:  # Skip the title section
                lines = section.strip().split('\n')
                if lines:
                    section_titles.append(lines[0].strip().lower())
            
            # Ensure essential sections exist
            essential_sections = ['introduction', 'key insights', 'conclusion']
            missing_essential_sections = [s for s in essential_sections if not any(s in title for title in section_titles)]
            
            # Add any missing essential sections
            final_draft = current_draft
            
            for missing_section in missing_essential_sections:
                if missing_section == 'introduction':
                    introduction = "\n\n## Introduction\n\n"
                    introduction += f"This response addresses the query: \"{state['query_text']}\". "
                    introduction += "The following sections provide a comprehensive analysis drawing on multiple perspectives."
                    
                    # Add after the title but before other sections
                    final_draft = final_draft.split('\n\n', 1)[0] + introduction + '\n\n' + final_draft.split('\n\n', 1)[1]
                
                elif missing_section == 'key insights':
                    insights = "\n\n## Key Insights\n\n"
                    insights += "The main insights from this analysis include:\n\n"
                    insights += "- Comprehensive understanding of the query context\n"
                    insights += "- Multiple expert perspectives integrated\n"
                    insights += "- Consideration of relevant regulatory and geographical factors"
                    
                    # Add after introduction if it exists
                    if 'introduction' in final_draft.lower():
                        parts = final_draft.split('## Introduction', 1)
                        intro_end = parts[1].split('##', 1)
                        final_draft = parts[0] + '## Introduction' + intro_end[0] + insights + '\n\n##' + intro_end[1]
                    else:
                        # Add after title
                        final_draft = final_draft.split('\n\n', 1)[0] + insights + '\n\n' + final_draft.split('\n\n', 1)[1]
                
                elif missing_section == 'conclusion':
                    conclusion = "\n\n## Conclusion\n\n"
                    conclusion += "To summarize the key points discussed above, this response has provided insights on the query based on multiple perspectives and relevant contextual factors."
                    
                    # Add at the end
                    final_draft += conclusion
            
            # Final polishing
            # Remove redundant newlines
            while '\n\n\n' in final_draft:
                final_draft = final_draft.replace('\n\n\n', '\n\n')
            
            # Check and add section numbering if there are many sections
            if len(section_titles) > 3:
                numbered_draft = final_draft
                section_number = 1
                
                for title in [t for t in section_titles if t != 'conclusion']:
                    # Don't number conclusion
                    if title != 'conclusion':
                        numbered_draft = numbered_draft.replace(f"## {title.title()}", f"## {section_number}. {title.title()}")
                        section_number += 1
                
                final_draft = numbered_draft
            
            # Calculate synthesis impact
            synthesis_change_ratio = abs(len(final_draft) - len(current_draft)) / max(1, len(current_draft))
            
            # Calculate step confidence
            # Some change is good, but not too much
            step_confidence = 0.7
            if synthesis_change_ratio > 0.1:
                step_confidence = 0.6  # Significant changes might indicate issues
            
            # Store results in state
            state['current_draft'] = final_draft
            
            final_synthesis_details = {
                'missing_essential_sections': missing_essential_sections,
                'synthesis_change_ratio': synthesis_change_ratio,
                'final_section_count': len(section_titles) + len(missing_essential_sections)
            }
            
            step_output = {
                'final_synthesis_details': final_synthesis_details,
                'step_confidence': step_confidence
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = step_confidence
            
            # Log the completion of this step
            self.smm.add_memory_entry(
                session_id=state['session_id'],
                pass_num=state['pass_num'],
                layer_num=2,
                entry_type=f'ro_{step_name.lower()}',
                content={
                    **step_output,
                    'draft_length_before': len(current_draft),
                    'draft_length_after': len(final_draft)
                },
                confidence=step_confidence
            )
            
            logging.info(f"[{datetime.now()}] RO_S9: Final synthesis complete. Change ratio: {synthesis_change_ratio:.3f}, Confidence: {step_confidence:.3f}")
            
            return state
        
        except Exception as e:
            error_msg = f"Error in Step 9: {str(e)}"
            logging.error(f"[{datetime.now()}] RO_S9: {error_msg}", exc_info=True)
            
            # Store error in state
            step_output = {
                'error': error_msg,
                'final_synthesis_details': {'error': error_msg},
                'step_confidence': 0.3  # Low confidence due to error
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = 0.3
            
            return state
    
    def _execute_step_10_answer_quality_evaluation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 10: Answer Quality Evaluation.
        
        Evaluate the quality of the final answer based on multiple criteria.
        
        Args:
            state (dict): Current refinement state
            
        Returns:
            dict: Updated refinement state
        """
        logging.info(f"[{datetime.now()}] RO_S10: Evaluating answer quality")
        
        step_name = "S10_Answer_Quality_Evaluation"
        current_draft = state['current_draft']
        
        try:
            # In a full implementation, this would use specialized KAs for evaluation
            # For simplicity, perform basic quality checks
            
            # Calculate scores for different quality dimensions
            
            # 1. Comprehensiveness
            # Based on length, section count, and coverage of query terms
            draft_length = len(current_draft)
            sections = current_draft.split('##')
            section_count = len(sections) - 1  # Subtract 1 for the title section
            
            query_terms = set(term.lower() for term in state['query_text'].split() if len(term) > 3)
            draft_text = current_draft.lower()
            covered_terms = sum(1 for term in query_terms if term in draft_text)
            term_coverage_ratio = covered_terms / max(1, len(query_terms))
            
            comprehensiveness_score = min(1.0, (
                (draft_length / 2000) * 0.4 +
                (min(section_count, 8) / 8) * 0.3 +
                term_coverage_ratio * 0.3
            ))
            
            # 2. Coherence
            # In a real system, this would use more sophisticated analysis
            # For simplicity, use a basic heuristic based on section titles
            section_titles = []
            for section in sections[1:]:
                lines = section.strip().split('\n')
                if lines:
                    section_titles.append(lines[0].strip())
            
            # Check if essential sections are present and in logical order
            essential_sections = ['introduction', 'key insights', 'conclusion']
            essential_present = all(any(s.lower() in title.lower() for title in section_titles) for s in essential_sections)
            
            # Check section ordering
            section_indices = {}
            for s in essential_sections:
                for i, title in enumerate(section_titles):
                    if s.lower() in title.lower():
                        section_indices[s] = i
                        break
            
            correct_order = (
                'introduction' in section_indices and
                'conclusion' in section_indices and
                section_indices['introduction'] < section_indices['conclusion']
            )
            
            coherence_score = (
                (0.5 if essential_present else 0.3) +
                (0.4 if correct_order else 0.1)
            )
            
            # 3. Factual accuracy
            # In a real system, this would validate facts against the UKG
            # For simplicity, use a placeholder score
            factual_accuracy_score = 0.8  # Placeholder
            
            # 4. Relevance
            # Based on term coverage and specificity
            relevance_score = term_coverage_ratio * 0.7 + 0.2  # Base relevance on term coverage
            
            # 5. Clarity
            # In a real system, this would use linguistic analysis
            # For simplicity, use a placeholder score
            clarity_score = 0.75  # Placeholder
            
            # Calculate overall quality score
            quality_scores = {
                'comprehensiveness': comprehensiveness_score,
                'coherence': coherence_score,
                'factual_accuracy': factual_accuracy_score,
                'relevance': relevance_score,
                'clarity': clarity_score
            }
            
            weights = {
                'comprehensiveness': 0.25,
                'coherence': 0.20,
                'factual_accuracy': 0.25,
                'relevance': 0.20,
                'clarity': 0.10
            }
            
            overall_quality_score = sum(score * weights[dimension] for dimension, score in quality_scores.items())
            
            # Identify areas for improvement
            improvement_areas = []
            
            for dimension, score in quality_scores.items():
                if score < 0.7:
                    improvement_areas.append({
                        'dimension': dimension,
                        'score': score,
                        'suggestion': f"Improve {dimension} by addressing gaps and enhancing structure."
                    })
            
            # Calculate step confidence
            # Higher overall quality = higher confidence
            step_confidence = min(0.9, 0.5 + overall_quality_score * 0.4)
            
            # Store results in state
            quality_evaluation_details = {
                'quality_scores': quality_scores,
                'overall_quality_score': overall_quality_score,
                'improvement_areas': improvement_areas
            }
            
            step_output = {
                'quality_evaluation_details': quality_evaluation_details,
                'step_confidence': step_confidence
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = step_confidence
            
            # Log the completion of this step
            self.smm.add_memory_entry(
                session_id=state['session_id'],
                pass_num=state['pass_num'],
                layer_num=2,
                entry_type=f'ro_{step_name.lower()}',
                content=step_output,
                confidence=step_confidence
            )
            
            logging.info(f"[{datetime.now()}] RO_S10: Quality evaluation complete. Overall score: {overall_quality_score:.3f}, Confidence: {step_confidence:.3f}")
            
            return state
        
        except Exception as e:
            error_msg = f"Error in Step 10: {str(e)}"
            logging.error(f"[{datetime.now()}] RO_S10: {error_msg}", exc_info=True)
            
            # Store error in state
            step_output = {
                'error': error_msg,
                'quality_evaluation_details': {'error': error_msg},
                'step_confidence': 0.3  # Low confidence due to error
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = 0.3
            
            return state
    
    def _execute_step_11_final_answer_generation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 11: Final Answer Generation.
        
        Generate the final answer based on all previous refinements.
        
        Args:
            state (dict): Current refinement state
            
        Returns:
            dict: Updated refinement state
        """
        logging.info(f"[{datetime.now()}] RO_S11: Generating final answer")
        
        step_name = "S11_Final_Answer_Generation"
        current_draft = state['current_draft']
        
        try:
            # In a full implementation, this might include additional formatting or adjustments
            # For simplicity, we'll use the current draft as the final answer
            
            final_answer = current_draft
            
            # Add a signature and timestamp
            signature = f"\n\n---\n*This response was generated by the Universal Knowledge Graph (UKG) system at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}.*"
            final_answer += signature
            
            # Calculate final scoring factors
            # Extract quality scores from Step 10
            quality_scores = state['refinement_steps_log'].get("S10_Answer_Quality_Evaluation", {}).get("quality_evaluation_details", {}).get("quality_scores", {})
            
            # Extract governance issues from Step 8
            governance_details = state['refinement_steps_log'].get("S8_Governance_Check", {}).get("governance_check_details", {})
            
            # Extract gaps from Step 3
            gaps_identified = state['refinement_steps_log'].get("S3_Gap_Identification", {}).get("gaps_identified_details", {})
            
            # Combine all factors
            final_scoring_factors = {
                'quality_scores': quality_scores,
                'governance_details': governance_details,
                'gaps_identified_details': gaps_identified,
                'self_critique_summary': state['refinement_steps_log'].get("S10_Answer_Quality_Evaluation", {}).get("quality_evaluation_details", {}).get("improvement_areas", [])
            }
            
            # Calculate confidence factors
            # Average of step confidence scores from key steps
            key_steps = ["S3_Gap_Identification", "S8_Governance_Check", "S10_Answer_Quality_Evaluation"]
            key_step_confidences = [state['step_confidence_scores'].get(step, 0.5) for step in key_steps]
            key_steps_confidence = sum(key_step_confidences) / len(key_step_confidences)
            
            # Get quality score from Step 10
            quality_score = state['refinement_steps_log'].get("S10_Answer_Quality_Evaluation", {}).get("quality_evaluation_details", {}).get("overall_quality_score", 0.7)
            
            # Get governance severity
            governance_severity = governance_details.get("overall_governance_severity", "Low")
            governance_penalty = 0.0 if governance_severity == "Low" else 0.1 if governance_severity == "Medium" else 0.2
            
            # Calculate final confidence
            final_confidence = min(0.95, (key_steps_confidence * 0.4 + quality_score * 0.6) - governance_penalty)
            
            # Store results in state
            state['current_draft'] = final_answer
            state['final_scoring_factors'] = final_scoring_factors
            
            step_output = {
                'final_answer_length': len(final_answer),
                'final_confidence_score': final_confidence,
                'final_scoring_factors': final_scoring_factors,
                'step_confidence': 0.9  # High confidence for this step
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = 0.9
            
            # Log the completion of this step
            self.smm.add_memory_entry(
                session_id=state['session_id'],
                pass_num=state['pass_num'],
                layer_num=2,
                entry_type=f'ro_{step_name.lower()}',
                content={
                    **step_output,
                    'final_answer_preview': final_answer[:500] + "..." if len(final_answer) > 500 else final_answer
                },
                confidence=final_confidence
            )
            
            logging.info(f"[{datetime.now()}] RO_S11: Final answer generation complete. Length: {len(final_answer)}, Confidence: {final_confidence:.3f}")
            
            return state
        
        except Exception as e:
            error_msg = f"Error in Step 11: {str(e)}"
            logging.error(f"[{datetime.now()}] RO_S11: {error_msg}", exc_info=True)
            
            # Store error in state
            step_output = {
                'error': error_msg,
                'final_confidence_score': 0.4,  # Low confidence due to error
                'step_confidence': 0.3
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = 0.3
            
            return state
    
    def _execute_step_12_meta_learning(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 12: Meta-Learning.
        
        Learn from the refinement process to improve future processing.
        
        Args:
            state (dict): Current refinement state
            
        Returns:
            dict: Updated refinement state
        """
        logging.info(f"[{datetime.now()}] RO_S12: Performing meta-learning")
        
        step_name = "S12_Meta_Learning"
        
        try:
            # In a full implementation, this would analyze the entire refinement process
            # For simplicity, identify patterns and log them
            
            # Analyze step confidence scores
            step_confidences = state['step_confidence_scores']
            avg_confidence = sum(step_confidences.values()) / max(1, len(step_confidences))
            min_confidence_step = min(step_confidences.items(), key=lambda x: x[1]) if step_confidences else ('none', 1.0)
            max_confidence_step = max(step_confidences.items(), key=lambda x: x[1]) if step_confidences else ('none', 0.0)
            
            # Identify ineffective steps
            ineffective_steps = [step for step, conf in step_confidences.items() if conf < 0.5]
            
            # Check for error patterns
            error_patterns = []
            for step, output in state['refinement_steps_log'].items():
                if 'error' in output:
                    error_patterns.append({
                        'step': step,
                        'error': output['error']
                    })
            
            # Generate learning insights
            learning_insights = []
            
            if ineffective_steps:
                learning_insights.append({
                    'type': 'ineffective_steps',
                    'steps': ineffective_steps,
                    'recommendation': "Review and improve the implementation of these steps."
                })
            
            if error_patterns:
                learning_insights.append({
                    'type': 'error_patterns',
                    'patterns': error_patterns,
                    'recommendation': "Address recurring errors in these steps."
                })
            
            # Generate process improvement suggestions
            improvement_suggestions = []
            
            if min_confidence_step[1] < 0.5:
                improvement_suggestions.append({
                    'target_step': min_confidence_step[0],
                    'suggestion': f"Improve {min_confidence_step[0]} to increase confidence."
                })
            
            # Calculate step confidence
            # Higher for more insights and suggestions
            insight_count = len(learning_insights) + len(improvement_suggestions)
            step_confidence = min(0.9, 0.5 + insight_count * 0.1)
            
            # Store results in state
            meta_learning_details = {
                'step_confidence_stats': {
                    'average': avg_confidence,
                    'min_step': min_confidence_step[0],
                    'min_confidence': min_confidence_step[1],
                    'max_step': max_confidence_step[0],
                    'max_confidence': max_confidence_step[1]
                },
                'learning_insights': learning_insights,
                'improvement_suggestions': improvement_suggestions
            }
            
            step_output = {
                'meta_learning_details': meta_learning_details,
                'step_confidence': step_confidence
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = step_confidence
            
            # Log the completion of this step
            self.smm.add_memory_entry(
                session_id=state['session_id'],
                pass_num=state['pass_num'],
                layer_num=2,
                entry_type=f'ro_{step_name.lower()}',
                content=step_output,
                confidence=step_confidence
            )
            
            logging.info(f"[{datetime.now()}] RO_S12: Meta-learning complete. Insights: {len(learning_insights)}, Suggestions: {len(improvement_suggestions)}, Confidence: {step_confidence:.3f}")
            
            return state
        
        except Exception as e:
            error_msg = f"Error in Step 12: {str(e)}"
            logging.error(f"[{datetime.now()}] RO_S12: {error_msg}", exc_info=True)
            
            # Store error in state
            step_output = {
                'error': error_msg,
                'meta_learning_details': {'error': error_msg},
                'step_confidence': 0.3  # Low confidence due to error
            }
            
            state['refinement_steps_log'][step_name] = step_output
            state['step_confidence_scores'][step_name] = 0.3
            
            return state
    
    def _calculate_final_confidence(self, state: Dict[str, Any]) -> float:
        """
        Calculate the final confidence score based on all step confidences.
        
        Args:
            state (dict): Current refinement state
            
        Returns:
            float: Final confidence score
        """
        # Use the confidence score from Step 11 if available
        if "S11_Final_Answer_Generation" in state['refinement_steps_log']:
            final_confidence = state['refinement_steps_log']["S11_Final_Answer_Generation"].get('final_confidence_score', 0.7)
        else:
            # Otherwise, calculate a weighted average of step confidences
            step_confidences = state['step_confidence_scores']
            
            # Define weights for each step
            step_weights = {
                "S1_Analysis_of_QPE_Outputs": 0.05,
                "S2_Initial_Synthesis": 0.05,
                "S3_Gap_Identification": 0.1,
                "S4_Premise_Validation": 0.1,
                "S5_Context_Expansion": 0.05,
                "S6_Logical_Flow_Enhancement": 0.05,
                "S7_Evidence_Strengthening": 0.1,
                "S8_Governance_Check": 0.1,
                "S9_Final_Synthesis": 0.1,
                "S10_Answer_Quality_Evaluation": 0.2,
                "S11_Final_Answer_Generation": 0.1,
                "S12_Meta_Learning": 0.0  # Meta-learning doesn't affect confidence
            }
            
            # Calculate weighted average
            weighted_sum = 0.0
            total_weight = 0.0
            
            for step, confidence in step_confidences.items():
                weight = step_weights.get(step, 0.0)
                weighted_sum += confidence * weight
                total_weight += weight
            
            # Ensure we don't divide by zero
            final_confidence = weighted_sum / max(0.001, total_weight)
        
        # Ensure the final confidence is between 0 and 1
        return max(0.0, min(0.95, final_confidence))
    
    def _identify_commonalities(self, personas_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify commonalities across persona outputs.
        
        Args:
            personas_output (dict): Outputs from all personas
            
        Returns:
            list: Identified commonalities
        """
        # In a full implementation, this would use NLP to identify common themes
        # For simplicity, return a placeholder
        return [{
            'type': 'shared_perspective',
            'description': 'All personas provided comprehensive analysis'
        }]
    
    def _identify_differences(self, personas_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify differences across persona outputs.
        
        Args:
            personas_output (dict): Outputs from all personas
            
        Returns:
            list: Identified differences
        """
        # In a full implementation, this would use NLP to identify differing viewpoints
        # For simplicity, return a placeholder
        differences = []
        
        for persona_type, output in personas_output.items():
            if output.get('status') == 'success':
                differences.append({
                    'persona': persona_type,
                    'unique_focus': output.get('persona_model', {}).get('knowledge_focus', 'unknown')
                })
        
        return differences
    
    def _get_term_context(self, text: str, term: str) -> str:
        """
        Get the context around a term in the text.
        
        Args:
            text (str): The text to search
            term (str): The term to find
            
        Returns:
            str: Context around the term
        """
        term_index = text.lower().find(term.lower())
        if term_index == -1:
            return ""
        
        # Get 50 characters before and after the term
        start = max(0, term_index - 50)
        end = min(len(text), term_index + len(term) + 50)
        
        return text[start:end]
    
    def _get_applicable_regulations(self, location_uids: List[str]) -> List[Dict[str, str]]:
        """
        Get regulations applicable to the given locations.
        
        Args:
            location_uids (list): List of location UIDs
            
        Returns:
            list: Applicable regulations
        """
        # In a full implementation, this would query the UKG
        # For simplicity, return a placeholder
        return [
            {'id': 'GDPR', 'name': 'General Data Protection Regulation'},
            {'id': 'CCPA', 'name': 'California Consumer Privacy Act'}
        ]

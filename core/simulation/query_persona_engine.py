import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

class QueryPersonaEngine:
    """
    The QueryPersonaEngine (QPE) processes queries through four distinct personas:
    - Knowledge Expert (KE): Focuses on factual knowledge and domain expertise
    - Skill Expert (SE): Focuses on practical skills and how-to knowledge
    - Role Expert (RE): Focuses on job roles, responsibilities, and workflows
    - Context Expert (CE): Focuses on situational context and adaptability
    
    Each persona analyzes the query from their unique perspective, generating insights
    that will be combined and refined by the RefinementOrchestrator.
    """
    
    def __init__(self, config, graph_manager, memory_manager, united_system_manager, ka_loader):
        """
        Initialize the QueryPersonaEngine.
        
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
        
        # Get configuration for Layer 2/QPE
        self.qpe_config = self.config.get('layer2_qpe_ro', {})
        self.enabled_personas = self.qpe_config.get('personas', ['KE', 'SE', 'RE', 'CE'])
        
        logging.info(f"[{datetime.now()}] QueryPersonaEngine initialized with personas: {', '.join(self.enabled_personas)}")
    
    def run(self, query_text: str, query_topic_uid: str, initial_axis_context_scores: Dict[str, float],
            active_location_context: List[str], session_id: str, pass_num: int) -> Dict[str, Any]:
        """
        Run the query through all enabled personas.
        
        Args:
            query_text (str): The original query text
            query_topic_uid (str): The UID for the query topic
            initial_axis_context_scores (dict): Scores for each axis relevance from Layer 1
            active_location_context (list): List of active location UIDs
            session_id (str): The session ID
            pass_num (int): Current pass number
            
        Returns:
            dict: Results from all personas
        """
        logging.info(f"[{datetime.now()}] QPE: Processing query through {len(self.enabled_personas)} personas for session {session_id[:8] if session_id else 'N/A'}, pass {pass_num}")
        
        try:
            # Process through each enabled persona
            persona_outputs = {}
            overall_confidence = 0.0
            personas_run = 0
            
            # Create a QPE execution record in memory
            qpe_execution_uid = self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=2,
                entry_type='qpe_execution',
                content={
                    'query_text': query_text,
                    'query_topic_uid': query_topic_uid,
                    'enabled_personas': self.enabled_personas,
                    'start_time': datetime.now().isoformat()
                },
                confidence=0.5  # Initial confidence, will be updated
            )
            
            # Run each persona
            for persona_type in self.enabled_personas:
                persona_result = self._run_persona(
                    persona_type=persona_type,
                    query_text=query_text,
                    query_topic_uid=query_topic_uid,
                    initial_axis_context_scores=initial_axis_context_scores,
                    active_location_context=active_location_context,
                    session_id=session_id,
                    pass_num=pass_num
                )
                
                persona_outputs[persona_type] = persona_result
                
                if persona_result.get('status') == 'success':
                    overall_confidence += persona_result.get('confidence', 0.0)
                    personas_run += 1
            
            # Calculate average confidence if any personas ran successfully
            if personas_run > 0:
                overall_confidence /= personas_run
            
            # Update the QPE execution record
            self.smm.update_memory_entry(
                uid=qpe_execution_uid,
                updates={
                    'content': {
                        'query_text': query_text,
                        'query_topic_uid': query_topic_uid,
                        'enabled_personas': self.enabled_personas,
                        'persona_outputs': persona_outputs,
                        'overall_confidence': overall_confidence,
                        'end_time': datetime.now().isoformat()
                    },
                    'confidence': overall_confidence
                }
            )
            
            # Prepare final output
            result = {
                'status': 'success',
                'personas_output': persona_outputs,
                'overall_confidence': overall_confidence,
                'query_topic_uid': query_topic_uid
            }
            
            logging.info(f"[{datetime.now()}] QPE: Processing complete. Overall confidence: {overall_confidence:.3f}")
            
            return result
        
        except Exception as e:
            error_msg = f"Error in QPE: {str(e)}"
            logging.error(f"[{datetime.now()}] QPE: {error_msg}", exc_info=True)
            
            return {
                'status': 'error',
                'error': error_msg
            }
    
    def _run_persona(self, persona_type: str, query_text: str, query_topic_uid: str,
                   initial_axis_context_scores: Dict[str, float], active_location_context: List[str],
                   session_id: str, pass_num: int) -> Dict[str, Any]:
        """
        Run a specific persona on the query.
        
        Args:
            persona_type (str): The persona type ('KE', 'SE', 'RE', or 'CE')
            query_text (str): The original query text
            query_topic_uid (str): The UID for the query topic
            initial_axis_context_scores (dict): Scores for each axis relevance from Layer 1
            active_location_context (list): List of active location UIDs
            session_id (str): The session ID
            pass_num (int): Current pass number
            
        Returns:
            dict: Results from the persona
        """
        logging.info(f"[{datetime.now()}] QPE: Running {persona_type} persona")
        
        try:
            # Map persona types to axis numbers
            persona_axis_map = {
                'KE': 8,  # Knowledge Expert (Axis 8)
                'SE': 9,  # Skill Expert (Axis 9)
                'RE': 10, # Role Expert (Axis 10)
                'CE': 11  # Context Expert (Axis 11)
            }
            
            if persona_type not in persona_axis_map:
                return {
                    'status': 'error',
                    'error': f"Unknown persona type: {persona_type}",
                    'confidence': 0.0
                }
            
            # Get the axis number for this persona
            axis_number = persona_axis_map[persona_type]
            
            # Retrieve persona templates from UKG
            # In a full implementation, this would query the UKG to find the most relevant personas
            # For simplicity, we'll use a default persona model for each type
            persona_model = self._get_persona_model(persona_type)
            
            if not persona_model:
                return {
                    'status': 'error',
                    'error': f"Failed to retrieve persona model for {persona_type}",
                    'confidence': 0.0
                }
            
            # Step 1: Initial query analysis - run KA specific to this persona type
            # This would be implemented in a real system with specialized KAs for each persona
            # For now, we'll use a mock analysis
            
            persona_ka_id = {
                'KE': 3,  # KA03 for Knowledge Expert (not implemented in this example)
                'SE': 4,  # KA04 for Skill Expert (not implemented in this example)
                'RE': 5,  # KA05 for Role Expert (not implemented in this example)
                'CE': 6   # KA06 for Context Expert (not implemented in this example)
            }.get(persona_type, 1)  # Default to KA01 if specific KA not available
            
            # Try to use the specific persona KA if available, otherwise use generic KA01
            try:
                ka_input = {
                    'query_text': query_text,
                    'persona_type': persona_type,
                    'initial_axis_context_scores': initial_axis_context_scores,
                    'active_location_context': active_location_context
                }
                
                ka_result = self.ka_loader.execute_ka(
                    ka_id=persona_ka_id,
                    input_data=ka_input,
                    session_id=session_id,
                    pass_num=pass_num,
                    layer_num=2
                )
                
                if ka_result.get('status') != 'success':
                    # Fall back to using KA01 if the specific KA fails
                    ka_result = self.ka_loader.execute_ka(
                        ka_id=1,
                        input_data={'query_text': query_text},
                        session_id=session_id,
                        pass_num=pass_num,
                        layer_num=2
                    )
            except:
                # Fallback to KA01 if the specific KA doesn't exist
                ka_result = self.ka_loader.execute_ka(
                    ka_id=1,
                    input_data={'query_text': query_text},
                    session_id=session_id,
                    pass_num=pass_num,
                    layer_num=2
                )
            
            # Step 2: Generate persona-specific answer
            answer = self._generate_persona_answer(
                persona_type=persona_type,
                persona_model=persona_model,
                query_text=query_text,
                ka_result=ka_result,
                initial_axis_context_scores=initial_axis_context_scores,
                active_location_context=active_location_context
            )
            
            # Step 3: Calculate confidence
            confidence = self._calculate_persona_confidence(
                persona_type=persona_type,
                ka_result=ka_result,
                answer_length=len(answer),
                initial_axis_context_scores=initial_axis_context_scores
            )
            
            # Create a record of this persona's processing
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=2,
                entry_type=f'qpe_{persona_type.lower()}_output',
                content={
                    'query_text': query_text,
                    'query_topic_uid': query_topic_uid,
                    'ka_result': ka_result,
                    'answer': answer,
                    'confidence': confidence,
                    'persona_model': persona_model
                },
                confidence=confidence
            )
            
            return {
                'status': 'success',
                'persona_type': persona_type,
                'answer': answer,
                'confidence': confidence,
                'ka_result': ka_result,
                'persona_model': persona_model
            }
        
        except Exception as e:
            error_msg = f"Error running {persona_type} persona: {str(e)}"
            logging.error(f"[{datetime.now()}] QPE: {error_msg}", exc_info=True)
            
            return {
                'status': 'error',
                'persona_type': persona_type,
                'error': error_msg,
                'confidence': 0.0
            }
    
    def _get_persona_model(self, persona_type: str) -> Dict[str, Any]:
        """
        Get a persona model from the UKG.
        
        Args:
            persona_type (str): The persona type ('KE', 'SE', 'RE', or 'CE')
            
        Returns:
            dict: The persona model
        """
        # In a full implementation, this would query the UKG to find the most relevant persona model
        # For simplicity, return a default model for each persona type
        
        default_models = {
            'KE': {
                'id': 'KE_DEFAULT',
                'name': 'Knowledge Expert',
                'description': 'Focused on factual knowledge and domain expertise',
                'personality_traits': ['analytical', 'detail-oriented', 'factual'],
                'reasoning_style': 'deductive',
                'knowledge_focus': 'domain expertise',
                'components': [
                    {'name': 'Knowledge Base', 'weight': 0.4},
                    {'name': 'Analytical Methods', 'weight': 0.3},
                    {'name': 'Critical Analysis', 'weight': 0.2},
                    {'name': 'Historical Context', 'weight': 0.1},
                    {'name': 'Factual Accuracy', 'weight': 0.5},
                    {'name': 'Conceptual Framework', 'weight': 0.2},
                    {'name': 'Theoretical Foundations', 'weight': 0.4}
                ]
            },
            'SE': {
                'id': 'SE_DEFAULT',
                'name': 'Skill Expert',
                'description': 'Focused on practical skills and how-to knowledge',
                'personality_traits': ['practical', 'hands-on', 'solution-oriented'],
                'reasoning_style': 'procedural',
                'knowledge_focus': 'practical application',
                'components': [
                    {'name': 'Procedural Knowledge', 'weight': 0.5},
                    {'name': 'Tools & Techniques', 'weight': 0.4},
                    {'name': 'Best Practices', 'weight': 0.3},
                    {'name': 'Practical Experience', 'weight': 0.4},
                    {'name': 'Efficiency Assessment', 'weight': 0.3},
                    {'name': 'Implementation Strategy', 'weight': 0.4},
                    {'name': 'Technical Accuracy', 'weight': 0.5}
                ]
            },
            'RE': {
                'id': 'RE_DEFAULT',
                'name': 'Role Expert',
                'description': 'Focused on job roles, responsibilities, and workflows',
                'personality_traits': ['organized', 'process-oriented', 'collaborative'],
                'reasoning_style': 'systematic',
                'knowledge_focus': 'organizational roles',
                'components': [
                    {'name': 'Role Definition', 'weight': 0.5},
                    {'name': 'Responsibility Mapping', 'weight': 0.4},
                    {'name': 'Workflow Analysis', 'weight': 0.4},
                    {'name': 'Organizational Context', 'weight': 0.3},
                    {'name': 'Stakeholder Management', 'weight': 0.3},
                    {'name': 'Process Optimization', 'weight': 0.2},
                    {'name': 'Team Dynamics', 'weight': 0.2}
                ]
            },
            'CE': {
                'id': 'CE_DEFAULT',
                'name': 'Context Expert',
                'description': 'Focused on situational context and adaptability',
                'personality_traits': ['adaptable', 'holistic', 'intuitive'],
                'reasoning_style': 'contextual',
                'knowledge_focus': 'environmental context',
                'components': [
                    {'name': 'Contextual Analysis', 'weight': 0.5},
                    {'name': 'Situational Awareness', 'weight': 0.4},
                    {'name': 'Environmental Factors', 'weight': 0.4},
                    {'name': 'Cultural Considerations', 'weight': 0.3},
                    {'name': 'Temporal Dimensions', 'weight': 0.2},
                    {'name': 'Adaptive Strategies', 'weight': 0.3},
                    {'name': 'Multidimensional Thinking', 'weight': 0.3}
                ]
            }
        }
        
        return default_models.get(persona_type, {})
    
    def _generate_persona_answer(self, persona_type: str, persona_model: Dict[str, Any],
                               query_text: str, ka_result: Dict[str, Any],
                               initial_axis_context_scores: Dict[str, float],
                               active_location_context: List[str]) -> str:
        """
        Generate an answer from the persona's perspective.
        
        Args:
            persona_type (str): The persona type
            persona_model (dict): The persona model
            query_text (str): The original query text
            ka_result (dict): Results from KA processing
            initial_axis_context_scores (dict): Axis context scores
            active_location_context (list): Active location UIDs
            
        Returns:
            str: The generated answer
        """
        # In a full implementation, this would use more sophisticated generation techniques
        # For simplicity, we'll generate a template-based answer
        
        persona_name = persona_model.get('name', persona_type)
        persona_focus = persona_model.get('knowledge_focus', '')
        
        # Get relevant findings from KA result
        entities = []
        topics = []
        
        if ka_result.get('status') == 'success' and 'findings' in ka_result:
            entities = ka_result['findings'].get('extracted_entities', [])
            topics = ka_result['findings'].get('identified_topics', [])
        
        # Extract entity and topic names
        entity_names = [e.get('text', '') for e in entities if e.get('text')]
        topic_names = [t.get('topic', '') for t in topics if t.get('topic')]
        
        # Build an answer using the persona's components
        components = persona_model.get('components', [])
        component_sections = []
        
        for component in components:
            component_name = component.get('name', '')
            component_weight = component.get('weight', 0.0)
            
            # Only include components with sufficient weight
            if component_weight >= 0.3:
                component_sections.append(f"**{component_name}**: This component analyzes the query from a {component_name.lower()} perspective.")
        
        # Build the final answer
        answer = f"# {persona_name} Analysis\n\n"
        answer += f"As a {persona_name} with focus on {persona_focus}, I provide the following insights on the query:\n\n"
        answer += "## Query Analysis\n\n"
        
        if entity_names:
            answer += f"Key entities identified: {', '.join(entity_names)}\n\n"
        
        if topic_names:
            answer += f"Relevant topics: {', '.join(topic_names)}\n\n"

        answer += "## Detailed Response\n\n"
        
        if component_sections:
            answer += "\n\n".join(component_sections)
        else:
            answer += f"Based on my expertise as a {persona_name}, this query requires a focus on {persona_focus}."
        
        # Add location context if available
        if active_location_context:
            answer += "\n\n## Contextual Considerations\n\n"
            answer += "This analysis considers the specific regulatory and geographical context of the locations mentioned."
        
        return answer
    
    def _calculate_persona_confidence(self, persona_type: str, ka_result: Dict[str, Any],
                                    answer_length: int, initial_axis_context_scores: Dict[str, float]) -> float:
        """
        Calculate the confidence score for a persona's answer.
        
        Args:
            persona_type (str): The persona type
            ka_result (dict): Results from KA processing
            answer_length (int): Length of the generated answer
            initial_axis_context_scores (dict): Axis context scores
            
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        confidence = 0.7  # Base confidence
        
        # Add confidence based on KA result
        if ka_result.get('status') == 'success':
            confidence += min(0.2, ka_result.get('ka_confidence', 0.0) * 0.2)
        else:
            confidence -= 0.1
        
        # Add confidence based on answer length (longer answers might indicate more confidence)
        # But not too long, which might indicate verbosity without substance
        if 200 <= answer_length <= 2000:
            confidence += 0.1
        elif answer_length > 2000:
            confidence += 0.05
        else:
            confidence -= 0.05
        
        # Add confidence based on axis context scores
        # Each persona corresponds to a different axis
        axis_map = {
            'KE': 'Axis8',  # Knowledge Expert
            'SE': 'Axis9',  # Skill Expert
            'RE': 'Axis10', # Role Expert
            'CE': 'Axis11'  # Context Expert
        }
        
        if persona_type in axis_map:
            axis_id = axis_map[persona_type]
            if axis_id in initial_axis_context_scores:
                # Higher axis relevance score means higher confidence for that persona
                confidence += initial_axis_context_scores[axis_id] * 0.2
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))

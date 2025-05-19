"""
Universal Knowledge Graph (UKG) System - Chat API

This module provides API functionality for the chat interface,
integrating the 13-axis system with the quad persona framework.
"""

import uuid
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from backend.middleware import api_response
from app import db
from models import KnowledgeNode, Conversation, Message
from core.persona.persona_system import PersonaSystem
from core.axes.axis_system import AxisSystem

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint for Chat API
chat_api = Blueprint('chat_api', __name__, url_prefix='/api')

# Initialize the systems
persona_system = PersonaSystem()
axis_system = AxisSystem()

@chat_api.route('/chat', methods=['POST'])
@api_response
def process_chat_message():
    """Process a chat message using the UKG system."""
    try:
        data = request.json
        message = data.get('message', '')
        selected_axis = data.get('axis')
        selected_persona = data.get('persona')
        
        if not message:
            return {
                'success': False,
                'error': 'No message provided'
            }, 400
        
        # Create a conversation record if conversation_id not provided
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            # This is a new conversation
            conversation = Conversation(
                uid=str(uuid.uuid4()),
                title=message[:50] + '...' if len(message) > 50 else message,
                metadata={
                    'selected_axis': selected_axis,
                    'selected_persona': selected_persona
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(conversation)
            db.session.flush()
            conversation_id = conversation.id
        else:
            # Get existing conversation
            conversation = db.session.query(Conversation).get(conversation_id)
            if not conversation:
                return {
                    'success': False, 
                    'error': f'Conversation with ID {conversation_id} not found'
                }, 404
            
            # Update conversation
            conversation.updated_at = datetime.utcnow()
        
        # Store user message
        user_message = Message(
            uid=str(uuid.uuid4()),
            conversation_id=conversation_id,
            content=message,
            role='user',
            metadata={},
            created_at=datetime.utcnow()
        )
        db.session.add(user_message)
        
        # Process the message through the UKG system
        response = process_message_with_ukg(message, selected_axis, selected_persona)
        
        # Store system response
        system_message = Message(
            uid=str(uuid.uuid4()),
            conversation_id=conversation_id,
            content=response,
            role='system',
            metadata={
                'axis': selected_axis,
                'persona': selected_persona
            },
            created_at=datetime.utcnow()
        )
        db.session.add(system_message)
        
        # Commit all changes
        db.session.commit()
        
        return {
            'success': True,
            'response': response,
            'conversation_id': conversation_id
        }
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        db.session.rollback()
        return {
            'success': False,
            'error': str(e)
        }, 500

@chat_api.route('/conversations', methods=['GET'])
@api_response
def get_conversations():
    """Get all conversations."""
    try:
        conversations = db.session.query(Conversation).order_by(Conversation.updated_at.desc()).all()
        return {
            'success': True,
            'conversations': [conv.to_dict() for conv in conversations]
        }
    except Exception as e:
        logger.error(f"Error retrieving conversations: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }, 500

@chat_api.route('/conversations/<conversation_id>', methods=['GET'])
@api_response
def get_conversation(conversation_id):
    """Get a specific conversation with messages."""
    try:
        conversation = db.session.query(Conversation).get(conversation_id)
        if not conversation:
            return {
                'success': False,
                'error': f'Conversation with ID {conversation_id} not found'
            }, 404
            
        messages = db.session.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
        
        return {
            'success': True,
            'conversation': conversation.to_dict(),
            'messages': [msg.to_dict() for msg in messages]
        }
    except Exception as e:
        logger.error(f"Error retrieving conversation {conversation_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }, 500

def process_message_with_ukg(message, selected_axis, selected_persona):
    """
    Process a message using the UKG system with selected axis and persona.
    
    Args:
        message: The user's message
        selected_axis: The selected axis for processing
        selected_persona: The selected persona for processing
        
    Returns:
        A response message
    """
    try:
        # If no axis or persona is selected, provide a default response
        if not selected_axis and not selected_persona:
            return """
Welcome to the Universal Knowledge Graph system! To get the most out of this interaction, 
please select an axis and persona from the options above.

The 13-axis system helps organize knowledge across different dimensions:
- **Axis 1 (Knowledge)**: Manages information levels from raw data to wisdom
- **Axis 2 (Sector)**: Classifies knowledge by sector (science, arts, etc.)
- **Axis 3 (Domain)**: Further categorizes knowledge within sectors
- **Axis 4 (Context)**: Considers the contextual factors of knowledge
- **Axis 5 (Temporal)**: Deals with time-related aspects of knowledge
- **Axis 12 (Location)**: Adds geographic and spatial context
- **Axis 13 (Meta)**: Provides meta-knowledge about the system itself

The quad persona system offers four different perspectives:
- **Explorer**: Discovers new connections and possibilities
- **Analyst**: Examines patterns and draws conclusions
- **Critic**: Identifies limitations and challenges
- **Synthesizer**: Integrates diverse perspectives

Please select an axis and persona to begin exploring the Universal Knowledge Graph.
"""
        
        # Determine which axis to use for processing
        if selected_axis:
            # Get the appropriate axis handler
            axis = axis_system.get_axis(int(selected_axis))
            if not axis:
                return f"Sorry, Axis {selected_axis} is not yet fully implemented. Please try another axis."
            
            # Process message with the selected axis
            axis_response = axis.process_query(message)
        else:
            axis_response = None
        
        # Process with selected persona if provided
        if selected_persona:
            # Create a knowledge structure for persona processing
            knowledge_structure = {
                "content": message,
                "axis_response": axis_response,
                "type": "user_query"
            }
            
            # Process through persona system
            persona_result = persona_system.process_knowledge(knowledge_structure)
            
            # Get the specific persona's perspective
            if selected_persona in persona_result.get("perspectives", {}):
                perspective = persona_result["perspectives"][selected_persona]
                
                # Format the response based on the persona
                response = f"""
## {perspective.get('perspective_name', 'Perspective')}

{perspective.get('key_insights', [''])[0] if perspective.get('key_insights') else ''}

**Strengths Identified:**
{' '.join(['- ' + s for s in perspective.get('strengths_identified', ['No specific strengths identified.'])])}

**Potential Blind Spots:**
{' '.join(['- ' + b for b in perspective.get('blind_spots', ['No specific blind spots identified.'])])}

**Recommendations:**
{' '.join(['- ' + r for r in perspective.get('recommendations', ['No specific recommendations at this time.'])])}
"""
            else:
                # Use the integrated view if specific persona not found
                integrated = persona_result.get("integrated_view", {})
                response = f"""
## Integrated Perspective

{integrated.get('key_insights', [''])[0] if integrated.get('key_insights') else ''}

**Comprehensive Strengths:**
{' '.join(['- ' + s for s in integrated.get('comprehensive_strengths', ['No specific strengths identified.'])])}

**Potential Limitations:**
{' '.join(['- ' + l for l in integrated.get('potential_limitations', ['No specific limitations identified.'])])}

**Balanced Recommendations:**
{' '.join(['- ' + r for r in integrated.get('balanced_recommendations', ['No specific recommendations at this time.'])])}
"""
        elif axis_response:
            # If only axis is selected but no persona
            response = f"""
## Knowledge from Axis {selected_axis}

{axis_response}

*This response is provided without a persona filter. Select a persona for a more nuanced perspective.*
"""
        else:
            # Fallback response if neither axis nor persona provided useful results
            response = """
I'm not sure how to process your request with the current settings. 

Please try:
1. Selecting a different axis that might be more relevant to your query
2. Choosing a persona to get a more tailored perspective
3. Rephrasing your question to focus on specific knowledge domains or sectors
"""
        
        return response
    
    except Exception as e:
        logger.error(f"Error in UKG processing: {str(e)}")
        return f"I apologize, but I encountered an error while processing your request: {str(e)}"

def register_chat_api(app):
    """Register the chat API blueprint with the Flask app."""
    app.register_blueprint(chat_api)
    logger.info("Registered Chat API Blueprint")
"""
Universal Knowledge Graph (UKG) System - Chat API

This module provides API endpoints for the UKG chat interface.
"""

import uuid
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from models import Conversation, Message, db

# Set up logging
logger = logging.getLogger(__name__)

chat_api = Blueprint('chat_api', __name__)

def register_chat_api(app):
    """Register chat API endpoints with the application."""
    # Set up database reference for routes to use
    global db
    db = app.config.get('DB')
    
    app.register_blueprint(chat_api, url_prefix='/api/chat')
    logger.info("Chat API endpoints registered")

@chat_api.route('/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations."""
    try:
        conversations = Conversation.query.order_by(Conversation.created_at.desc()).all()
        return jsonify({
            'conversations': [conversation.to_dict() for conversation in conversations]
        }), 200
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        return jsonify({
            'error': 'Error getting conversations',
            'message': str(e)
        }), 500

@chat_api.route('/conversations', methods=['POST'])
def create_conversation():
    """Create a new conversation."""
    try:
        data = request.json
        title = data.get('title', 'New Conversation')
        metadata = data.get('metadata', {})
        
        conversation = Conversation(
            uid=str(uuid.uuid4()),
            title=title,
            meta_data=metadata,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(conversation)
        db.session.commit()
        
        return jsonify({
            'conversation': conversation.to_dict()
        }), 201
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        return jsonify({
            'error': 'Error creating conversation',
            'message': str(e)
        }), 500

@chat_api.route('/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get a conversation by ID."""
    try:
        conversation = Conversation.query.filter_by(uid=conversation_id).first()
        if not conversation:
            return jsonify({
                'error': 'Conversation not found',
                'message': f'No conversation found with ID {conversation_id}'
            }), 404
        
        messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
        
        return jsonify({
            'conversation': conversation.to_dict(),
            'messages': [message.to_dict() for message in messages]
        }), 200
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        return jsonify({
            'error': 'Error getting conversation',
            'message': str(e)
        }), 500

@chat_api.route('/conversations/<conversation_id>/messages', methods=['POST'])
def create_message(conversation_id):
    """Create a new message in a conversation."""
    try:
        data = request.json
        content = data.get('content')
        role = data.get('role', 'user')
        metadata = data.get('metadata', {})
        
        if not content:
            return jsonify({
                'error': 'Missing content',
                'message': 'Message content is required'
            }), 400
        
        conversation = Conversation.query.filter_by(uid=conversation_id).first()
        if not conversation:
            return jsonify({
                'error': 'Conversation not found',
                'message': f'No conversation found with ID {conversation_id}'
            }), 404
        
        message = Message(
            uid=str(uuid.uuid4()),
            conversation_id=conversation.id,
            content=content,
            role=role,
            meta_data=metadata,
            created_at=datetime.utcnow()
        )
        
        db.session.add(message)
        
        # Update conversation
        conversation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Generate system response if the message is from a user
        if role == 'user':
            system_response = generate_system_response(conversation, content)
            
            system_message = Message(
                uid=str(uuid.uuid4()),
                conversation_id=conversation.id,
                content=system_response,
                role='system',
                meta_data={},
                created_at=datetime.utcnow()
            )
            
            db.session.add(system_message)
            db.session.commit()
        
        messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at).all()
        
        return jsonify({
            'message': message.to_dict(),
            'conversation': conversation.to_dict(),
            'messages': [msg.to_dict() for msg in messages]
        }), 201
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        return jsonify({
            'error': 'Error creating message',
            'message': str(e)
        }), 500

def generate_system_response(conversation, user_message):
    """Generate a system response based on user input."""
    try:
        # Simple response for demonstration purposes
        greeting_phrases = ["hello", "hi", "hey", "greetings"]
        greeting_response = "Hello! I'm your UKG assistant. How can I help you today?"
        
        knowledge_phrases = ["what is", "how does", "explain", "tell me about"]
        knowledge_response = "The Universal Knowledge Graph (UKG) system is designed to manage and interconnect complex information across 13 axes of knowledge. It provides a framework for organizing, accessing, and reasoning with diverse types of information."
        
        # Check for greetings
        if any(phrase in user_message.lower() for phrase in greeting_phrases):
            return greeting_response
        
        # Check for knowledge queries
        if any(phrase in user_message.lower() for phrase in knowledge_phrases):
            return knowledge_response
        
        # Default response
        return "I'm processing your request through the UKG system. This is a demonstration of the chat functionality. In a production environment, this would connect to sophisticated knowledge processing algorithms."
    except Exception as e:
        logger.error(f"Error generating system response: {str(e)}")
        return "I apologize, but I encountered an error processing your request."
"""
Universal Knowledge Graph (UKG) System - Main Application

This file serves as the main application for the UKG system,
initializing the Flask app, configuring the database, and setting up routes.
"""

import os
import logging
from datetime import datetime
import uuid

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "ukg_development_key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define database models
class Conversation(db.Model):
    """Model for chat conversations in the UKG system."""
    __tablename__ = 'ukg_conversations'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert conversation to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'title': self.title,
            'metadata': self.meta_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Message(db.Model):
    """Model for chat messages in the UKG system."""
    __tablename__ = 'ukg_messages'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    conversation_id = Column(Integer, ForeignKey('ukg_conversations.id'), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(String(50), nullable=False)  # e.g., "user", "system"
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def to_dict(self):
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'conversation_id': self.conversation_id,
            'content': self.content,
            'role': self.role,
            'metadata': self.meta_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Configure error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return {"error": "Not found", "message": str(error)}, 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"Server error: {str(error)}")
    return {"error": "Server error", "message": str(error)}, 500

# Routes
@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html', title="Universal Knowledge Graph System")

@app.route('/chat')
def chat():
    """Render the chat interface."""
    return render_template('chat.html', title="UKG Chat Interface")

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('static', path)

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "online",
        "system": "UKG Chat System Ready",
        "version": "1.0.0"
    })

# API Routes
@app.route('/api/chat/conversations', methods=['GET'])
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

@app.route('/api/chat/conversations', methods=['POST'])
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

@app.route('/api/chat/conversations/<conversation_id>', methods=['GET'])
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

@app.route('/api/chat/conversations/<conversation_id>/messages', methods=['POST'])
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

# Create database tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created")

# Entry point
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
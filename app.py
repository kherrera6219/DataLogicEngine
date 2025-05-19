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

# Import the persona API blueprint
from backend.persona_api import persona_api

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "ukg_development_key")

# Register blueprints
app.register_blueprint(persona_api)

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

@app.route('/login')
def login():
    """Render the login page."""
    return render_template('login.html', title="Login - Universal Knowledge Graph")

@app.route('/persona-demo')
def persona_demo():
    """Render the quad persona engine demo page."""
    return render_template('persona_demo.html', title="Quad Persona Engine Demo - Universal Knowledge Graph")

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
    """Generate a system response based on user input using the quad persona engine."""
    try:
        # Import here to avoid circular imports
        from core.persona.persona_manager import get_persona_manager
        
        # Get the persona manager
        persona_manager = get_persona_manager()
        
        # Simple greeting detection for immediate responses without persona analysis
        greeting_phrases = ["hello", "hi", "hey", "greetings"]
        if any(phrase in user_message.lower() for phrase in greeting_phrases):
            return "Hello! I'm your UKG assistant, powered by the 13-axis knowledge framework and quad persona engine. How can I help you explore our universal knowledge graph today?"
        
        # Process the query through the quad persona engine
        response_data = persona_manager.generate_response(user_message, {
            "conversation_id": conversation.uid if conversation else None,
            "conversation_context": [msg.to_dict() for msg in conversation.messages] if conversation and conversation.messages else []
        })
        
        # Return the generated content
        return response_data["content"]
        
    except ImportError as e:
        logger.warning(f"PersonaManager not available, falling back to basic response: {str(e)}")
        return fallback_generate_response(user_message)
    except Exception as e:
        logger.error(f"Error generating system response: {str(e)}")
        return "I apologize, but I encountered an error processing your request through the UKG system. Please try rephrasing your question."

def fallback_generate_response(user_message):
    """Generate a basic response when the persona engine is not available."""
    try:
        # Knowledge axis responses (Axis 1)
        knowledge_phrases = ["what is", "how does", "explain", "tell me about", "can you describe"]
        ukg_concepts = ["universal knowledge graph", "knowledge graph", "ukg", "knowledge framework", "13 axis", "13-axis"]
        
        # Sector and domain responses (Axes 2 and 3)
        sector_phrases = ["business", "healthcare", "finance", "technology", "government", "education"]
        domain_phrases = ["cybersecurity", "artificial intelligence", "data science", "machine learning", "blockchain"]
        
        # Method responses (Axis 4)
        method_phrases = ["method", "approach", "technique", "framework", "methodology", "process", "algorithm"]
        
        # Location responses (Axis 12)
        location_phrases = ["where", "location", "place", "region", "country", "spatial"]
        
        # Time responses (Axis 13)
        time_phrases = ["when", "time", "temporal", "history", "future", "chronological", "timeline"]
        
        # Check for UKG concept explanations
        if any(phrase in user_message.lower() for phrase in knowledge_phrases) and any(concept in user_message.lower() for concept in ukg_concepts):
            return """The Universal Knowledge Graph (UKG) is an advanced cognitive system built on a 13-axis framework:

1. **Knowledge & Cognitive Framework** - Organizing information at different abstraction levels
2. **Sectors** - Industry and field categorizations (Healthcare, Finance, etc.)
3. **Domains** - Specific areas of expertise within sectors
4. **Methods** - Techniques and approaches to problem-solving
5. **Identity** - Entity and actor identification and relationships
6. **Regulatory** - Laws, rules, and governance structures
7. **Compliance** - Standards adherence and verification mechanisms
8. **Ethical** - Moral and ethical considerations and frameworks
9. **Risk** - Threat assessment and mitigation strategies
10. **Value** - Worth measurement and exchange systems
11. **Form** - Representation and communication formats
12. **Location** - Spatial and geographical contexts
13. **Time** - Temporal dimensions and chronological relationships

This multi-dimensional approach allows for sophisticated knowledge representation and reasoning across complex information spaces."""
        
        # Check for sector/domain specific queries
        if any(sector in user_message.lower() for sector in sector_phrases) or any(domain in user_message.lower() for domain in domain_phrases):
            # Extract which sector/domain was mentioned
            mentioned_sectors = [s for s in sector_phrases if s in user_message.lower()]
            mentioned_domains = [d for d in domain_phrases if d in user_message.lower()]
            
            if mentioned_sectors and mentioned_domains:
                sector = mentioned_sectors[0]
                domain = mentioned_domains[0]
                return f"I see you're interested in {domain} within the {sector} sector. The UKG system can provide insights by analyzing the intersections between domains and sectors, identifying regulatory frameworks, compliance requirements, and best practices specific to {domain} in {sector}."
            elif mentioned_sectors:
                sector = mentioned_sectors[0]
                return f"The {sector} sector has its own unique knowledge structures, regulatory frameworks, and domain-specific methodologies within the UKG system. I can explore specific domains within {sector} or analyze how this sector connects with others in the knowledge graph."
            elif mentioned_domains:
                domain = mentioned_domains[0]
                return f"{domain} is mapped across multiple sectors in the UKG system, with connections to related technologies, methodologies, and regulatory considerations. The knowledge graph helps identify how {domain} impacts different sectors and connects to other domains."
        
        # Check for method queries
        if any(method in user_message.lower() for method in method_phrases):
            return "The UKG system organizes methods and methodologies (Axis 4) hierarchically from high-level approaches to specific techniques. These methods can be context-specific or universal, and the system can identify which methods are most effective for particular domains or sectors based on historical data and expert knowledge."
        
        # Check for location-based queries
        if any(location in user_message.lower() for location in location_phrases):
            return "The Location Context Engine (Axis 12) in the UKG system provides spatial intelligence by connecting knowledge to physical and conceptual spaces. This enables location-aware reasoning and decision support, helping to understand how geographical context impacts other axes like regulatory requirements, sector-specific practices, or domain knowledge."
        
        # Check for time-based queries
        if any(time in user_message.lower() for time in time_phrases):
            return "The Temporal Framework (Axis 13) in the UKG system models time-dependent relationships and knowledge evolution. This allows for tracking how concepts, regulations, methods, and other knowledge elements change over time, supporting historical analysis and future trend prediction based on temporal patterns."
        
        # Default intelligent response
        return """I'm analyzing your query through the Universal Knowledge Graph's 13-axis framework. This demonstration shows how the UKG system processes natural language inputs to find relevant connections across different knowledge dimensions.

In a fully implemented system, I would:
1. Extract key concepts from your message
2. Map them to relevant axes in the knowledge graph
3. Identify connections across sectors, domains, and methodologies
4. Provide context-aware responses with spatial and temporal awareness

Is there a specific axis of knowledge you'd like to explore further?"""
    except Exception as e:
        logger.error(f"Error in fallback response generation: {str(e)}")
        return "I apologize, but I encountered an error processing your request. Please try again with a different question."

# Create database tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created")

# Entry point
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
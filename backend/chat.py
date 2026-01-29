"""
Chat API - Connected to LLM Gateway

Provides chat endpoints that route through the UKG-enhanced LLM Gateway
for real AI responses with knowledge graph context.
"""
import asyncio
import logging
import uuid
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import db, Chat, Message

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)


def run_async(coro):
    """Run async coroutine in sync context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@chat_bp.route('/chats', methods=['GET'])
@jwt_required()
def get_chats():
    user_id = get_jwt_identity()
    chats = Chat.query.filter_by(user_id=user_id).order_by(Chat.created_at.desc()).all()
    return jsonify([chat.to_dict() for chat in chats]), 200


@chat_bp.route('/chats', methods=['POST'])
@jwt_required()
def create_chat():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    new_chat = Chat(
        title=data.get('title', 'New Chat'),
        user_id=user_id
    )
    
    db.session.add(new_chat)
    db.session.commit()
    
    return jsonify(new_chat.to_dict()), 201


@chat_bp.route('/chats/<int:chat_id>', methods=['GET'])
@jwt_required()
def get_chat(chat_id):
    user_id = get_jwt_identity()
    chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
    
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at).all()
    
    return jsonify({
        'chat': chat.to_dict(),
        'messages': [message.to_dict() for message in messages]
    }), 200


@chat_bp.route('/chats/<int:chat_id>/messages', methods=['POST'])
@jwt_required()
def add_message(chat_id):
    """Add a message to a chat and get AI response via LLM Gateway."""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('content'):
        return jsonify({'error': 'Message content is required'}), 400
    
    chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
    
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    
    # Add user message
    user_message = Message(
        chat_id=chat_id,
        role='user',
        content=data['content']
    )
    db.session.add(user_message)
    db.session.flush()  # Get ID for RAG storage
    
    # Store user message embedding for semantic search
    try:
        from backend.services.rag_service import get_rag_service
        rag = get_rag_service()
        rag.store_chat_message(
            session_id=str(chat_id),
            message_id=str(user_message.id),
            role='user',
            content=data['content']
        )
    except Exception as e:
        logger.warning(f"Failed to store chat embedding: {e}")
    
    # Get conversation history for context
    history_messages = Message.query.filter_by(chat_id=chat_id).order_by(
        Message.created_at.desc()
    ).limit(10).all()
    
    messages_for_llm = [
        {"role": msg.role, "content": msg.content}
        for msg in reversed(history_messages)
    ]
    
    # Process with LLM Gateway
    assistant_response = _call_llm_gateway(
        messages=messages_for_llm,
        user_id=user_id,
        session_id=str(chat_id),
        use_rag=data.get('use_rag', True)
    )
    
    # Add assistant message
    assistant_message = Message(
        chat_id=chat_id,
        role='assistant',
        content=assistant_response['content']
    )
    db.session.add(assistant_message)
    
    # Store assistant message embedding
    try:
        rag.store_chat_message(
            session_id=str(chat_id),
            message_id=str(assistant_message.id),
            role='assistant',
            content=assistant_response['content']
        )
    except Exception:
        pass
    
    db.session.commit()
    
    return jsonify({
        'user_message': user_message.to_dict(),
        'assistant_message': assistant_message.to_dict(),
        'metadata': {
            'provider': assistant_response.get('provider'),
            'model': assistant_response.get('model'),
            'run_id': assistant_response.get('run_id')
        }
    }), 201


def _call_llm_gateway(
    messages: list,
    user_id: int,
    session_id: str,
    use_rag: bool = True
) -> dict:
    """
    Call the LLM Gateway with the given messages.
    
    Returns dict with 'content', 'provider', 'model', 'run_id'.
    """
    try:
        from backend.llm_gateway.gateway import LLMGateway, GatewayRequest
        
        gateway = LLMGateway(db_session=db.session)
        
        request = GatewayRequest(
            messages=messages,
            run_ukg_pipeline=True,
            user_id=user_id,
            session_id=session_id,
            meta={
                "use_rag": use_rag,
                "source": "chat_api"
            }
        )
        
        # Run async gateway in sync context
        response = run_async(gateway.process(request))
        
        if response.ok:
            return {
                'content': response.content,
                'provider': response.provider_used,
                'model': response.model_used,
                'run_id': response.run_id
            }
        else:
            logger.error(f"LLM Gateway error: {response.error}")
            return {
                'content': f"I apologize, but I encountered an error processing your request. Please try again.",
                'provider': None,
                'model': None,
                'run_id': response.run_id,
                'error': response.error
            }
            
    except ImportError as e:
        logger.error(f"LLM Gateway not available: {e}")
        return {
            'content': "The AI system is currently unavailable. Please try again later.",
            'provider': None,
            'model': None,
            'run_id': None
        }
    except Exception as e:
        logger.error(f"Error calling LLM Gateway: {e}", exc_info=True)
        return {
            'content': "An unexpected error occurred. Please try again.",
            'provider': None,
            'model': None,
            'run_id': None,
            'error': str(e)
        }


@chat_bp.route('/chats/<int:chat_id>/search', methods=['GET'])
@jwt_required()
def search_chat_history(chat_id):
    """Semantic search within chat history."""
    user_id = get_jwt_identity()
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({'error': 'Query parameter q is required'}), 400
    
    chat = Chat.query.filter_by(id=chat_id, user_id=user_id).first()
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404
    
    try:
        from backend.services.rag_service import get_rag_service
        rag = get_rag_service()
        results = rag.search_chat_history(
            session_id=str(chat_id),
            query=query,
            k=5
        )
        return jsonify({'results': results}), 200
    except Exception as e:
        logger.error(f"Chat search failed: {e}")
        return jsonify({'error': 'Search failed'}), 500

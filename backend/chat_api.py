"""Chat API blueprint used by the UKG demo interface."""

import logging
from datetime import datetime
from http import HTTPStatus

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest

from .models import Chat, Message, db

logger = logging.getLogger(__name__)

chat_api = Blueprint('chat_api', __name__)


def register_chat_api(app):
    """Register chat API endpoints with the given Flask application."""
    if 'sqlalchemy' not in getattr(app, 'extensions', {}):
        db.init_app(app)

    app.register_blueprint(chat_api, url_prefix='/api/chat')
    logger.info("Chat API endpoints registered")


def _json_error_response(message, status=HTTPStatus.BAD_REQUEST, details=None):
    """Return a consistent JSON error response."""
    payload = {"error": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status


def _get_request_payload():
    """Parse the request JSON payload and ensure it is an object."""
    data = request.get_json(silent=True)
    if data is None:
        raise BadRequest("Request body must be valid JSON.")
    if not isinstance(data, dict):
        raise BadRequest("JSON payload must be an object.")
    return data

@chat_api.route('/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations."""
    try:
        conversations = Chat.query.order_by(Chat.updated_at.desc()).all()
        return jsonify({'conversations': [conversation.to_dict() for conversation in conversations]}), HTTPStatus.OK
    except SQLAlchemyError:
        logger.exception("Error getting conversations")
        return _json_error_response('Error getting conversations', HTTPStatus.INTERNAL_SERVER_ERROR)

@chat_api.route('/conversations', methods=['POST'])
def create_conversation():
    """Create a new conversation."""
    try:
        data = _get_request_payload()
    except BadRequest as exc:
        logger.warning("Invalid create_conversation payload: %s", exc)
        return _json_error_response(str(exc), HTTPStatus.BAD_REQUEST)

    title = data.get('title') or 'New Conversation'
    metadata = data.get('metadata') or {}
    user_id = data.get('user_id')

    if not isinstance(title, str):
        return _json_error_response('Conversation title must be a string.')
    if not isinstance(metadata, dict):
        return _json_error_response('Conversation metadata must be an object.')
    if user_id is not None and not isinstance(user_id, int):
        return _json_error_response('Conversation user_id must be an integer.')

    conversation = Chat(
        title=title.strip() or 'New Conversation',
        meta_data=metadata,
        user_id=user_id
    )

    try:
        db.session.add(conversation)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Error creating conversation")
        return _json_error_response('Error creating conversation', HTTPStatus.INTERNAL_SERVER_ERROR)

    return jsonify({'conversation': conversation.to_dict()}), HTTPStatus.CREATED

@chat_api.route('/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get a conversation by ID."""
    try:
        conversation = Chat.query.filter_by(uid=conversation_id).first()
    except SQLAlchemyError:
        logger.exception("Database error while fetching conversation")
        return _json_error_response('Error getting conversation', HTTPStatus.INTERNAL_SERVER_ERROR)

    if not conversation:
        return _json_error_response(
            f'No conversation found with ID {conversation_id}',
            HTTPStatus.NOT_FOUND
        )

    try:
        messages = Message.query.filter_by(chat_id=conversation.id).order_by(Message.created_at).all()
    except SQLAlchemyError:
        logger.exception("Database error while fetching conversation messages")
        return _json_error_response('Error getting conversation messages', HTTPStatus.INTERNAL_SERVER_ERROR)

    return jsonify({
        'conversation': conversation.to_dict(),
        'messages': [message.to_dict() for message in messages]
    }), HTTPStatus.OK

@chat_api.route('/conversations/<conversation_id>/messages', methods=['POST'])
def create_message(conversation_id):
    """Create a new message in a conversation."""
    try:
        data = _get_request_payload()
    except BadRequest as exc:
        logger.warning("Invalid create_message payload: %s", exc)
        return _json_error_response(str(exc), HTTPStatus.BAD_REQUEST)

    content = data.get('content')
    role = data.get('role', 'user')
    metadata = data.get('metadata') or {}

    if not isinstance(content, str) or not content.strip():
        return _json_error_response('Message content is required.')
    if role not in {'user', 'assistant', 'system'}:
        return _json_error_response('Invalid message role provided.')
    if not isinstance(metadata, dict):
        return _json_error_response('Message metadata must be an object.')

    try:
        conversation = Chat.query.filter_by(uid=conversation_id).first()
    except SQLAlchemyError:
        logger.exception("Database error while loading conversation")
        return _json_error_response('Error creating message', HTTPStatus.INTERNAL_SERVER_ERROR)

    if not conversation:
        return _json_error_response(
            f'No conversation found with ID {conversation_id}',
            HTTPStatus.NOT_FOUND
        )

    message = Message(
        chat_id=conversation.id,
        content=content.strip(),
        role=role,
        meta_data=metadata,
        created_at=datetime.utcnow()
    )

    db.session.add(message)
    conversation.updated_at = datetime.utcnow()

    system_message = None
    if role == 'user':
        response_text = generate_system_response(conversation, content)
        system_message = Message(
            chat_id=conversation.id,
            content=response_text,
            role='system',
            meta_data={},
            created_at=datetime.utcnow()
        )
        db.session.add(system_message)
        conversation.updated_at = datetime.utcnow()

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Error committing message transaction")
        return _json_error_response('Error creating message', HTTPStatus.INTERNAL_SERVER_ERROR)

    try:
        messages = Message.query.filter_by(chat_id=conversation.id).order_by(Message.created_at).all()
    except SQLAlchemyError:
        logger.exception("Error loading conversation messages after create")
        return _json_error_response('Error loading conversation messages', HTTPStatus.INTERNAL_SERVER_ERROR)

    response_payload = {
        'message': message.to_dict(),
        'conversation': conversation.to_dict(),
        'messages': [msg.to_dict() for msg in messages]
    }
    if system_message:
        response_payload['system_message'] = system_message.to_dict()

    return jsonify(response_payload), HTTPStatus.CREATED

def generate_system_response(conversation, user_message):
    """Generate a system response based on user input."""
    try:
        # Simple response for demonstration purposes
        greeting_phrases = ["hello", "hi", "hey", "greetings"]
        greeting_response = "Hello! I'm your UKG assistant. How can I help you today?"

        knowledge_phrases = ["what is", "how does", "explain", "tell me about"]
        knowledge_response = (
            "The Universal Knowledge Graph (UKG) system is designed to manage and interconnect complex "
            "information across 13 axes of knowledge. It provides a framework for organizing, accessing, "
            "and reasoning with diverse types of information."
        )

        lower_message = user_message.lower()

        if any(phrase in lower_message for phrase in greeting_phrases):
            return greeting_response

        if any(phrase in lower_message for phrase in knowledge_phrases):
            return knowledge_response

        return (
            "I'm processing your request through the UKG system. This is a demonstration of the chat "
            "functionality. In a production environment, this would connect to sophisticated knowledge "
            "processing algorithms."
        )
    except Exception:  # pragma: no cover - defensive fallback
        logger.exception("Error generating system response")
        return "I apologize, but I encountered an error processing your request."
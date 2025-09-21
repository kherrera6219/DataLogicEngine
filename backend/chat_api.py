"""Universal Knowledge Graph (UKG) System - Chat API."""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from app import db
from models import Conversation, ConversationMessage, User

logger = logging.getLogger(__name__)


chat_api = Blueprint("chat_api", __name__)


def register_chat_api(app):
    """Register chat API endpoints with the application."""

    app.register_blueprint(chat_api, url_prefix="/api/chat")
    logger.info("Chat API endpoints registered")


@chat_api.route("/conversations", methods=["GET"])
def get_conversations():
    """Return all stored conversations ordered by most recent activity."""

    try:
        conversations = (
            Conversation.query.order_by(Conversation.updated_at.desc()).all()
        )
        return (
            jsonify(
                {
                    "conversations": [
                        conversation.to_dict(include_messages=False)
                        for conversation in conversations
                    ]
                }
            ),
            200,
        )
    except SQLAlchemyError as exc:
        logger.exception("Error getting conversations")
        return (
            jsonify(
                {
                    "error": "Error getting conversations",
                    "message": str(exc),
                }
            ),
            500,
        )


@chat_api.route("/conversations", methods=["POST"])
def create_conversation():
    """Create a new conversation optionally associated with a user."""

    payload = request.get_json(silent=True) or {}
    title = payload.get("title") or "New Conversation"
    metadata = payload.get("metadata") or {}
    user_id = payload.get("user_id")

    conversation = Conversation(title=title, metadata=metadata)

    if user_id is not None:
        user = db.session.get(User, user_id)
        if user is None:
            return (
                jsonify(
                    {
                        "error": "User not found",
                        "message": f"No user exists with id {user_id}",
                    }
                ),
                404,
            )
        conversation.user_id = user.id

    try:
        db.session.add(conversation)
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.exception("Error creating conversation")
        return (
            jsonify(
                {
                    "error": "Error creating conversation",
                    "message": str(exc),
                }
            ),
            500,
        )

    return jsonify({"conversation": conversation.to_dict()}), 201


@chat_api.route("/conversations/<string:conversation_uid>", methods=["GET"])
def get_conversation(conversation_uid):
    """Return a conversation and its messages by UID."""

    conversation = Conversation.query.filter_by(uid=conversation_uid).first()
    if conversation is None:
        return (
            jsonify(
                {
                    "error": "Conversation not found",
                    "message": f"No conversation found with ID {conversation_uid}",
                }
            ),
            404,
        )

    messages = (
        ConversationMessage.query.filter_by(conversation_id=conversation.id)
        .order_by(ConversationMessage.created_at)
        .all()
    )

    return (
        jsonify(
            {
                "conversation": conversation.to_dict(include_messages=False),
                "messages": [message.to_dict() for message in messages],
            }
        ),
        200,
    )


@chat_api.route(
    "/conversations/<string:conversation_uid>/messages", methods=["POST"]
)
def create_message(conversation_uid):
    """Store a new message in the specified conversation."""

    payload = request.get_json(silent=True) or {}
    content = payload.get("content")
    role = payload.get("role", "user")
    metadata = payload.get("metadata") or {}

    if not content:
        return (
            jsonify(
                {
                    "error": "Missing content",
                    "message": "Message content is required",
                }
            ),
            400,
        )

    conversation = Conversation.query.filter_by(uid=conversation_uid).first()
    if conversation is None:
        return (
            jsonify(
                {
                    "error": "Conversation not found",
                    "message": f"No conversation found with ID {conversation_uid}",
                }
            ),
            404,
        )

    message = ConversationMessage(
        conversation_id=conversation.id,
        content=content,
        role=role,
        metadata=metadata,
    )

    conversation.updated_at = datetime.utcnow()

    try:
        db.session.add(message)
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.exception("Error creating message")
        return (
            jsonify({"error": "Error creating message", "message": str(exc)}),
            500,
        )

    response_payload = {
        "message": message.to_dict(),
        "conversation": conversation.to_dict(include_messages=False),
    }

    if role == "user":
        system_response = generate_system_response(content)
        system_message = ConversationMessage(
            conversation_id=conversation.id,
            content=system_response,
            role="system",
            metadata={},
        )

        try:
            db.session.add(system_message)
            db.session.commit()
            response_payload["messages"] = [
                message.to_dict(),
                system_message.to_dict(),
            ]
        except SQLAlchemyError as exc:
            db.session.rollback()
            logger.exception("Error storing system response")
            response_payload["system_error"] = str(exc)

    return jsonify(response_payload), 201


def generate_system_response(user_message: str) -> str:
    """Generate a simple canned system response for demonstration purposes."""

    try:
        normalized_message = user_message.lower()
        greeting_phrases = {"hello", "hi", "hey", "greetings"}
        knowledge_phrases = {"what is", "how does", "explain", "tell me about"}

        if any(phrase in normalized_message for phrase in greeting_phrases):
            return "Hello! I'm your UKG assistant. How can I help you today?"

        if any(phrase in normalized_message for phrase in knowledge_phrases):
            return (
                "The Universal Knowledge Graph (UKG) system is designed to manage and "
                "interconnect complex information across 13 axes of knowledge. It "
                "provides a framework for organizing, accessing, and reasoning with "
                "diverse types of information."
            )
    except Exception:  # pragma: no cover - defensive fallback
        logger.exception("Error generating system response")
        return "I apologize, but I encountered an error processing your request."

    return (
        "I'm processing your request through the UKG system. This is a demonstration "
        "of the chat functionality. In a production environment, this would connect "
        "to sophisticated knowledge processing algorithms."
    )

"""
WebSocket Support for DataLogicEngine

Provides real-time communication for:
- Simulation progress updates
- Live notifications
- Chat functionality
"""

import os
import logging
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room

logger = logging.getLogger(__name__)

# Initialize Flask-SocketIO
socketio = SocketIO()


def init_socketio(app: Flask) -> None:
    """Initialize WebSocket support with Flask app."""
    # Configure SocketIO CORS — no wildcard allowed in production.
    raw_origins = os.environ.get('CORS_ORIGINS', '')
    is_production = os.environ.get('FLASK_ENV') == 'production'

    if raw_origins and raw_origins.strip() != '*':
        cors_origins = [o.strip() for o in raw_origins.split(',') if o.strip()]
    elif is_production:
        raise RuntimeError(
            "CORS_ORIGINS must be explicitly configured in production (wildcard is disallowed for WebSockets)"
        )
    else:
        # Development / test fallback — never reaches production due to guard above.
        cors_origins = ['http://localhost:3000', 'http://127.0.0.1:3000', 'app://-']

    socketio.init_app(
        app,
        cors_allowed_origins=cors_origins,
        async_mode='threading',  # Use 'eventlet' or 'gevent' in production
        logger=True,
        engineio_logger=True if os.environ.get('FLASK_ENV') == 'development' else False
    )
    
    logger.info("WebSocket support initialized")


# Connection events
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'status': 'connected', 'sid': request.sid})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")


# Room management
@socketio.on('join')
def handle_join(data):
    """Join a room for receiving targeted updates."""
    room = data.get('room')
    if room:
        join_room(room)
        logger.info(f"Client {request.sid} joined room: {room}")
        emit('joined', {'room': room}, room=room)


@socketio.on('leave')
def handle_leave(data):
    """Leave a room."""
    room = data.get('room')
    if room:
        leave_room(room)
        logger.info(f"Client {request.sid} left room: {room}")


# Simulation events
@socketio.on('subscribe_simulation')
def handle_subscribe_simulation(data):
    """Subscribe to simulation updates."""
    simulation_id = data.get('simulation_id')
    if simulation_id:
        room = f"simulation_{simulation_id}"
        join_room(room)
        emit('subscribed', {'simulation_id': simulation_id, 'room': room})


def emit_simulation_progress(simulation_id: str, progress: dict):
    """Emit simulation progress update to subscribers."""
    room = f"simulation_{simulation_id}"
    socketio.emit('simulation_progress', {
        'simulation_id': simulation_id,
        **progress
    }, room=room)


def emit_simulation_complete(simulation_id: str, results: dict):
    """Emit simulation completion to subscribers."""
    room = f"simulation_{simulation_id}"
    socketio.emit('simulation_complete', {
        'simulation_id': simulation_id,
        'results': results
    }, room=room)


# Notification events
def emit_notification(user_id: str, notification: dict):
    """Emit notification to a specific user."""
    room = f"user_{user_id}"
    socketio.emit('notification', notification, room=room)


def emit_broadcast(event: str, data: dict):
    """Broadcast event to all connected clients."""
    socketio.emit(event, data)


# Chat events
@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle incoming chat message."""
    message = data.get('message')
    session_id = data.get('session_id')
    
    if message and session_id:
        # Echo back to sender
        emit('chat_response', {
            'status': 'received',
            'session_id': session_id
        })
        
        # Process message asynchronously
        # In production, this would trigger AI processing
        room = f"chat_{session_id}"
        emit('chat_typing', {'session_id': session_id}, room=room)


def emit_chat_response(session_id: str, response: str, personas: list = None):
    """Emit chat response to session."""
    room = f"chat_{session_id}"
    socketio.emit('chat_response', {
        'session_id': session_id,
        'response': response,
        'personas': personas or []
    }, room=room)

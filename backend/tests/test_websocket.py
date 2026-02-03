
import pytest
from unittest.mock import MagicMock, patch
from backend.websocket import init_socketio, handle_connect, handle_disconnect, handle_join, handle_leave, handle_chat_message
from flask import Flask, request

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'
    app.config['TESTING'] = True
    return app

@pytest.fixture
def socketio_client(app):
    # Mocking socketio for unit testing without full server
    with patch('backend.websocket.socketio') as mock_socketio:
        init_socketio(app)
        yield mock_socketio

@patch('backend.websocket.emit')
def test_connect(mock_emit, app):
    with app.test_request_context('/?sid=123'):
         # Manually set sid if needed, but test_request_context handles basic request
         # We need to mock request.sid though, as Flask's default doesn't have it
         with patch('backend.websocket.request') as mock_request:
             mock_request.sid = '123'
             handle_connect()
             mock_emit.assert_called_with('connected', {'status': 'connected', 'sid': '123'})

@patch('backend.websocket.logger')
def test_disconnect(mock_logger, app):
    with app.test_request_context():
        with patch('backend.websocket.request') as mock_request:
            mock_request.sid = '123'
            handle_disconnect()
            mock_logger.info.assert_called_with("Client disconnected: 123")

@patch('backend.websocket.join_room')
@patch('backend.websocket.emit')
def test_join_room(mock_emit, mock_join_room, app):
    with app.test_request_context():
        with patch('backend.websocket.request') as mock_request:
            mock_request.sid = '123'
            handle_join({'room': 'test_room'})
            mock_join_room.assert_called_with('test_room')
            mock_emit.assert_called_with('joined', {'room': 'test_room'}, room='test_room')

@patch('backend.websocket.leave_room')
def test_leave_room(mock_leave_room, app):
    with app.test_request_context():
        with patch('backend.websocket.request') as mock_request:
            mock_request.sid = '123'
            handle_leave({'room': 'test_room'})
            mock_leave_room.assert_called_with('test_room')

@patch('backend.websocket.emit')
def test_chat_message_flow(mock_emit, app):
    with app.test_request_context():
        # Chat message flow doesn't use request.sid in this simplified handlers?
        # Let's check handle_chat_message. It doesn't use request.
        data = {'message': 'hello', 'session_id': 'sess_1'}
        handle_chat_message(data)
        
        # Check echo
        mock_emit.assert_any_call('chat_response', {
            'status': 'received',
            'session_id': 'sess_1'
        })
        
        # Check typing indicator
        mock_emit.assert_any_call('chat_typing', {'session_id': 'sess_1'}, room='chat_sess_1')

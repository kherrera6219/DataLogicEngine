"""
Tests for WebSocket functionality.

Tests the following:
- Socket connection
- Event emission
- Room subscription
"""

from unittest.mock import patch


class TestWebSocketClient:
    """Unit tests for WebSocket client functionality."""

    def test_emit_simulation_progress(self):
        """Test simulation progress emission."""
        from backend.websocket import emit_simulation_progress
        
        with patch('backend.websocket.socketio') as mock_socketio:
            emit_simulation_progress('sim-123', {
                'step': 5,
                'total_steps': 10,
                'status': 'running'
            })
            
            mock_socketio.emit.assert_called_once()
            call_args = mock_socketio.emit.call_args
            assert call_args[0][0] == 'simulation_progress'
            assert call_args[0][1]['simulation_id'] == 'sim-123'
            assert call_args[0][1]['step'] == 5

    def test_emit_simulation_complete(self):
        """Test simulation completion emission."""
        from backend.websocket import emit_simulation_complete
        
        with patch('backend.websocket.socketio') as mock_socketio:
            emit_simulation_complete('sim-456', {'result': 'success'})
            
            mock_socketio.emit.assert_called_once()
            call_args = mock_socketio.emit.call_args
            assert call_args[0][0] == 'simulation_complete'
            assert call_args[0][1]['simulation_id'] == 'sim-456'

    def test_emit_notification(self):
        """Test notification emission to user."""
        from backend.websocket import emit_notification
        
        with patch('backend.websocket.socketio') as mock_socketio:
            emit_notification('user-789', {
                'type': 'info',
                'title': 'Test',
                'message': 'Test notification'
            })
            
            mock_socketio.emit.assert_called_once()
            call_args = mock_socketio.emit.call_args
            assert call_args[0][0] == 'notification'
            assert call_args[1]['room'] == 'user_user-789'

    def test_emit_broadcast(self):
        """Test broadcast to all clients."""
        from backend.websocket import emit_broadcast
        
        with patch('backend.websocket.socketio') as mock_socketio:
            emit_broadcast('system_event', {'message': 'Hello all'})
            
            mock_socketio.emit.assert_called_once_with(
                'system_event',
                {'message': 'Hello all'}
            )

    def test_emit_chat_response(self):
        """Test chat response emission."""
        from backend.websocket import emit_chat_response
        
        with patch('backend.websocket.socketio') as mock_socketio:
            emit_chat_response('session-abc', 'AI response here', ['Expert1'])
            
            mock_socketio.emit.assert_called_once()
            call_args = mock_socketio.emit.call_args
            assert call_args[0][0] == 'chat_response'
            assert call_args[0][1]['response'] == 'AI response here'
            assert call_args[0][1]['personas'] == ['Expert1']


class TestWebSocketIntegration:
    """Integration tests for WebSocket module."""

    def test_socketio_instance_exists(self):
        """Test SocketIO instance is created."""
        from backend.websocket import socketio
        assert socketio is not None

    def test_init_socketio_function(self):
        """Test init_socketio configures app correctly."""
        from flask import Flask
        from backend.websocket import init_socketio
        
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret'
        
        # Should not raise
        init_socketio(app)

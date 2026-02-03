import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { socketClient, useSocket } from './socket';
import { io } from 'socket.io-client';

// Mock socket.io-client
const mockSocket = {
  on: vi.fn(),
  emit: vi.fn(),
  off: vi.fn(),
  connect: vi.fn(),
  disconnect: vi.fn(),
  connected: false,
};

vi.mock('socket.io-client', () => ({
  io: vi.fn(() => mockSocket),
}));

describe('Socket Logic', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSocket.connected = false;
    // Reset singleton private fields
    (socketClient as any).socket = null;
    (socketClient as any).handlers = {};
  });

  describe('SocketClient', () => {
    it('should connect only once if already connected', () => {
      mockSocket.connected = true;
      (socketClient as any).socket = mockSocket;
      
      socketClient.connect();
      expect(io).not.toHaveBeenCalled();
    });

    it('should initialize socket connection with correct options', () => {
      socketClient.connect('http://test-url.com');
      
      expect(io).toHaveBeenCalledWith('http://test-url.com', expect.objectContaining({
        transports: ['websocket', 'polling'],
        reconnection: true
      }));
    });

    it('should disconnect and clear socket instance', () => {
      (socketClient as any).socket = mockSocket;
      socketClient.disconnect();
      
      expect(mockSocket.disconnect).toHaveBeenCalled();
      expect((socketClient as any).socket).toBeNull();
    });

    it('should emit join event when joinRoom is called', () => {
      (socketClient as any).socket = mockSocket;
      socketClient.joinRoom('test-room');
      
      expect(mockSocket.emit).toHaveBeenCalledWith('join', { room: 'test-room' });
    });

    it('should emit leave event when leaveRoom is called', () => {
      (socketClient as any).socket = mockSocket;
      socketClient.leaveRoom('test-room');
      
      expect(mockSocket.emit).toHaveBeenCalledWith('leave', { room: 'test-room' });
    });

    it('should emit chat_message event when sendChatMessage is called', () => {
      (socketClient as any).socket = mockSocket;
      socketClient.sendChatMessage('session-1', 'Hello');
      
      expect(mockSocket.emit).toHaveBeenCalledWith('chat_message', { 
        session_id: 'session-1', 
        message: 'Hello' 
      });
    });

    it('should register event listeners and trigger handlers', () => {
      const handlers = {
        onChatResponse: vi.fn(),
        onNotification: vi.fn(),
        onDisconnected: vi.fn()
      };
      
      socketClient.connect();
      socketClient.setHandlers(handlers);
      
      // Find the 'chat_response' listener registered during setupEventListeners
      const chatResponseCall = mockSocket.on.mock.calls.find(
        (call: any) => call[0] === 'chat_response'
      );
      expect(chatResponseCall).toBeDefined();
      
      const chatResponseListener = chatResponseCall[1];
      const responseData = { session_id: '1', response: 'hi' };
      chatResponseListener(responseData);
      expect(handlers.onChatResponse).toHaveBeenCalledWith(responseData);
      
      // Test disconnect listener
      const disconnectCall = mockSocket.on.mock.calls.find(
        (call: any) => call[0] === 'disconnect'
      );
      expect(disconnectCall).toBeDefined();
      
      const disconnectListener = disconnectCall[1];
      disconnectListener();
      expect(handlers.onDisconnected).toHaveBeenCalled();
    });

    it('should return correct connection status', () => {
      (socketClient as any).socket = null;
      expect(socketClient.isConnected).toBe(false);
      
      (socketClient as any).socket = mockSocket;
      mockSocket.connected = true;
      expect(socketClient.isConnected).toBe(true);
    });
  });

  describe('useSocket', () => {
    it('should initialize connection and set handlers', () => {
      const handlers = { onChatResponse: vi.fn() };
      
      renderHook(() => useSocket(handlers));
      
      expect(io).toHaveBeenCalled();
      // Verify handlers were set
      expect((socketClient as any).handlers.onChatResponse).toBeDefined();
    });
  });
});

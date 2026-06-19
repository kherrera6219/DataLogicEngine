import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { socketClient, useSocket } from '@/lib/socket';
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
    mockSocket.on.mockClear();
    mockSocket.emit.mockClear();
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

    it('should use default URL if not provided', () => {
      socketClient.connect();
      expect(io).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(Object)
      );
    });

    it('should disconnect and clear socket instance', () => {
      (socketClient as any).socket = mockSocket;
      socketClient.disconnect();
      
      expect(mockSocket.disconnect).toHaveBeenCalled();
      expect((socketClient as any).socket).toBeNull();
    });

    it('should handle disconnect when socket is null', () => {
      (socketClient as any).socket = null;
      socketClient.disconnect();
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

    it('should emit trace room join and leave events', () => {
      (socketClient as any).socket = mockSocket;
      socketClient.joinRunRoom('run-1');
      socketClient.leaveRunRoom('run-1');

      expect(mockSocket.emit).toHaveBeenNthCalledWith(1, 'join_run_room', { run_id: 'run-1' });
      expect(mockSocket.emit).toHaveBeenNthCalledWith(2, 'leave_run_room', { run_id: 'run-1' });
    });

    it('should emit chat_message event when sendChatMessage is called', () => {
      (socketClient as any).socket = mockSocket;
      socketClient.sendChatMessage('session-1', 'Hello');
      
      expect(mockSocket.emit).toHaveBeenCalledWith('chat_message', { 
        session_id: 'session-1', 
        message: 'Hello' 
      });
    });

    it('should subscribe to simulation updates', () => {
      (socketClient as any).socket = mockSocket;
      socketClient.subscribeToSimulation('sim-123');
      
      expect(mockSocket.emit).toHaveBeenCalledWith('subscribe_simulation', {
        simulation_id: 'sim-123'
      });
    });

    it('should set event handlers correctly', () => {
      const handlers = {
        onChatResponse: vi.fn(),
        onNotification: vi.fn(),
      };
      
      socketClient.setHandlers(handlers);
      
      expect((socketClient as any).handlers.onChatResponse).toBe(handlers.onChatResponse);
      expect((socketClient as any).handlers.onNotification).toBe(handlers.onNotification);
    });

    it('should merge new handlers with existing ones', () => {
      const handlers1 = { onChatResponse: vi.fn() };
      const handlers2 = { onNotification: vi.fn() };
      
      socketClient.setHandlers(handlers1);
      socketClient.setHandlers(handlers2);
      
      expect((socketClient as any).handlers.onChatResponse).toBeDefined();
      expect((socketClient as any).handlers.onNotification).toBeDefined();
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

      const traceUpdateCall = mockSocket.on.mock.calls.find(
        (call: any) => call[0] === 'trace_stage_update'
      );
      expect(traceUpdateCall).toBeDefined();
      
      // Test disconnect listener
      const disconnectCall = mockSocket.on.mock.calls.find(
        (call: any) => call[0] === 'disconnect'
      );
      expect(disconnectCall).toBeDefined();
      
      const disconnectListener = disconnectCall[1];
      disconnectListener();
      expect(handlers.onDisconnected).toHaveBeenCalled();
    });

    it('should handle connection event and reset reconnect attempts', () => {
      const handlers = { onConnected: vi.fn() };
      socketClient.connect();
      socketClient.setHandlers(handlers);
      
      const connectCall = mockSocket.on.mock.calls.find(
        (call: any) => call[0] === 'connect'
      );
      expect(connectCall).toBeDefined();
      
      const connectListener = connectCall[1];
      connectListener();
      // Verify reconnect attempts are reset (private field)
      expect((socketClient as any).reconnectAttempts).toBe(0);
    });

    it('should handle connection errors', () => {
      socketClient.connect();
      
      const connectErrorCall = mockSocket.on.mock.calls.find(
        (call: any) => call[0] === 'connect_error'
      );
      expect(connectErrorCall).toBeDefined();
      
      const errorListener = connectErrorCall[1];
      const error = new Error('Connection failed');
      errorListener(error);
      expect((socketClient as any).reconnectAttempts).toBe(1);
    });

    it('should trigger all registered event handlers', () => {
      const handlers = {
        onSimulationProgress: vi.fn(),
        onSimulationComplete: vi.fn(),
        onNotification: vi.fn(),
        onChatTyping: vi.fn(),
        onTraceStageUpdate: vi.fn(),
        onConnected: vi.fn(),
      };
      
      socketClient.connect();
      socketClient.setHandlers(handlers);
      
      // Trigger simulation progress
      const simProgressCall = mockSocket.on.mock.calls.find(
        (call: any) => call[0] === 'simulation_progress'
      );
      simProgressCall[1]({ simulation_id: 'sim-1', step: 1, total_steps: 10, status: 'running' });
      expect(handlers.onSimulationProgress).toHaveBeenCalled();
      
      // Trigger simulation complete
      const simCompleteCall = mockSocket.on.mock.calls.find(
        (call: any) => call[0] === 'simulation_complete'
      );
      simCompleteCall[1]({ simulation_id: 'sim-1', results: {} });
      expect(handlers.onSimulationComplete).toHaveBeenCalled();
      
      // Trigger notification
      const notificationCall = mockSocket.on.mock.calls.find(
        (call: any) => call[0] === 'notification'
      );
      notificationCall[1]({ id: 'notif-1', type: 'info', title: 'Test', message: 'test', timestamp: new Date().toISOString() });
      expect(handlers.onNotification).toHaveBeenCalled();
    });

    it('should return correct connection status', () => {
      (socketClient as any).socket = null;
      expect(socketClient.isConnected).toBe(false);
      
      (socketClient as any).socket = mockSocket;
      mockSocket.connected = true;
      expect(socketClient.isConnected).toBe(true);
      
      mockSocket.connected = false;
      expect(socketClient.isConnected).toBe(false);
    });

    it('should handle socket being null when checking connection', () => {
      (socketClient as any).socket = null;
      expect(socketClient.isConnected).toBe(false);
    });
  });

  describe('useSocket', () => {
    it('should initialize connection and set handlers', () => {
      const handlers = { onChatResponse: vi.fn() };
      
      renderHook(() => useSocket(handlers));
      
      expect(io).toHaveBeenCalled();
      expect((socketClient as any).handlers.onChatResponse).toBeDefined();
    });

    it('should return socket client instance', () => {
      const { result } = renderHook(() => useSocket());
      expect(result.current).toBe(socketClient);
    });

    it('should not reconnect if already connected', () => {
      mockSocket.connected = true;
      (socketClient as any).socket = mockSocket;
      vi.clearAllMocks();
      
      renderHook(() => useSocket());
      expect(io).not.toHaveBeenCalled();
    });

    it('should work without handlers', () => {
      const { result } = renderHook(() => useSocket());
      expect(result.current).toBe(socketClient);
    });
  });
});

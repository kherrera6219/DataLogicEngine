/**
 * WebSocket Client for DataLogicEngine
 *
 * Provides real-time communication with the backend for:
 * - Simulation progress updates
 * - Live notifications
 * - Chat responses
 */

import { io, Socket } from "socket.io-client";

// Types
export interface SimulationProgress {
  simulation_id: string;
  step: number;
  total_steps: number;
  status: "running" | "completed" | "failed";
  message?: string;
}

export interface Notification {
  id: string;
  type: "info" | "success" | "warning" | "error";
  title: string;
  message: string;
  timestamp: string;
}

export interface ChatResponse {
  session_id: string;
  response: string;
  personas?: string[];
}

export interface TraceStageUpdate {
  run_id: string;
  stage_id?: string;
  name?: string;
  status?: string;
  layer_index?: number;
  step_index?: number;
  timing?: {
    duration_ms?: number | null;
  };
  inputs?: unknown;
  outputs?: unknown;
  metrics?: Record<string, unknown> | null;
}

// Event handlers type
export interface SocketEventHandlers {
  onSimulationProgress?: (data: SimulationProgress) => void;
  onSimulationComplete?: (data: {
    simulation_id: string;
    results: Record<string, unknown>;
  }) => void;
  onNotification?: (data: Notification) => void;
  onChatResponse?: (data: ChatResponse) => void;
  onChatTyping?: (data: { session_id: string }) => void;
  onTraceStageUpdate?: (data: TraceStageUpdate) => void;
  onConnected?: (data: { status: string; sid: string }) => void;
  onDisconnected?: () => void;
}

class SocketClient {
  private socket: Socket | null = null;
  private handlers: SocketEventHandlers = {};
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  /**
   * Connect to the WebSocket server
   */
  connect(url?: string): void {
    if (this.socket?.connected) {
      return;
    }

    const socketUrl =
      url || process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

    this.socket = io(socketUrl, {
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });

    this.setupEventListeners();
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  /**
   * Set event handlers
   */
  setHandlers(handlers: SocketEventHandlers): void {
    this.handlers = { ...this.handlers, ...handlers };
  }

  /**
   * Subscribe to simulation updates
   */
  subscribeToSimulation(simulationId: string): void {
    this.socket?.emit("subscribe_simulation", { simulation_id: simulationId });
  }

  /**
   * Join a room for targeted updates
   */
  joinRoom(room: string): void {
    this.socket?.emit("join", { room });
  }

  /**
   * Leave a room
   */
  leaveRoom(room: string): void {
    this.socket?.emit("leave", { room });
  }

  joinRunRoom(runId: string): void {
    this.socket?.emit("join_run_room", { run_id: runId });
  }

  leaveRunRoom(runId: string): void {
    this.socket?.emit("leave_run_room", { run_id: runId });
  }

  /**
   * Send a chat message
   */
  sendChatMessage(sessionId: string, message: string): void {
    this.socket?.emit("chat_message", { session_id: sessionId, message });
  }

  /**
   * Check if connected
   */
  get isConnected(): boolean {
    return this.socket?.connected ?? false;
  }

  private setupEventListeners(): void {
    if (!this.socket) return;

    // Connection events
    this.socket.on("connect", () => {
      this.reconnectAttempts = 0;
      console.log("[Socket] Connected");
    });

    this.socket.on("disconnect", () => {
      console.log("[Socket] Disconnected");
      this.handlers.onDisconnected?.();
    });

    this.socket.on("connect_error", (error) => {
      console.error("[Socket] Connection error:", error);
      this.reconnectAttempts++;
    });

    // Custom events
    this.socket.on("connected", (data) => {
      this.handlers.onConnected?.(data);
    });

    this.socket.on("simulation_progress", (data: SimulationProgress) => {
      this.handlers.onSimulationProgress?.(data);
    });

    this.socket.on("simulation_complete", (data) => {
      this.handlers.onSimulationComplete?.(data);
    });

    this.socket.on("notification", (data: Notification) => {
      this.handlers.onNotification?.(data);
    });

    this.socket.on("chat_response", (data: ChatResponse) => {
      this.handlers.onChatResponse?.(data);
    });

    this.socket.on("chat_typing", (data) => {
      this.handlers.onChatTyping?.(data);
    });

    this.socket.on("trace_stage_update", (data: TraceStageUpdate) => {
      this.handlers.onTraceStageUpdate?.(data);
    });
  }
}

// Singleton instance
export const socketClient = new SocketClient();

// React hook for socket connection
export function useSocket(handlers?: SocketEventHandlers) {
  if (typeof window !== "undefined") {
    if (handlers) {
      socketClient.setHandlers(handlers);
    }

    if (!socketClient.isConnected) {
      socketClient.connect();
    }
  }

  return socketClient;
}

export interface McpServer {
  id: string;
  name: string;
  type: 'enterprise' | 'devops' | 'data' | 'other';
  status: 'connected' | 'disconnected' | 'error';
  url: string;
  protocol: 'websocket' | 'stdio' | 'sse';
  toolsCount: number;
  resourcesCount: number;
  promptsCount: number;
  latencyMs: number;
  lastActivity: string;
  errorMessage?: string;
}

export interface McpTool {
  name: string;
  server: string;
  category: string;
  description: string;
  isEnabled: boolean;
  callsToday: number;
  avgTimeMs: number;
  successRate: number;
  version?: string;
  complexity?: string;
  inputSchema?: Record<string, unknown>;
  outputSchema?: Record<string, unknown>;
}

export interface McpResource {
  name: string;
  server: string;
  uri: string;
  description: string;
  isEnabled: boolean;
}

export interface McpPrompt {
  name: string;
  server: string;
  description: string;
  variables: string[];
}

export interface McpStats {
  activeServers: number;
  activeClients: number;
  totalTools: number;
  messagesToday: number;
}

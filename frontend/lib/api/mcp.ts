import { request } from './index';

// Types
export interface MCPServer {
    id?: string;
    server_id: string;
    name: string;
    version: string;
    description: string;
    status: 'active' | 'inactive' | 'error';
    capabilities?: {
        resources?: boolean;
        tools?: boolean;
        prompts?: boolean;
        logging?: boolean;
    };
    stats?: {
        resources: number;
        tools: number;
        prompts: number;
        connections: number;
    }
}

// JSON Schema can be complex, so we use a flexible type
// Keep as 'any' since JSON Schema structure is highly dynamic and standardized
export interface MCPTool {
    name: string;
    description: string;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    inputSchema: any; // JSON Schema - dynamic structure, safe to use any
}

export interface MCPResource {
    uri: string;
    name: string;
    mimeType: string;
}

export interface MCPStats {
    total_servers: number;
    active_servers: number;
    total_resources: number;
    total_tools: number;
    active_connections: number;
}

export interface MCPRuntimeServer {
    id: string;
    name: string;
    status: string;
    [key: string]: unknown; // Allow additional dynamic properties
}

// API Methods
export const mcp = {
    // Servers
    getServers: (): Promise<{ servers: MCPServer[], runtime_servers: MCPRuntimeServer[] }> => 
        request('/mcp/servers'),

    getServer: (serverId: string): Promise<MCPServer> => 
        request<{ server: MCPServer }>(`/mcp/servers/${serverId}`).then(d => d.server),

    createServer: (data: Partial<MCPServer>): Promise<MCPServer> => 
        request('/mcp/servers', {
            method: 'POST',
            body: JSON.stringify(data)
        }),

    deleteServer: (serverId: string): Promise<void> => 
        request(`/mcp/servers/${serverId}`, {
            method: 'DELETE'
        }),

    // Resources & Tools
    getTools: (serverId: string): Promise<MCPTool[]> => 
        request<{ tools: MCPTool[] }>(`/mcp/servers/${serverId}/tools`).then(d => d.tools),

    getResources: (serverId: string): Promise<MCPResource[]> => 
        request<{ resources: MCPResource[] }>(`/mcp/servers/${serverId}/resources`).then(d => d.resources),

    // Stats
    getStats: (): Promise<MCPStats> => 
        request<{ stats: MCPStats }>('/mcp/stats').then(d => d.stats)
};

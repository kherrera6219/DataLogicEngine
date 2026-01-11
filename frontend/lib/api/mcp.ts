import { API_BASE } from './index';

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
export const mcpApi = {
    // Servers
    getServers: async (): Promise<{ servers: MCPServer[], runtime_servers: MCPRuntimeServer[] }> => {
        const res = await fetch(`${API_BASE}/mcp/servers`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        return res.json();
    },

    getServer: async (serverId: string): Promise<MCPServer> => {
        const res = await fetch(`${API_BASE}/mcp/servers/${serverId}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const data = await res.json();
        return data.server;
    },

    createServer: async (data: Partial<MCPServer>): Promise<MCPServer> => {
        const res = await fetch(`${API_BASE}/mcp/servers`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error('Failed to create server');
        return res.json();
    },

    deleteServer: async (serverId: string): Promise<void> => {
        const res = await fetch(`${API_BASE}/mcp/servers/${serverId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (!res.ok) throw new Error('Failed to delete server');
    },

    // Resources & Tools
    getTools: async (serverId: string): Promise<MCPTool[]> => {
        const res = await fetch(`${API_BASE}/mcp/servers/${serverId}/tools`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const data = await res.json();
        return data.tools;
    },

    getResources: async (serverId: string): Promise<MCPResource[]> => {
        const res = await fetch(`${API_BASE}/mcp/servers/${serverId}/resources`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const data = await res.json();
        return data.resources;
    },

    // Stats
    getStats: async (): Promise<MCPStats> => {
        const res = await fetch(`${API_BASE}/mcp/stats`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        const data = await res.json();
        return data.stats;
    }
};

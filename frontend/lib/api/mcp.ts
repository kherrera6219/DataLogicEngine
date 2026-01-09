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

export interface MCPTool {
    name: string;
    description: string;
    inputSchema: any;
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

// API Methods
export const mcpApi = {
    // Servers
    getServers: async (): Promise<{ servers: MCPServer[], runtime_servers: any[] }> => {
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

import { describe, it, expect, vi } from 'vitest';
import { mcp } from './mcp';
import { request } from './index';

vi.mock('./index', () => ({
    request: vi.fn()
}));

describe('MCP API Client', () => {
    it('getServers should call /mcp/servers', async () => {
        const mockData = { servers: [], runtime_servers: [] };
        vi.mocked(request).mockResolvedValue(mockData);

        const result = await mcp.getServers();
        
        expect(request).toHaveBeenCalledWith('/mcp/servers');
        expect(result).toEqual(mockData);
    });

    it('getServer should return unwrapped server data', async () => {
        const mockServer = { name: 'Test Server', server_id: 's1' };
        vi.mocked(request).mockResolvedValue({ server: mockServer });

        const result = await mcp.getServer('s1');
        
        expect(request).toHaveBeenCalledWith('/mcp/servers/s1');
        expect(result).toEqual(mockServer);
    });

    it('getTools should return unwrapped tools list', async () => {
        const mockTools = [{ name: 'tool1', description: 'd1', inputSchema: {} }];
        vi.mocked(request).mockResolvedValue({ tools: mockTools });

        const result = await mcp.getTools('s1');
        
        expect(request).toHaveBeenCalledWith('/mcp/servers/s1/tools');
        expect(result).toEqual(mockTools);
    });

    it('getStats should return unwrapped stats', async () => {
        const mockStats = { total_servers: 1, active_servers: 1, total_resources: 0, total_tools: 5, active_connections: 1 };
        vi.mocked(request).mockResolvedValue({ stats: mockStats });

        const result = await mcp.getStats();
        
        expect(request).toHaveBeenCalledWith('/mcp/stats');
        expect(result).toEqual(mockStats);
    });
});

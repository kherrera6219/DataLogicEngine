import { describe, it, expect, vi } from 'vitest';
import { mcp } from '@/lib/api/mcp';
import { request } from '@/lib/api/index';

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

    it('createServer should post data', async () => {
        const mockData = { name: 'New Server', server_id: 'new1' };
        vi.mocked(request).mockResolvedValue(mockData);

        const result = await mcp.createServer(mockData);

        expect(request).toHaveBeenCalledWith('/mcp/servers', expect.objectContaining({
            method: 'POST',
            body: JSON.stringify(mockData)
        }));
        expect(result).toEqual(mockData);
    });

    it('deleteServer should send delete request', async () => {
        vi.mocked(request).mockResolvedValue(undefined);

        await mcp.deleteServer('s1');

        expect(request).toHaveBeenCalledWith('/mcp/servers/s1', expect.objectContaining({
            method: 'DELETE'
        }));
    });

    it('getResources should return unwrapped resources list', async () => {
         const mockResources = [{ name: 'res1', uri: 'file:///', mimeType: 'text/plain' }];
         vi.mocked(request).mockResolvedValue({ resources: mockResources });

         const result = await mcp.getResources('s1');

         expect(request).toHaveBeenCalledWith('/mcp/servers/s1/resources');
         expect(result).toEqual(mockResources);
    });
});

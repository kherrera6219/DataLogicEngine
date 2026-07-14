import { describe, it, expect, vi } from 'vitest';
import { mcp } from '@/lib/api/mcp';
import { request } from '@/lib/api/client';

vi.mock('@/lib/api/client', () => ({
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
        const mockData = {
            name: 'new-server',
            version: '1.0.0',
            description: 'New Server',
            config: {
                transport: 'stdio' as const,
                protocol_version: '2025-11-25' as const,
                command: 'C:\\connector.exe',
                args: [],
                cwd: 'C:\\data',
                env: {},
                credential_env: {},
                file_roots: ['C:\\data'],
                network_destinations: [],
                requested_scopes: ['connector:new-server:read'],
                limits: {
                    request_timeout_seconds: 30,
                    max_message_bytes: 65536,
                    max_stderr_bytes: 16384,
                    max_process_memory_mb: 256,
                },
            },
        };
        const created = { ...mockData, server_id: 'new1' };
        vi.mocked(request).mockResolvedValue({ server: created });

        const result = await mcp.createServer(mockData);

        expect(request).toHaveBeenCalledWith('/mcp/servers', expect.objectContaining({
            method: 'POST',
            body: JSON.stringify(mockData)
        }));
        expect(result).toEqual(created);
    });

    it('approveConsent should bind the exact fingerprint and scopes', async () => {
        const server = { server_id: 's1', command_fingerprint: 'abc' };
        vi.mocked(request).mockResolvedValue({ server });

        const result = await mcp.approveConsent('s1', 'abc', ['connector:test:read']);

        expect(request).toHaveBeenCalledWith('/mcp/servers/s1/consent', {
            method: 'POST',
            body: JSON.stringify({
                command_fingerprint: 'abc',
                approved_scopes: ['connector:test:read'],
            }),
        });
        expect(result).toEqual(server);
    });

    it.each([
        ['startServer', '/mcp/servers/s1/start'],
        ['stopServer', '/mcp/servers/s1/stop'],
        ['restartServer', '/mcp/servers/s1/restart'],
    ] as const)('%s should call its lifecycle endpoint', async (method, endpoint) => {
        vi.mocked(request).mockResolvedValue({ server: { server_id: 's1' } });

        await mcp[method]('s1');

        expect(request).toHaveBeenCalledWith(endpoint, { method: 'POST' });
    });

    it('revokeConsent should call the consent delete endpoint', async () => {
        vi.mocked(request).mockResolvedValue({ server: { server_id: 's1' } });

        await mcp.revokeConsent('s1');

        expect(request).toHaveBeenCalledWith('/mcp/servers/s1/consent', { method: 'DELETE' });
    });

    it('getLifecycle should unwrap durable lifecycle events', async () => {
        const events = [{ id: 'event-1', event_type: 'started' }];
        vi.mocked(request).mockResolvedValue({ events });

        expect(await mcp.getLifecycle('s1')).toEqual(events);
        expect(request).toHaveBeenCalledWith('/mcp/servers/s1/lifecycle');
    });

    it('getExecutions should unwrap governed execution records', async () => {
        const executions = [{ execution_id: 'execution-1', status: 'succeeded' }];
        vi.mocked(request).mockResolvedValue({ executions });

        expect(await mcp.getExecutions('s1')).toEqual(executions);
        expect(request).toHaveBeenCalledWith('/mcp/servers/s1/executions');
    });

    it('cancelExecution should use the server-bound durable execution route', async () => {
        const execution = { execution_id: 'execution-1', status: 'cancelled' };
        vi.mocked(request).mockResolvedValue({ execution });

        expect(await mcp.cancelExecution('s1', 'execution-1')).toEqual(execution);
        expect(request).toHaveBeenCalledWith(
            '/mcp/servers/s1/executions/execution-1/cancel',
            { method: 'POST' },
        );
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

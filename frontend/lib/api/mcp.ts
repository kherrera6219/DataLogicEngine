import { request } from '@/lib/api/client';

export type MCPConsentState = 'pending' | 'approved' | 'revoked' | 'stale';

export interface MCPConnectorConfig {
    schema_version: 'mcp-connector-config.v1';
    name: string;
    transport: 'stdio';
    protocol_version: '2025-11-25';
    command: string;
    args: string[];
    cwd: string;
    env: Record<string, string>;
    credential_env: Record<string, string>;
    file_roots: string[];
    network_destinations: string[];
    requested_scopes: string[];
    limits: {
        request_timeout_seconds: number;
        max_message_bytes: number;
        max_stderr_bytes: number;
        max_process_memory_mb: number;
    };
}

export interface MCPServer {
    id: number;
    server_id: string;
    name: string;
    version: string;
    description: string;
    status: 'active' | 'inactive' | 'error';
    protocol_version: string;
    transport: 'stdio';
    enabled: boolean;
    consent_state: MCPConsentState;
    requested_scopes: string[];
    approved_scopes: string[];
    command_fingerprint: string;
    containment_status: string;
    health_status: string;
    last_error_code?: string | null;
    last_error_message?: string | null;
    config_revision: number;
    config: MCPConnectorConfig;
    capabilities?: {
        resources?: boolean;
        tools?: boolean;
        prompts?: boolean;
        logging?: boolean;
    };
    stats?: {
        total_requests?: number;
        successful_requests?: number;
        failed_requests?: number;
    };
}

export interface MCPServerRegistration {
    name: string;
    version: string;
    description: string;
    config: Omit<MCPConnectorConfig, 'schema_version' | 'name'>;
    credentials?: Record<string, string>;
}

export interface MCPLifecycleEvent {
    id: string;
    event_type: string;
    status: string;
    details: Record<string, unknown>;
    created_at: string | null;
}

export interface MCPExecution {
    execution_id: string;
    operation: string;
    status: string;
    result_sha256?: string | null;
    result_size_bytes?: number | null;
    result_trust?: string | null;
    prompt_injection_risk: boolean;
    error_code?: string | null;
    duration_ms?: number | null;
    started_at: string | null;
    completed_at: string | null;
}

export interface MCPTool {
    id: number;
    name: string;
    description: string;
    input_schema?: unknown;
}

export interface MCPResource {
    id: number;
    uri: string;
    name: string;
    mime_type?: string;
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
    [key: string]: unknown;
}

export const mcp = {
    getServers: (): Promise<{ servers: MCPServer[], runtime_servers: MCPRuntimeServer[] }> =>
        request('/mcp/servers'),

    getServer: (serverId: string): Promise<MCPServer> =>
        request<{ server: MCPServer }>(`/mcp/servers/${serverId}`).then((data) => data.server),

    createServer: (data: MCPServerRegistration): Promise<MCPServer> =>
        request<{ server: MCPServer }>('/mcp/servers', {
            method: 'POST',
            body: JSON.stringify(data),
        }).then((response) => response.server),

    approveConsent: (serverId: string, commandFingerprint: string, approvedScopes: string[]): Promise<MCPServer> =>
        request<{ server: MCPServer }>(`/mcp/servers/${serverId}/consent`, {
            method: 'POST',
            body: JSON.stringify({
                command_fingerprint: commandFingerprint,
                approved_scopes: approvedScopes,
            }),
        }).then((response) => response.server),

    revokeConsent: (serverId: string): Promise<MCPServer> =>
        request<{ server: MCPServer }>(`/mcp/servers/${serverId}/consent`, {
            method: 'DELETE',
        }).then((response) => response.server),

    startServer: (serverId: string): Promise<MCPServer> =>
        request<{ server: MCPServer }>(`/mcp/servers/${serverId}/start`, { method: 'POST' })
            .then((response) => response.server),

    stopServer: (serverId: string): Promise<MCPServer> =>
        request<{ server: MCPServer }>(`/mcp/servers/${serverId}/stop`, { method: 'POST' })
            .then((response) => response.server),

    restartServer: (serverId: string): Promise<MCPServer> =>
        request<{ server: MCPServer }>(`/mcp/servers/${serverId}/restart`, { method: 'POST' })
            .then((response) => response.server),

    deleteServer: (serverId: string): Promise<void> =>
        request(`/mcp/servers/${serverId}`, { method: 'DELETE' }),

    getLifecycle: (serverId: string): Promise<MCPLifecycleEvent[]> =>
        request<{ events: MCPLifecycleEvent[] }>(`/mcp/servers/${serverId}/lifecycle`)
            .then((response) => response.events),

    getExecutions: (serverId: string): Promise<MCPExecution[]> =>
        request<{ executions: MCPExecution[] }>(`/mcp/servers/${serverId}/executions`)
            .then((response) => response.executions),

    cancelExecution: (serverId: string, executionId: string): Promise<MCPExecution> =>
        request<{ execution: MCPExecution }>(
            `/mcp/servers/${serverId}/executions/${executionId}/cancel`,
            { method: 'POST' },
        ).then((response) => response.execution),

    getTools: (serverId: string): Promise<MCPTool[]> =>
        request<{ tools: MCPTool[] }>(`/mcp/servers/${serverId}/tools`).then((data) => data.tools),

    getResources: (serverId: string): Promise<MCPResource[]> =>
        request<{ resources: MCPResource[] }>(`/mcp/servers/${serverId}/resources`).then((data) => data.resources),

    getStats: (): Promise<MCPStats> =>
        request<{ stats: MCPStats }>('/mcp/stats').then((data) => data.stats),
};

import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import MCPServersPage from './page';
import { ToastProvider } from '@/components/ui/use-toast';
import { mcp } from '@/lib/api/mcp';

vi.mock('@/lib/api/mcp', () => ({
  mcp: {
    getServers: vi.fn(),
    approveConsent: vi.fn(),
    revokeConsent: vi.fn(),
    startServer: vi.fn(),
    stopServer: vi.fn(),
    restartServer: vi.fn(),
    deleteServer: vi.fn(),
    createServer: vi.fn(),
  },
}));

const server = {
  id: 1,
  server_id: 'server-1',
  name: 'documents',
  version: '1.0.0',
  description: 'Local documents',
  status: 'inactive' as const,
  protocol_version: '2025-11-25',
  transport: 'stdio' as const,
  enabled: false,
  consent_state: 'pending' as const,
  requested_scopes: ['connector:documents:read'],
  approved_scopes: [],
  command_fingerprint: 'a'.repeat(64),
  containment_status: 'windows_job_object_pending_installed_qualification',
  health_status: 'not_started',
  config_revision: 1,
  config: {
    schema_version: 'mcp-connector-config.v1' as const,
    name: 'documents',
    transport: 'stdio' as const,
    protocol_version: '2025-11-25' as const,
    command: 'C:\\Program Files\\Connector\\connector.exe',
    args: ['--stdio'],
    cwd: 'C:\\Data',
    env: {},
    credential_env: { SERVICE_API_KEY: 'service-key' },
    file_roots: ['C:\\Data'],
    network_destinations: [],
    requested_scopes: ['connector:documents:read'],
    limits: {
      request_timeout_seconds: 30,
      max_message_bytes: 65_536,
      max_stderr_bytes: 16_384,
      max_process_memory_mb: 256,
    },
  },
};

describe('managed MCP connectors page', () => {
  beforeEach(() => {
    vi.mocked(mcp.getServers).mockResolvedValue({ servers: [server], runtime_servers: [] });
  });

  it('shows exact authority and qualification truth without exposing credentials', async () => {
    render(<ToastProvider><MCPServersPage /></ToastProvider>);

    await waitFor(() => expect(screen.getByText('documents')).toBeInTheDocument());
    expect(screen.getByText(/connector\.exe.*--stdio/)).toBeInTheDocument();
    expect(screen.getByText('C:\\Data')).toBeInTheDocument();
    expect(screen.getByText(/pending installed qualification/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /review and approve/i })).toBeInTheDocument();
    expect(screen.queryByText('service-key')).not.toBeInTheDocument();
  });
});

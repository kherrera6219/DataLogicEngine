import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ClientGatewayConfig } from './ClientGatewayConfig';

const mocks = vi.hoisted(() => ({
  toast: vi.fn(),
  clientKeys: vi.fn(),
  capabilities: vi.fn(),
  controlPlaneStatus: vi.fn(),
  health: vi.fn(),
  usage: vi.fn(),
  jobs: vi.fn(),
  clientKeyAudit: vi.fn(),
  createClientKey: vi.fn(),
  rotateClientKey: vi.fn(),
  revokeClientKey: vi.fn(),
  expireClientKey: vi.fn(),
  deleteClientKey: vi.fn(),
}));

vi.mock('@/components/ui/use-toast', () => ({ useToast: () => ({ toast: mocks.toast }) }));
vi.mock('@/lib/api', () => ({
  buildApiUrl: (path: string) => `http://localhost:5000/api/v1${path}`,
  GATEWAY_SCOPES: ['chat', 'stream', 'run:create', 'run:read', 'run:cancel', 'models:read'],
  api: {
    gateway: {
      clientKeys: mocks.clientKeys,
      capabilities: mocks.capabilities,
      controlPlaneStatus: mocks.controlPlaneStatus,
      health: mocks.health,
      usage: mocks.usage,
      jobs: mocks.jobs,
      clientKeyAudit: mocks.clientKeyAudit,
      createClientKey: mocks.createClientKey,
      rotateClientKey: mocks.rotateClientKey,
      revokeClientKey: mocks.revokeClientKey,
      expireClientKey: mocks.expireClientKey,
      deleteClientKey: mocks.deleteClientKey,
    },
  },
}));

beforeEach(() => {
  Object.values(mocks).forEach((mock) => mock.mockReset());
  mocks.clientKeys.mockResolvedValue({ api_keys: [] });
  mocks.capabilities.mockResolvedValue({
    contract_version: 'dle-gateway.v1',
    profile: 'desktop_loopback',
    provider_credentials_exposed: false,
    scopes: [],
    virtual_models: {
      'dle-standard': { mode: 'standard', max_provider_calls: 1, description: 'Governed standard route' },
    },
  });
  mocks.controlPlaneStatus.mockResolvedValue({
    gateway_contract_version: 'dle-gateway.v1',
    profile: 'desktop_loopback',
    bind_addresses: ['127.0.0.1', '::1'],
    private_gateway_enabled: false,
    private_gateway_qualified: false,
    tls: { state: 'not_applicable_loopback', certificate: null },
    mtls: { state: 'disabled' },
    firewall: { state: 'no_private_rule' },
    cors: { state: 'disabled_by_default' },
    dependencies: { redis: { state: 'ready', required: true } },
  });
  mocks.health.mockResolvedValue({ status: 'healthy' });
  mocks.usage.mockResolvedValue({ monthly: { calls: 3, tokens_in: 20, tokens_out: 10 } });
  mocks.jobs.mockResolvedValue({ jobs: [] });
  mocks.clientKeyAudit.mockResolvedValue({ events: [] });
  mocks.createClientKey.mockResolvedValue({
    id: 'key-1',
    name: 'Business app',
    key_prefix: 'ukg_12345678',
    api_key: 'ukg_12345678_copy_once_secret',
    warning: 'Save this API key',
    is_active: true,
    scopes: ['chat'],
  });
  mocks.rotateClientKey.mockResolvedValue({
    id: 'key-1',
    name: 'Business app',
    key_prefix: 'ukg_rotated',
    api_key: 'ukg_rotated_secret',
    warning: 'Save this API key',
    is_active: true,
    scopes: ['chat'],
  });
  mocks.revokeClientKey.mockResolvedValue({});
  mocks.expireClientKey.mockResolvedValue({});
  mocks.deleteClientKey.mockResolvedValue({});
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('ClientGatewayConfig', () => {
  it('separates inbound client access and keeps private mode disabled', async () => {
    render(<ClientGatewayConfig />);
    expect(await screen.findByText('Client Gateway')).toBeInTheDocument();
    expect(screen.getByText(/Provider keys stay in Provider Connections/i)).toBeInTheDocument();
    expect(await screen.findByText('desktop loopback')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Private gateway not qualified' })).toBeDisabled();
  });

  it('creates a bounded client and exposes its secret once', async () => {
    render(<ClientGatewayConfig />);
    fireEvent.click(await screen.findByRole('tab', { name: 'Clients' }));
    fireEvent.change(screen.getByLabelText('Client name'), { target: { value: 'Business app' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create client' }));

    await waitFor(() => {
      expect(mocks.createClientKey).toHaveBeenCalledWith(expect.objectContaining({
        name: 'Business app',
        rate_limit_rpm: 60,
        max_concurrent_requests: 2,
      }));
      expect(screen.getByText('ukg_12345678_copy_once_secret')).toBeInTheDocument();
      expect(screen.getByText(/only time the full key is available/i)).toBeInTheDocument();
    });
  });

  it('validates client input and exercises policy controls', async () => {
    render(<ClientGatewayConfig />);
    fireEvent.click(await screen.findByRole('tab', { name: 'Clients' }));
    fireEvent.click(screen.getByRole('button', { name: 'Create client' }));
    expect(mocks.toast).toHaveBeenCalledWith(
      'Enter a client name and select at least one permission.',
      'warning',
    );

    fireEvent.click(screen.getByRole('tab', { name: 'Policies' }));
    fireEvent.change(screen.getByLabelText('Requests per minute'), { target: { value: '75' } });
    fireEvent.change(screen.getByLabelText('Requests per day'), { target: { value: '1500' } });
    fireEvent.change(screen.getByLabelText('Tokens per request'), { target: { value: '8192' } });
    fireEvent.change(screen.getByLabelText('Concurrent requests'), { target: { value: '4' } });
    fireEvent.click(screen.getByRole('checkbox', { name: 'stream' }));

    fireEvent.click(screen.getByRole('tab', { name: 'Clients' }));
    fireEvent.change(screen.getByLabelText('Client name'), { target: { value: '  Policy app  ' } });
    fireEvent.change(screen.getByLabelText('Expires after days'), { target: { value: '30' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create client' }));

    await waitFor(() => expect(mocks.createClientKey).toHaveBeenCalledWith({
      name: 'Policy app',
      scopes: ['chat', 'run:create', 'run:read', 'run:cancel', 'models:read'],
      rate_limit_rpm: 75,
      rate_limit_daily: 1500,
      max_tokens_per_request: 8192,
      max_concurrent_requests: 4,
      expires_in_days: 30,
    }));
  });

  it('renders populated gateway views and copy-once controls', async () => {
    mocks.clientKeys.mockResolvedValue({ api_keys: [{
      id: 'key-active', name: 'Active app', key_prefix: 'ukg_active', scopes: ['chat'],
      is_active: true, total_requests: 7, last_used_at: null, expires_at: 'invalid-date',
    }] });
    mocks.capabilities.mockResolvedValue({
      profile: '',
      virtual_models: {
        'dle-standard': { mode: 'standard', max_provider_calls: 0, description: '' },
        'dle-deep': { mode: 'deep', max_provider_calls: null, description: 'Deep governed route' },
      },
    });
    mocks.controlPlaneStatus.mockResolvedValue({
      profile: 'private_network', bind_addresses: ['10.0.0.5'],
      tls: { state: 'ready' }, firewall: { state: 'ready' },
      dependencies: { redis: { state: 'ready' }, database: { state: 'degraded' } },
    });
    mocks.health.mockResolvedValue({ status: 'degraded_mode' });
    mocks.usage.mockResolvedValue({ monthly: { calls: 9, tokens_in: 40, tokens_out: 22 } });
    mocks.jobs.mockResolvedValue({ jobs: [{ id: 'job-1' }] });
    mocks.clientKeyAudit.mockResolvedValue({ events: [{
      id: 'event-1', action: 'client_key_created', timestamp: '2026-08-16T12:00:00Z',
    }] });

    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
    });

    render(<ClientGatewayConfig />);
    expect(await screen.findByText('private network')).toBeInTheDocument();
    expect(screen.getByText('10.0.0.5')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('tab', { name: 'Clients' }));
    expect(screen.getByText('Active app')).toBeInTheDocument();
    expect(screen.getByText(/Last used: Never/)).toBeInTheDocument();
    expect(screen.getByText(/Expires: Unknown/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Client name'), { target: { value: 'Copy app' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create client' }));
    expect(await screen.findByText('ukg_12345678_copy_once_secret')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Copy key' }));
    await waitFor(() => expect(navigator.clipboard.writeText).toHaveBeenCalledWith('ukg_12345678_copy_once_secret'));
    fireEvent.click(screen.getByRole('button', { name: 'I saved it' }));

    fireEvent.click(screen.getByRole('tab', { name: 'Virtual Models & Routing' }));
    expect(screen.getByText('Server-owned governed route')).toBeInTheDocument();
    expect(screen.getByText(/Provider-call ceiling: Unknown/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('tab', { name: 'Usage' }));
    expect(screen.getByText('9')).toBeInTheDocument();
    expect(screen.getByText(/1 recent jobs/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('tab', { name: 'Audit' }));
    expect(screen.getByText('client key created')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('tab', { name: 'Health' }));
    expect(screen.getByText(/Gateway health: degraded mode/)).toBeInTheDocument();
    expect(screen.getByText('database')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('tab', { name: 'Examples' }));
    expect(screen.getByText(/Invoke-RestMethod/)).toBeInTheDocument();
  });

  it('runs every confirmed client-key lifecycle action and honors cancellation', async () => {
    mocks.clientKeys.mockResolvedValue({ api_keys: [
      { id: 'active', name: 'Active app', key_prefix: 'ukg_active', scopes: ['chat'], is_active: true, total_requests: 0, last_used_at: '2026-08-16T12:00:00Z', expires_at: null },
      { id: 'inactive', name: 'Inactive app', key_prefix: 'ukg_inactive', scopes: [], is_active: false, total_requests: 2, last_used_at: null, expires_at: null },
    ] });
    const confirm = vi.spyOn(window, 'confirm')
      .mockReturnValueOnce(false)
      .mockReturnValue(true);

    render(<ClientGatewayConfig />);
    fireEvent.click(await screen.findByRole('tab', { name: 'Clients' }));
    const [rotate] = await screen.findAllByRole('button', { name: 'Rotate' });
    fireEvent.click(rotate);
    expect(mocks.rotateClientKey).not.toHaveBeenCalled();
    fireEvent.click(rotate);
    await waitFor(() => expect(mocks.rotateClientKey).toHaveBeenCalledWith('active', 300));
    fireEvent.click(screen.getByRole('button', { name: 'I saved it' }));
    fireEvent.click(screen.getAllByRole('button', { name: 'Expire' })[0]);
    await waitFor(() => expect(mocks.expireClientKey).toHaveBeenCalledWith('active', 'owner_expired_from_desktop'));
    fireEvent.click(screen.getAllByRole('button', { name: 'Revoke' })[0]);
    await waitFor(() => expect(mocks.revokeClientKey).toHaveBeenCalledWith('active', 'owner_revoked_from_desktop'));
    fireEvent.click(screen.getAllByRole('button', { name: 'Delete material' })[1]);
    await waitFor(() => expect(mocks.deleteClientKey).toHaveBeenCalledWith('inactive'));
    confirm.mockRestore();
  });

  it('reports refresh, create, and lifecycle failures', async () => {
    mocks.clientKeys.mockRejectedValueOnce('offline');
    render(<ClientGatewayConfig />);
    await waitFor(() => expect(mocks.toast).toHaveBeenCalledWith(
      'Client Gateway could not be loaded: offline',
      'error',
    ));

    mocks.clientKeys.mockResolvedValue({ api_keys: [{
      id: 'key-1', name: 'Failure app', key_prefix: 'ukg_failure', scopes: ['chat'],
      is_active: true, total_requests: 0, last_used_at: null, expires_at: null,
    }] });
    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));
    fireEvent.click(await screen.findByRole('tab', { name: 'Clients' }));
    mocks.createClientKey.mockRejectedValueOnce(new Error('create denied'));
    fireEvent.change(screen.getByLabelText('Client name'), { target: { value: 'Failure app' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create client' }));
    await waitFor(() => expect(mocks.toast).toHaveBeenCalledWith(
      'Client could not be created: create denied',
      'error',
    ));

    vi.spyOn(window, 'confirm').mockReturnValue(true);
    mocks.rotateClientKey.mockRejectedValueOnce('rotation denied');
    fireEvent.click((await screen.findAllByRole('button', { name: 'Rotate' }))[0]);
    await waitFor(() => expect(mocks.toast).toHaveBeenCalledWith(
      'Client key action failed: rotation denied',
      'error',
    ));
  });
});

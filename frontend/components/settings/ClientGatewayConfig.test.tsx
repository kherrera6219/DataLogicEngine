import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ClientGatewayConfig } from './ClientGatewayConfig';

const mocks = vi.hoisted(() => ({
  toast: vi.fn(),
  createClientKey: vi.fn(),
}));

vi.mock('@/components/ui/use-toast', () => ({ useToast: () => ({ toast: mocks.toast }) }));
vi.mock('@/lib/api', () => ({
  buildApiUrl: (path: string) => `http://localhost:5000/api/v1${path}`,
  GATEWAY_SCOPES: ['chat', 'stream', 'run:create', 'run:read', 'run:cancel', 'models:read'],
  api: {
    gateway: {
      clientKeys: vi.fn(async () => ({ api_keys: [] })),
      capabilities: vi.fn(async () => ({
        contract_version: 'dle-gateway.v1',
        profile: 'desktop_loopback',
        provider_credentials_exposed: false,
        scopes: [],
        virtual_models: {
          'dle-standard': { mode: 'standard', max_provider_calls: 1, description: 'Governed standard route' },
        },
      })),
      controlPlaneStatus: vi.fn(async () => ({
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
      })),
      health: vi.fn(async () => ({ status: 'healthy' })),
      usage: vi.fn(async () => ({ month: { calls: 3, tokens_in: 20, tokens_out: 10 } })),
      jobs: vi.fn(async () => ({ jobs: [] })),
      clientKeyAudit: vi.fn(async () => ({ events: [] })),
      createClientKey: mocks.createClientKey,
      rotateClientKey: vi.fn(),
      revokeClientKey: vi.fn(),
      expireClientKey: vi.fn(),
      deleteClientKey: vi.fn(),
    },
  },
}));

beforeEach(() => {
  mocks.toast.mockReset();
  mocks.createClientKey.mockReset();
  mocks.createClientKey.mockResolvedValue({
    id: 'key-1',
    name: 'Business app',
    key_prefix: 'ukg_12345678',
    api_key: 'ukg_12345678_copy_once_secret',
    warning: 'Save this API key',
    is_active: true,
    scopes: ['chat'],
  });
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
});

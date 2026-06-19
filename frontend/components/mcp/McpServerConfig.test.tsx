import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { McpServerConfig } from './McpServerConfig';

// Mock Lucide icons
vi.mock('lucide-react', async (importOriginal) => {
  const actual = await importOriginal<typeof import('lucide-react')>();
  return {
    ...actual,
    Settings: () => <span data-testid="icon-settings" />,
    Terminal: () => <span data-testid="icon-terminal" />,
  };
});

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async () => ({
    ok: true,
    json: async () => ({
      servers: [
        { id: 1, server_id: 'ukg-prod', name: 'UKG Production', version: '1.0.0', description: 'Primary', status: 'active' }
      ]
    })
  })));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('McpServerConfig', () => {
  it('should render server list', async () => {
    render(<McpServerConfig />);
    expect(screen.getByText('MCP Server Configuration')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('UKG Production (ukg-prod)')).toBeInTheDocument();
    });
  });

  it('should expose labeled inventory controls', async () => {
    render(<McpServerConfig />);

    expect(screen.getByRole('button', { name: 'Refresh MCP server inventory' })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole('combobox', { name: 'Server' })).toBeInTheDocument();
    });
  });
});

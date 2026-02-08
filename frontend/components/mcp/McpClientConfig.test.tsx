import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { McpClientConfig } from './McpClientConfig';

// Mock UI components
vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardContent: ({ children }: { children: React.ReactNode }) => <div data-testid="card-content">{children}</div>
}));

vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ open, children }: { open: boolean; children: React.ReactNode }) => open ? <div>{children}</div> : null,
  DialogContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogFooter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/ui/select', () => ({
  Select: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SelectItem: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url =
      typeof input === 'string'
        ? input
        : input instanceof URL
          ? input.toString()
          : (input as Request).url;
    if (url.includes('/mcp/servers') && !url.includes('/tools')) {
      return {
        ok: true,
        json: async () => ({
          servers: [
            { id: 1, server_id: 'ukg-prod', name: 'UKG Production', version: '1.0.0', description: 'Primary', status: 'active' }
          ]
        })
      } as Response;
    }
    if (url.includes('/mcp/stats')) {
      return {
        ok: true,
        json: async () => ({
          stats: { total_servers: 1, active_servers: 1, total_tools: 2, active_connections: 1 }
        })
      } as Response;
    }
    if (url.includes('/mcp/servers/ukg-prod/tools')) {
      return {
        ok: true,
        json: async () => ({
          tools: [
            { id: 10, server_id: 1, name: 'query_knowledge', description: 'Query graph', stats: { execution_count: 5 } }
          ]
        })
      } as Response;
    }
    return {
      ok: true,
      json: async () => ({})
    } as Response;
  }));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('McpClientConfig', () => {
  it('should render client configuration header', async () => {
    render(<McpClientConfig />);
    expect(screen.getByText('MCP Client Configuration')).toBeInTheDocument();
    await screen.findAllByText(/UKG Production/i);
  });

  it('should list live servers from API response', async () => {
    render(<McpClientConfig />);
    const matches = await screen.findAllByText(/UKG Production/i);
    expect(matches.length).toBeGreaterThan(0);
  });

  it('should open add server dialog', async () => {
    render(<McpClientConfig />);
    await screen.findAllByText(/UKG Production/i);
    const addButton = screen.getByText('Add New Server Connection');
    fireEvent.click(addButton);
    expect(screen.getByText('Add New MCP Server Connection')).toBeInTheDocument();
  });
});

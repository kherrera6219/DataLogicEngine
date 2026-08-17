import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

  it('renders live tools, resources, prompts, and tool details', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith('/tools')) return {
        ok: true,
        json: async () => ({ tools: [
          {
            id: 1, name: 'lookup_record', description: 'Looks up a record',
            input_schema: { type: 'object' },
            stats: { execution_count: 4, success_count: 3, failure_count: 1 },
            last_executed: '2026-08-16T10:00:00Z',
          },
          { id: 2, name: 'empty_stats', description: 'No executions' },
        ] }),
      };
      if (url.endsWith('/resources')) return {
        ok: true,
        json: async () => ({ resources: [
          { id: 1, name: 'records', description: '', uri: 'dle://records' },
        ] }),
      };
      if (url.endsWith('/prompts')) return {
        ok: true,
        json: async () => ({ prompts: [
          { id: 1, name: 'review', description: '', arguments: [{ name: 'topic' }, {}] },
          { id: 2, name: 'empty_prompt' },
        ] }),
      };
      return {
        ok: true,
        json: async () => ({ servers: [
          { id: 1, server_id: 'ukg-prod', name: 'UKG Production', version: '1.0.0', description: 'Primary', status: 'active' },
          { id: 2, server_id: 'ukg-idle', name: 'UKG Idle', version: '0.9.0', description: '', status: 'inactive' },
        ] }),
      };
    }));

    render(<McpServerConfig />);
    expect(await screen.findByText('lookup_record')).toBeInTheDocument();
    expect(screen.getByText('exec: 4')).toBeInTheDocument();
    expect(screen.getAllByText('No description available.')).toHaveLength(3);
    expect(screen.getByText('topic')).toBeInTheDocument();
    expect(screen.getByText('arg_2')).toBeInTheDocument();
    expect(screen.getByText('No prompt arguments defined.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Inspect tool lookup_record' }));
    expect(await screen.findByText(/"type": "object"/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Close tool details' }));

    fireEvent.change(screen.getByRole('combobox', { name: 'Server' }), { target: { value: 'ukg-idle' } });
    expect(await screen.findByText('inactive')).toBeInTheDocument();
    expect(screen.getByText('No description provided for this MCP server.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Refresh MCP server inventory' }));
    await waitFor(() => expect(fetch).toHaveBeenCalled());
  });

  it('renders an empty inventory when the server response omits its list', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, json: async () => ({}) })));
    render(<McpServerConfig />);
    expect(await screen.findByText('No server found')).toBeInTheDocument();
    expect(screen.getByText('Unknown')).toBeInTheDocument();
    expect(screen.getByText('No tools registered for this server.')).toBeInTheDocument();
    expect(screen.getByText('No resources found.')).toBeInTheDocument();
    expect(screen.getByText('No prompts found.')).toBeInTheDocument();
  });

  it('reports server and detail loading failures', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw 'server unavailable'; }));
    const view = render(<McpServerConfig />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Failed to load MCP servers');

    view.unmount();
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith('/mcp/servers')) {
        return {
          ok: true,
          json: async () => ({ servers: [
            { id: 1, server_id: 'broken', name: 'Broken server', version: '1', description: '', status: 'error' },
          ] }),
        };
      }
      throw new Error('detail endpoint unavailable');
    }));
    render(<McpServerConfig />);
    expect(await screen.findByRole('alert')).toHaveTextContent('detail endpoint unavailable');
    expect(screen.getByText('error')).toBeInTheDocument();
  });
});

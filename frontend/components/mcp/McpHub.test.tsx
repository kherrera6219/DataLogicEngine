import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { McpHub } from './McpHub';
import { useRouter } from 'next/navigation';

// Mock useRouter
vi.mock('next/navigation', () => ({
  useRouter: vi.fn(),
}));

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async () => ({
    ok: true,
    json: async () => ({ stats: { total_servers: 2, active_servers: 1, total_tools: 3, active_connections: 1 } })
  })));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('McpHub', () => {
  it('should render correctly', () => {
    (useRouter as any).mockReturnValue({ push: vi.fn() });
    render(<McpHub />);
    expect(screen.getByText('UKG Model Context Protocol (MCP) Hub')).toBeInTheDocument();
    expect(screen.getByText('Active Servers')).toBeInTheDocument();
  });

  it('should navigate on click', () => {
    const push = vi.fn();
    (useRouter as any).mockReturnValue({ push });
    render(<McpHub />);
    
    // Find the "Manage Servers" button
    const manageBtn = screen.getByText('Manage Servers');
    fireEvent.click(manageBtn);
    expect(push).toHaveBeenCalledWith('/mcp?tab=server');
  });
});

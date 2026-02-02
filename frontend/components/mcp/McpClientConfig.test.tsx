import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
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

describe('McpClientConfig', () => {
  it('should render client configuration header', () => {
    render(<McpClientConfig />);
    expect(screen.getByText('MCP Client Configuration')).toBeInTheDocument();
  });

  it('should list mock servers', () => {
    render(<McpClientConfig />);
    // screen.debug(); // Uncomment to debug
    expect(screen.getAllByText(/Google Drive/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Slack/i)[0]).toBeInTheDocument();
  });

  it('should open add server dialog', () => {
    render(<McpClientConfig />);
    const addButton = screen.getByText('Add New Server Connection');
    fireEvent.click(addButton);
    expect(screen.getByText('Add New MCP Server Connection')).toBeInTheDocument();
  });
});

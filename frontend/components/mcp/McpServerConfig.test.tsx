import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { McpServerConfig } from './McpServerConfig';

// Mock Lucide icons
vi.mock('lucide-react', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    Settings: () => <span data-testid="icon-settings" />,
    Terminal: () => <span data-testid="icon-terminal" />,
  };
});

describe('McpServerConfig', () => {
  it('should render server list', () => {
    render(<McpServerConfig />);
    expect(screen.getByText('MCP Server Configuration')).toBeInTheDocument();
    // Assuming static data or empty state
  });
});

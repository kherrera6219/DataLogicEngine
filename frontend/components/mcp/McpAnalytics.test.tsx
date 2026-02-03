import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { McpAnalytics } from './McpAnalytics';
import { api } from '@/lib/api';

// Mock API
vi.mock('@/lib/api', () => ({
  api: {
    analytics: {
      mcp: vi.fn()
    }
  }
}));

// Mock Recharts
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <svg>{children}</svg>,
  AreaChart: ({ children }: { children: React.ReactNode }) => <g>{children}</g>,
  PieChart: ({ children }: { children: React.ReactNode }) => <g>{children}</g>,
  Area: () => <g />,
  Pie: () => <g />,
  Line: () => <g />,
  XAxis: () => <g />,
  YAxis: () => <g />,
  Tooltip: () => <div />,
  Cell: () => <g />,
}));

describe('McpAnalytics', () => {
  it('should render loading state initially', () => {
    vi.mocked(api.analytics.mcp).mockReturnValue(new Promise(() => {})); // Never resolves
    render(<McpAnalytics />);
    // Check for spinner or loading indicator
    // The component renders a spinner div
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('should render dashboard data after fetch', async () => {
    const mockData = {
      time_series: [],
      top_tools: [{ name: 'Test Tool', calls: 100, percent: 10 }],
      server_health: [{ name: 'Server 1', status: 'Healthy', latency: 20 }],
      error_stats: [{ name: 'Error 1', value: 5, color: 'red' }]
    };
    vi.mocked(api.analytics.mcp).mockResolvedValue(mockData as any);

    render(<McpAnalytics />);

    await waitFor(() => {
      expect(screen.getByText('MCP Performance Analytics')).toBeInTheDocument();
      expect(screen.getByText('Top Tools')).toBeInTheDocument();
      expect(screen.getByText('Test Tool')).toBeInTheDocument();
      expect(screen.getByText('Server 1')).toBeInTheDocument();
    });
  });
});

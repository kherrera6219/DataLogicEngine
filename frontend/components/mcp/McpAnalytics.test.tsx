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
vi.mock('recharts', () => {
  const OriginalModule = vi.importActual('recharts');
  return {
    ...OriginalModule,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    AreaChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    PieChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    Area: () => null,
    Pie: () => null,
    Line: () => null,
    XAxis: () => null,
    YAxis: () => null,
    Tooltip: () => null,
    Cell: () => null,
  };
});

describe('McpAnalytics', () => {
  it('should render loading state initially', () => {
    (api.analytics.mcp as any).mockReturnValue(new Promise(() => {})); // Never resolves
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
    (api.analytics.mcp as any).mockResolvedValue(mockData);

    render(<McpAnalytics />);

    await waitFor(() => {
      expect(screen.getByText('MCP Performance Analytics')).toBeInTheDocument();
      expect(screen.getByText('Top Tools')).toBeInTheDocument();
      expect(screen.getByText('Test Tool')).toBeInTheDocument();
      expect(screen.getByText('Server 1')).toBeInTheDocument();
    });
  });
});

import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ComplianceTrendChart } from './ComplianceTrendChart';
import useSWR from 'swr';

// Mock SWR
vi.mock('swr');

// Mock API
vi.mock('@/lib/api', () => ({
  api: {
    analytics: {
      trends: vi.fn()
    }
  }
}));

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <svg>{children}</svg>,
  AreaChart: ({ children }: { children: React.ReactNode }) => <g>{children}</g>,
  Area: () => <g />,
  XAxis: () => <g />,
  YAxis: () => <g />,
  CartesianGrid: () => <g />,
  Tooltip: () => <div />,
}));

// Mock Skeleton
vi.mock('@/components/ui/skeleton', () => ({
  Skeleton: () => <div data-testid="skeleton" />
}));

describe('ComplianceTrendChart', () => {
  it('should render loading skeleton initially', () => {
    (useSWR as any).mockReturnValue({
      data: undefined,
      isLoading: true
    });
    render(<ComplianceTrendChart />);
    expect(screen.getByTestId('skeleton')).toBeInTheDocument();
  });

  it('should render chart when data loads', () => {
    vi.mocked(useSWR).mockReturnValue({
      data: { data: { data_points: [{ date: '2023-01-01', value: 10 }] } },
      error: undefined,
      mutate: vi.fn(),
      isValidating: false,
      isLoading: false
    });
    render(<ComplianceTrendChart />);
    expect(screen.getByText('Compliance & Intelligence Trends')).toBeInTheDocument();
    expect(screen.getByText('Sessions')).toBeInTheDocument();
  });
});

import React from 'react';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import ToolExecutionHistoryPage from './page';

const { requestMock } = vi.hoisted(() => ({
  requestMock: vi.fn(),
}));

vi.mock('@/lib/api', () => ({
  request: requestMock,
}));

vi.mock('next/link', () => ({
  default: ({ href, children, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

describe('ToolExecutionHistoryPage', () => {
  beforeEach(() => {
    requestMock.mockReset();
  });

  it('renders nullable persisted KA execution fields without invalid date output', async () => {
    requestMock.mockResolvedValueOnce({
      executions: [
        {
          id: '1',
          ka_id: 'ka-001',
          ka_name: '',
          risk_tier: 'destructive',
          status: 'failure',
          triggered_by: '',
          run_id: null,
          duration_ms: null,
          created_at: null,
          error: 'boom',
        },
      ],
    });

    render(<ToolExecutionHistoryPage />);

    expect(await screen.findAllByText('ka-001')).toHaveLength(2);
    expect(screen.getByText('Unknown time')).toBeInTheDocument();
    expect(screen.getByText('by user')).toBeInTheDocument();
    expect(screen.getByText('boom')).toBeInTheDocument();
    expect(screen.queryByText('Invalid Date')).not.toBeInTheDocument();
    expect(screen.queryByText(/View trace run/i)).not.toBeInTheDocument();
  });

  it('links to a trace run only when the backend provides a trace run id', async () => {
    requestMock.mockResolvedValueOnce({
      executions: [
        {
          id: '2',
          ka_id: 'ka-002',
          ka_name: 'Trace-backed KA',
          risk_tier: 'read_only',
          status: 'success',
          triggered_by: 'user',
          run_id: 'trace-run-1',
          duration_ms: 12,
          created_at: '2026-07-04T08:15:00Z',
          error: null,
        },
      ],
    });

    render(<ToolExecutionHistoryPage />);

    const link = await screen.findByRole('link', { name: /View trace run/i });
    expect(link).toHaveAttribute('href', '/runs/view?id=trace-run-1');
    expect(screen.getByText('12ms')).toBeInTheDocument();
  });
});

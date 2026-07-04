import React from 'react';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import TraceRunsPage from './page';

const { traceListMock } = vi.hoisted(() => ({
  traceListMock: vi.fn(),
}));

vi.mock('@/lib/api', () => ({
  api: {
    trace: {
      list: traceListMock,
    },
  },
}));

vi.mock('next/link', () => ({
  default: ({ href, children, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

describe('TraceRunsPage', () => {
  beforeEach(() => {
    traceListMock.mockReset();
  });

  it('renders nullable trace rows without invalid date output', async () => {
    traceListMock.mockResolvedValueOnce([
      {
        run_id: 'run/one',
        status: 'pass',
        created_at: null,
        ka_id: null,
        model_name: null,
      },
      {
        run_id: '',
        status: null,
        created_at: 'not-a-date',
        ka_id: 'KA-001',
      },
    ]);

    render(<TraceRunsPage />);

    expect(await screen.findByText('run/one')).toBeInTheDocument();
    expect(screen.getAllByText('Unknown time')).toHaveLength(2);
    expect(screen.getByText('pass')).toBeInTheDocument();
    expect(screen.getAllByText('unknown')).toHaveLength(2);
    expect(screen.getAllByText('N/A').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole('link', { name: /View Trace/i })).toHaveAttribute('href', '/runs/view?id=run%2Fone');
    expect(screen.getByRole('button', { name: /Unavailable/i })).toBeDisabled();
    expect(screen.queryByText('Invalid Date')).not.toBeInTheDocument();
  });

  it('surfaces trace list load errors', async () => {
    traceListMock.mockRejectedValueOnce(new Error('offline'));

    render(<TraceRunsPage />);

    expect(await screen.findByText('Trace list is unavailable.')).toBeInTheDocument();
    expect(screen.queryByText('No traces found.')).not.toBeInTheDocument();
  });
});

import React from 'react';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import ToolExecutionHistoryPage from './page';

const { runsMock } = vi.hoisted(() => ({
  runsMock: vi.fn(),
}));

vi.mock('@/lib/api', () => ({
  algorithms: {
    runs: runsMock,
  },
}));

vi.mock('next/link', () => ({
  default: ({ href, children, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

describe('ToolExecutionHistoryPage', () => {
  beforeEach(() => {
    runsMock.mockReset();
  });

  it('renders durable KA failure fields without invalid date output', async () => {
    runsMock.mockResolvedValueOnce({
      runs: [
        {
          schema_version: 'dle.ka-product-run.v1',
          run_id: 'run-1',
          request_id: 'request-1',
          canonical_id: 'KA-001',
          manifest_version: 'test',
          status: 'failed',
          mode: 'production',
          risk_tier: 'destructive',
          confirmation_required: true,
          confirmed: true,
          cancellation_requested: false,
          result_size_bytes: null,
          error_code: 'KA_RUN_INTERNAL_ERROR',
          error_message: 'boom',
          created_at: '',
          updated_at: '',
          started_at: null,
          completed_at: null,
          expires_at: '',
        },
      ],
    });

    render(<ToolExecutionHistoryPage />);

    expect(await screen.findByText('KA-001')).toBeInTheDocument();
    expect(screen.getByText('Unknown time')).toBeInTheDocument();
    expect(screen.getByText('boom')).toBeInTheDocument();
    expect(screen.getByText('confirmed')).toBeInTheDocument();
    expect(screen.queryByText('Invalid Date')).not.toBeInTheDocument();
  });

  it('links every principal-owned ledger record to the governed run inspector', async () => {
    runsMock.mockResolvedValueOnce({
      runs: [
        {
          schema_version: 'dle.ka-product-run.v1',
          run_id: 'run-2',
          request_id: 'request-2',
          canonical_id: 'KA-002',
          manifest_version: 'test',
          status: 'succeeded',
          mode: 'evaluation',
          risk_tier: 'read_only',
          confirmation_required: false,
          confirmed: false,
          cancellation_requested: false,
          result_size_bytes: 100,
          error_code: null,
          error_message: null,
          created_at: '2026-07-04T08:15:00Z',
          updated_at: '2026-07-04T08:15:00.012Z',
          started_at: '2026-07-04T08:15:00Z',
          completed_at: '2026-07-04T08:15:00.012Z',
          expires_at: '2026-07-05T08:15:00Z',
        },
      ],
    });

    render(<ToolExecutionHistoryPage />);

    const link = await screen.findByRole('link', { name: /Inspect governed run/i });
    expect(link).toHaveAttribute('href', '/algorithms?run=run-2');
    expect(screen.getByText('12ms')).toBeInTheDocument();
  });
});

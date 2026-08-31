import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SWRConfig } from 'swr';
import AnalyticsPage from './page';

const { analyticsMock } = vi.hoisted(() => ({
  analyticsMock: vi.fn(),
}));

vi.mock('@/lib/api', () => ({
  api: {
    trace: {
      analytics: analyticsMock,
    },
  },
}));

function renderPage() {
  return render(
    <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0 }}>
      <AnalyticsPage />
    </SWRConfig>,
  );
}

describe('AnalyticsPage', () => {
  beforeEach(() => {
    analyticsMock.mockReset();
  });

  it('renders observed trace analytics and preserves unmeasured values', async () => {
    analyticsMock.mockResolvedValue({
      scope: 'principal',
      partial: false,
      filters: { days: 30, limit: 50, status: null, mode: null, provider: null },
      summary: {
        run_count: 1,
        status_counts: { completed: 1 },
        confidence: { average: null, measured_runs: 0, status: 'not_measured' },
        tokens: { total: null, measured_runs: 0, status: 'not_measured' },
        evidence: { total: 2, status: 'measured' },
        refinement: { recorded_runs: 1, status_counts: { not_needed: 1 }, status: 'measured' },
      },
      runs: [
        {
          run_id: 'run/1',
          created_at: '2026-08-30T20:00:00+00:00',
          completed_at: '2026-08-30T20:00:02+00:00',
          status: 'completed',
          mode: 'governed',
          provider: 'google',
          model: 'gemini-3.7-flash',
          confidence: null,
          confidence_status: 'not_measured',
          token_cost: null,
          token_status: 'not_measured',
          evidence_count: 2,
          refinement: { status: 'not_needed', measurement_status: 'measured', reason: 'confidence_sufficient' },
          detail_url: '/runs/view?trace=run%2F1',
        },
      ],
    });

    renderPage();

    expect(await screen.findByText('Observed governed runs')).toBeInTheDocument();
    expect(screen.getAllByText('Not measured').length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText('2 evidence links')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Open trace/i })).toHaveAttribute(
      'href',
      '/runs/view?trace=run%2F1',
    );
  });

  it('distinguishes empty analytics from unavailable authority', async () => {
    analyticsMock.mockResolvedValueOnce({
      scope: 'principal',
      partial: false,
      filters: { days: 30, limit: 50, status: null, mode: null, provider: null },
      summary: {
        run_count: 0,
        status_counts: {},
        confidence: { average: null, measured_runs: 0, status: 'not_measured' },
        tokens: { total: null, measured_runs: 0, status: 'not_measured' },
        evidence: { total: 0, status: 'measured' },
        refinement: { recorded_runs: 0, status_counts: {}, status: 'not_measured' },
      },
      runs: [],
    });

    const { unmount } = renderPage();
    expect(await screen.findByText('No governed runs match these filters.')).toBeInTheDocument();
    unmount();

    analyticsMock.mockRejectedValueOnce(new Error('trace authority unavailable'));
    renderPage();
    expect(await screen.findByText(/Analytics authority is unavailable/i)).toBeInTheDocument();
    expect(screen.queryByText('0%')).not.toBeInTheDocument();
  });

  it('requests the selected bounded filters', async () => {
    analyticsMock.mockResolvedValue({
      scope: 'principal',
      partial: false,
      filters: { days: 30, limit: 50, status: null, mode: null, provider: null },
      summary: {
        run_count: 0,
        status_counts: {},
        confidence: { average: null, measured_runs: 0, status: 'not_measured' },
        tokens: { total: null, measured_runs: 0, status: 'not_measured' },
        evidence: { total: 0, status: 'measured' },
        refinement: { recorded_runs: 0, status_counts: {}, status: 'not_measured' },
      },
      runs: [],
    });
    renderPage();

    fireEvent.change(screen.getByLabelText('Time range'), { target: { value: '7' } });
    fireEvent.change(screen.getByLabelText('Run status'), { target: { value: 'failed' } });
    fireEvent.change(screen.getByLabelText('Execution mode'), { target: { value: 'governed' } });
    fireEvent.change(screen.getByLabelText('Provider'), { target: { value: 'google' } });
    fireEvent.change(screen.getByLabelText('Visibility'), { target: { value: 'all' } });

    await waitFor(() => expect(analyticsMock).toHaveBeenLastCalledWith({
      days: 7,
      limit: 50,
      status: 'failed',
      mode: 'governed',
      provider: 'google',
      scope: 'all',
    }));
  });
});

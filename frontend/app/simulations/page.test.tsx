import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import SimulationsPage from './page';

const {
  listMock,
  runMock,
  pauseMock,
  resumeMock,
  retryMock,
  cancelMock,
  subscribeMock,
} = vi.hoisted(() => ({
  listMock: vi.fn(),
  runMock: vi.fn(),
  pauseMock: vi.fn(),
  resumeMock: vi.fn(),
  retryMock: vi.fn(),
  cancelMock: vi.fn(),
  subscribeMock: vi.fn(),
}));

vi.mock('@/lib/api', () => ({
  api: {
    simulation: {
      list: listMock,
      get: vi.fn(),
      preflight: vi.fn(),
      create: vi.fn(),
      run: runMock,
      pause: pauseMock,
      resume: resumeMock,
      retry: retryMock,
      cancel: cancelMock,
      events: vi.fn(),
    },
  },
}));

vi.mock('@/lib/socket', () => ({
  useSocket: () => ({
    subscribeToSimulation: subscribeMock,
  }),
}));

describe('SimulationsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    runMock.mockResolvedValue({});
    pauseMock.mockResolvedValue({});
    resumeMock.mockResolvedValue({});
    retryMock.mockResolvedValue({});
    cancelMock.mockResolvedValue({});
    listMock.mockResolvedValue([
      {
        session_id: 'draft-id',
        name: 'Draft scenario',
        status: 'draft',
        current_step: 0,
        total_steps: 4,
        user_id: 1,
        created_at: '2026-07-14T12:00:00Z',
        plan: { max_provider_calls: 4 },
      },
      {
        session_id: 'running-id',
        name: 'Running scenario',
        status: 'running',
        current_step: 2,
        total_steps: 5,
        user_id: 1,
        created_at: '2026-07-14T12:00:00Z',
        plan: { max_provider_calls: 5 },
      },
      {
        session_id: 'failed-id',
        name: 'Failed scenario',
        status: 'failed',
        current_step: 1,
        total_steps: 5,
        user_id: 1,
        created_at: '2026-07-14T12:00:00Z',
        plan: { max_provider_calls: 5 },
      },
      {
        session_id: 'complete-id',
        name: 'Completed scenario',
        status: 'completed',
        current_step: 4,
        total_steps: 4,
        user_id: 1,
        created_at: '2026-07-14T12:00:00Z',
        plan: { max_provider_calls: 4 },
        results: {
          final_conclusion: 'Qualification result',
          confidence_score: null,
          validation: {
            status: 'qualification_only',
            confidence_measured: false,
            validators: [],
          },
        },
      },
    ]);
  });

  it('shows truthful lifecycle controls, progress, and unmeasured confidence', async () => {
    render(<SimulationsPage />);

    expect(await screen.findByText('Draft scenario')).toBeInTheDocument();
    expect(screen.getByText('2/5')).toBeInTheDocument();
    expect(screen.getByText(/Confidence: Not measured/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Run simulation' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Pause simulation' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Retry simulation' })).toBeEnabled();

    fireEvent.click(screen.getByRole('button', { name: 'Run simulation' }));
    await waitFor(() => expect(runMock).toHaveBeenCalledWith('draft-id'));
  });
});

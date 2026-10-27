import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import TruthEnginePage from './page';

const { list } = vi.hoisted(() => ({ list: vi.fn() }));
vi.mock('@/lib/api', () => ({ api: { trace: { list } } }));

describe('Truth Engine summaries', () => {
  beforeEach(() => list.mockReset());

  it('distinguishes unmeasured data from a measured zero', async () => {
    list.mockResolvedValue([]);
    const view = render(<TruthEnginePage />);
    expect(await screen.findByText('No trace runs available yet.')).toBeInTheDocument();
    expect(screen.getAllByText('Not measured')).toHaveLength(2);
    view.unmount();
    list.mockResolvedValue([
      { run_id: 'one', status: 'completed', scores: { confidence: 0 } },
      { run_id: 'two', status: 'failed', scores: { confidence: NaN } },
    ]);
    render(<TruthEnginePage />);
    expect(await screen.findByText('1 measured of 2 recent runs')).toBeInTheDocument();
    expect(screen.getAllByText('0.0%').length).toBeGreaterThan(0);
    expect(screen.getByText('50.0%')).toBeInTheDocument();
    expect(screen.queryByText('NaN%')).not.toBeInTheDocument();
  });

  it('distinguishes failed loading from empty history', async () => {
    list.mockRejectedValueOnce(new Error('trace unavailable'));
    render(<TruthEnginePage />);
    await waitFor(() => expect(screen.getAllByText('Unavailable')).toHaveLength(3));
    expect(screen.getByText('trace unavailable')).toBeInTheDocument();
    expect(screen.queryByText('No trace runs available yet.')).not.toBeInTheDocument();
  });
});

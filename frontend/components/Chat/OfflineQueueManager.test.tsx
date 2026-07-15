import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ToastProvider } from '@/components/ui/use-toast';
import { request } from '@/lib/api';
import { OfflineQueueManager } from './OfflineQueueManager';

vi.mock('@/lib/api', () => ({ request: vi.fn() }));

const pendingQueue = {
  items: [
    {
      id: 'queue-item-12345678',
      status: 'pending',
      failure_class: 'network',
      created_at: '2026-07-14T10:00:00Z',
      expires_at: '2026-07-17T10:00:00Z',
      attempts: 0,
      payload_bytes: 128,
      encrypted: true,
    },
  ],
  counts: { pending: 1 },
  snapshot_at: '2026-07-14T10:01:00Z',
};

const emptyQueue = {
  items: [],
  counts: {},
  snapshot_at: '2026-07-14T10:02:00Z',
};

function renderManager() {
  return render(
    <ToastProvider>
      <OfflineQueueManager />
    </ToastProvider>,
  );
}

describe('OfflineQueueManager', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (request as ReturnType<typeof vi.fn>).mockResolvedValue(pendingQueue);
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: vi.fn(() => 'blob:queue-export') });
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: vi.fn() });
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  });

  it('reviews redacted queue metadata and replays pending requests', async () => {
    (request as ReturnType<typeof vi.fn>).mockImplementation((endpoint: string) => {
      if (endpoint === '/gateway/offline-queue/replay') {
        return Promise.resolve({
          replayed: 1,
          results: [{ id: 'queue-item-12345678', status: 'completed' }],
          queue: { ...emptyQueue, counts: { completed: 1 } },
        });
      }
      return Promise.resolve(pendingQueue);
    });

    renderManager();
    fireEvent.click(await screen.findByRole('button', { name: /review offline replay queue, 1 pending/i }));

    expect(await screen.findByText(/queue-item-12345678/)).toBeInTheDocument();
    expect(screen.getByText(/encrypted payload/i)).toBeInTheDocument();
    expect(screen.queryByText(/prompt/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /replay pending/i }));
    await waitFor(() => expect(request).toHaveBeenCalledWith('/gateway/offline-queue/replay', { method: 'POST' }));
    expect((await screen.findAllByText(/replay finished: 1 request completed/i)).length).toBeGreaterThan(0);
  });

  it('exports redacted metadata and clears every queue record through delete APIs', async () => {
    let cleared = false;
    (request as ReturnType<typeof vi.fn>).mockImplementation((endpoint: string) => {
      if (endpoint.startsWith('/gateway/offline-queue/') && endpoint !== '/gateway/offline-queue/replay') {
        cleared = true;
        return Promise.resolve({ deleted: true });
      }
      return Promise.resolve(cleared ? emptyQueue : pendingQueue);
    });

    renderManager();
    fireEvent.click(await screen.findByRole('button', { name: /review offline replay queue, 1 pending/i }));
    await screen.findByText(/queue-item-12345678/);

    fireEvent.click(screen.getByRole('button', { name: /export redacted metadata/i }));
    expect(URL.createObjectURL).toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: /clear queue/i }));
    await waitFor(() => expect(request).toHaveBeenCalledWith(
      '/gateway/offline-queue/queue-item-12345678',
      { method: 'DELETE' },
    ));
    expect(await screen.findByText(/offline replay queue is empty/i)).toBeInTheDocument();
  });

  it('reports queue status as unavailable when metadata cannot be loaded', async () => {
    (request as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Backend unavailable'));

    renderManager();
    fireEvent.click(screen.getByRole('button', { name: /review offline replay queue/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Backend unavailable');
  });
});

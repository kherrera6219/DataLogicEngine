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

  it('renders optional metadata fallbacks and deletes one record', async () => {
    const detailedQueue = {
      items: [
        {
          id: 'second-item-87654321', status: '', created_at: 'not-a-date', expires_at: null,
          encrypted: false, response: { run_id: 'run-22' }, last_error: 'previous failure',
        },
        {
          id: 'first-item-12345678', status: 'failed', failure_class: null,
          created_at: '2026-07-15T10:00:00Z', payload_bytes: 0, attempts: 2,
        },
      ],
      counts: { pending: 2 },
      snapshot_at: 'not-a-date',
    };
    let deleted = false;
    (request as ReturnType<typeof vi.fn>).mockImplementation((endpoint: string) => {
      if (endpoint.includes('second-item-87654321')) {
        deleted = true;
        return Promise.resolve({ deleted: true });
      }
      return Promise.resolve(deleted ? emptyQueue : detailedQueue);
    });

    renderManager();
    fireEvent.click(await screen.findByRole('button', { name: /review offline replay queue, 2 pending/i }));
    expect(await screen.findAllByText(/failure class unavailable/i)).toHaveLength(2);
    expect(screen.getByText(/Encryption state unavailable · Unknown bytes · 0 replay attempts/i)).toBeInTheDocument();
    expect(screen.getByText('Last error: previous failure')).toBeInTheDocument();
    expect(screen.getByText('Run: run-22')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /delete queue record second-i/i }));
    await waitFor(() => expect(request).toHaveBeenCalledWith(
      '/gateway/offline-queue/second-item-87654321',
      { method: 'DELETE' },
    ));
    expect(await screen.findByText(/queue record second-i deleted/i)).toBeInTheDocument();
  });

  it('reports failed replay results and honors replay cancellation', async () => {
    (request as ReturnType<typeof vi.fn>).mockImplementation((endpoint: string) => {
      if (endpoint === '/gateway/offline-queue/replay') {
        return Promise.resolve({
          replayed: 2,
          results: [
            { id: 'one', status: 'completed' },
            { id: 'two', status: 'failed', error: 'still offline' },
          ],
          queue: pendingQueue,
        });
      }
      return Promise.resolve({ ...pendingQueue, counts: { pending: 2 } });
    });
    vi.mocked(window.confirm).mockReturnValueOnce(false).mockReturnValue(true);

    renderManager();
    fireEvent.click(await screen.findByRole('button', { name: /review offline replay queue, 2 pending/i }));
    const replay = screen.getByRole('button', { name: /replay pending/i });
    fireEvent.click(replay);
    expect(request).not.toHaveBeenCalledWith('/gateway/offline-queue/replay', { method: 'POST' });
    fireEvent.click(replay);
    expect((await screen.findAllByText(/1 completed and 1 remain pending or failed/i)).length).toBeGreaterThan(0);
  });

  it('reports invalid replay, delete, and refresh responses', async () => {
    let mode = 'initial';
    (request as ReturnType<typeof vi.fn>).mockImplementation((endpoint: string) => {
      if (endpoint === '/gateway/offline-queue/replay') return Promise.resolve({ replayed: 0, results: [], queue: {} });
      if (endpoint.includes('queue-item-12345678')) return Promise.reject('delete unavailable');
      if (mode === 'invalid-refresh') return Promise.resolve({ items: [] });
      return Promise.resolve(pendingQueue);
    });

    renderManager();
    fireEvent.click(await screen.findByRole('button', { name: /review offline replay queue, 1 pending/i }));
    fireEvent.click(screen.getByRole('button', { name: /replay pending/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Replay response was invalid.');

    fireEvent.click(screen.getByRole('button', { name: /delete queue record queue-it/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Queue record deletion failed.');

    mode = 'invalid-refresh';
    fireEvent.click(screen.getByRole('button', { name: /^refresh$/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Queue status response was invalid.');
  });

  it('reports partial failures while clearing multiple records', async () => {
    const twoItems = {
      ...pendingQueue,
      items: [
        pendingQueue.items[0],
        { ...pendingQueue.items[0], id: 'queue-item-abcdefgh' },
      ],
      counts: { pending: 2 },
    };
    let clearing = false;
    (request as ReturnType<typeof vi.fn>).mockImplementation((endpoint: string) => {
      if (endpoint.includes('queue-item-12345678')) {
        clearing = true;
        return Promise.reject(new Error('locked'));
      }
      if (endpoint.includes('queue-item-abcdefgh')) return Promise.resolve({ deleted: true });
      return Promise.resolve(clearing ? emptyQueue : twoItems);
    });

    renderManager();
    fireEvent.click(await screen.findByRole('button', { name: /review offline replay queue, 2 pending/i }));
    fireEvent.click(screen.getByRole('button', { name: /clear queue/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent('1 queue record could not be deleted.');
  });
});

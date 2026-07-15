'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Archive, Download, Play, RefreshCw, Trash2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useToast } from '@/components/ui/use-toast';
import { request } from '@/lib/api';

type OfflineQueueItem = {
  id: string;
  status: string;
  failure_class?: string | null;
  created_at?: string | null;
  expires_at?: string | null;
  updated_at?: string | null;
  attempts?: number;
  last_error?: string | null;
  payload_bytes?: number;
  encrypted?: boolean;
  response?: {
    run_id?: string | null;
    provider_used?: string | null;
    model_used?: string | null;
  } | null;
};

type OfflineQueueSnapshot = {
  items: OfflineQueueItem[];
  counts: Record<string, number>;
  snapshot_at?: string;
};

type ReplayResponse = {
  replayed: number;
  results: Array<{ id: string; status: string; error?: string }>;
  queue: OfflineQueueSnapshot;
};

function isQueueSnapshot(value: unknown): value is OfflineQueueSnapshot {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as Partial<OfflineQueueSnapshot>;
  return Array.isArray(candidate.items) && Boolean(candidate.counts) && typeof candidate.counts === 'object';
}

function formatDate(value?: string | null): string {
  if (!value) return 'Not recorded';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}

function downloadJson(filename: string, payload: unknown): void {
  const blob = new Blob([`${JSON.stringify(payload, null, 2)}\n`], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function OfflineQueueManager() {
  const { toast } = useToast();
  const [open, setOpen] = useState(false);
  const [snapshot, setSnapshot] = useState<OfflineQueueSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState<'replay' | 'clear' | string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState('');

  const refresh = useCallback(async (announce = false) => {
    setLoading(true);
    setError(null);
    try {
      const result = await request<OfflineQueueSnapshot>('/gateway/offline-queue');
      if (!isQueueSnapshot(result)) throw new Error('Queue status response was invalid.');
      setSnapshot(result);
      if (announce) setAnnouncement('Offline replay queue refreshed.');
    } catch (refreshError) {
      setSnapshot(null);
      setError(refreshError instanceof Error ? refreshError.message : 'Offline replay queue is unavailable.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    void request<OfflineQueueSnapshot>('/gateway/offline-queue')
      .then((result) => {
        if (cancelled) return;
        if (!isQueueSnapshot(result)) throw new Error('Queue status response was invalid.');
        setSnapshot(result);
        setError(null);
      })
      .catch((refreshError: unknown) => {
        if (cancelled) return;
        setSnapshot(null);
        setError(refreshError instanceof Error ? refreshError.message : 'Offline replay queue is unavailable.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const pendingCount = snapshot?.counts.pending ?? 0;
  const itemCount = snapshot?.items.length ?? 0;
  const orderedItems = useMemo(
    () => [...(snapshot?.items ?? [])].sort((left, right) =>
      String(right.created_at ?? '').localeCompare(String(left.created_at ?? '')),
    ),
    [snapshot],
  );

  const handleReplay = async () => {
    if (!pendingCount) return;
    if (!window.confirm(`Replay ${pendingCount} pending request${pendingCount === 1 ? '' : 's'} through current policy and budget checks?`)) return;
    setAction('replay');
    setError(null);
    try {
      const result = await request<ReplayResponse>('/gateway/offline-queue/replay', { method: 'POST' });
      if (!result || !isQueueSnapshot(result.queue)) throw new Error('Replay response was invalid.');
      setSnapshot(result.queue);
      const failed = result.results.filter((item) => item.status !== 'completed').length;
      const message = failed
        ? `Replay finished: ${result.replayed - failed} completed and ${failed} remain pending or failed.`
        : `Replay finished: ${result.replayed} request${result.replayed === 1 ? '' : 's'} completed.`;
      setAnnouncement(message);
      toast(message, failed ? 'warning' : 'success');
    } catch (replayError) {
      const message = replayError instanceof Error ? replayError.message : 'Offline replay failed.';
      setError(message);
      toast(message, 'error');
    } finally {
      setAction(null);
    }
  };

  const handleDelete = async (item: OfflineQueueItem) => {
    if (!window.confirm(`Delete queue record ${item.id.slice(0, 8)}? This cannot be undone.`)) return;
    setAction(item.id);
    setError(null);
    try {
      await request(`/gateway/offline-queue/${encodeURIComponent(item.id)}`, { method: 'DELETE' });
      await refresh();
      setAnnouncement(`Queue record ${item.id.slice(0, 8)} deleted.`);
    } catch (deleteError) {
      const message = deleteError instanceof Error ? deleteError.message : 'Queue record deletion failed.';
      setError(message);
      toast(message, 'error');
    } finally {
      setAction(null);
    }
  };

  const handleClear = async () => {
    if (!snapshot?.items.length) return;
    if (!window.confirm(`Delete all ${snapshot.items.length} offline queue records? This cannot be undone.`)) return;
    setAction('clear');
    setError(null);
    const results = await Promise.allSettled(
      snapshot.items.map((item) => request(`/gateway/offline-queue/${encodeURIComponent(item.id)}`, { method: 'DELETE' })),
    );
    await refresh();
    const failed = results.filter((result) => result.status === 'rejected').length;
    if (failed) {
      const message = `${failed} queue record${failed === 1 ? '' : 's'} could not be deleted.`;
      setError(message);
      toast(message, 'error');
    } else {
      setAnnouncement('Offline replay queue cleared.');
      toast('Offline replay queue cleared.', 'success');
    }
    setAction(null);
  };

  const handleExport = () => {
    if (!snapshot) return;
    downloadJson(`datalogic-offline-queue-${new Date().toISOString().slice(0, 10)}.json`, {
      schema_version: 'offline-queue-export.v1',
      exported_at: new Date().toISOString(),
      content_notice: 'Redacted metadata only. Encrypted request content is not included.',
      queue: snapshot,
    });
    setAnnouncement('Redacted offline queue metadata exported.');
    toast('Redacted offline queue metadata exported.', 'success');
  };

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        className="h-8 gap-2"
        onClick={() => setOpen(true)}
        aria-label={`Review offline replay queue${snapshot ? `, ${pendingCount} pending` : ''}`}
      >
        <Archive className="h-3.5 w-3.5" aria-hidden="true" />
        Replay Queue{snapshot ? ` (${pendingCount})` : ''}
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent size="xl" className="max-h-[88vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Offline Replay Queue</DialogTitle>
            <DialogDescription>
              Review redacted metadata for encrypted transient-failure requests. Replay always re-runs current policy and budget checks.
            </DialogDescription>
          </DialogHeader>

          <div className="sr-only" aria-live="polite">{announcement}</div>
          {error && <p role="alert" className="rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-700 dark:text-red-300">{error}</p>}

          {loading ? (
            <p className="py-8 text-center text-sm text-muted-foreground">Loading encrypted queue metadata...</p>
          ) : snapshot ? (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-3 rounded-md border p-3 text-sm">
                <span><strong>{pendingCount}</strong> pending</span>
                <span><strong>{snapshot.counts.completed ?? 0}</strong> completed</span>
                <span><strong>{snapshot.counts.failed ?? 0}</strong> failed</span>
                <span className="text-muted-foreground">Snapshot: {formatDate(snapshot.snapshot_at)}</span>
              </div>

              {orderedItems.length ? (
                <ul className="space-y-3" aria-label="Offline queue records">
                  {orderedItems.map((item) => (
                    <li key={item.id} className="rounded-md border p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0 space-y-1 text-sm">
                          <p className="font-semibold">{item.status || 'unknown'} · {item.failure_class || 'failure class unavailable'}</p>
                          <p className="font-mono text-xs text-muted-foreground">ID {item.id}</p>
                          <p>Created: {formatDate(item.created_at)} · Expires: {formatDate(item.expires_at)}</p>
                          <p>{item.encrypted ? 'Encrypted payload' : 'Encryption state unavailable'} · {item.payload_bytes ?? 'Unknown'} bytes · {item.attempts ?? 0} replay attempts</p>
                          {item.last_error && <p className="text-red-700 dark:text-red-300">Last error: {item.last_error}</p>}
                          {item.response?.run_id && <p>Run: {item.response.run_id}</p>}
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => void handleDelete(item)}
                          disabled={action !== null}
                          aria-label={`Delete queue record ${item.id.slice(0, 8)}`}
                        >
                          <Trash2 className="h-4 w-4" aria-hidden="true" />
                        </Button>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="rounded-md border border-dashed p-8 text-center text-sm text-muted-foreground">The offline replay queue is empty.</p>
              )}
            </div>
          ) : null}

          <DialogFooter className="flex-wrap gap-2 sm:space-x-0">
            <Button variant="outline" onClick={() => void refresh(true)} disabled={loading || action !== null}>
              <RefreshCw className="mr-2 h-4 w-4" aria-hidden="true" /> Refresh
            </Button>
            <Button variant="outline" onClick={handleExport} disabled={!snapshot || loading || action !== null}>
              <Download className="mr-2 h-4 w-4" aria-hidden="true" /> Export redacted metadata
            </Button>
            <Button variant="destructive" onClick={() => void handleClear()} disabled={!itemCount || loading || action !== null}>
              <Trash2 className="mr-2 h-4 w-4" aria-hidden="true" /> Clear queue
            </Button>
            <Button onClick={() => void handleReplay()} disabled={!pendingCount || loading || action !== null}>
              <Play className="mr-2 h-4 w-4" aria-hidden="true" /> {action === 'replay' ? 'Replaying...' : 'Replay pending'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

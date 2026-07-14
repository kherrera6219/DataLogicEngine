'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { ArchiveRestore, Download, Loader2, RefreshCw, Trash2 } from 'lucide-react';

import { api } from '@/lib/api';
import type { MemoryReviewItem, MemoryStats } from '@/lib/api/memory';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/components/ui/use-toast';

export function MemoryManagementSettings() {
  const { toast } = useToast();
  const [items, setItems] = useState<MemoryReviewItem[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [includeWorking, setIncludeWorking] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.memory.review(includeWorking);
      setItems(result.items || []);
      setStats(result.stats);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Memory review is unavailable.');
    } finally {
      setLoading(false);
    }
  }, [includeWorking]);

  useEffect(() => {
    let cancelled = false;
    void api.memory.review(includeWorking)
      .then((result) => {
        if (cancelled) return;
        setItems(result.items || []);
        setStats(result.stats);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Memory review is unavailable.');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [includeWorking]);

  const exportMemory = async () => {
    const payload = await api.memory.exportGraph();
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'datalogic-memory-export.json';
    link.click();
    URL.revokeObjectURL(url);
    toast('Memory export created.', 'success');
  };

  const deleteMemory = async (item: MemoryReviewItem) => {
    if (!window.confirm('Delete this memory record and its graph edges?')) return;
    await api.memory.remove(item.vertex_id);
    toast('Memory record deleted.', 'success');
    await load();
  };

  const compactMemory = async () => {
    if (!window.confirm('Compact working memory to the newest 500 records? Validated memory is retained.')) return;
    const result = await api.memory.compact(500);
    toast(`Memory compacted: ${result.removed} working records removed.`, 'success');
    await load();
  };

  const recoverMemory = async () => {
    if (!window.confirm('Restore memory from the latest integrity-verified backup?')) return;
    await api.memory.recover();
    toast('Memory recovered from the verified backup.', 'success');
    await load();
  };

  return (
    <Card className="fluent-card">
      <CardHeader>
        <CardTitle>Memory Review and Recovery</CardTitle>
        <CardDescription>Review validated memory, inspect working state, export, delete, compact, or recover the versioned owner memory file.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Switch checked={includeWorking} onCheckedChange={setIncludeWorking} aria-label="Include working memory" />
            <span className="text-sm">Include session-working memory</span>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="outline" onClick={() => void load()} disabled={loading}><RefreshCw className="mr-2 h-3.5 w-3.5" />Refresh</Button>
            <Button size="sm" variant="outline" onClick={() => void exportMemory()}><Download className="mr-2 h-3.5 w-3.5" />Export</Button>
            <Button size="sm" variant="outline" onClick={() => void compactMemory()}><Trash2 className="mr-2 h-3.5 w-3.5" />Compact</Button>
            <Button size="sm" variant="outline" onClick={() => void recoverMemory()}><ArchiveRestore className="mr-2 h-3.5 w-3.5" />Recover</Button>
          </div>
        </div>
        {stats && (
          <div className="flex flex-wrap gap-2 text-xs">
            <Badge variant="outline">{stats.memory_vertices} records</Badge>
            <Badge variant="outline">{stats.memory_edges} edges</Badge>
            <Badge variant="outline">Last recall: {stats.last_recall_timestamp ? new Date(stats.last_recall_timestamp).toLocaleString() : 'never'}</Badge>
          </div>
        )}
        {error && <Alert variant="destructive"><AlertTitle>Memory controls unavailable</AlertTitle><AlertDescription>{error}</AlertDescription></Alert>}
        {loading ? (
          <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />Loading memory records…</div>
        ) : items.length ? items.map((item) => (
          <div key={item.vertex_id} className="rounded-lg border border-slate-200 p-4 dark:border-white/10">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="line-clamp-3 text-sm text-slate-800 dark:text-gray-200">{item.content}</div>
                <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                  <Badge variant="outline">{item.validation_state}</Badge>
                  <span>{item.retention_class || 'retention not recorded'}</span>
                  <span>{item.policy_result || 'policy not recorded'}</span>
                  {item.source_run_id && <Link className="text-blue-600 hover:underline dark:text-blue-400" href={`/runs/view?id=${encodeURIComponent(item.source_run_id)}`}>Source trace</Link>}
                </div>
              </div>
              <Button size="sm" variant="ghost" onClick={() => void deleteMemory(item)} aria-label={`Delete memory ${item.vertex_id}`}><Trash2 className="h-4 w-4" /></Button>
            </div>
          </div>
        )) : (
          <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">No memory records match this review filter.</div>
        )}
      </CardContent>
    </Card>
  );
}

export default MemoryManagementSettings;

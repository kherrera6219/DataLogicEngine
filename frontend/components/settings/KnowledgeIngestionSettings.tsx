'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { DatabaseZap, FileText, FolderOpen, History, Loader2, Pause, Play, RefreshCw, ShieldCheck, Trash2, UploadCloud, Wrench, Zap } from 'lucide-react';
import { api } from '@/lib/api';
import type { IngestionResult, IngestionSupportedTypes } from '@/lib/api/types';
import type { AsyncIngestionStatus } from '@/lib/api/ingestion';
import type { DesktopPathCapability } from '@/types/electron';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/components/ui/use-toast';

function formatBytes(value?: number | null): string {
  if (!value || value < 1) return '0 B';
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatResultSummary(result: IngestionResult): string {
  return `${result.files_ingested} files, ${result.chunks_created} chunks, ${result.chunks_indexed} indexed`;
}

export function KnowledgeIngestionSettings() {
  const { toast } = useToast();
  const [supported, setSupported] = useState<IngestionSupportedTypes | null>(null);
  const [history, setHistory] = useState<IngestionResult[]>([]);
  const [sourceCapability, setSourceCapability] = useState<DesktopPathCapability | null>(null);
  const [sourceLabel, setSourceLabel] = useState('');
  const [recursive, setRecursive] = useState(true);
  const [chunkSize, setChunkSize] = useState(1200);
  const [maxFileMb, setMaxFileMb] = useState(10);
  const [maxTotalMb, setMaxTotalMb] = useState(100);
  const [maxFiles, setMaxFiles] = useState(1000);
  const [maxPages, setMaxPages] = useState(500);
  const [maxArchiveEntries, setMaxArchiveEntries] = useState(10000);
  const [maxExpandedMb, setMaxExpandedMb] = useState(100);
  const [maxArchiveDepth, setMaxArchiveDepth] = useState(1);
  const [parserTimeoutSeconds, setParserTimeoutSeconds] = useState(60);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<IngestionResult | null>(null);
  const [asyncMode, setAsyncMode] = useState(false);
  const [syncNeo4j, setSyncNeo4j] = useState(false);
  const [asyncId, setAsyncId] = useState<string | null>(null);
  const [asyncStatus, setAsyncStatus] = useState<AsyncIngestionStatus | null>(null);
  const [consistency, setConsistency] = useState<{ scanned_jobs: number; consistent_jobs: number; divergence_count: number } | null>(null);
  const [activeOperationId, setActiveOperationId] = useState<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const extensionLabel = useMemo(
    () => supported?.extensions.join(', ') || '.txt, .md, .csv, .json, .yaml, .log',
    [supported?.extensions]
  );

  const loadHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const [supportedTypes, items] = await Promise.all([
        api.ingestion.supported(),
        api.ingestion.history(10),
      ]);
      setSupported(supportedTypes);
      setHistory(items);
      setChunkSize((current) => current || supportedTypes.default_chunk_size);
      setMaxFileMb(Math.max(1, Math.round(supportedTypes.default_max_file_bytes / (1024 * 1024))));
      setMaxTotalMb(Math.max(1, Math.round(supportedTypes.default_max_total_bytes / (1024 * 1024))));
      setMaxFiles(Math.max(1, supportedTypes.default_max_files));
      setMaxPages(Math.max(1, supportedTypes.default_max_pages));
      setMaxArchiveEntries(Math.max(1, supportedTypes.default_max_archive_entries));
      setMaxExpandedMb(Math.max(1, Math.round(supportedTypes.default_max_decompressed_bytes / (1024 * 1024))));
      setMaxArchiveDepth(Math.max(0, supportedTypes.default_max_archive_depth));
      setParserTimeoutSeconds(Math.max(1, supportedTypes.default_parser_timeout_seconds));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load ingestion status.');
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function init() {
      await loadHistory();
      if (cancelled) return;
    }
    void init();
    return () => { cancelled = true; };
  }, [loadHistory]);

  const startIngestion = async () => {
    if (!sourceCapability) {
      setError('Select a local file or folder first.');
      return;
    }

    setRunning(true);
    setError(null);

    const payload = {
      source_capability: sourceCapability.token,
      recursive,
      chunk_size: Math.max(100, chunkSize || 1200),
      max_file_bytes: Math.max(1, maxFileMb || 10) * 1024 * 1024,
      max_total_bytes: Math.max(1, maxTotalMb || 100) * 1024 * 1024,
      max_files: Math.max(1, maxFiles || 1000),
      max_pages: Math.max(1, maxPages || 500),
      max_archive_entries: Math.max(1, maxArchiveEntries || 10000),
      max_decompressed_bytes: Math.max(1, maxExpandedMb || 100) * 1024 * 1024,
      max_archive_depth: Math.max(0, maxArchiveDepth),
      parser_timeout_seconds: Math.max(1, parserTimeoutSeconds || 60),
      source_label: sourceLabel.trim() || undefined,
      async_mode: asyncMode,
      sync_neo4j: syncNeo4j,
      operation_id: crypto.randomUUID(),
    };

    try {
      if (!window.electronAPI?.runLocalIngestion) {
        throw new Error('Local ingestion is available only in the desktop application.');
      }
      const selectedDisplayName = sourceCapability.display_name;
      setSourceCapability(null);
      setActiveOperationId(payload.operation_id);
      const response = await window.electronAPI.runLocalIngestion(payload);
      setActiveOperationId(null);
      if (asyncMode) {
        if (!('status' in response)) {
          throw new Error('Desktop ingestion returned an invalid async response.');
        }
        setAsyncId(response.ingestion_id);
        setAsyncStatus({ status: 'running', source: selectedDisplayName, started_at: new Date().toISOString() });
        toast('Async ingestion started — polling for completion.', 'success');
        // Don't setRunning(false) — the polling effect will handle it.
      } else {
        if ('status' in response) {
          throw new Error('Desktop ingestion returned an invalid synchronous response.');
        }
        const result = response;
        setLastResult(result);
        setHistory((items) => [result, ...items.filter((item) => item.ingestion_id !== result.ingestion_id)].slice(0, 10));
        toast(`Ingestion complete: ${formatResultSummary(result)}`, 'success');
        setRunning(false);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Local ingestion failed.';
      setError(message);
      toast(message, 'error');
      setActiveOperationId(null);
      setRunning(false);
    }
  };

  const cancelIngestion = async () => {
    if (asyncId) {
      const status = await api.ingestion.cancel(asyncId);
      setAsyncStatus(status);
      setRunning(false);
      toast('Ingestion cancellation requested.', 'success');
      return;
    }
    if (activeOperationId && window.electronAPI?.cancelDesktopOperation) {
      const result = await window.electronAPI.cancelDesktopOperation(activeOperationId);
      if (result.cancelled) {
        setActiveOperationId(null);
        toast('Ingestion cancellation requested.', 'success');
      }
    }
  };

  const pauseIngestion = async () => {
    if (!asyncId) return;
    const status = await api.ingestion.pause(asyncId);
    setAsyncStatus(status);
    toast('Ingestion will pause at its next safe checkpoint.', 'success');
  };

  const resumeIngestion = async () => {
    if (!asyncId) return;
    const status = await api.ingestion.resume(asyncId);
    setAsyncStatus(status);
    setRunning(true);
    toast('Ingestion resumed.', 'success');
  };

  const repairIngestion = async (ingestionId: string) => {
    await api.ingestion.repair(ingestionId);
    toast('Failed cross-store writes were requeued where repair was safe.', 'success');
    void loadHistory();
  };

  const retryIngestion = async (ingestionId: string) => {
    await api.ingestion.retry(ingestionId);
    toast('Ingestion retry queued from its retained app staging copy.', 'success');
    void loadHistory();
  };

  const scanConsistency = async () => {
    const report = await api.ingestion.consistency();
    setConsistency(report);
    toast(report.divergence_count ? 'Corpus differences require attention.' : 'Corpus stores are consistent.', report.divergence_count ? 'error' : 'success');
  };

  const deleteIngestion = async (ingestionId: string) => {
    if (!window.confirm('Delete this source revision from PostgreSQL, vector, graph, and object storage?')) return;
    await api.ingestion.remove(ingestionId);
    toast('Cross-store deletion started.', 'success');
    void loadHistory();
  };

  const chooseIngestionSource = async () => {
    setError(null);
    if (!window.electronAPI?.chooseIngestionSource) {
      setError('Local ingestion is available only in the desktop application.');
      return;
    }
    try {
      const selected = await window.electronAPI.chooseIngestionSource();
      if (selected) {
        setSourceCapability(selected);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to select an ingestion source.');
    }
  };

  // Poll async ingestion status.
  useEffect(() => {
    const activeStates = ['queued', 'running', 'materialization_pending', 'deletion_pending'];
    if (!asyncId || !activeStates.includes(asyncStatus?.status || '')) {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
      return;
    }
    pollingRef.current = setInterval(async () => {
      try {
        const status = await api.ingestion.status(asyncId);
        setAsyncStatus(status);
        if (!activeStates.includes(status.status)) {
          setRunning(false);
          if (status.status === 'completed' && status.result) {
            setLastResult(status.result as IngestionResult);
            toast(`Async ingestion complete: ${formatResultSummary(status.result as IngestionResult)}`, 'success');
            void loadHistory();
          } else if (status.status === 'failed') {
            setError(status.error || 'Async ingestion failed.');
          }
        }
      } catch {
        // Polling failure is not fatal; retry on next interval.
      }
    }, 2000);
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [asyncId, asyncStatus?.status, loadHistory, toast]);

  return (
    <div className="space-y-6" aria-busy={running || loadingHistory}>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Card className="fluent-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UploadCloud className="h-5 w-5 text-blue-500" />
              Local Knowledge Ingestion
            </CardTitle>
            <CardDescription>Supported: {extensionLabel}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="ingestion-path">Local path</Label>
              <div className="flex gap-2">
                <Input
                  id="ingestion-path"
                  value={sourceCapability?.display_name || ''}
                  readOnly
                  placeholder="No file or folder selected"
                  disabled={running}
                />
                <Button type="button" variant="outline" onClick={() => void chooseIngestionSource()} disabled={running} aria-label="Choose local ingestion source">
                  Browse
                </Button>
                <Button type="button" variant="outline" onClick={() => setSourceCapability(null)} disabled={running || !sourceCapability} aria-label="Clear local path">
                  Clear
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
              <div className="space-y-2 md:col-span-1">
                <Label htmlFor="source-label">Source label</Label>
                <Input
                  id="source-label"
                  value={sourceLabel}
                  onChange={(event) => setSourceLabel(event.target.value)}
                  placeholder="Compliance corpus"
                  disabled={running}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="chunk-size">Chunk size</Label>
                <Input
                  id="chunk-size"
                  type="number"
                  min={100}
                  step={100}
                  value={chunkSize}
                  onChange={(event) => setChunkSize(Number(event.target.value))}
                  disabled={running}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="max-file-mb">Max file MB</Label>
                <Input
                  id="max-file-mb"
                  type="number"
                  min={1}
                  value={maxFileMb}
                  onChange={(event) => setMaxFileMb(Number(event.target.value))}
                  disabled={running}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="max-total-mb">Max job MB</Label>
                <Input
                  id="max-total-mb"
                  type="number"
                  min={1}
                  value={maxTotalMb}
                  onChange={(event) => setMaxTotalMb(Number(event.target.value))}
                  disabled={running}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="max-files">Max files</Label>
                <Input
                  id="max-files"
                  type="number"
                  min={1}
                  value={maxFiles}
                  onChange={(event) => setMaxFiles(Number(event.target.value))}
                  disabled={running}
                />
              </div>
            </div>

            <div className="space-y-3 rounded-xl border border-slate-200 bg-white/60 p-4 dark:border-white/10 dark:bg-black/20">
              <div>
                <div className="text-sm font-medium text-slate-900 dark:text-gray-100">Document safety limits</div>
                <div className="text-xs text-slate-500 dark:text-gray-400">Large, deeply nested, or slow documents stop safely before indexing.</div>
              </div>
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
                <div className="space-y-2">
                  <Label htmlFor="max-pages">Max pages</Label>
                  <Input id="max-pages" type="number" min={1} value={maxPages} onChange={(event) => setMaxPages(Number(event.target.value))} disabled={running} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="parser-timeout">Parser seconds</Label>
                  <Input id="parser-timeout" type="number" min={1} max={300} value={parserTimeoutSeconds} onChange={(event) => setParserTimeoutSeconds(Number(event.target.value))} disabled={running} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="archive-entries">Archive items</Label>
                  <Input id="archive-entries" type="number" min={1} value={maxArchiveEntries} onChange={(event) => setMaxArchiveEntries(Number(event.target.value))} disabled={running} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="expanded-size">Expanded MB</Label>
                  <Input id="expanded-size" type="number" min={1} value={maxExpandedMb} onChange={(event) => setMaxExpandedMb(Number(event.target.value))} disabled={running} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="archive-depth">Archive depth</Label>
                  <Input id="archive-depth" type="number" min={0} max={3} value={maxArchiveDepth} onChange={(event) => setMaxArchiveDepth(Number(event.target.value))} disabled={running} />
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white/60 p-4 dark:border-white/10 dark:bg-black/20">
              <div className="flex items-center gap-3">
                <FolderOpen className="h-5 w-5 text-slate-500" />
                <div>
                  <div className="text-sm font-medium text-slate-900 dark:text-gray-100">Recursive folder scan</div>
                  <div className="text-xs text-slate-500 dark:text-gray-400">Subfolders are included when enabled.</div>
                </div>
              </div>
              <Switch checked={recursive} onCheckedChange={setRecursive} disabled={running} aria-label="Recursive folder scan" />
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white/60 p-4 dark:border-white/10 dark:bg-black/20">
              <div className="flex items-center gap-3">
                <Zap className="h-5 w-5 text-amber-500" />
                <div>
                  <div className="text-sm font-medium text-slate-900 dark:text-gray-100">Async mode</div>
                  <div className="text-xs text-slate-500 dark:text-gray-400">Run ingestion in the background.</div>
                </div>
              </div>
              <Switch checked={asyncMode} onCheckedChange={setAsyncMode} disabled={running} aria-label="Async mode" />
            </div>

            {asyncMode && (
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white/60 p-4 dark:border-white/10 dark:bg-black/20">
                <div className="flex items-center gap-3">
                  <DatabaseZap className="h-5 w-5 text-emerald-500" />
                  <div>
                    <div className="text-sm font-medium text-slate-900 dark:text-gray-100">Sync to Neo4j</div>
                    <div className="text-xs text-slate-500 dark:text-gray-400">Sync new nodes to the graph database after ingestion.</div>
                  </div>
                </div>
                <Switch checked={syncNeo4j} onCheckedChange={setSyncNeo4j} disabled={running} aria-label="Sync to Neo4j" />
              </div>
            )}

            {asyncStatus && ['queued', 'running', 'materialization_pending', 'deletion_pending', 'paused'].includes(asyncStatus.status) && (
              <Alert>
                {asyncStatus.status === 'paused' ? <Pause className="h-4 w-4" /> : <Loader2 className="h-4 w-4 animate-spin" />}
                <AlertTitle>Async ingestion {asyncStatus.status.replaceAll('_', ' ')}</AlertTitle>
                <AlertDescription>
                  Source: {asyncStatus.source}. {asyncStatus.files_ingested || 0} files accepted, {asyncStatus.files_rejected || 0} rejected, {asyncStatus.materializations_pending || 0} store updates pending.
                </AlertDescription>
              </Alert>
            )}

            {consistency && (
              <Alert variant={consistency.divergence_count ? 'destructive' : 'default'}>
                <ShieldCheck className="h-4 w-4" />
                <AlertTitle>Corpus consistency</AlertTitle>
                <AlertDescription>{consistency.consistent_jobs}/{consistency.scanned_jobs} jobs consistent; {consistency.divergence_count} differences.</AlertDescription>
              </Alert>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertTitle>Ingestion unavailable</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {lastResult && (
              <Alert>
                <DatabaseZap className="h-4 w-4" />
                <AlertTitle>Last ingestion</AlertTitle>
                <AlertDescription>{formatResultSummary(lastResult)}</AlertDescription>
              </Alert>
            )}

            <div className="flex flex-wrap gap-2">
              <Button onClick={() => void startIngestion()} disabled={running || !sourceCapability} className="bg-blue-600 hover:bg-blue-700" aria-label="Start local knowledge ingestion">
                {running ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <UploadCloud className="mr-2 h-4 w-4" />}
                Start ingestion
              </Button>
              {(activeOperationId || (asyncId && ['queued', 'running', 'paused'].includes(asyncStatus?.status || ''))) && (
                <Button variant="outline" onClick={() => void cancelIngestion()} aria-label="Cancel local knowledge ingestion">
                  Cancel ingestion
                </Button>
              )}
              {asyncId && ['queued', 'running'].includes(asyncStatus?.status || '') && (
                <Button variant="outline" onClick={() => void pauseIngestion()} aria-label="Pause local knowledge ingestion">
                  <Pause className="mr-2 h-4 w-4" /> Pause
                </Button>
              )}
              {asyncId && asyncStatus?.status === 'paused' && (
                <Button variant="outline" onClick={() => void resumeIngestion()} aria-label="Resume local knowledge ingestion">
                  <Play className="mr-2 h-4 w-4" /> Resume
                </Button>
              )}
              <Button variant="outline" onClick={() => void loadHistory()} disabled={loadingHistory || running} aria-label="Refresh ingestion history">
                <RefreshCw className={`mr-2 h-4 w-4 ${loadingHistory ? 'animate-spin' : ''}`} />
                Refresh history
              </Button>
              <Button variant="outline" onClick={() => void scanConsistency()} aria-label="Scan corpus consistency">
                <ShieldCheck className="mr-2 h-4 w-4" /> Scan stores
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="fluent-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-emerald-500" />
              Corpus Status
            </CardTitle>
            <CardDescription>Latest PostgreSQL-authoritative run totals.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(lastResult || history[0]) ? (
              [
                ['Files ingested', String((lastResult || history[0]).files_ingested)],
                ['Files rejected', String((lastResult || history[0]).files_rejected)],
                ['Chunks created', String((lastResult || history[0]).chunks_created)],
                ['Chunks indexed', String((lastResult || history[0]).chunks_indexed)],
              ].map(([label, value]) => (
                <div key={label} className="flex items-center justify-between rounded-lg border border-slate-200 bg-white/60 px-3 py-2 dark:border-white/10 dark:bg-black/20">
                  <span className="text-sm text-slate-600 dark:text-gray-400">{label}</span>
                  <span className="font-mono text-sm font-semibold">{value}</span>
                </div>
              ))
            ) : (
              <div className="rounded-lg border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500 dark:border-white/10 dark:text-gray-400">
                No local ingestion manifests found.
              </div>
            )}
            {supported && (
              <div className="text-xs text-slate-500 dark:text-gray-400">
                Defaults: {formatBytes(supported.default_max_file_bytes)} per file,
                {' '}{formatBytes(supported.default_max_total_bytes)} per job,
                {' '}{supported.default_max_files} files
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="fluent-card">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <History className="h-5 w-5 text-slate-500" />
              Ingestion History
            </CardTitle>
            <CardDescription>Recent durable ingestion jobs and cross-store state.</CardDescription>
          </div>
          {loadingHistory && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
        </CardHeader>
        <CardContent className="space-y-3">
          {history.map((item) => (
            <div key={item.ingestion_id} className="rounded-lg border border-slate-200 bg-white/70 p-4 dark:border-white/10 dark:bg-black/20">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="truncate font-mono text-xs text-slate-500 dark:text-gray-400">{item.ingestion_id}</div>
                  <div className="truncate text-sm font-medium text-slate-900 dark:text-gray-100">{item.source}</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {item.status && <Badge variant="outline">{item.status.replaceAll('_', ' ')}</Badge>}
                  <Badge variant="outline">{item.files_ingested} files</Badge>
                  <Badge variant="outline">{item.chunks_indexed}/{item.chunks_created} indexed</Badge>
                  {item.files_rejected > 0 && <Badge variant="destructive">{item.files_rejected} rejected</Badge>}
                  {item.materializations_pending ? <Badge variant="destructive">{item.materializations_pending} pending</Badge> : null}
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {item.materializations_pending ? (
                  <Button size="sm" variant="outline" onClick={() => void repairIngestion(item.ingestion_id)} aria-label={`Repair ingestion ${item.ingestion_id}`}>
                    <Wrench className="mr-2 h-3.5 w-3.5" /> Repair
                  </Button>
                ) : null}
                {['failed', 'cancelled'].includes(item.status || '') && (
                  <Button size="sm" variant="outline" onClick={() => void retryIngestion(item.ingestion_id)} aria-label={`Retry ingestion ${item.ingestion_id}`}>
                    <RefreshCw className="mr-2 h-3.5 w-3.5" /> Retry
                  </Button>
                )}
                {!['deletion_pending', 'superseded'].includes(item.status || '') && (
                  <Button size="sm" variant="outline" onClick={() => void deleteIngestion(item.ingestion_id)} aria-label={`Delete ingestion ${item.ingestion_id}`}>
                    <Trash2 className="mr-2 h-3.5 w-3.5" /> Delete source
                  </Button>
                )}
              </div>
              {item.files?.slice(0, 5).map((file) => (
                <div key={file.relative_path} className="mt-3 rounded-md border border-slate-200/70 p-3 text-xs dark:border-white/10">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-medium text-slate-800 dark:text-gray-200">{file.relative_path}</span>
                    <Badge variant="outline">{file.status.replaceAll('_', ' ')}</Badge>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2 text-slate-500 dark:text-gray-400">
                    <span>Parser: {file.parser_result?.status || file.error_code || 'pending'}</span>
                    <span>Defense: {file.defense_result?.disposition || 'pending'}</span>
                    <span>Original: {file.object_status || 'pending'}</span>
                    <span>Normalized: {file.normalized_object_status || 'pending'}</span>
                    <span>Vector: {file.vector_status || 'pending'}</span>
                    <span>Graph: {file.graph_status || 'pending'}</span>
                    <span>Embedding: {file.embedding_revision || 'not recorded'}</span>
                    <span>Last retrieval: {file.last_retrieved_at ? new Date(file.last_retrieved_at).toLocaleString() : 'never'}</span>
                    {file.last_retrieval_trace_id && (
                      <Link className="text-blue-600 hover:underline dark:text-blue-400" href={`/runs/view?id=${encodeURIComponent(file.last_retrieval_trace_id)}`}>
                        View last answer trace
                      </Link>
                    )}
                  </div>
                  {file.source_revision && <div className="mt-2 truncate font-mono text-[10px] text-slate-400">{file.source_revision}</div>}
                </div>
              ))}
              {item.manifest_path && (
                <div className="mt-2 truncate text-xs text-slate-500 dark:text-gray-400">{item.manifest_path}</div>
              )}
              {item.rejected_files?.length > 0 && (
                <div className="mt-3 space-y-1">
                  {item.rejected_files.slice(0, 3).map((entry) => (
                    <div key={`${entry.path}-${entry.reason}`} className="text-xs text-amber-700 dark:text-amber-300">
                      {entry.reason}: {entry.path}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
          {!loadingHistory && history.length === 0 && (
            <div className="rounded-lg border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500 dark:border-white/10 dark:text-gray-400">
              No ingestion runs recorded.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default KnowledgeIngestionSettings;

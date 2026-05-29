'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { DatabaseZap, FileText, FolderOpen, History, Loader2, RefreshCw, UploadCloud } from 'lucide-react';
import { api } from '@/lib/api';
import type { IngestionResult, IngestionSupportedTypes } from '@/lib/api/types';
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
  const [path, setPath] = useState('');
  const [sourceLabel, setSourceLabel] = useState('');
  const [recursive, setRecursive] = useState(true);
  const [chunkSize, setChunkSize] = useState(1200);
  const [maxFileMb, setMaxFileMb] = useState(10);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<IngestionResult | null>(null);

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
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load ingestion status.');
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  const startIngestion = async () => {
    const trimmedPath = path.trim();
    if (!trimmedPath) {
      setError('Local path is required.');
      return;
    }

    setRunning(true);
    setError(null);
    try {
      const result = await api.ingestion.startLocal({
        path: trimmedPath,
        recursive,
        chunk_size: Math.max(100, chunkSize || 1200),
        max_file_bytes: Math.max(1, maxFileMb || 10) * 1024 * 1024,
        source_label: sourceLabel.trim() || undefined,
      });
      setLastResult(result);
      setHistory((items) => [result, ...items.filter((item) => item.ingestion_id !== result.ingestion_id)].slice(0, 10));
      toast(`Ingestion complete: ${formatResultSummary(result)}`, 'success');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Local ingestion failed.';
      setError(message);
      toast(message, 'error');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
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
                  value={path}
                  onChange={(event) => setPath(event.target.value)}
                  placeholder="C:/software/DataLogicEngine/corpus"
                  disabled={running}
                />
                <Button type="button" variant="outline" onClick={() => setPath('')} disabled={running || !path}>
                  Clear
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
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
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white/60 p-4 dark:border-white/10 dark:bg-black/20">
              <div className="flex items-center gap-3">
                <FolderOpen className="h-5 w-5 text-slate-500" />
                <div>
                  <div className="text-sm font-medium text-slate-900 dark:text-gray-100">Recursive folder scan</div>
                  <div className="text-xs text-slate-500 dark:text-gray-400">Subfolders are included when enabled.</div>
                </div>
              </div>
              <Switch checked={recursive} onCheckedChange={setRecursive} disabled={running} />
            </div>

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
              <Button onClick={() => void startIngestion()} disabled={running || !path.trim()} className="bg-blue-600 hover:bg-blue-700">
                {running ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <UploadCloud className="mr-2 h-4 w-4" />}
                Start ingestion
              </Button>
              <Button variant="outline" onClick={() => void loadHistory()} disabled={loadingHistory || running}>
                <RefreshCw className={`mr-2 h-4 w-4 ${loadingHistory ? 'animate-spin' : ''}`} />
                Refresh history
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
            <CardDescription>Latest manifest-backed run totals.</CardDescription>
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
                Default limit: {formatBytes(supported.default_max_file_bytes)}
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
            <CardDescription>Recent local manifest records.</CardDescription>
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
                  <Badge variant="outline">{item.files_ingested} files</Badge>
                  <Badge variant="outline">{item.chunks_indexed}/{item.chunks_created} indexed</Badge>
                  {item.files_rejected > 0 && <Badge variant="destructive">{item.files_rejected} rejected</Badge>}
                </div>
              </div>
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

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import { request } from '@/lib/api';
import type { KAExecutionFeed, KAExecutionFeedItem } from '@/lib/api/types';
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  Clock,
  RefreshCw,
  ShieldCheck,
  AlertCircle,
  ChevronRight
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface TraceRunRecord {
  run_id: string;
  status?: string;
  created_at?: string;
  input_message?: string;
  scores?: {
    confidence?: number;
    entropy?: number;
    bias_risk?: number;
  };
}

interface TraceStageRecord {
  stage_id: string;
  name: string;
  status?: string;
  layer_index?: number;
  step_index?: number;
  timing?: {
    duration_ms?: number;
  };
}

interface ReasoningLayerProgress {
  active_run_id: string | null;
  status: string;
  current_layer: number | null;
  layer_name: string | null;
  kas_running: Array<{
    ka_id: string;
    ka_name?: string | null;
    status?: string;
    confidence?: number | null;
    duration_ms?: number | null;
  }>;
  confidence_so_far: number | null;
  persona_confidences: Array<{
    persona: string;
    confidence: number;
    status?: string;
  }>;
  frost_snapshot_count: number;
}

function formatStatus(value?: string): string {
  if (!value) return 'unknown';
  return value.replace(/_/g, ' ');
}

function statusClass(status?: string): string {
  const normalized = (status || '').toLowerCase();
  if (normalized === 'pass' || normalized === 'completed') return 'text-green-500';
  if (normalized === 'running') return 'text-blue-400';
  if (normalized === 'warn') return 'text-yellow-500';
  if (normalized === 'fail' || normalized === 'failed') return 'text-red-400';
  return 'text-slate-500 dark:text-gray-500';
}

function scoreToPercent(value?: number): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return '--';
  const normalized = value <= 1 ? value * 100 : value;
  return `${normalized.toFixed(1)}%`;
}

function formatExecutionDuration(value?: number | null): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '';
  return ` (${Math.max(0, Math.round(value))}ms)`;
}

function kaFeedItemKey(item: KAExecutionFeedItem): string {
  return item.uid || `${item.id}-${item.ka_id || 'unknown'}-${item.started_at || 'unstarted'}`;
}

export function LiveTracePanel() {
  const [runs, setRuns] = useState<TraceRunRecord[]>([]);
  const [stages, setStages] = useState<TraceStageRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reasoningProgress, setReasoningProgress] = useState<ReasoningLayerProgress | null>(null);
  const [kaFeed, setKaFeed] = useState<KAExecutionFeed | null>(null);

  const loadTraceData = useCallback(async () => {
    setError(null);
    try {
      // Treat transient backend errors (startup race, 500, IPC timeout) as an
      // empty state rather than surfacing the error banner.  The 15-second poll
      // will recover automatically once the backend is ready.
      const runsPromise = api.trace.list(12)
        .catch(() => [] as unknown[]) as Promise<TraceRunRecord[]>;

      // IPC calls use invokeWithTimeout which throws on a 5-second timeout.
      // Catch those individually so a slow backend start doesn't abort the
      // whole loadTraceData and blank the panel.
      const progressPromise = window.electronAPI?.getReasoningLayerProgress
        ? window.electronAPI.getReasoningLayerProgress().catch(() => null)
        : request<ReasoningLayerProgress>('/trace/live-progress').catch(() => null);

      const feedPromise = window.electronAPI?.getKAExecutionFeed
        ? window.electronAPI.getKAExecutionFeed().catch(() => null)
        : request<KAExecutionFeed>('/trace/ka-execution-feed?limit=20').catch(() => null);

      const [recentRuns, progressPayload, feedPayload] = await Promise.all([
        runsPromise,
        progressPromise,
        feedPromise,
      ]) as [
        TraceRunRecord[],
        ReasoningLayerProgress | null,
        KAExecutionFeed | null,
      ];
      setRuns(recentRuns || []);

      const selectedRun = (recentRuns || []).find((run) => run.status === 'running') || recentRuns?.[0];
      const stagePayload: { stages?: TraceStageRecord[] } = selectedRun
        ? await api.trace
          .getStages(selectedRun.run_id)
          .catch(() => ({ stages: [] as TraceStageRecord[] })) as { stages?: TraceStageRecord[] }
        : { stages: [] as TraceStageRecord[] };

      setStages(stagePayload.stages || []);
      setReasoningProgress(progressPayload);
      setKaFeed(feedPayload);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load trace telemetry');
      setRuns([]);
      setStages([]);
      setReasoningProgress(null);
      setKaFeed(null);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function init() {
      setLoading(true);
      await loadTraceData();
      if (!cancelled) {
        setLoading(false);
      }
    }
    void init();

    const interval = window.setInterval(() => {
      void loadTraceData();
    }, 15000);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [loadTraceData]);

  const currentRun = useMemo(
    () => runs.find((run) => run.status === 'running') || runs[0],
    [runs]
  );

  const currentStage = useMemo(
    () =>
      stages.find((stage) => stage.status === 'running') ||
      stages.find((stage) => stage.status !== 'pass' && stage.status !== 'completed') ||
      stages[stages.length - 1],
    [stages]
  );

  const progress = useMemo(() => {
    if (!currentRun) return 0;
    if (!stages.length) {
      const status = (currentRun.status || '').toLowerCase();
      if (status === 'running') return 10;
      if (status === 'pass' || status === 'completed') return 100;
      return 0;
    }
    const finished = stages.filter((stage) =>
      ['pass', 'completed', 'warn', 'fail', 'failed', 'skipped'].includes((stage.status || '').toLowerCase())
    ).length;
    return Math.round((finished / stages.length) * 100);
  }, [currentRun, stages]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadTraceData();
    setRefreshing(false);
  };

  return (
    <div className="h-full flex flex-col bg-slate-100/80 dark:bg-gray-900/50 text-gray-900 dark:text-white font-sans overflow-hidden">
      <div className="p-4 border-b border-white/10 flex items-center justify-between">
        <h2 className="text-sm font-bold flex items-center gap-2">
          <Activity className="h-4 w-4 text-green-500" />
          Live Trace
        </h2>
        <div className="flex items-center gap-2">
          {currentRun ? (
            <Badge variant="outline" className="bg-green-900/20 text-green-400 border-green-500/30 text-[10px] px-1.5 py-0 h-5">
              {formatStatus(currentRun.status).toUpperCase()}
            </Badge>
          ) : (
            <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-5">
              IDLE
            </Badge>
          )}
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => void handleRefresh()} disabled={refreshing}>
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {loading && <div className="text-xs text-slate-500 dark:text-gray-500">Loading trace telemetry...</div>}
        {!loading && error && (
          <div className="text-xs text-red-600 dark:text-red-400 border border-red-500/20 rounded-md p-2">
            {typeof error === 'string' ? error : 'Failed to load trace telemetry'}
          </div>
        )}
        {!loading && !error && !currentRun && (
          <div className="text-xs text-slate-500 dark:text-gray-500 border border-slate-300 dark:border-white/10 rounded-md p-3">
            No trace runs found yet. Run a query to populate live telemetry.
          </div>
        )}

        {!loading && currentRun && (
          <>
            <div className="space-y-2">
              <div className="text-xs text-slate-500 dark:text-gray-500 font-mono uppercase tracking-wider">Active Run</div>
              <Card className="bg-white/70 dark:bg-black/40 border border-slate-200 dark:border-white/10">
                <CardContent className="p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-slate-700 dark:text-gray-300">{currentRun.run_id}</span>
                    <span className={`text-[10px] uppercase font-semibold ${statusClass(currentRun.status)}`}>
                      {formatStatus(currentRun.status)}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-gray-400 line-clamp-3">
                    {currentRun.input_message || 'No captured input text for this run.'}
                  </p>
                  <div className="text-[10px] text-slate-500 dark:text-gray-500">
                    Created: {currentRun.created_at ? new Date(currentRun.created_at).toLocaleString() : 'Unknown'}
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-end">
                <div className="text-xs text-slate-500 dark:text-gray-500 font-mono uppercase tracking-wider">Pipeline Progress</div>
                <div className="text-xs font-mono text-blue-400">{progress}%</div>
              </div>
              <Progress value={progress} className="h-1.5 bg-blue-900/30 [&>div]:bg-blue-500" />
              <div className="flex justify-between mt-1 text-[10px] text-slate-500 dark:text-gray-500">
                <span>{stages.length ? `${stages.filter((stage) => (stage.status || '').toLowerCase() === 'running').length} active` : 'No stages'}</span>
                <span>{stages.length ? `${stages.length} total` : 'Waiting for stage data'}</span>
              </div>
            </div>

            {reasoningProgress && (
              <div className="space-y-2">
                <div className="text-xs text-slate-500 dark:text-gray-500 font-mono uppercase tracking-wider">Reasoning Feed</div>
                <Card className="bg-white/70 dark:bg-black/40 border border-slate-200 dark:border-white/10">
                  <CardContent className="p-3 space-y-3">
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div>
                        <div className="text-[10px] uppercase text-slate-500 dark:text-gray-500">Layer</div>
                        <div className="text-sm font-semibold">{reasoningProgress.current_layer ?? '--'}</div>
                      </div>
                      <div>
                        <div className="text-[10px] uppercase text-slate-500 dark:text-gray-500">Confidence</div>
                        <div className="text-sm font-semibold">{scoreToPercent(reasoningProgress.confidence_so_far ?? undefined)}</div>
                      </div>
                      <div>
                        <div className="text-[10px] uppercase text-slate-500 dark:text-gray-500">FROST</div>
                        <div className="text-sm font-semibold">{reasoningProgress.frost_snapshot_count}</div>
                      </div>
                    </div>
                    <div className="text-xs text-slate-600 dark:text-gray-400">
                      {reasoningProgress.layer_name || 'No active reasoning layer'}
                    </div>
                    <div className="space-y-1">
                      {reasoningProgress.kas_running.slice(0, 5).map((ka) => (
                        <div key={`${ka.ka_id}-${ka.status}`} className="flex items-center justify-between text-xs">
                          <span className="truncate">{ka.ka_name || ka.ka_id}</span>
                          <span className={statusClass(ka.status)}>{formatStatus(ka.status)}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {reasoningProgress?.persona_confidences?.length ? (
              <div className="space-y-2">
                <div className="text-xs text-slate-500 dark:text-gray-500 font-mono uppercase tracking-wider">Persona Confidence</div>
                <div className="space-y-2">
                  {reasoningProgress.persona_confidences.slice(0, 6).map((persona) => {
                    const pct = Math.max(0, Math.min(100, (persona.confidence <= 1 ? persona.confidence * 100 : persona.confidence)));
                    return (
                      <div key={persona.persona} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="truncate">{persona.persona}</span>
                          <span>{pct.toFixed(1)}%</span>
                        </div>
                        <Progress value={pct} className="h-1 bg-slate-200 dark:bg-white/10 [&>div]:bg-emerald-500" />
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : null}

            {currentStage && (
              <div className="space-y-2">
                <div className="text-xs text-slate-500 dark:text-gray-500 font-mono uppercase tracking-wider">Current Stage</div>
                <Card className="bg-blue-900/10 border-blue-500/20">
                  <CardContent className="p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-bold text-blue-300 flex items-center gap-2">
                        <ChevronRight className="h-3 w-3" /> {currentStage.name}
                      </span>
                      <span className="text-xs text-blue-400 font-mono">
                        {typeof currentStage.timing?.duration_ms === 'number' ? `${currentStage.timing.duration_ms}ms` : '--'}
                      </span>
                    </div>
                    <div className={`text-[10px] uppercase font-semibold ${statusClass(currentStage.status)}`}>
                      {formatStatus(currentStage.status)}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {stages.length > 0 && (
              <div className="space-y-2">
                <div className="text-xs text-slate-500 dark:text-gray-500 font-mono uppercase tracking-wider">Trace Log</div>
                <div className="space-y-1">
                  {stages.slice(0, 8).map((stage) => (
                    <div key={stage.stage_id} className="flex items-center justify-between text-xs p-1.5 rounded hover:bg-slate-200/70 dark:hover:bg-white/5 transition-colors">
                      <div className="flex items-center gap-2">
                        {['pass', 'completed'].includes((stage.status || '').toLowerCase()) ? (
                          <ShieldCheck className="h-3 w-3 text-green-500" />
                        ) : ['fail', 'failed', 'warn'].includes((stage.status || '').toLowerCase()) ? (
                          <AlertCircle className="h-3 w-3 text-yellow-500" />
                        ) : (
                          <Clock className="h-3 w-3 text-blue-400" />
                        )}
                        <span className={statusClass(stage.status)}>{stage.name}</span>
                      </div>
                      <span className="text-[10px] text-slate-500 dark:text-gray-600 font-mono">
                        {typeof stage.timing?.duration_ms === 'number' ? `${stage.timing.duration_ms}ms` : '--'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="space-y-2 pt-2 border-t border-white/10">
              <div className="text-xs text-slate-500 dark:text-gray-500 font-mono uppercase tracking-wider mb-3">Run Scores</div>
              <div className="grid grid-cols-1 gap-2">
                <div className="p-2 bg-white/70 dark:bg-white/5 rounded border border-slate-200 dark:border-white/5 flex items-center justify-between">
                  <span className="text-[10px] text-slate-500 dark:text-gray-500 uppercase">Confidence</span>
                  <span className="text-sm font-semibold">{scoreToPercent(currentRun.scores?.confidence)}</span>
                </div>
                <div className="p-2 bg-white/70 dark:bg-white/5 rounded border border-slate-200 dark:border-white/5 flex items-center justify-between">
                  <span className="text-[10px] text-slate-500 dark:text-gray-500 uppercase">Entropy</span>
                  <span className="text-sm font-semibold">{scoreToPercent(currentRun.scores?.entropy)}</span>
                </div>
                <div className="p-2 bg-white/70 dark:bg-white/5 rounded border border-slate-200 dark:border-white/5 flex items-center justify-between">
                  <span className="text-[10px] text-slate-500 dark:text-gray-500 uppercase">Bias Risk</span>
                  <span className="text-sm font-semibold">{scoreToPercent(currentRun.scores?.bias_risk)}</span>
                </div>
              </div>
            </div>
          </>
        )}

        {!loading && !error && kaFeed?.items?.length ? (
          <div className="space-y-2">
            <div className="text-xs text-slate-500 dark:text-gray-500 font-mono uppercase tracking-wider">KA Execution Feed</div>
            <div className="space-y-1">
              {kaFeed.items.slice(0, 6).map((item) => (
                <div key={kaFeedItemKey(item)} className="flex items-center justify-between gap-3 text-xs p-1.5 rounded bg-white/60 dark:bg-white/5">
                  <span className="font-mono truncate">{item.ka_id || 'unknown KA'}</span>
                  <span className={statusClass(item.status || undefined)}>
                    {formatStatus(item.status || undefined)}{formatExecutionDuration(item.execution_time_ms)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : null}

      </div>
    </div>
  );
}

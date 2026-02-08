import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
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

export function LiveTracePanel() {
  const [runs, setRuns] = useState<TraceRunRecord[]>([]);
  const [stages, setStages] = useState<TraceStageRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTraceData = useCallback(async () => {
    setError(null);
    try {
      const recentRuns = await api.trace.list(12) as TraceRunRecord[];
      setRuns(recentRuns || []);

      const selectedRun = (recentRuns || []).find((run) => run.status === 'running') || recentRuns?.[0];
      if (!selectedRun) {
        setStages([]);
        return;
      }

      const stagePayload = await api.trace
        .getStages(selectedRun.run_id)
        .catch(() => ({ stages: [] as TraceStageRecord[] })) as { stages?: TraceStageRecord[] };
      setStages(stagePayload.stages || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load trace telemetry');
      setRuns([]);
      setStages([]);
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
            {error}
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
      </div>
    </div>
  );
}

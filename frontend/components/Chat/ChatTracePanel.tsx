'use client';

import React, { useMemo, useState } from 'react';
import { Activity, ChevronDown, FileDown, Layers, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import type { AuditTrail, TraceBundle } from '@/lib/api/types';
import type { ConfidenceDisplay } from '@/lib/api/types';
import { useTraceStream } from '@/hooks/useTraceStream';
import { ConfidenceDisplayCard } from './ConfidenceDisplayCard';
import { RefinementDispositionCard } from './RefinementDispositionCard';
import { AnalystContributions } from './AnalystContributions';

interface ChatTracePanelProps {
  runId?: string;
  auditTrail?: AuditTrail;
}

export function ChatTracePanel({ runId, auditTrail }: ChatTracePanelProps) {
  const resolvedRunId = useMemo(() => {
    if (runId) return runId;
    const match = auditTrail?.complete_trace_url?.match(/\/runs\/([^/]+)/);
    return match?.[1];
  }, [auditTrail?.complete_trace_url, runId]);

  const [expanded, setExpanded] = useState(false);
  const [bundle, setBundle] = useState<TraceBundle | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isLive = bundle?.status === 'running';
  const traceStream = useTraceStream(isLive && resolvedRunId ? resolvedRunId : null);
  const displayedStages = useMemo(() => {
    const reconciled = [...(bundle?.frost_layers || [])];
    for (const live of traceStream.layers) {
      const index = reconciled.findIndex((stage) => stage.stage_id === live.stage_id);
      if (index >= 0) {
        reconciled[index] = { ...reconciled[index], ...live };
      } else {
        reconciled.push(live);
      }
    }
    return reconciled.sort((left, right) => (left.sequence || 0) - (right.sequence || 0));
  }, [bundle?.frost_layers, traceStream.layers]);
  const confidenceDisplay = useMemo<ConfidenceDisplay | null>(() => {
    const recorded = bundle?.run?.data_snapshot?.confidence_display;
    if (recorded) return recorded;
    const measurement = bundle?.run?.data_snapshot?.confidence_measurement;
    if (measurement?.status) {
      return {
        status: measurement.status === 'measured' && typeof measurement.value === 'number'
          ? 'measured'
          : 'not_measured',
        measurement_status: measurement.status,
        value: measurement.status === 'measured' && typeof measurement.value === 'number'
          ? measurement.value
          : null,
        formula_version: measurement.formula_version,
        reason: measurement.status === 'measured'
          ? 'legacy_trace_measurement'
          : 'required_measurement_components_unavailable',
        missing_components: measurement.missing_components || [],
        explanation: measurement.explanation || 'No versioned evidence-support measurement is available for this run.',
      };
    }
    const legacyValue = bundle?.metrics?.confidence;
    if (typeof legacyValue !== 'number' || Number.isNaN(legacyValue)) return null;
    return {
      status: 'measured',
      measurement_status: 'measured',
      value: legacyValue,
      formula_version: null,
      reason: 'legacy_trace_measurement',
      missing_components: [],
      explanation: 'Versioned evidence-support measurement recorded by this historical trace.',
    };
  }, [bundle]);

  if (!resolvedRunId && !auditTrail) return null;

  const loadBundle = async () => {
    if (!resolvedRunId || bundle || loading) return;
    setLoading(true);
    setError(null);
    try {
      setBundle(await api.trace.getBundle(resolvedRunId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Trace bundle unavailable');
    } finally {
      setLoading(false);
    }
  };

  const toggleExpanded = async () => {
    const next = !expanded;
    setExpanded(next);
    if (next) {
      await loadBundle();
    }
  };

  const exportBundle = async () => {
    if (!resolvedRunId) return;
    const exported = await api.trace.export(resolvedRunId);
    if (!exported) return;
    const blob = new Blob([typeof exported === 'string' ? exported : JSON.stringify(exported, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `trace_${resolvedRunId}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="mt-3 rounded-md border border-slate-200 bg-slate-50/80 text-slate-800 dark:border-white/10 dark:bg-black/20 dark:text-slate-100">
      <button
        type="button"
        onClick={() => void toggleExpanded()}
        className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left"
        aria-expanded={expanded}
      >
        <span className="flex min-w-0 items-center gap-2">
          <Activity className="h-4 w-4 shrink-0 text-blue-500" />
          <span className="truncate text-xs font-semibold uppercase tracking-wide">Reasoning Trace</span>
          {resolvedRunId && (
            <span className="truncate font-mono text-[11px] text-slate-500 dark:text-slate-400">
              {resolvedRunId.slice(0, 8)}
            </span>
          )}
        </span>
        <ChevronDown className={`h-4 w-4 shrink-0 transition-transform ${expanded ? 'rotate-180' : ''}`} />
      </button>

      {expanded && (
        <div className="space-y-3 border-t border-slate-200 px-3 py-3 text-xs dark:border-white/10">
          {loading && <div className="text-slate-500 dark:text-slate-400">Loading trace bundle...</div>}
          {error && <div className="text-red-600 dark:text-red-400">{error}</div>}
          {bundle && (
            <>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                <ConfidenceDisplayCard display={confidenceDisplay} compact />
                <div className="rounded border border-slate-200 bg-white/80 p-2 dark:border-white/10 dark:bg-white/5">
                  <div className="mb-1 flex items-center gap-1 text-slate-500 dark:text-slate-400">
                    <Layers className="h-3.5 w-3.5" />
                    Stages
                  </div>
                  <div className="font-semibold">{bundle.metrics?.stage_count ?? bundle.stages?.length ?? 0}</div>
                </div>
                <div className="rounded border border-slate-200 bg-white/80 p-2 dark:border-white/10 dark:bg-white/5">
                  <div className="mb-1 flex items-center gap-1 text-slate-500 dark:text-slate-400">
                    <Users className="h-3.5 w-3.5" />
                    Personas
                  </div>
                  <div className="font-semibold">{bundle.personas?.length ?? 0}</div>
                </div>
                <div className="rounded border border-slate-200 bg-white/80 p-2 dark:border-white/10 dark:bg-white/5">
                  <div className="mb-1 text-slate-500 dark:text-slate-400">Evidence</div>
                  <div className="font-semibold">{bundle.evidence_sources?.length ?? 0}</div>
                </div>
              </div>
              <RefinementDispositionCard
                disposition={bundle.run?.data_snapshot?.refinement_disposition}
                compact
              />
              <AnalystContributions personas={bundle.personas} compact />

              <div className="space-y-1">
                {displayedStages.slice(0, 8).map((stage) => (
                  <div key={stage.stage_id || `${stage.layer_index}-${stage.name}`} className="rounded bg-white/70 px-2 py-1 dark:bg-white/5">
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate">{stage.layer_index ? `L${stage.layer_index} ` : ''}{stage.name || 'Trace update'}</span>
                      <Badge variant="outline" className="h-5 shrink-0 text-[10px]">
                        {stage.status || 'live'}
                      </Badge>
                    </div>
                    {stage.narrative && (
                      <p className="mt-1 text-[11px] leading-relaxed text-slate-500 dark:text-slate-400">
                        {stage.narrative}
                      </p>
                    )}
                  </div>
                ))}
                {!displayedStages.length && (
                  <div className="rounded bg-white/70 px-2 py-2 text-slate-500 dark:bg-white/5 dark:text-slate-400">
                    No stage records are attached to this run yet.
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                {auditTrail?.decision_path && (
                  <Button size="sm" variant="outline" asChild>
                    <a href={auditTrail.decision_path.replace('/api/v1/trace/runs/', '/runs/view?id=')}>
                      Open details
                    </a>
                  </Button>
                )}
                {resolvedRunId && (
                  <Button size="sm" variant="outline" onClick={() => void exportBundle()}>
                    <FileDown className="mr-1 h-3.5 w-3.5" />
                    Export
                  </Button>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

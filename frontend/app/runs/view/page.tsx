'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { api, type TraceDetail } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge, type BadgeProps } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type {
  TraceAxisVector,
  TraceBundle,
  TraceEvidenceSource,
  TraceKAInvocation,
  TracePersona,
  TraceStage,
} from '@/lib/api/types';

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function formatDateTime(value?: string | null): string {
  if (!value) return 'Unknown time';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Unknown time' : date.toLocaleString();
}

function formatTime(value?: string | null): string {
  if (!value) return 'Unknown time';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Unknown time' : date.toLocaleTimeString();
}

function formatCount(value: unknown, fallback = 0): string {
  return isFiniteNumber(value) ? String(value) : String(fallback);
}

function formatMs(value: unknown): string {
  return isFiniteNumber(value) ? String(value) + ' ms' : '--';
}

function scoreToPercent(value: unknown, digits = 0): string {
  if (!isFiniteNumber(value)) return '--';
  const normalized = value <= 1 ? value * 100 : value;
  return normalized.toFixed(digits) + '%';
}

function scoreToFixed(value: unknown): string {
  return isFiniteNumber(value) ? value.toFixed(2) : '--';
}

function statusVariant(status?: string | null): BadgeProps['variant'] {
  const normalized = status?.toLowerCase();
  if (normalized === 'pass' || normalized === 'completed' || normalized === 'success') return 'success';
  if (normalized === 'fail' || normalized === 'failed' || normalized === 'error') return 'destructive';
  return 'secondary';
}

function statusPillClass(status?: string | null): string {
  const normalized = status?.toLowerCase();
  if (normalized === 'pass' || normalized === 'completed' || normalized === 'success') {
    return 'bg-green-100 text-green-700';
  }
  if (normalized === 'fail' || normalized === 'failed' || normalized === 'error') {
    return 'bg-red-100 text-red-700';
  }
  return 'bg-gray-100 text-gray-600';
}

function statusLabel(status?: string | null): string {
  return status || 'unknown';
}

function stageIndicator(step: TraceStage): string | null {
  if (step.stage_type === 'layer' && step.layer_index != null) return 'L' + step.layer_index;
  if (step.stage_type === 'step' && step.step_index != null) return 'S' + step.step_index;
  if (step.layer_index != null) return 'L' + step.layer_index;
  if (step.step_index != null) return 'S' + step.step_index;
  return null;
}

function jsonPreview(value: unknown): string | null {
  if (value == null) return null;
  try {
    const serialized = typeof value === 'string' ? value : JSON.stringify(value);
    if (!serialized) return null;
    return serialized.length > 100 ? serialized.slice(0, 100) + '...' : serialized;
  } catch {
    return '[unserializable output]';
  }
}

function arrayOrEmpty<T>(value: T[] | null | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

function axisEntries(axisVector: TraceAxisVector | null): Array<[string, { name?: string | null; selected?: boolean | null }]> {
  const axes = axisVector?.axes;
  if (!axes || typeof axes !== 'object' || Array.isArray(axes)) return [];
  return Object.entries(axes).filter(([, axis]) => axis && typeof axis === 'object') as Array<[
    string,
    { name?: string | null; selected?: boolean | null },
  ]>;
}

function TraceDetailContent() {
  const searchParams = useSearchParams();
  const runId = searchParams.get('id') || searchParams.get('trace');

  const [trace, setTrace] = useState<TraceDetail | null>(null);
  const [personas, setPersonas] = useState<TracePersona[]>([]);
  const [axes, setAxes] = useState<TraceAxisVector | null>(null);
  const [stages, setStages] = useState<TraceStage[]>([]);
  const [evidence, setEvidence] = useState<TraceEvidenceSource[]>([]);
  const [kas, setKas] = useState<TraceKAInvocation[]>([]);
  const [policyDecisions, setPolicyDecisions] = useState<Record<string, unknown>[]>([]);
  const [memoryEvents, setMemoryEvents] = useState<Record<string, unknown>[]>([]);
  const [metrics, setMetrics] = useState<TraceBundle['metrics'] | null>(null);
  const [activeTab, setActiveTab] = useState('stages');
  const [isLoading, setIsLoading] = useState(Boolean(runId));
  const [loadError, setLoadError] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    if (!runId) {
      return () => { mounted = false; };
    }

    const loadBundle = async () => {
      setIsLoading(true);
      setLoadError(null);
      try {
        const bundle = await api.trace.getBundle(runId);
        if (!mounted) return;
        setTrace((bundle.run || { run_id: bundle.run_id, status: bundle.status, created_at: null }) as TraceDetail);
        setPersonas(arrayOrEmpty(bundle.personas));
        setAxes(bundle.axes || bundle.coordinate || null);
        setStages(arrayOrEmpty(bundle.stages).length ? arrayOrEmpty(bundle.stages) : arrayOrEmpty(bundle.frost_layers));
        setEvidence(arrayOrEmpty(bundle.evidence_sources).length ? arrayOrEmpty(bundle.evidence_sources) : arrayOrEmpty(bundle.evidence));
        setKas(arrayOrEmpty(bundle.ka_invocations).length ? arrayOrEmpty(bundle.ka_invocations) : arrayOrEmpty(bundle.kas));
        setPolicyDecisions(arrayOrEmpty(bundle.policy_decisions));
        setMemoryEvents(arrayOrEmpty(bundle.memory_events));
        setMetrics(bundle.metrics || null);
        setIsLoading(false);
      } catch (err) {
        if (!mounted) return;
        setTrace(null);
        setLoadError(err instanceof Error ? err.message : 'Trace details are unavailable.');
        setIsLoading(false);
      }
    };

    void loadBundle();

    return () => { mounted = false; };
  }, [runId]);

  const exportTrace = async () => {
    if (!runId) return;
    setExportError(null);
    try {
      const exported = await api.trace.export(runId);
      if (!exported) {
        setExportError('Trace export is unavailable.');
        return;
      }
      const blob = new Blob([typeof exported === 'string' ? exported : JSON.stringify(exported, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = 'trace_' + runId + '.json';
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 0);
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'Trace export failed.');
    }
  };

  if (!runId) {
    return <div className="p-8 text-center text-red-500">No trace ID provided</div>;
  }

  if (isLoading) {
    return <div className="p-8 text-center text-gray-500">Loading trace details...</div>;
  }

  if (!trace) {
    return <div className="p-8 text-center text-red-500">{loadError || 'Trace not found'}</div>;
  }

  const traceId = trace.run_id || runId || 'unknown';
  const coordinateAxes = axisEntries(axes);

  return (
    <div className="container mx-auto max-w-7xl space-y-8">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Trace Detail</h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <span className="break-all font-mono text-gray-500">{traceId}</span>
            <Badge variant={statusVariant(trace.status)}>{statusLabel(trace.status)}</Badge>
          </div>
        </div>
        <Button variant="outline" onClick={() => void exportTrace()} disabled={!runId}>Download Trace</Button>
      </header>
      {exportError && <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{exportError}</div>}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Tabs defaultValue="stages" value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="stages">Stages</TabsTrigger>
              <TabsTrigger value="evidence">Evidence</TabsTrigger>
              <TabsTrigger value="personas">Expert Analysis</TabsTrigger>
              <TabsTrigger value="kas">KAs</TabsTrigger>
              <TabsTrigger value="coordinates">Coordinates</TabsTrigger>
            </TabsList>

            <TabsContent value="stages" className="mt-4 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Reasoning Trace</CardTitle>
                  <CardDescription>Layered execution path.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {!stages.length && <p className="italic text-gray-500">No detailed stage information available.</p>}
                  {stages.map((step, i) => {
                    const indicator = stageIndicator(step);
                    const outputPreview = jsonPreview(step.outputs);
                    return (
                      <div key={step.stage_id || 'stage-' + i} className="relative overflow-hidden rounded-lg border bg-white p-4 dark:bg-gray-900">
                        {indicator && (
                          <div className="absolute right-0 top-0 rounded-bl-lg bg-gray-100 px-2 py-1 font-mono text-xs text-gray-500 dark:bg-gray-800">
                            {indicator}
                          </div>
                        )}

                        <div className="mb-2 flex justify-between gap-3">
                          <h4 className="text-sm font-semibold">{step.algorithm_name || step.name || 'Processing'}</h4>
                          <span className={'rounded-full px-2 py-0.5 text-xs ' + statusPillClass(step.status)}>
                            {statusLabel(step.status)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-300">
                          Started: {formatTime(step.started_at || step.start_time)}
                        </p>
                        {outputPreview && (
                          <div className="mt-2 rounded bg-gray-50 p-2 font-mono text-xs text-gray-500 dark:bg-gray-950">
                            {outputPreview}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="evidence" className="mt-4 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Evidence Sources</CardTitle>
                  <CardDescription>Claim support and source provenance.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {evidence.map((item, index) => (
                    <div key={item.evidence_id || item.source_id || 'evidence-' + index} className="rounded-lg border bg-white p-4 dark:bg-gray-900">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h4 className="font-semibold">{item.title || item.source_id || 'Evidence source'}</h4>
                          <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">{item.snippet || 'No snippet recorded.'}</p>
                        </div>
                        <Badge variant="outline">{item.evidence_tier || 'UNVERIFIED'}</Badge>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2 text-xs text-gray-500">
                        <span>Source: {item.source_type || 'unknown'}</span>
                        <span>KA: {item.ka_that_invoked || 'N/A'}</span>
                        <span>Claims: {item.claims_supported?.length ?? 0}</span>
                      </div>
                    </div>
                  ))}
                  {!evidence.length && (
                    <div className="rounded-lg border border-dashed p-8 text-center text-gray-500">
                      No evidence sources found for this run.
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="personas" className="mt-4 space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {personas.map((p, index) => {
                  const personaName = p.persona_name || p.persona_type || 'Persona';
                  const draftText = p.draft?.text || p.final_position || p.initial_position || '';
                  return (
                    <Card key={p.persona_id || 'persona-' + index} className="border-l-4 border-l-blue-500">
                      <CardHeader className="pb-2">
                        <CardTitle className="flex justify-between gap-3 text-lg">
                          <span>{personaName}</span>
                          <Badge variant="outline" className="text-xs uppercase">{p.persona_type || 'unknown'}</Badge>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="mb-3 text-sm italic text-gray-600 dark:text-gray-300">
                          {draftText ? <>&quot;{draftText.slice(0, 150)}{draftText.length > 150 ? '...' : ''}&quot;</> : 'No draft recorded.'}
                        </p>
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <span>Confidence: {scoreToPercent(p.confidence ?? p.draft?.confidence)}</span>
                          <span className="capitalize">{statusLabel(p.status)}</span>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
                {!personas.length && (
                  <div className="col-span-2 rounded-lg border border-dashed p-8 text-center text-gray-500">
                    No persona activation data found for this run.
                  </div>
                )}
              </div>
            </TabsContent>

            <TabsContent value="coordinates" className="mt-4 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>17-Axis Vector</CardTitle>
                  <CardDescription>Multidimensional logic coordinates.</CardDescription>
                </CardHeader>
                <CardContent>
                  {coordinateAxes.length ? (
                    <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
                      {coordinateAxes.map(([id, axis]) => (
                        <div key={id} className={'rounded-lg border p-3 ' + (axis.selected ? 'border-blue-200 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-900/20' : 'border-gray-100 bg-gray-50 dark:border-gray-800 dark:bg-gray-900/50')}>
                          <div className="mb-1 text-xs font-bold uppercase text-gray-500">Axis {id}</div>
                          <div className="truncate text-sm font-medium" title={axis.name || 'Unnamed axis'}>{axis.name || 'Unnamed axis'}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="rounded-lg border border-dashed p-8 text-center text-gray-500">
                      No coordinate vector data found for this run.
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="kas" className="mt-4 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Knowledge Algorithm Feed</CardTitle>
                  <CardDescription>KA invocations, policy decisions, and memory events.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    {kas.map((ka, index) => (
                      <div key={ka.invocation_id || 'ka-' + index} className="flex items-center justify-between rounded-lg border bg-white px-4 py-3 dark:bg-gray-900">
                        <div>
                          <div className="font-semibold">{ka.ka_id || 'Unknown KA'}</div>
                          <div className="text-sm text-gray-500">{ka.ka_name || 'Unnamed KA'}</div>
                        </div>
                        <div className="text-right">
                          <Badge variant="outline">{statusLabel(ka.status)}</Badge>
                          <div className="mt-1 text-xs text-gray-500">{formatMs(ka.timing?.duration_ms)}</div>
                        </div>
                      </div>
                    ))}
                    {!kas.length && <p className="text-sm text-gray-500">No KA invocations recorded.</p>}
                  </div>
                  <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                    <div className="rounded-lg border p-3">
                      <div className="text-xs font-semibold uppercase text-gray-500">Policy Decisions</div>
                      <div className="mt-1 text-2xl font-bold">{policyDecisions.length}</div>
                    </div>
                    <div className="rounded-lg border p-3">
                      <div className="text-xs font-semibold uppercase text-gray-500">Memory Events</div>
                      <div className="mt-1 text-2xl font-bold">{memoryEvents.length}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Metadata</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="flex justify-between gap-3">
                <span className="text-gray-500">KA ID</span>
                <span className="rounded bg-gray-100 px-1 font-mono">{trace.ka_id || 'N/A'}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-gray-500">Created</span>
                <span className="font-medium">{formatDateTime(trace.created_at)}</span>
              </div>
              {trace.scores && (
                <>
                  <div className="flex justify-between gap-3">
                    <span className="text-gray-500">Confidence</span>
                    <span className="font-medium">{scoreToPercent(trace.scores.confidence)}</span>
                  </div>
                  <div className="flex justify-between gap-3">
                    <span className="text-gray-500">Bias Risk</span>
                    <span className="font-medium">{scoreToFixed(trace.scores.bias_risk)}</span>
                  </div>
                </>
              )}
              {metrics && (
                <>
                  <div className="flex justify-between gap-3">
                    <span className="text-gray-500">Stages</span>
                    <span className="font-medium">{formatCount(metrics.stage_count, stages.length)}</span>
                  </div>
                  <div className="flex justify-between gap-3">
                    <span className="text-gray-500">Duration</span>
                    <span className="font-medium">{formatMs(metrics.total_duration_ms)}</span>
                  </div>
                  <div className="flex justify-between gap-3">
                    <span className="text-gray-500">Retrievals</span>
                    <span className="font-medium">{formatCount(metrics.total_retrievals)}</span>
                  </div>
                </>
              )}
              {(trace.model_name || trace.provider_used) && (
                <>
                  <div className="mt-1 border-t border-white/5 pt-3" />
                  {trace.model_name && (
                    <div className="flex justify-between gap-3">
                      <span className="text-gray-500">Model</span>
                      <span className="font-mono text-xs">{trace.model_name}</span>
                    </div>
                  )}
                  {trace.provider_used && (
                    <div className="flex justify-between gap-3">
                      <span className="text-gray-500">Provider</span>
                      <span className="font-medium capitalize">{trace.provider_used}</span>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function TraceDetailPage() {
  return (
    <main className="min-h-screen bg-gray-50/50 p-6 dark:bg-gray-950 md:p-8">
      <Suspense fallback={<div className="p-8 text-center text-gray-500">Loading...</div>}>
        <TraceDetailContent />
      </Suspense>
    </main>
  );
}

'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Cpu,
  FileJson,
  Loader2,
  Play,
  RefreshCw,
  Search,
  Square,
} from 'lucide-react';

import { ConfirmationDialog } from '@/components/ConfirmationDialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  algorithms as algorithmsApi,
  isKATerminalStatus,
  request,
} from '@/lib/api';
import type {
  KAProductPlanEnvelope,
  KAProductRun,
} from '@/lib/api';

interface AlgorithmRecord {
  id: string;
  name: string;
  category?: string;
  purpose?: string;
  description?: string;
  notes?: string;
  risk_class?: string;
  status?: string;
  classification?: string;
  production_enabled?: boolean;
  deterministic?: boolean;
  guarantee?: string;
  limitations?: string;
  catalog_version?: string;
}

interface AlgorithmListResponse {
  algorithms?: AlgorithmRecord[];
  total_count?: number;
  manifest_version?: string;
}

interface RunEvidence {
  result?: Record<string, unknown>;
  trace?: Record<string, unknown>;
  artifacts?: Array<Record<string, unknown>>;
  effects?: Array<Record<string, unknown>>;
}

function algorithmDescription(entry: AlgorithmRecord): string {
  return (
    entry.purpose?.trim()
    || entry.description?.trim()
    || entry.notes?.trim()
    || 'No algorithm description is available.'
  );
}

const UNDECLARED = 'Not declared in manifest';

/**
 * A capability is executable only when the manifest admits it. KA-033 is a
 * reserved expansion slot and KA-Master is the controller authority with
 * self-selection disabled; planning either always fails server-side.
 */
function isExecutable(entry: AlgorithmRecord): boolean {
  return entry.production_enabled === true;
}

function notExecutableReason(entry: AlgorithmRecord): string {
  if (entry.classification === 'placeholder_not_production_enabled') {
    return 'Reserved slot - not admitted to production by the manifest.';
  }
  if (entry.id === 'KA-Master') {
    return 'Controller authority - self-selection is disabled by design.';
  }
  return 'Not production-enabled in the current manifest.';
}

function newIdempotencyKey(): string {
  return globalThis.crypto?.randomUUID?.()
    ?? `ka-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function formatJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

export default function AlgorithmsPage() {
  const [catalog, setCatalog] = useState<AlgorithmRecord[]>([]);
  const [recentRuns, setRecentRuns] = useState<KAProductRun[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<AlgorithmRecord | null>(null);
  const [workflowOpen, setWorkflowOpen] = useState(false);
  const [inputJson, setInputJson] = useState('{\n  "query": ""\n}');
  const [plan, setPlan] = useState<KAProductPlanEnvelope | null>(null);
  const [currentRun, setCurrentRun] = useState<KAProductRun | null>(null);
  const [evidence, setEvidence] = useState<RunEvidence>({});
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmationOpen, setConfirmationOpen] = useState(false);
  const [manifestVersion, setManifestVersion] = useState<string | null>(null);
  const [runsWarning, setRunsWarning] = useState<string | null>(null);
  const [pollExhausted, setPollExhausted] = useState(false);
  const pollCount = useRef(0);
  const initialRunHandled = useRef(false);
  const idempotencyKey = useRef(newIdempotencyKey());

  const loadRegistry = useCallback(async () => {
    setLoading(true);
    setError(null);
    const [catalogResult, runResult] = await Promise.allSettled([
      request<AlgorithmListResponse>('/ka/algorithms?per_page=300'),
      algorithmsApi.runs(10),
    ]);
    if (catalogResult.status === 'fulfilled') {
      setCatalog(catalogResult.value.algorithms || []);
      setManifestVersion(catalogResult.value.manifest_version ?? null);
    } else {
      setCatalog([]);
      setError(
        catalogResult.reason instanceof Error
          ? catalogResult.reason.message
          : 'Failed to load algorithm registry',
      );
    }
    if (runResult.status === 'fulfilled') {
      setRecentRuns(runResult.value.runs || []);
      setRunsWarning(null);
    } else {
      setRecentRuns([]);
      setRunsWarning(
        runResult.reason instanceof Error
          ? `Recent governed runs could not be loaded: ${runResult.reason.message}`
          : 'Recent governed runs could not be loaded.',
      );
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadRegistry();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadRegistry]);

  const filteredAlgorithms = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return catalog;
    return catalog.filter((entry) =>
      `${entry.id} ${entry.name} ${entry.category || ''} ${algorithmDescription(entry)}`
        .toLowerCase()
        .includes(needle),
    );
  }, [catalog, query]);

  const refreshRun = useCallback(async (runId: string) => {
    const status = await algorithmsApi.run(runId);
    setCurrentRun(status.run);
    setRecentRuns((existing) => [
      status.run,
      ...existing.filter((entry) => entry.run_id !== runId),
    ].slice(0, 10));
    if (!isKATerminalStatus(status.run.status)) {
      return;
    }
    const [result, trace, artifacts, effects] = await Promise.allSettled([
      algorithmsApi.result(runId),
      algorithmsApi.trace(runId),
      algorithmsApi.artifacts(runId),
      algorithmsApi.effects(runId),
    ]);
    setEvidence({
      ...(result.status === 'fulfilled' ? { result: result.value } : {}),
      ...(trace.status === 'fulfilled' ? { trace: trace.value } : {}),
      ...(artifacts.status === 'fulfilled' ? { artifacts: artifacts.value.artifacts } : {}),
      ...(effects.status === 'fulfilled' ? { effects: effects.value.effects } : {}),
    });
  }, []);

  const MAX_POLLS = 60;

  useEffect(() => {
    if (!currentRun || !['queued', 'running'].includes(currentRun.status)) {
      return;
    }
    if (pollCount.current >= MAX_POLLS) {
      setPollExhausted(true);
      return;
    }
    // Linear backoff caps automatic polling at roughly five minutes so a run
    // stuck in `running` cannot poll the backend indefinitely. Manual Refresh
    // stays available after the cap.
    const attempt = pollCount.current;
    const delay = Math.min(1000 + attempt * 250, 5000);
    const timer = globalThis.setTimeout(() => {
      pollCount.current += 1;
      void refreshRun(currentRun.run_id).catch(() => undefined);
    }, delay);
    return () => globalThis.clearTimeout(timer);
  }, [currentRun, refreshRun]);

  function openWorkflow(entry: AlgorithmRecord) {
    setSelected(entry);
    setWorkflowOpen(true);
    setInputJson('{\n  "query": ""\n}');
    setPlan(null);
    setCurrentRun(null);
    setEvidence({});
    setWorkflowError(null);
    pollCount.current = 0;
    setPollExhausted(false);
    idempotencyKey.current = newIdempotencyKey();
  }

  function editRequest() {
    setPlan(null);
    setCurrentRun(null);
    setEvidence({});
    setWorkflowError(null);
    pollCount.current = 0;
    setPollExhausted(false);
    idempotencyKey.current = newIdempotencyKey();
  }

  async function createPlan() {
    if (!selected) return;
    setBusy(true);
    setWorkflowError(null);
    try {
      const parsed = JSON.parse(inputJson) as unknown;
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        throw new TypeError('Algorithm input must be a JSON object.');
      }
      const response = await algorithmsApi.plan({
        ka_id: selected.id,
        input: parsed as Record<string, unknown>,
        idempotency_key: idempotencyKey.current,
        mode: selected.production_enabled ? 'production' : 'evaluation',
        metadata: { client_surface: 'desktop_algorithms' },
      });
      setPlan(response);
      setCurrentRun(response.run);
      setEvidence({});
    } catch (caught) {
      setWorkflowError(
        caught instanceof Error ? caught.message : 'The execution plan could not be created.',
      );
    } finally {
      setBusy(false);
    }
  }

  async function executePlan() {
    if (!plan) return;
    setBusy(true);
    setWorkflowError(null);
    try {
      const response = await algorithmsApi.execute(
        plan.run.run_id,
        plan.confirmation_token,
      );
      setCurrentRun(response.run);
      setRecentRuns((existing) => [
        response.run,
        ...existing.filter((entry) => entry.run_id !== response.run.run_id),
      ].slice(0, 10));
    } catch (caught) {
      setWorkflowError(
        caught instanceof Error ? caught.message : 'The algorithm run could not be queued.',
      );
    } finally {
      setBusy(false);
    }
  }

  async function cancelRun() {
    if (!currentRun) return;
    setBusy(true);
    setWorkflowError(null);
    try {
      const response = await algorithmsApi.cancel(currentRun.run_id);
      setCurrentRun(response.run);
    } catch (caught) {
      setWorkflowError(
        caught instanceof Error ? caught.message : 'The algorithm run could not be cancelled.',
      );
    } finally {
      setBusy(false);
    }
  }

  const inspectRun = useCallback(async (run: KAProductRun) => {
    setWorkflowOpen(true);
    setSelected(catalog.find((entry) => entry.id === run.canonical_id) ?? {
      id: run.canonical_id,
      name: run.canonical_id,
    });
    setPlan(null);
    setCurrentRun(run);
    setEvidence({});
    setWorkflowError(null);
    pollCount.current = 0;
    setPollExhausted(false);
    setBusy(true);
    await refreshRun(run.run_id)
      .catch((caught) => {
        setWorkflowError(
          caught instanceof Error ? caught.message : 'The run could not be refreshed.',
        );
      })
      .finally(() => setBusy(false));
  }, [catalog, refreshRun]);

  const canCancel = currentRun
    && ['planned', 'queued', 'running'].includes(currentRun.status);

  useEffect(() => {
    if (initialRunHandled.current || loading) return;
    const requestedRunId = new URLSearchParams(globalThis.location?.search ?? '').get('run');
    if (!requestedRunId) {
      initialRunHandled.current = true;
      return;
    }
    initialRunHandled.current = true;
    void algorithmsApi.run(requestedRunId).then(
      ({ run }) => inspectRun(run),
    ).catch((caught) => {
      setWorkflowError(
        caught instanceof Error ? caught.message : 'The run could not be refreshed.',
      );
      setWorkflowOpen(true);
    });
  }, [inspectRun, loading]);

  return (
    <div className="min-h-full bg-background text-foreground font-sans">
      <div className="min-h-full bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed">
        <div className="h-16 border-b border-white/5 fluent-acrylic sticky top-0 z-10 flex items-center justify-between px-8 backdrop-blur-3xl">
          <div className="flex items-center gap-3">
            <div className="bg-amber-500/10 p-2 rounded-lg border border-amber-500/20">
              <Cpu className="h-5 w-5 text-amber-400" />
            </div>
            <div>
              <h1 className="text-title font-bold text-slate-900 dark:text-gray-100">Algorithm Registry</h1>
              <div className="text-[10px] text-slate-500 dark:text-gray-500 font-mono uppercase tracking-widest">
                Plan, confirm, execute, cancel, and inspect canonical KA runs
                {manifestVersion && <span> · manifest {manifestVersion}</span>}
              </div>
            </div>
          </div>
          <div className="relative w-64">
            <Search
              className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 dark:text-gray-500"
              aria-hidden="true"
            />
            <Input
              aria-label="Search algorithms"
              placeholder="Search algorithms..."
              className="pl-9 h-9 bg-white/70 dark:bg-black/20 border-slate-200 dark:border-white/10 text-sm"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>
        </div>

        <div className="max-w-[1600px] w-full mx-auto p-8 space-y-8 animate-connected-enter">
          {error && (
            <Card className="border-red-500/30 bg-red-500/10">
              <CardContent className="p-4 text-sm text-red-600 dark:text-red-300">{error}</CardContent>
            </Card>
          )}

          {runsWarning && (
            <Card className="border-amber-500/30 bg-amber-500/10">
              <CardContent className="p-4 text-sm text-amber-700 dark:text-amber-300" role="status">
                {runsWarning}
              </CardContent>
            </Card>
          )}

          {recentRuns.length > 0 && (
            <Card className="fluent-card">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <CardTitle className="text-base">Recent governed runs</CardTitle>
                    <CardDescription>Principal-owned plans and executions from the durable KA ledger.</CardDescription>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => void loadRegistry()}>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                {recentRuns.map((run) => (
                  <Button
                    key={run.run_id}
                    variant="outline"
                    size="sm"
                    onClick={() => void inspectRun(run)}
                  >
                    <span className="font-mono">{run.canonical_id}</span>
                    <Badge variant="secondary" className="ml-2">{run.status}</Badge>
                  </Button>
                ))}
              </CardContent>
            </Card>
          )}

          {loading && (
            <Card className="fluent-card">
              <CardContent className="p-6 text-sm text-muted-foreground">
                Loading algorithm registry...
              </CardContent>
            </Card>
          )}

          {!loading && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredAlgorithms.map((entry) => (
                <Card key={entry.id} className="fluent-card hover:-translate-y-1 group">
                  <CardHeader>
                    <div className="flex justify-between items-start mb-2">
                      <Badge variant="outline" className="font-mono text-xs bg-white/70 dark:bg-white/5 border-slate-200 dark:border-white/10">
                        {entry.id}
                      </Badge>
                      {entry.risk_class ? (
                        <Badge
                          variant="secondary"
                          className="bg-amber-500/10 text-amber-400 border-amber-500/20 text-[10px] font-bold uppercase"
                        >
                          Risk: {entry.risk_class}
                        </Badge>
                      ) : (
                        <Badge
                          variant="outline"
                          className="text-[10px] font-medium text-slate-500 dark:text-gray-500 border-dashed"
                          title="The manifest contract declares no risk class for this capability."
                        >
                          Risk {UNDECLARED.toLowerCase()}
                        </Badge>
                      )}
                    </div>
                    <CardTitle className="text-lg text-slate-900 dark:text-gray-100 group-hover:text-blue-400 transition-colors">
                      {entry.name}
                    </CardTitle>
                    <CardDescription className="text-slate-500 dark:text-gray-500">
                      {entry.category || <span className="italic">Category {UNDECLARED.toLowerCase()}</span>}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex flex-wrap gap-2">
                      <Badge variant={entry.production_enabled ? 'default' : 'outline'}>
                        {entry.production_enabled ? 'Production enabled' : 'Evaluation only'}
                      </Badge>
                      {entry.classification && (
                        <Badge variant="outline">{entry.classification.replaceAll('_', ' ')}</Badge>
                      )}
                    </div>
                    <p className="text-sm text-slate-600 dark:text-gray-400">
                      {algorithmDescription(entry)}
                    </p>
                    {entry.guarantee && (
                      <p className="text-xs text-slate-700 dark:text-gray-300">
                        <span className="font-semibold">Guarantee:</span> {entry.guarantee}
                      </p>
                    )}
                    {entry.limitations && (
                      <p className="text-xs text-slate-500 dark:text-gray-500">
                        <span className="font-semibold">Limit:</span> {entry.limitations}
                      </p>
                    )}
                    {isExecutable(entry) ? (
                      <Button className="w-full" onClick={() => openWorkflow(entry)}>
                        <Play className="h-4 w-4 mr-2" />
                        Plan and run
                      </Button>
                    ) : (
                      <div className="space-y-1">
                        <Button
                          className="w-full"
                          disabled
                          title={notExecutableReason(entry)}
                        >
                          <Play className="h-4 w-4 mr-2" />
                          Not executable
                        </Button>
                        <p className="text-xs text-slate-500 dark:text-gray-500">
                          {notExecutableReason(entry)}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
              {!error && filteredAlgorithms.length === 0 && (
                <Card className="col-span-full fluent-card flex items-center justify-center p-8 border-dashed">
                  <p className="text-slate-500 dark:text-gray-400 text-sm text-center">
                    No algorithms matched your filters.
                  </p>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>

      <Dialog open={workflowOpen} onOpenChange={setWorkflowOpen}>
        <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selected ? `${selected.id} · ${selected.name}` : 'Knowledge Algorithm run'}
            </DialogTitle>
            <DialogDescription>
              The server derives authority, dependencies, policy, budget, and confirmation from the canonical manifest.
            </DialogDescription>
          </DialogHeader>

          {workflowError && (
            <div role="alert" className="rounded border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-600 dark:text-red-300">
              {workflowError}
            </div>
          )}

          {!currentRun && (
            <div className="space-y-2">
              <Label htmlFor="ka-input">Algorithm input (JSON object)</Label>
              <textarea
                id="ka-input"
                className="min-h-44 w-full rounded-md border bg-background p-3 font-mono text-sm"
                value={inputJson}
                onChange={(event) => {
                  setInputJson(event.target.value);
                  idempotencyKey.current = newIdempotencyKey();
                }}
                spellCheck={false}
              />
            </div>
          )}

          {plan && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Reviewed execution plan</CardTitle>
                <CardDescription className="font-mono text-xs">{plan.plan.plan_id}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex flex-wrap gap-2">
                  <Badge>{plan.plan.risk.tier.replaceAll('_', ' ')}</Badge>
                  <Badge variant="outline">{plan.plan.selected_count} selected</Badge>
                  <Badge variant="outline">{plan.plan.dependency_count} dependencies</Badge>
                  <Badge variant="outline">{plan.plan.effect_proposal_count} effect proposals</Badge>
                </div>
                <p><span className="font-semibold">Selected:</span> {plan.plan.selected_ids.join(', ')}</p>
                {plan.plan.validation_errors.length > 0 && (
                  <p className="text-red-500">{plan.plan.validation_errors.join('; ')}</p>
                )}
              </CardContent>
            </Card>
          )}

          {currentRun && (
            <div className="space-y-4" aria-live="polite">
              <Card>
                <CardContent className="pt-5 space-y-2 text-sm">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge>{currentRun.status}</Badge>
                    <Badge variant="outline">{currentRun.risk_tier.replaceAll('_', ' ')}</Badge>
                    <span className="font-mono text-xs text-muted-foreground">{currentRun.run_id}</span>
                    {['queued', 'running'].includes(currentRun.status) && (
                      <Loader2 className="h-4 w-4 animate-spin" aria-label="Run in progress" />
                    )}
                  </div>
                  {currentRun.error_message && (
                    <p className="text-red-500">{currentRun.error_message}</p>
                  )}
                  {pollExhausted && (
                    <p className="text-amber-600 dark:text-amber-400" role="status">
                      Automatic status polling stopped after the retry limit. Use Refresh to check again.
                    </p>
                  )}
                </CardContent>
              </Card>

              {Object.keys(evidence).length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <FileJson className="h-4 w-4" />
                      Result and evidence
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {evidence.result && (
                      <details open>
                        <summary className="cursor-pointer font-medium">Result</summary>
                        <pre className="mt-2 max-h-72 overflow-auto rounded bg-muted p-3 text-xs">
                          {formatJson(evidence.result)}
                        </pre>
                      </details>
                    )}
                    {evidence.trace && (
                      <details>
                        <summary className="cursor-pointer font-medium">Trace</summary>
                        <pre className="mt-2 max-h-72 overflow-auto rounded bg-muted p-3 text-xs">
                          {formatJson(evidence.trace)}
                        </pre>
                      </details>
                    )}
                    <details>
                      <summary className="cursor-pointer font-medium">
                        Artifacts ({evidence.artifacts?.length ?? 0})
                      </summary>
                      <pre className="mt-2 max-h-72 overflow-auto rounded bg-muted p-3 text-xs">
                        {formatJson(evidence.artifacts ?? [])}
                      </pre>
                    </details>
                    <details>
                      <summary className="cursor-pointer font-medium">
                        Effects ({evidence.effects?.length ?? 0})
                      </summary>
                      <pre className="mt-2 max-h-72 overflow-auto rounded bg-muted p-3 text-xs">
                        {formatJson(evidence.effects ?? [])}
                      </pre>
                    </details>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          <DialogFooter className="flex-wrap gap-2">
            {!currentRun && (
              <Button onClick={() => void createPlan()} disabled={busy}>
                {busy && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Review execution plan
              </Button>
            )}
            {plan && currentRun?.status === 'planned' && (
              <Button
                onClick={() => {
                  if (currentRun.confirmation_required) {
                    setConfirmationOpen(true);
                  } else {
                    void executePlan();
                  }
                }}
                disabled={busy || !plan.plan.valid}
              >
                <Play className="h-4 w-4 mr-2" />
                {currentRun.confirmation_required ? 'Confirm and execute' : 'Execute plan'}
              </Button>
            )}
            {currentRun && (
              <Button
                variant="outline"
                onClick={() => void refreshRun(currentRun.run_id)}
                disabled={busy}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            )}
            {canCancel && (
              <Button variant="destructive" onClick={() => void cancelRun()} disabled={busy}>
                <Square className="h-4 w-4 mr-2" />
                Cancel run
              </Button>
            )}
            {currentRun && isKATerminalStatus(currentRun.status) && (
              <Button variant="outline" onClick={editRequest} disabled={busy}>
                Edit request and create a new plan
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmationDialog
        open={confirmationOpen}
        onOpenChange={setConfirmationOpen}
        onConfirm={() => void executePlan()}
        title="Confirm the exact KA execution plan"
        description={
          plan
            ? `Execute ${plan.plan.selected_ids.join(', ')} using plan ${plan.plan.plan_id}. Any manifest change invalidates this confirmation.`
            : 'Confirm this exact Knowledge Algorithm plan.'
        }
        riskTier={plan?.plan.risk.tier ?? 'write'}
        confirmLabel="Confirm exact plan"
      />
    </div>
  );
}

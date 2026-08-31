'use client';

import Link from 'next/link';
import { useState } from 'react';
import useSWR from 'swr';
import { AlertTriangle, BarChart3, ExternalLink } from 'lucide-react';
import { api } from '@/lib/api';
import type { TraceAnalytics, TraceAnalyticsFilters, TraceAnalyticsRun } from '@/lib/api/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

function measuredPercent(value?: number | null): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'Not measured';
  const normalized = value <= 1 ? value * 100 : value;
  return `${normalized.toFixed(1)}%`;
}

function readable(value?: string | null): string {
  if (!value) return 'Not recorded';
  return value.replace(/_/g, ' ');
}

function runTime(value?: string | null): string {
  if (!value) return 'Unknown time';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? 'Unknown time' : parsed.toLocaleString();
}

function MetricCard({ title, value, detail }: { title: string; value: string; detail: string }) {
  return (
    <Card className="fluent-card">
      <CardHeader className="pb-2">
        <CardDescription>{title}</CardDescription>
        <CardTitle className="text-2xl">{value}</CardTitle>
      </CardHeader>
      <CardContent className="text-xs text-slate-500 dark:text-slate-400">{detail}</CardContent>
    </Card>
  );
}

function RunRow({ run }: { run: TraceAnalyticsRun }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white/70 p-4 dark:border-white/10 dark:bg-white/5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border px-2 py-0.5 text-xs font-medium capitalize">{readable(run.status)}</span>
            <span className="text-xs text-slate-500 dark:text-slate-400">{runTime(run.created_at)}</span>
          </div>
          <p className="mt-2 break-all font-mono text-xs text-slate-600 dark:text-slate-300">{run.run_id}</p>
          <p className="mt-1 text-sm text-slate-700 dark:text-slate-200">
            {run.provider || 'Provider not recorded'} / {run.model || 'Model not recorded'} · {run.mode || 'Mode not recorded'}
          </p>
        </div>
        <Link
          href={run.detail_url}
          className="inline-flex min-h-10 items-center justify-center gap-2 rounded-lg border border-purple-500/30 px-3 text-sm font-medium text-purple-700 hover:bg-purple-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500 dark:text-purple-300"
        >
          Open trace <ExternalLink className="h-4 w-4" aria-hidden="true" />
        </Link>
      </div>
      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
        <div><dt className="text-xs text-slate-500">Confidence</dt><dd>{measuredPercent(run.confidence)}</dd></div>
        <div><dt className="text-xs text-slate-500">Tokens</dt><dd>{run.token_cost ?? 'Not measured'}</dd></div>
        <div><dt className="text-xs text-slate-500">Evidence</dt><dd>{run.evidence_count} evidence links</dd></div>
        <div><dt className="text-xs text-slate-500">Refinement</dt><dd className="capitalize">{readable(run.refinement.status)}</dd></div>
      </dl>
    </article>
  );
}

export default function AnalyticsPage() {
  const [days, setDays] = useState(30);
  const [status, setStatus] = useState('');
  const [mode, setMode] = useState('');
  const [provider, setProvider] = useState('');
  const [scope, setScope] = useState<'principal' | 'all'>('principal');
  const filters: TraceAnalyticsFilters = {
    days,
    limit: 50,
    status: status || undefined,
    mode: mode || undefined,
    provider: provider || undefined,
    scope,
  };
  const { data, error, isLoading } = useSWR<TraceAnalytics>(
    ['trace-analytics', days, status, mode, provider, scope],
    () => api.trace.analytics(filters),
  );

  return (
    <div className="min-h-full bg-background text-foreground">
      <header className="sticky top-0 z-10 flex min-h-16 items-center border-b border-white/5 px-4 backdrop-blur-3xl sm:px-8">
        <div className="flex items-center gap-3">
          <div className="rounded-lg border border-purple-500/20 bg-purple-500/10 p-2">
            <BarChart3 className="h-5 w-5 text-purple-500" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-title font-bold">Analytics</h1>
            <p className="text-xs text-slate-500">Persisted governed-run authority</p>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-[1600px] space-y-6 p-4 sm:p-8">
        <Card className="fluent-card">
          <CardHeader>
            <CardTitle>Trace filters</CardTitle>
            <CardDescription>All values come from saved run traces. Filters are limited to the selected local time window.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
            <label className="space-y-1 text-sm">Time range
              <select value={days} onChange={(event) => setDays(Number(event.target.value))} className="mt-1 min-h-10 w-full rounded-lg border bg-background px-3">
                <option value={7}>Last 7 days</option><option value={30}>Last 30 days</option><option value={90}>Last 90 days</option>
              </select>
            </label>
            <label className="space-y-1 text-sm">Run status
              <select value={status} onChange={(event) => setStatus(event.target.value)} className="mt-1 min-h-10 w-full rounded-lg border bg-background px-3">
                <option value="">All statuses</option><option value="completed">Completed</option><option value="failed">Failed</option><option value="blocked">Blocked</option><option value="running">Running</option>
              </select>
            </label>
            <label className="space-y-1 text-sm">Execution mode
              <select value={mode} onChange={(event) => setMode(event.target.value)} className="mt-1 min-h-10 w-full rounded-lg border bg-background px-3">
                <option value="">All modes</option><option value="governed">Governed</option><option value="standard">Standard</option>
              </select>
            </label>
            <label className="space-y-1 text-sm">Provider
              <select value={provider} onChange={(event) => setProvider(event.target.value)} className="mt-1 min-h-10 w-full rounded-lg border bg-background px-3">
                <option value="">All providers</option><option value="google">Google</option><option value="openai">OpenAI</option><option value="local">Local</option>
              </select>
            </label>
            <label className="space-y-1 text-sm">Visibility
              <select value={scope} onChange={(event) => setScope(event.target.value as 'principal' | 'all')} className="mt-1 min-h-10 w-full rounded-lg border bg-background px-3">
                <option value="principal">My runs</option><option value="all">All owner-visible runs</option>
              </select>
            </label>
          </CardContent>
        </Card>

        {error && (
          <Card className="border-red-500/30 bg-red-500/10" role="alert">
            <CardContent className="flex gap-3 p-4 text-sm text-red-700 dark:text-red-200">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <div><strong>Analytics authority is unavailable.</strong> No missing value is being represented as zero. {error instanceof Error ? error.message : ''}</div>
            </CardContent>
          </Card>
        )}

        {isLoading && !data && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4" aria-label="Loading analytics">
            {[0, 1, 2, 3].map((item) => <Skeleton key={item} className="h-32 w-full" />)}
          </div>
        )}

        {data && !error && (
          <>
            {data.partial && (
              <Card className="border-amber-500/30 bg-amber-500/10" role="status">
                <CardContent className="p-4 text-sm">This is a partial view: the bounded scan limit was reached. Narrow the filters for a complete result.</CardContent>
              </Card>
            )}
            <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4" aria-label="Trace analytics summary">
              <MetricCard title="Runs" value={String(data.summary.run_count)} detail={`${days}-day observed window`} />
              <MetricCard title="Average confidence" value={measuredPercent(data.summary.confidence.average)} detail={`${data.summary.confidence.measured_runs} measured runs`} />
              <MetricCard title="Tokens" value={data.summary.tokens.total?.toLocaleString() ?? 'Not measured'} detail={`${data.summary.tokens.measured_runs} measured runs`} />
              <MetricCard title="Evidence links" value={String(data.summary.evidence.total)} detail="Counted from persisted trace evidence" />
            </section>

            <Card className="fluent-card">
              <CardHeader>
                <CardTitle>Observed governed runs</CardTitle>
                <CardDescription>Open a run to review its complete saved trace.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {data.runs.length === 0 ? (
                  <p className="rounded-lg border border-dashed p-6 text-center text-sm text-slate-500">No governed runs match these filters.</p>
                ) : data.runs.map((run) => <RunRow key={run.run_id} run={run} />)}
              </CardContent>
            </Card>
          </>
        )}
      </main>
    </div>
  );
}

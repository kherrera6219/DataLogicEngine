'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  ExternalLink,
  RefreshCw,
  XCircle,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { PageLayout } from '@/components/ui/page-layout';
import { algorithms } from '@/lib/api';
import type { KAProductRun } from '@/lib/api';

const TIER_BADGE: Record<string, { label: string; class: string }> = {
  read_only: { label: 'Read-only', class: 'border-blue-500/40 text-blue-400' },
  write: { label: 'Write', class: 'border-yellow-500/40 text-yellow-500' },
  destructive: { label: 'Destructive', class: 'border-red-500/40 text-red-500' },
};

const SUCCESS_STATES = new Set(['succeeded', 'partial', 'dry_run']);
const FAILURE_STATES = new Set(['failed', 'timed_out', 'expired']);

function statusIcon(status: string) {
  if (SUCCESS_STATES.has(status)) {
    return <CheckCircle2 className="h-4 w-4 text-green-500" />;
  }
  if (FAILURE_STATES.has(status)) {
    return <XCircle className="h-4 w-4 text-red-500" />;
  }
  return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
}

function formatTimestamp(value?: string | null): string {
  if (!value) return 'Unknown time';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Unknown time' : date.toLocaleString();
}

function formatDuration(run: KAProductRun): string | null {
  if (!run.started_at || !run.completed_at) return null;
  const started = new Date(run.started_at).getTime();
  const completed = new Date(run.completed_at).getTime();
  if (!Number.isFinite(started) || !Number.isFinite(completed)) return null;
  return `${Math.max(0, Math.round(completed - started))}ms`;
}

export default function ToolExecutionHistoryPage() {
  const [runs, setRuns] = useState<KAProductRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await algorithms.runs(100);
      setRuns(data.runs ?? []);
    } catch {
      setError('Failed to load governed Knowledge Algorithm run history.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  return (
    <PageLayout
      title="Tool Execution History"
      description="Principal-owned plans and executions from the durable Knowledge Algorithm ledger."
      breadcrumbs={[
        { label: 'Dashboard', href: '/dashboard' },
        { label: 'Tools', href: '/tools' },
        { label: 'History' },
      ]}
    >
      <div className="flex justify-end mb-4">
        <Button variant="outline" size="sm" onClick={() => void load()} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <Card role="alert" className="border-destructive bg-destructive/5 mb-4">
          <CardContent className="pt-4 text-sm text-destructive">{error}</CardContent>
        </Card>
      )}

      {!loading && runs.length === 0 && !error && (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground text-sm">
            No governed Knowledge Algorithm runs recorded yet.
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {runs.map((run) => {
          const tierBadge = TIER_BADGE[run.risk_tier] ?? TIER_BADGE.read_only;
          const duration = formatDuration(run);
          return (
            <Card key={run.run_id} className="border-premium">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    {statusIcon(run.status)}
                    <CardTitle className="text-sm font-mono">{run.canonical_id}</CardTitle>
                    <span className="text-xs font-mono text-muted-foreground">{run.run_id}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge variant="outline" className={`text-[10px] ${tierBadge.class}`}>
                      {tierBadge.label}
                    </Badge>
                    <Badge variant="outline" className="text-[10px]">
                      {run.status}
                    </Badge>
                  </div>
                </div>
                <CardDescription className="flex items-center gap-3 text-xs pt-1">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatTimestamp(run.created_at)}
                  </span>
                  {duration && <span>{duration}</span>}
                  <span>{run.mode}</span>
                  {run.confirmation_required && (
                    <span>{run.confirmed ? 'confirmed' : 'confirmation required'}</span>
                  )}
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0 space-y-2">
                {run.error_message && (
                  <p className="text-xs text-red-400 bg-red-500/10 rounded p-2">
                    {run.error_message}
                  </p>
                )}
                <Link
                  href={`/algorithms?run=${encodeURIComponent(run.run_id)}`}
                  className="flex items-center gap-1 text-xs text-blue-400 hover:underline"
                >
                  <ExternalLink className="h-3 w-3" />
                  Inspect governed run
                </Link>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </PageLayout>
  );
}

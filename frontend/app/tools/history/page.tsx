'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { Clock, CheckCircle2, XCircle, AlertTriangle, ExternalLink, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { PageLayout } from '@/components/ui/page-layout';
import { request } from '@/lib/api';
import type { ToolExecutionHistoryItem, ToolExecutionHistoryResponse } from '@/lib/api/types';

const TIER_BADGE: Record<string, { label: string; class: string }> = {
  read_only: { label: 'Read-only', class: 'border-blue-500/40 text-blue-400' },
  write:     { label: 'Write',     class: 'border-yellow-500/40 text-yellow-500' },
  destructive: { label: 'Destructive', class: 'border-red-500/40 text-red-500' },
};

const STATUS_ICON: Record<string, React.ReactNode> = {
  success: <CheckCircle2 className="h-4 w-4 text-green-500" />,
  failure: <XCircle className="h-4 w-4 text-red-500" />,
  blocked: <AlertTriangle className="h-4 w-4 text-yellow-500" />,
};

function formatTimestamp(value?: string | null): string {
  if (!value) return 'Unknown time';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Unknown time' : date.toLocaleString();
}

function formatDuration(value?: number | null): string | null {
  if (typeof value !== 'number' || !Number.isFinite(value)) return null;
  return `${Math.max(0, Math.round(value))}ms`;
}

export default function ToolExecutionHistoryPage() {
  const [executions, setExecutions] = useState<ToolExecutionHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await request<ToolExecutionHistoryResponse>('/ka/history');
      setExecutions(data.executions ?? []);
    } catch {
      setError('Failed to load tool execution history.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function init() {
      await load();
      if (cancelled) return;
    }
    void init();
    return () => { cancelled = true; };
  }, [load]);

  return (
    <PageLayout
      title="Tool Execution History"
      description="Audit log of every Knowledge Algorithm invocation."
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
        <Card className="border-destructive bg-destructive/5 mb-4">
          <CardContent className="pt-4 text-sm text-destructive">{error}</CardContent>
        </Card>
      )}

      {!loading && executions.length === 0 && !error && (
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground text-sm">
            No tool executions recorded yet.
          </CardContent>
        </Card>
      )}

      <div className="space-y-3">
        {executions.map((exec) => {
          const tierBadge = TIER_BADGE[exec.risk_tier] ?? TIER_BADGE.read_only;
          const status = exec.status || 'blocked';
          const duration = formatDuration(exec.duration_ms);
          const triggeredBy = exec.triggered_by || 'user';
          return (
            <Card key={exec.id} className="border-premium">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    {STATUS_ICON[status] ?? STATUS_ICON.blocked}
                    <CardTitle className="text-sm font-mono">
                      {exec.ka_id}
                    </CardTitle>
                    <span className="text-sm text-muted-foreground">{exec.ka_name || exec.ka_id}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge variant="outline" className={`text-[10px] ${tierBadge.class}`}>
                      {tierBadge.label}
                    </Badge>
                    <Badge
                      variant="outline"
                      className={`text-[10px] ${
                        status === 'success'
                          ? 'border-green-500/40 text-green-500'
                          : status === 'blocked'
                          ? 'border-yellow-500/40 text-yellow-500'
                          : 'border-red-500/40 text-red-500'
                      }`}
                    >
                      {status}
                    </Badge>
                  </div>
                </div>
                <CardDescription className="flex items-center gap-3 text-xs pt-1">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatTimestamp(exec.created_at)}
                  </span>
                  {duration && (
                    <span>{duration}</span>
                  )}
                  <span>by {triggeredBy}</span>
                </CardDescription>
              </CardHeader>
              {(exec.error || exec.run_id) && (
                <CardContent className="pt-0 space-y-2">
                  {exec.error && (
                    <p className="text-xs text-red-400 bg-red-500/10 rounded p-2">{exec.error}</p>
                  )}
                  {exec.run_id && (
                    <Link
                      href={`/runs/view?id=${exec.run_id}`}
                      className="flex items-center gap-1 text-xs text-blue-400 hover:underline"
                    >
                      <ExternalLink className="h-3 w-3" />
                      View trace run
                    </Link>
                  )}
                </CardContent>
              )}
            </Card>
          );
        })}
      </div>
    </PageLayout>
  );
}

'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, type TraceRun } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge, type BadgeProps } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { PageLayout } from '@/components/ui/page-layout';

function formatTraceDate(value?: string | null): string {
  if (!value) return 'Unknown time';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Unknown time' : date.toLocaleString();
}

function shortRunId(value?: string | null): string {
  return value ? value.slice(0, 8) : 'unknown';
}

function statusVariant(status?: string | null): BadgeProps['variant'] {
  const normalized = status?.toLowerCase();
  if (normalized === 'pass' || normalized === 'completed' || normalized === 'success') return 'success';
  if (normalized === 'fail' || normalized === 'failed' || normalized === 'error') return 'destructive';
  return 'secondary';
}

function statusLabel(status?: string | null): string {
  return status || 'unknown';
}

export default function TraceRunsPage() {
  const [runs, setRuns] = useState<TraceRun[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    api.trace.list(20)
      .then((data) => {
        if (!mounted) return;
        setRuns(data || []);
        setError(null);
        setIsLoading(false);
      })
      .catch(() => {
        if (!mounted) return;
        setError('Trace list is unavailable.');
        setIsLoading(false);
      });
    return () => { mounted = false; };
  }, []);

  return (
    <PageLayout
      title="Trace History"
      description="Recent system reasoning traces and execution logs."
      breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'System Traces' }]}
    >
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Trace Explorer</h1>
        <p className="text-gray-500">Detailed execution logs of Knowledge Algorithms.</p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Recent Execution Runs</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Run ID</TableHead>
                <TableHead>Algorithm (KA)</TableHead>
                <TableHead>Start Time</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Model / Tier</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading && (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center text-gray-500">
                    Loading traces...
                  </TableCell>
                </TableRow>
              )}
              {!isLoading && error && (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center text-red-600">
                    {error}
                  </TableCell>
                </TableRow>
              )}
              {!isLoading && !error && runs.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center text-gray-500">
                    No traces found.
                  </TableCell>
                </TableRow>
              )}
              {runs.map((run, index) => {
                const runId = run.run_id || '';
                return (
                  <TableRow key={runId || `trace-row-${index}` }>
                    <TableCell className="font-mono text-xs">{shortRunId(runId)}</TableCell>
                    <TableCell>{run.ka_id || 'N/A'}</TableCell>
                    <TableCell className="text-gray-500">{formatTraceDate(run.created_at)}</TableCell>
                    <TableCell>
                      <Badge variant={statusVariant(run.status)}>{statusLabel(run.status)}</Badge>
                    </TableCell>
                    <TableCell>
                      {run.model_name ? (
                        <span className="font-mono text-xs text-muted-foreground">{run.model_name}</span>
                      ) : (
                        <span className="text-xs text-muted-foreground">N/A</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      {runId ? (
                        <Button size="sm" variant="outline" asChild>
                          <Link href={`/runs/view?id=${encodeURIComponent(runId)}`}>View Trace</Link>
                        </Button>
                      ) : (
                        <Button size="sm" variant="outline" disabled>Unavailable</Button>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </PageLayout>
  );
}
